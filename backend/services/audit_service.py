"""Audit log write API + @audited decorator.

Design contract:
  - `log_event` is the ONLY sanctioned public writer.
  - It is defensive: audit write failures must NEVER break the real request.
    (We swallow exceptions and emit a backend log instead, because a failed
     audit must not mask a failed ACK, for example.)
  - `@audited` wraps Flask view functions. It records the response status
    and swallowed exceptions; the wrapped view's return value is untouched.
  - Request metadata (ip, UA, user) is pulled from Flask's request/g.

On PostgreSQL, an AFTER-UPDATE / AFTER-DELETE trigger (installed by Alembic
migration 0003) raises an exception, enforcing append-only at the DB layer.
SQLite does not need the trigger — dev tests only.
"""
from __future__ import annotations

import json
import logging
from functools import wraps
from typing import Any, Callable

from flask import g, request

from backend.extensions import db
from backend.models.audit_log import AuditLog

logger = logging.getLogger('audit')


def _actor_snapshot() -> dict[str, Any]:
    """Extract the current actor (if any) from Flask's g."""
    user = getattr(g, 'current_user', None)
    if user is None:
        return {'actor_id': None, 'actor_username': None, 'actor_role': None}
    return {
        'actor_id': getattr(user, 'id', None),
        'actor_username': getattr(user, 'username', None),
        'actor_role': getattr(user, 'role', None),
    }


def _request_snapshot() -> dict[str, Any]:
    """Extract request metadata; degrade gracefully outside a request."""
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr) or None
        ua = (request.user_agent.string or None) if request.user_agent else None
        req_id = request.headers.get('X-Request-Id') or None
    except RuntimeError:
        ip = ua = req_id = None
    return {'ip': ip, 'user_agent': ua, 'request_id': req_id}


def _safe_meta(meta: Any) -> str:
    if meta is None:
        return '{}'
    if isinstance(meta, str):
        return meta
    try:
        return json.dumps(meta, default=str)[:8000]
    except (TypeError, ValueError):
        return json.dumps({'_serialize_error': True})


def log_event(
    action: str,
    *,
    target_type: str | None = None,
    target_id: str | int | None = None,
    status: str = 'ok',
    meta: Any = None,
) -> AuditLog | None:
    """Append an audit row. Returns the row, or None on swallowed failure."""
    try:
        row = AuditLog(
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            status=status,
            meta=_safe_meta(meta),
            **_actor_snapshot(),
            **_request_snapshot(),
        )
        db.session.add(row)
        db.session.commit()
        try:
            from backend.observability import record_audit_event
            record_audit_event(action)
        except Exception:
            pass
        return row
    except Exception as exc:
        try:
            db.session.rollback()
        except Exception:
            pass
        logger.warning('audit write failed: action=%s target=%s:%s err=%s',
                       action, target_type, target_id, exc)
        return None


def _resolve_target_id(kwargs: dict, target_id_from: str | None) -> str | None:
    if not target_id_from:
        return None
    val = kwargs.get(target_id_from)
    return str(val) if val is not None else None


def audited(
    action: str,
    *,
    target_type: str | None = None,
    target_id_from: str | None = None,
) -> Callable:
    """Decorator: log an audit entry after the view returns.

    Args:
        action: Free-form verb, e.g. ``user.create``, ``alert.resolve``.
        target_type: Static label for the thing being acted on.
        target_id_from: Name of the Flask route kwarg that holds the target id.
            e.g. ``'user_id'`` for ``/users/<int:user_id>``.
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:
                log_event(
                    action,
                    target_type=target_type,
                    target_id=_resolve_target_id(kwargs, target_id_from),
                    status='error',
                    meta={'error': str(exc)[:500]},
                )
                raise

            status_code = 200
            if isinstance(result, tuple) and len(result) >= 2:
                try:
                    status_code = int(result[1])
                except (TypeError, ValueError):
                    status_code = 200

            log_event(
                action,
                target_type=target_type,
                target_id=_resolve_target_id(kwargs, target_id_from),
                status='ok' if 200 <= status_code < 400 else 'fail',
                meta={'status_code': status_code},
            )
            return result

        return wrapper
    return decorator
