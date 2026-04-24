"""Multi-camera correlation API — stampede propagation detection."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.extensions import limiter
from backend.services.correlation_service import detect_waves
from backend.utils.decorators import token_required
from config import Config

correlation_bp = Blueprint('correlation', __name__)


@correlation_bp.route('/waves', methods=['GET'])
@token_required
@limiter.limit('30 per minute')
def get_waves():
    """Return top-k camera pairs showing wave-like risk propagation."""
    if not Config.CORRELATION_ENABLED:
        return jsonify({'error': 'Correlation disabled'}), 503

    window = request.args.get('window_seconds', type=int)
    step = request.args.get('step_seconds', default=5, type=int)
    max_lag = request.args.get('max_lag_seconds', type=int)
    min_corr = request.args.get('min_correlation', type=float)
    top_k = request.args.get('top_k', default=10, type=int)
    cam_filter = request.args.get('camera_ids')

    camera_ids = [c.strip() for c in cam_filter.split(',')] if cam_filter else None

    step = max(1, min(step, 60))
    top_k = max(1, min(top_k, 50))

    result = detect_waves(
        camera_ids=camera_ids,
        window_seconds=window,
        step_seconds=step,
        max_lag_seconds=max_lag,
        min_correlation=min_corr,
        top_k=top_k,
    )
    return jsonify(result)
