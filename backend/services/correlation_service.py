"""Multi-camera correlation — detect crowd waves propagating across cameras.

A stampede or surge is rarely contained to a single camera view. If camera
A's risk score spikes at t=0 and camera B's spikes at t=+8s, the crowd is
likely flowing from A toward B. This module:

  1. Resamples each active camera's recent metrics onto a common time grid
  2. Computes lagged Pearson correlation between every pair
  3. Reports the top-correlated pairs with their lead/lag direction

Used by /api/correlation/waves to drive the propagation overlay on the ops
dashboard. Pure NumPy; no graph/ML libs.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import radians, sin, cos, asin, sqrt

import numpy as np

from backend.models.camera import Camera
from backend.models.metric import Metric
from config import Config


@dataclass
class CameraSeries:
    camera_id: str
    name: str
    timestamps: np.ndarray
    risk: np.ndarray
    latitude: float | None
    longitude: float | None


@dataclass
class WaveEvent:
    source_camera: str
    target_camera: str
    correlation: float
    lag_seconds: float
    distance_m: float | None

    def to_dict(self) -> dict:
        return {
            'source_camera': self.source_camera,
            'target_camera': self.target_camera,
            'correlation': round(self.correlation, 3),
            'lag_seconds': round(self.lag_seconds, 1),
            'distance_m': round(self.distance_m, 1) if self.distance_m is not None else None,
        }


def _haversine_m(a_lat, a_lng, b_lat, b_lng) -> float | None:
    if None in (a_lat, a_lng, b_lat, b_lng):
        return None
    R = 6371000.0
    phi1, phi2 = radians(a_lat), radians(b_lat)
    dphi = radians(b_lat - a_lat)
    dlam = radians(b_lng - a_lng)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlam / 2) ** 2
    return 2 * R * asin(sqrt(a))


def _resample_to_grid(
    timestamps: np.ndarray,
    values: np.ndarray,
    grid: np.ndarray,
) -> np.ndarray:
    """Linear interpolation onto the common grid.

    For samples outside the observed range we hold the nearest value rather
    than extrapolating — risk doesn't linearly extend past the window edge.
    """
    if len(timestamps) < 2:
        if len(timestamps) == 1:
            return np.full(len(grid), values[0], dtype=float)
        return np.zeros(len(grid), dtype=float)
    ts = timestamps.astype('datetime64[s]').astype(np.float64)
    g = grid.astype('datetime64[s]').astype(np.float64)
    return np.interp(g, ts, values, left=values[0], right=values[-1])


def _load_series(
    camera_ids: list[str] | None,
    since: datetime,
    until: datetime,
) -> list[CameraSeries]:
    cams = Camera.query
    if camera_ids:
        cams = cams.filter(Camera.id.in_(camera_ids))
    cams = cams.filter(Camera.is_active.is_(True)).all()

    series: list[CameraSeries] = []
    for cam in cams:
        rows = (
            Metric.query.filter(
                Metric.camera_id == cam.id,
                Metric.timestamp >= since,
                Metric.timestamp <= until,
            )
            .order_by(Metric.timestamp.asc())
            .all()
        )
        if len(rows) < 3:
            continue
        ts = np.array([r.timestamp for r in rows], dtype='datetime64[us]')
        risk = np.array([r.risk_score for r in rows], dtype=float)
        series.append(CameraSeries(
            camera_id=cam.id,
            name=cam.name,
            timestamps=ts,
            risk=risk,
            latitude=cam.latitude,
            longitude=cam.longitude,
        ))
    return series


def _best_lag_correlation(
    a: np.ndarray,
    b: np.ndarray,
    *,
    max_lag_steps: int,
) -> tuple[float, int]:
    """Return (best_pearson, lag_steps) where lag>0 means A leads B."""
    if np.std(a) < 1e-6 or np.std(b) < 1e-6:
        return 0.0, 0
    a_norm = (a - a.mean()) / (np.std(a) * len(a))
    b_norm = (b - b.mean()) / np.std(b)
    # Full cross-correlation; pick the best within +/- max_lag_steps.
    xcorr = np.correlate(b_norm, a_norm, mode='full')
    center = len(a) - 1
    lo = max(0, center - max_lag_steps)
    hi = min(len(xcorr), center + max_lag_steps + 1)
    window = xcorr[lo:hi]
    best_idx = int(np.argmax(np.abs(window)))
    lag = (lo + best_idx) - center
    return float(window[best_idx]), lag


def detect_waves(
    *,
    camera_ids: list[str] | None = None,
    window_seconds: int | None = None,
    step_seconds: int = 5,
    max_lag_seconds: int | None = None,
    min_correlation: float | None = None,
    top_k: int = 10,
) -> dict:
    """Return the top-k most correlated camera pairs in the recent window."""
    window = window_seconds or Config.CORRELATION_WINDOW_SECONDS
    max_lag = max_lag_seconds or Config.CORRELATION_MAX_LAG_SECONDS
    min_corr = (min_correlation
                if min_correlation is not None
                else Config.CORRELATION_MIN_PEARSON)

    until = datetime.now(timezone.utc)
    since = until - timedelta(seconds=window)

    series = _load_series(camera_ids, since, until)
    if len(series) < 2:
        return {
            'window_seconds': window,
            'step_seconds': step_seconds,
            'camera_count': len(series),
            'waves': [],
            'status': 'insufficient_cameras',
        }

    # Strip tz before np.datetime64 (NumPy treats tz-aware inputs as UTC
    # but emits a UserWarning; dropping tzinfo is explicit and silent).
    grid = np.arange(
        np.datetime64(since.replace(tzinfo=None), 's'),
        np.datetime64(until.replace(tzinfo=None), 's'),
        np.timedelta64(step_seconds, 's'),
    )
    if len(grid) < 4:
        return {
            'window_seconds': window,
            'step_seconds': step_seconds,
            'camera_count': len(series),
            'waves': [],
            'status': 'window_too_short',
        }

    resampled: dict[str, np.ndarray] = {
        s.camera_id: _resample_to_grid(s.timestamps, s.risk, grid)
        for s in series
    }
    by_id = {s.camera_id: s for s in series}

    max_lag_steps = max(1, max_lag // step_seconds)
    waves: list[WaveEvent] = []

    for i, src in enumerate(series):
        for j in range(i + 1, len(series)):
            tgt = series[j]
            a = resampled[src.camera_id]
            b = resampled[tgt.camera_id]
            corr, lag_steps = _best_lag_correlation(a, b, max_lag_steps=max_lag_steps)
            if abs(corr) < min_corr:
                continue

            lag_sec = float(lag_steps * step_seconds)
            if lag_sec >= 0:
                source, target = src, tgt
                direction_lag = lag_sec
            else:
                source, target = tgt, src
                direction_lag = -lag_sec

            distance = _haversine_m(
                src.latitude, src.longitude,
                tgt.latitude, tgt.longitude,
            )
            waves.append(WaveEvent(
                source_camera=source.camera_id,
                target_camera=target.camera_id,
                correlation=corr,
                lag_seconds=direction_lag,
                distance_m=distance,
            ))

    waves.sort(key=lambda w: abs(w.correlation), reverse=True)

    return {
        'window_seconds': window,
        'step_seconds': step_seconds,
        'max_lag_seconds': max_lag,
        'min_correlation': min_corr,
        'camera_count': len(series),
        'waves': [w.to_dict() for w in waves[:top_k]],
        'status': 'ok',
    }
