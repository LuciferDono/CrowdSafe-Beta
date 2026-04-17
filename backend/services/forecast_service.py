"""Short-horizon risk forecast.

Uses Holt linear exponential smoothing (level + trend) on recent metric
history to project risk_score, density, and count ``N`` seconds ahead.
Pure NumPy — no heavy TS library, no GPU. Fast enough to run per-request.

For production-grade multi-horizon forecasts, swap for Moirai/Chronos via
backend.services.hf_service. This module is the always-on fallback.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np

from backend.models.metric import Metric
from config import Config


@dataclass
class ForecastPoint:
    t_plus_sec: float
    risk_score: float
    risk_level: str
    density: float
    count: float


def _risk_level(score: float) -> str:
    if score >= Config.RISK_CRITICAL:
        return 'CRITICAL'
    if score >= Config.RISK_WARNING:
        return 'WARNING'
    return 'SAFE'


def _holt(series: np.ndarray, steps: int, alpha: float = 0.6, beta: float = 0.2) -> np.ndarray:
    """Holt linear exponential smoothing → `steps` ahead."""
    if len(series) == 0:
        return np.zeros(steps)
    if len(series) == 1:
        return np.full(steps, series[0])

    level = series[0]
    trend = series[1] - series[0]
    for y in series[1:]:
        prev_level = level
        level = alpha * y + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
    return np.array([level + (h + 1) * trend for h in range(steps)])


def forecast_camera(
    camera_id: str,
    *,
    horizon_seconds: int | None = None,
    lookback_seconds: int = 120,
    step_seconds: int = 5,
) -> dict:
    """Return a forecast bundle for one camera."""
    horizon = horizon_seconds or Config.FORECAST_HORIZON_SECONDS

    since = datetime.now(timezone.utc) - timedelta(seconds=lookback_seconds)
    rows = (
        Metric.query.filter(
            Metric.camera_id == camera_id,
            Metric.timestamp >= since,
        )
        .order_by(Metric.timestamp.asc())
        .all()
    )

    if len(rows) < 3:
        return {
            'camera_id': camera_id,
            'horizon_seconds': horizon,
            'method': 'insufficient_history',
            'points': [],
            'peak_risk': None,
            'eta_to_critical_sec': None,
        }

    risk = np.array([r.risk_score for r in rows], dtype=float)
    density = np.array([r.density for r in rows], dtype=float)
    count = np.array([float(r.count) for r in rows], dtype=float)

    steps = max(1, horizon // step_seconds)
    risk_fc = np.clip(_holt(risk, steps), 0.0, 1.0)
    density_fc = np.clip(_holt(density, steps), 0.0, None)
    count_fc = np.clip(_holt(count, steps), 0.0, None)

    points: list[dict] = []
    eta_critical: float | None = None
    crit_threshold = Config.RISK_CRITICAL

    for i in range(steps):
        t = (i + 1) * step_seconds
        score = float(risk_fc[i])
        point = ForecastPoint(
            t_plus_sec=float(t),
            risk_score=round(score, 3),
            risk_level=_risk_level(score),
            density=round(float(density_fc[i]), 3),
            count=round(float(count_fc[i]), 1),
        )
        points.append(point.__dict__)
        if eta_critical is None and score >= crit_threshold:
            eta_critical = float(t)

    return {
        'camera_id': camera_id,
        'horizon_seconds': horizon,
        'step_seconds': step_seconds,
        'method': 'holt_linear',
        'lookback_samples': len(rows),
        'points': points,
        'peak_risk': round(float(risk_fc.max()), 3),
        'peak_risk_at_sec': float((int(np.argmax(risk_fc)) + 1) * step_seconds),
        'eta_to_critical_sec': eta_critical,
    }
