import json
from backend.extensions import db
from datetime import datetime, timezone


class Camera(db.Model):
    __tablename__ = 'cameras'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), default='')
    source_type = db.Column(db.String(20), default='file')  # rtsp, http, file, usb
    source_url = db.Column(db.Text, default='')
    area_sqm = db.Column(db.Float, default=100.0)
    expected_capacity = db.Column(db.Integer, default=500)
    calibration_method = db.Column(db.String(20), default='manual')  # aruco, manual, reference
    calibration_data = db.Column(db.Text, default='{}')  # JSON
    roi = db.Column(db.Text, default='{}')  # JSON - Region of Interest
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='offline')  # online, offline, error, processing
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    fps_target = db.Column(db.Integer, default=30)
    resolution = db.Column(db.String(20), default='1280x720')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    metrics = db.relationship('Metric', backref='camera', lazy='dynamic', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='camera', lazy='dynamic', cascade='all, delete-orphan')
    recordings = db.relationship('Recording', backref='camera', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'source_type': self.source_type,
            'source_url': self.source_url,
            'area_sqm': self.area_sqm,
            'expected_capacity': self.expected_capacity,
            'calibration_method': self.calibration_method,
            'is_active': self.is_active,
            'status': self.status,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'fps_target': self.fps_target,
            'resolution': self.resolution,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
