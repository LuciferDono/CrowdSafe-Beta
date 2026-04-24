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


def _holt(
    series: np.ndarray,
    steps: int,
    alpha: float = 0.6,
    beta: float = 0.2,
    phi: float = 0.95,
) -> tuple[np.ndarray, float]:
    """Damped-trend Holt smoothing → (forecast[steps], residual_std).

    Damping (phi < 1) dampens the trend geometrically so long-horizon
    forecasts do not overshoot when the trend is transient.
    Residual std lets callers report widening uncertainty bands.
    """
    if len(series) == 0:
        return np.zeros(steps), 0.0
    if len(series) == 1:
        return np.full(steps, series[0]), 0.0

    level = series[0]
    trend = series[1] - series[0]
    residuals = []
    for y in series[1:]:
        one_step = level + phi * trend
        residuals.append(y - one_step)
        prev_level = level
        level = alpha * y + (1 - alpha) * one_step
        trend = beta * (level - prev_level) + (1 - beta) * phi * trend

    # Damped multi-step: f(h) = level + sum_{i=1..h} phi^i * trend
    cumulative_phi = np.cumsum(np.power(phi, np.arange(1, steps + 1)))
    forecast = level + cumulative_phi * trend
    residual_std = float(np.std(residuals)) if residuals else 0.0
    return forecast, residual_std


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
    risk_raw, risk_resid = _holt(risk, steps)
    density_raw, _ = _holt(density, steps)
    count_raw, _ = _holt(count, steps)
    risk_fc = np.clip(risk_raw, 0.0, 1.0)
    density_fc = np.clip(density_raw, 0.0, None)
    count_fc = np.clip(count_raw, 0.0, None)

    # Confidence bands on risk — widen with sqrt(h) per horizon.
    horizon_scale = np.sqrt(np.arange(1, steps + 1))
    risk_lower = np.clip(risk_raw - 1.96 * risk_resid * horizon_scale, 0.0, 1.0)
    risk_upper = np.clip(risk_raw + 1.96 * risk_resid * horizon_scale, 0.0, 1.0)

    # Reliability score: samples vs horizon/step ratio.
    # Fewer than 2x forecast-steps of history = low confidence.
    sample_ratio = len(rows) / max(steps, 1)
    if sample_ratio >= 2.0:
        reliability = 'high'
    elif sample_ratio >= 1.0:
        reliability = 'medium'
    else:
        reliability = 'low'

    points: list[dict] = []
    eta_critical: float | None = None
    crit_threshold = Config.RISK_CRITICAL

    for i in range(steps):
        t = (i + 1) * step_seconds
        score = float(risk_fc[i])
        points.append({
            't_plus_sec': float(t),
            'risk_score': round(score, 3),
            'risk_lower': round(float(risk_lower[i]), 3),
            'risk_upper': round(float(risk_upper[i]), 3),
            'risk_level': _risk_level(score),
            'density': round(float(density_fc[i]), 3),
            'count': round(float(count_fc[i]), 1),
        })
        if eta_critical is None and score >= crit_threshold:
            eta_critical = float(t)

    baseline_block = _baseline_block(camera_id, rows[-1])

    return {
        'camera_id': camera_id,
        'horizon_seconds': horizon,
        'step_seconds': step_seconds,
        'method': 'holt_damped',
        'lookback_samples': len(rows),
        'reliability': reliability,
        'residual_std': round(risk_resid, 4),
        'points': points,
        'peak_risk': round(float(risk_fc.max()), 3),
        'peak_risk_at_sec': float((int(np.argmax(risk_fc)) + 1) * step_seconds),
        'eta_to_critical_sec': eta_critical,
        'baseline': baseline_block,
    }


def _baseline_block(camera_id: str, latest_metric) -> dict | None:
    """Pull same-time-of-week historical baseline + deviation for latest metric."""
    if not getattr(Config, 'BASELINE_ENABLED', True):
        return None
    try:
        from backend.services.historical_baseline import (
            baseline_for_camera,
            deviation_vs_baseline,
        )
        baseline = baseline_for_camera(
            camera_id,
            reference_time=latest_metric.timestamp,
        )
    except Exception:
        return None
    if baseline is None:
        return {'status': 'insufficient_history'}
    deviation = deviation_vs_baseline(
        current_risk=float(latest_metric.risk_score or 0.0),
        current_count=float(latest_metric.count or 0),
        current_density=float(latest_metric.density or 0.0),
        baseline=baseline,
    )
    return {
        'status': 'ok',
        **baseline.to_dict(),
        **deviation,
    }
