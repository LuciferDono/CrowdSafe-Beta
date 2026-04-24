"""Venue-level aggregate risk.

Composes per-camera live metrics (from the running ``camera_manager`` when
processors are online, falling back to the latest DB row) into a venue
rollup the ops dashboard can render without walking every camera.

Aggregation strategy:
  - **peak_risk**: max risk across venue cameras — the worst zone sets the
    venue alert level.
  - **weighted_risk**: sum(risk * count) / sum(count) — headcount-weighted
    mean; how bad it feels "on average" given where the crowd actually is.
  - **total_count**: headcount across venue.
  - **utilization**: total_count / expected_capacity.
  - **venue_level**: max of per-camera effective levels (hysteresis-aware
    when `camera_manager` is running).
"""
from __future__ import annotations

from backend.models.camera import Camera
from backend.models.metric import Metric
from backend.models.venue import Venue
from backend.services.camera_manager import camera_manager


_LEVEL_RANK = {'SAFE': 0, 'CAUTION': 1, 'WARNING': 2, 'CRITICAL': 3}
_RANK_LEVEL = {v: k for k, v in _LEVEL_RANK.items()}


def _latest_metric_for(camera_id: str) -> dict | None:
    """Live processor snapshot preferred; fall back to newest DB row."""
    proc = camera_manager.get_processor(camera_id)
    if proc and proc.is_running and getattr(proc, 'latest_metrics', None):
        return proc.latest_metrics
    row = (
        Metric.query.filter_by(camera_id=camera_id)
        .order_by(Metric.timestamp.desc())
        .first()
    )
    return row.to_dict() if row else None


def _effective_level(metric: dict) -> str:
    return metric.get('risk_level_effective') or metric.get('risk_level') or 'SAFE'


def aggregate_venue_risk(venue_id: str) -> dict | None:
    """Return live rollup for one venue, or None if the venue doesn't exist."""
    venue = Venue.query.filter_by(id=venue_id).first()
    if venue is None:
        return None

    cameras = Camera.query.filter_by(venue_id=venue_id).all()
    camera_blocks: list[dict] = []

    peak_risk = 0.0
    weighted_num = 0.0
    weighted_den = 0.0
    total_count = 0
    max_rank = 0
    active_cams = 0

    for cam in cameras:
        metric = _latest_metric_for(cam.id)
        if metric is None:
            camera_blocks.append({
                'camera_id': cam.id,
                'name': cam.name,
                'status': 'no_data',
            })
            continue

        active_cams += 1
        risk = float(metric.get('risk_score') or 0.0)
        count = int(metric.get('count') or 0)
        peak_risk = max(peak_risk, risk)
        weighted_num += risk * count
        weighted_den += count
        total_count += count

        level = _effective_level(metric)
        max_rank = max(max_rank, _LEVEL_RANK.get(level.upper(), 0))

        camera_blocks.append({
            'camera_id': cam.id,
            'name': cam.name,
            'status': 'ok',
            'risk_score': round(risk, 3),
            'risk_level': level,
            'count': count,
            'density': round(float(metric.get('density') or 0.0), 3),
        })

    weighted_risk = weighted_num / weighted_den if weighted_den > 0 else 0.0
    capacity = venue.expected_capacity or 0
    utilization = (total_count / capacity) if capacity > 0 else None

    return {
        'venue': venue.to_dict(),
        'total_cameras': len(cameras),
        'active_cameras': active_cams,
        'peak_risk': round(peak_risk, 3),
        'weighted_risk': round(weighted_risk, 3),
        'total_count': total_count,
        'utilization': round(utilization, 3) if utilization is not None else None,
        'venue_level': _RANK_LEVEL[max_rank],
        'cameras': camera_blocks,
    }


def aggregate_all_venues() -> list[dict]:
    """Rollup for every active venue (used by the ops dashboard index)."""
    venues = Venue.query.filter_by(is_active=True).all()
    out = []
    for v in venues:
        block = aggregate_venue_risk(v.id)
        if block is not None:
            out.append(block)
    return out
