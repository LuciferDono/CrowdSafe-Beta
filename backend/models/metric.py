from backend.extensions import db
from datetime import datetime, timezone


class Metric(db.Model):
    __tablename__ = 'metrics'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    camera_id = db.Column(db.String(50), db.ForeignKey('cameras.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    count = db.Column(db.Integer, default=0)
    density = db.Column(db.Float, default=0.0)
    avg_velocity = db.Column(db.Float, default=0.0)
    max_velocity = db.Column(db.Float, default=0.0)
    surge_rate = db.Column(db.Float, default=0.0)
    flow_in = db.Column(db.Integer, default=0)
    flow_out = db.Column(db.Integer, default=0)
    risk_score = db.Column(db.Float, default=0.0)
    risk_level = db.Column(db.String(20), default='SAFE')
    capacity_utilization = db.Column(db.Float, default=0.0)
    frame_number = db.Column(db.Integer, default=0)

    @staticmethod
    def _utc_iso(dt):
        """Ensure timestamp is marked as UTC for frontend parsing."""
        if dt is None:
            return None
        s = dt.isoformat()
        if '+' not in s and 'Z' not in s:
            s += 'Z'
        return s

    def to_dict(self):
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'timestamp': self._utc_iso(self.timestamp),
            'count': self.count,
            'density': round(self.density, 3),
            'avg_velocity': round(self.avg_velocity, 2),
            'max_velocity': round(self.max_velocity, 2),
            'surge_rate': round(self.surge_rate, 3),
            'flow_in': self.flow_in,
            'flow_out': self.flow_out,
            'risk_score': round(self.risk_score, 3),
            'risk_level': self.risk_level,
            'capacity_utilization': round(self.capacity_utilization, 1),
            'frame_number': self.frame_number,
        }
