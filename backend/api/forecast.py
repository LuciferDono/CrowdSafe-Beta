"""Forecast API — projected risk for N seconds ahead + baseline comparison."""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from backend.extensions import limiter
from backend.models.metric import Metric
from backend.services.forecast_service import forecast_camera
from backend.services.historical_baseline import (
    baseline_for_camera,
    deviation_vs_baseline,
)
from backend.utils.decorators import token_required
from config import Config

forecast_bp = Blueprint('forecast', __name__)


@forecast_bp.route('/<camera_id>', methods=['GET'])
@token_required
@limiter.limit('60 per minute')
def get_forecast(camera_id):
    if not Config.FORECAST_ENABLED:
        return jsonify({'error': 'Forecast disabled'}), 503

    horizon = request.args.get('horizon_seconds', type=int)
    lookback_raw = request.args.get('lookback_seconds', type=int)
    step = request.args.get('step_seconds', default=5, type=int)

    effective_horizon = horizon or Config.FORECAST_HORIZON_SECONDS
    effective_horizon = max(Config.FORECAST_HORIZON_MIN,
                            min(effective_horizon, Config.FORECAST_HORIZON_MAX))

    # Lookback defaults to 2x horizon (or min 120s) for enough history to trend.
    if lookback_raw is None:
        lookback = max(120, effective_horizon * 2)
    else:
        lookback = lookback_raw
    lookback = max(30, min(lookback, Config.FORECAST_LOOKBACK_MAX))
    step = max(1, min(step, Config.FORECAST_STEP_MAX))

    result = forecast_camera(
        camera_id,
        horizon_seconds=effective_horizon,
        lookback_seconds=lookback,
        step_seconds=step,
    )
    return jsonify(result)


@forecast_bp.route('/<camera_id>/baseline', methods=['GET'])
@token_required
@limiter.limit('30 per minute')
def get_baseline(camera_id):
    """Same-weekday-same-hour baseline stats + current deviation."""
    if not Config.BASELINE_ENABLED:
        return jsonify({'error': 'Baseline disabled'}), 503

    ref_arg = request.args.get('at')
    if ref_arg:
        try:
            ref = datetime.fromisoformat(ref_arg.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid at= timestamp'}), 400
    else:
        ref = datetime.now(timezone.utc)

    baseline = baseline_for_camera(camera_id, reference_time=ref)
    if baseline is None:
        return jsonify({
            'camera_id': camera_id,
            'status': 'insufficient_history',
            'message': 'Not enough same-time-of-week history yet.',
        })

    latest = (Metric.query.filter_by(camera_id=camera_id)
              .order_by(Metric.timestamp.desc()).first())
    deviation = None
    if latest is not None:
        deviation = deviation_vs_baseline(
            current_risk=float(latest.risk_score or 0.0),
            current_count=float(latest.count or 0),
            current_density=float(latest.density or 0.0),
            baseline=baseline,
        )

    return jsonify({
        'camera_id': camera_id,
        'status': 'ok',
        'reference_time': ref.isoformat(),
        'baseline': baseline.to_dict(),
        'current': (latest.to_dict() if latest else None),
        'deviation': deviation,
    })
