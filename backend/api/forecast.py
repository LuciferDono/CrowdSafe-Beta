"""Forecast API — projected risk for N seconds ahead."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.extensions import limiter
from backend.services.forecast_service import forecast_camera
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
    lookback = request.args.get('lookback_seconds', default=120, type=int)
    step = request.args.get('step_seconds', default=5, type=int)

    lookback = max(30, min(lookback, 600))
    step = max(1, min(step, 30))

    result = forecast_camera(
        camera_id,
        horizon_seconds=horizon,
        lookback_seconds=lookback,
        step_seconds=step,
    )
    return jsonify(result)
