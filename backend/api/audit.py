"""Audit log read API.

Read-only. Admin-only. No write endpoints by design — audit entries are
created exclusively by the server-side :func:`log_event` /
:func:`audited` plumbing.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from backend.models.audit_log import AuditLog
from backend.utils.decorators import role_required

audit_bp = Blueprint('audit', __name__)


def _parse_dt(val: str | None):
    if not val:
        return None
    try:
        return datetime.fromisoformat(val.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None


@audit_bp.route('', methods=['GET'])
@role_required('admin')
def list_events():
    q = AuditLog.query

    actor = request.args.get('actor')
    action = request.args.get('action')
    target_type = request.args.get('target_type')
    target_id = request.args.get('target_id')
    status = request.args.get('status')
    since = _parse_dt(request.args.get('since'))
    until = _parse_dt(request.args.get('until'))
    limit = min(max(request.args.get('limit', 100, type=int), 1), 500)

    if actor:
        q = q.filter(AuditLog.actor_username == actor)
    if action:
        q = q.filter(AuditLog.action == action)
    if target_type:
        q = q.filter(AuditLog.target_type == target_type)
    if target_id:
        q = q.filter(AuditLog.target_id == target_id)
    if status:
        q = q.filter(AuditLog.status == status)
    if since:
        q = q.filter(AuditLog.timestamp >= since)
    if until:
        q = q.filter(AuditLog.timestamp <= until)

    rows = q.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return jsonify([r.to_dict() for r in rows])


@audit_bp.route('/summary', methods=['GET'])
@role_required('admin')
def summary():
    from sqlalchemy import func
    from backend.extensions import db

    window_hours = request.args.get('hours', 24, type=int)
    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    by_action = dict(
        db.session.query(AuditLog.action, func.count(AuditLog.id))
        .filter(AuditLog.timestamp >= since)
        .group_by(AuditLog.action)
        .all()
    )
    total = db.session.query(func.count(AuditLog.id)).filter(
        AuditLog.timestamp >= since
    ).scalar() or 0
    failures = db.session.query(func.count(AuditLog.id)).filter(
        AuditLog.timestamp >= since,
        AuditLog.status != 'ok',
    ).scalar() or 0

    return jsonify({
        'window_hours': window_hours,
        'total': total,
        'failures': failures,
        'by_action': by_action,
    })
