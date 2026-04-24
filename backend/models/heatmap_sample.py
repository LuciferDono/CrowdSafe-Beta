"""Per-camera spatial density samples.

Persists a coarse (default 16x16) density grid every N seconds per camera so
the ops dashboard can replay zone-level crowding, not just scalar risk. Cells
are quantized to uint8 (0..255) and base64-encoded to keep rows small —
16x16 grid is 256 bytes → ~344 chars base64 → trivial even at 100s of cameras.

The grid is *downsampled* from the AI engine's density_map (which is
typically ~180x320 for 720p video, too large to persist per-sample).
"""
from backend.extensions import db
from datetime import datetime, timezone


class HeatmapSample(db.Model):
    __tablename__ = 'heatmap_samples'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    camera_id = db.Column(db.String(50), db.ForeignKey('cameras.id'),
                          nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          index=True)
    grid_rows = db.Column(db.Integer, nullable=False)
    grid_cols = db.Column(db.Integer, nullable=False)
    # Base64-encoded uint8 buffer, row-major. Decode to np.frombuffer(..., dtype=uint8)
    # then reshape(grid_rows, grid_cols) and divide by 255 to get [0,1] density.
    grid_data = db.Column(db.Text, nullable=False)
    person_count = db.Column(db.Integer, default=0)
    peak_density = db.Column(db.Float, default=0.0)  # unnormalized max-cell

    @staticmethod
    def _utc_iso(dt):
        if dt is None:
            return None
        s = dt.isoformat()
        if '+' not in s and 'Z' not in s:
            s += 'Z'
        return s

    def to_dict(self, include_grid: bool = True):
        out = {
            'id': self.id,
            'camera_id': self.camera_id,
            'timestamp': self._utc_iso(self.timestamp),
            'grid_rows': self.grid_rows,
            'grid_cols': self.grid_cols,
            'person_count': self.person_count,
            'peak_density': round(float(self.peak_density), 4),
        }
        if include_grid:
            out['grid_data'] = self.grid_data
        return out
