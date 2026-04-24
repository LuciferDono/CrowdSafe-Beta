"""Venue — a logical grouping of cameras (stadium, temple, plaza, station)."""
from datetime import datetime, timezone

from backend.extensions import db


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Informational only — used by the dashboard to pick icons & default
    # capacity assumptions, not wired to risk calc yet.
    venue_type = db.Column(db.String(30), default='generic')
    location = db.Column(db.String(200), default='')
    expected_capacity = db.Column(db.Integer, default=0)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    cameras = db.relationship('Camera', backref='venue', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'venue_type': self.venue_type,
            'location': self.location,
            'expected_capacity': self.expected_capacity,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
