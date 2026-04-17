from backend.extensions import db
from datetime import datetime, timezone


class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alert_id = db.Column(db.String(50), unique=True, nullable=False)
    camera_id = db.Column(db.String(50), db.ForeignKey('cameras.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    risk_level = db.Column(db.String(20), nullable=False)
    trigger_condition = db.Column(db.String(100), default='')
    message = db.Column(db.Text, nullable=False)
    metrics_snapshot = db.Column(db.Text, default='{}')  # JSON
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    snapshot_path = db.Column(db.String(255), nullable=True)

    @staticmethod
    def _utc_iso(dt):
        if dt is None:
            return None
        s = dt.isoformat()
        if '+' not in s and 'Z' not in s:
            s += 'Z'
        return s

    def to_dict(self):
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'camera_id': self.camera_id,
            'timestamp': self._utc_iso(self.timestamp),
            'risk_level': self.risk_level,
            'trigger_condition': self.trigger_condition,
            'message': self.message,
            'metrics_snapshot': self.metrics_snapshot,
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self._utc_iso(self.acknowledged_at),
            'resolved': self.resolved,
            'resolved_at': self._utc_iso(self.resolved_at),
        }
