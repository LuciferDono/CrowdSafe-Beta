from backend.extensions import db
from datetime import datetime, timezone


class SystemLog(db.Model):
    __tablename__ = 'system_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    level = db.Column(db.String(20), default='info', index=True)
    component = db.Column(db.String(50), default='')
    message = db.Column(db.Text, default='')
    details = db.Column(db.Text, default='{}')  # JSON
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level,
            'component': self.component,
            'message': self.message,
            'user_id': self.user_id,
        }
