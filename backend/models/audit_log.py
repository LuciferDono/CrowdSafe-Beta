"""Append-only audit log.

Write once, never update or delete. Captures WHO did WHAT to WHICH target
from WHERE. Read-only service layer: use :func:`log_event` as the only
public writer. Direct ORM access is intentionally not wrapped with helpers.

On PostgreSQL, a database-level trigger (added via Alembic migration)
enforces immutability at the storage layer as well.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from backend.extensions import db


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          nullable=False, index=True)

    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    actor_username = db.Column(db.String(80), nullable=True, index=True)
    actor_role = db.Column(db.String(32), nullable=True)

    action = db.Column(db.String(80), nullable=False, index=True)
    target_type = db.Column(db.String(80), nullable=True, index=True)
    target_id = db.Column(db.String(120), nullable=True, index=True)

    ip = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    request_id = db.Column(db.String(64), nullable=True)

    status = db.Column(db.String(32), nullable=False, default='ok', index=True)
    meta = db.Column(db.Text, nullable=False, default='{}')

    def to_dict(self) -> dict:
        try:
            meta_obj = json.loads(self.meta) if self.meta else {}
        except (ValueError, TypeError):
            meta_obj = {}
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'actor_id': self.actor_id,
            'actor_username': self.actor_username,
            'actor_role': self.actor_role,
            'action': self.action,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'ip': self.ip,
            'user_agent': self.user_agent,
            'request_id': self.request_id,
            'status': self.status,
            'meta': meta_obj,
        }
