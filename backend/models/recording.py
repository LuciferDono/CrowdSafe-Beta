from backend.extensions import db
from datetime import datetime, timezone


class Recording(db.Model):
    __tablename__ = 'recordings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recording_id = db.Column(db.String(50), unique=True, nullable=False)
    camera_id = db.Column(db.String(50), db.ForeignKey('cameras.id'), nullable=False, index=True)
    filename = db.Column(db.String(256), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    start_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Float, default=0.0)
    frame_count = db.Column(db.Integer, default=0)
    width = db.Column(db.Integer, default=0)
    height = db.Column(db.Integer, default=0)
    fps = db.Column(db.Float, default=0.0)
    file_size_bytes = db.Column(db.BigInteger, default=0)
    thumbnail_path = db.Column(db.String(255), nullable=True)
    trigger_type = db.Column(db.String(50), default='manual')  # manual, alert, scheduled

    def to_dict(self):
        return {
            'id': self.id,
            'recording_id': self.recording_id,
            'camera_id': self.camera_id,
            'filename': self.filename,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': round(self.duration_seconds, 1),
            'frame_count': self.frame_count,
            'width': self.width,
            'height': self.height,
            'fps': round(self.fps, 1),
            'file_size_bytes': self.file_size_bytes,
            'trigger_type': self.trigger_type,
        }
