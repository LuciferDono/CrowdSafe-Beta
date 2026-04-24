"""Heatmap sample persistence.

Downsamples the AI engine's ~high-res density_map to a coarse (default
16x16) grid, quantizes to uint8, base64-encodes, and writes to DB. Only
called periodically (default every 10s per camera) to keep row counts
bounded — 10s cadence × 20 cameras × 24h = ~172k rows/day, each ~400 bytes.

The retrieval side reassembles the grid:
    import numpy as np, base64
    buf = base64.b64decode(row.grid_data)
    grid = np.frombuffer(buf, dtype=np.uint8).reshape(row.grid_rows, row.grid_cols) / 255.0
"""
from __future__ import annotations

import base64
import time
from typing import Any

import numpy as np

from backend.extensions import db
from backend.models.heatmap_sample import HeatmapSample


DEFAULT_GRID_ROWS = 16
DEFAULT_GRID_COLS = 16
DEFAULT_SAMPLE_INTERVAL_S = 10.0


def downsample_grid(density_map: np.ndarray,
                    rows: int = DEFAULT_GRID_ROWS,
                    cols: int = DEFAULT_GRID_COLS) -> np.ndarray:
    """Block-average ``density_map`` into a ``rows x cols`` grid.

    Input can be any 2D float array (the AI engine produces ~h/4 x w/4).
    Output preserves the *relative* intensity — we normalize so the grid's
    max cell is 1.0, same convention as the AI engine's density_map.
    """
    if density_map is None or density_map.size == 0:
        return np.zeros((rows, cols), dtype=np.float32)

    h, w = density_map.shape[:2]
    if h < rows or w < cols:
        # Tiny inputs: just resize via nearest-ish (avoids div-by-zero).
        return _nearest_resize(density_map.astype(np.float32), rows, cols)

    # Crop to a size that divides evenly — simpler than fractional block sums.
    row_block = h // rows
    col_block = w // cols
    cropped = density_map[:row_block * rows, :col_block * cols].astype(np.float32)
    pooled = cropped.reshape(rows, row_block, cols, col_block).mean(axis=(1, 3))

    peak = float(pooled.max())
    if peak > 0:
        pooled = pooled / peak
    return pooled


def _nearest_resize(arr: np.ndarray, rows: int, cols: int) -> np.ndarray:
    """Fallback for degenerate small inputs."""
    h, w = arr.shape[:2]
    if h == 0 or w == 0:
        return np.zeros((rows, cols), dtype=np.float32)
    y_idx = (np.linspace(0, h - 1, rows)).astype(int)
    x_idx = (np.linspace(0, w - 1, cols)).astype(int)
    return arr[np.ix_(y_idx, x_idx)].astype(np.float32)


def encode_grid(grid: np.ndarray) -> str:
    """Quantize grid to uint8 and return base64 string."""
    q = np.clip(grid * 255.0, 0, 255).astype(np.uint8)
    return base64.b64encode(q.tobytes()).decode('ascii')


def decode_grid(data_b64: str, rows: int, cols: int) -> np.ndarray:
    """Inverse of ``encode_grid`` — returns [0,1] float grid."""
    buf = base64.b64decode(data_b64)
    return np.frombuffer(buf, dtype=np.uint8).reshape(rows, cols).astype(np.float32) / 255.0


def persist_sample(
    camera_id: str,
    density_map: np.ndarray,
    person_count: int,
    *,
    rows: int = DEFAULT_GRID_ROWS,
    cols: int = DEFAULT_GRID_COLS,
) -> HeatmapSample | None:
    """Downsample + persist one sample. Returns the row or None on failure.

    Defensive: a heatmap write must never break the video pipeline.
    """
    try:
        grid = downsample_grid(density_map, rows=rows, cols=cols)
        peak = float(np.asarray(density_map).max()) if density_map is not None else 0.0
        sample = HeatmapSample(
            camera_id=camera_id,
            grid_rows=rows,
            grid_cols=cols,
            grid_data=encode_grid(grid),
            person_count=int(person_count),
            peak_density=peak,
        )
        db.session.add(sample)
        db.session.commit()
        return sample
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass
        return None


class SampleRateGate:
    """Throttle: returns True at most once every ``interval_s`` seconds."""

    def __init__(self, interval_s: float = DEFAULT_SAMPLE_INTERVAL_S):
        self.interval_s = interval_s
        self._last: float = 0.0

    def should_sample(self, now: float | None = None) -> bool:
        t = now if now is not None else time.time()
        if t - self._last >= self.interval_s:
            self._last = t
            return True
        return False


def recent_samples(camera_id: str, limit: int = 20,
                   include_grid: bool = True) -> list[dict[str, Any]]:
    rows = (
        HeatmapSample.query.filter_by(camera_id=camera_id)
        .order_by(HeatmapSample.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [r.to_dict(include_grid=include_grid) for r in rows]


def latest_sample(camera_id: str) -> dict[str, Any] | None:
    row = (
        HeatmapSample.query.filter_by(camera_id=camera_id)
        .order_by(HeatmapSample.timestamp.desc())
        .first()
    )
    return row.to_dict(include_grid=True) if row else None
