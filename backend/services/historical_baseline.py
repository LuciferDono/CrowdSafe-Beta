"""Historical pattern-of-life baseline.

Crowds are not random. A temple at 6 PM Friday has a predictable envelope
week-over-week; a stadium after a match has a predictable dump curve. This
module answers: *"for this camera, at this time of this weekday, what is the
normal density / count / risk?"* — and flags live metrics that deviate from
that envelope by more than N standard deviations.

Backed by the same ``metrics`` table the live pipeline already writes to. No
external ML deps; pure SQL + NumPy. Designed to be called from the forecast
API to enrich Holt forecasts with "is this abnormal?" context.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

import numpy as np
from sqlalchemy import and_, extract, func

from backend.extensions import db
from backend.models.metric import Metric
from config import Config


# Minimum samples within the comparison window before we trust the baseline.
_MIN_SAMPLES = 10


@dataclass
class BaselineStats:
    samples: int
    mean_risk: float
    std_risk: float
    mean_count: float
    std_count: float
    mean_density: float
    std_density: float

    def to_dict(self) -> dict:
        return {
            'samples': self.samples,
            'mean_risk': round(self.mean_risk, 3),
            'std_risk': round(self.std_risk, 3),
            'mean_count': round(self.mean_count, 1),
            'std_count': round(self.std_count, 1),
            'mean_density': round(self.mean_density, 3),
            'std_density': round(self.std_density, 3),
        }


def _window_for_timestamp(
    ts: datetime,
    lookback_weeks: int,
    hour_window: int,
) -> tuple[int, int, int, datetime]:
    """Return (weekday, hour_lo, hour_hi, since) for the baseline query."""
    weekday = ts.weekday()  # 0 = Monday
    hour = ts.hour
    hour_lo = max(0, hour - hour_window)
    hour_hi = min(23, hour + hour_window)
    since = ts - timedelta(weeks=lookback_weeks)
    return weekday, hour_lo, hour_hi, since


def baseline_for_camera(
    camera_id: str,
    *,
    reference_time: datetime | None = None,
    lookback_weeks: int | None = None,
    hour_window: int | None = None,
) -> BaselineStats | None:
    """Compute baseline stats for the same weekday+hour bucket over past weeks.

    Returns ``None`` when there's not enough history to trust the numbers.
    """
    ref = reference_time or datetime.now(timezone.utc)
    weeks = lookback_weeks or Config.BASELINE_LOOKBACK_WEEKS
    hour_pad = hour_window if hour_window is not None else Config.BASELINE_HOUR_WINDOW

    weekday, hour_lo, hour_hi, since = _window_for_timestamp(ref, weeks, hour_pad)

    # SQLite + Postgres both support extract() via SQLAlchemy.
    q = db.session.query(
        Metric.risk_score,
        Metric.count,
        Metric.density,
    ).filter(
        Metric.camera_id == camera_id,
        Metric.timestamp >= since,
        Metric.timestamp < ref - timedelta(minutes=5),  # Exclude very recent.
        extract('dow', Metric.timestamp) == weekday if _dialect_is_postgres()
        else _sqlite_weekday_match(weekday),
        extract('hour', Metric.timestamp) >= hour_lo,
        extract('hour', Metric.timestamp) <= hour_hi,
    )

    rows = q.all()
    if len(rows) < _MIN_SAMPLES:
        return None

    risk = np.array([r.risk_score for r in rows], dtype=float)
    count = np.array([float(r.count) for r in rows], dtype=float)
    density = np.array([r.density for r in rows], dtype=float)

    return BaselineStats(
        samples=len(rows),
        mean_risk=float(risk.mean()),
        std_risk=float(risk.std(ddof=0)),
        mean_count=float(count.mean()),
        std_count=float(count.std(ddof=0)),
        mean_density=float(density.mean()),
        std_density=float(density.std(ddof=0)),
    )


def deviation_vs_baseline(
    current_risk: float,
    current_count: float,
    current_density: float,
    baseline: BaselineStats,
) -> dict:
    """Return z-scores and flags for the current observation vs baseline."""
    def _z(current: float, mean: float, std: float) -> float:
        if std < 1e-6:
            return 0.0
        return (current - mean) / std

    z_risk = _z(current_risk, baseline.mean_risk, baseline.std_risk)
    z_count = _z(current_count, baseline.mean_count, baseline.std_count)
    z_density = _z(current_density, baseline.mean_density, baseline.std_density)

    max_z = max(abs(z_risk), abs(z_count), abs(z_density))
    if max_z >= 3.0:
        anomaly = 'severe'
    elif max_z >= 2.0:
        anomaly = 'moderate'
    elif max_z >= 1.0:
        anomaly = 'mild'
    else:
        anomaly = 'normal'

    return {
        'z_risk': round(z_risk, 2),
        'z_count': round(z_count, 2),
        'z_density': round(z_density, 2),
        'max_z': round(max_z, 2),
        'anomaly': anomaly,
    }


def _dialect_is_postgres() -> bool:
    try:
        return db.engine.dialect.name.startswith('postgres')
    except Exception:
        return False


def _sqlite_weekday_match(weekday_py: int):
    """SQLite strftime('%w') returns 0=Sunday..6=Saturday; Python is 0=Monday..6=Sunday."""
    sqlite_dow = (weekday_py + 1) % 7
    return func.cast(func.strftime('%w', Metric.timestamp), db.Integer) == sqlite_dow
