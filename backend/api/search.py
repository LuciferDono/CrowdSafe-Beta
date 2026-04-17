"""Natural-language search over metrics + alerts.

Operator types:  "show me critical alerts on gate A in the last hour"
Pipeline: NL → LLM returns {"table": ..., "filters": ...} → safe SQLAlchemy
query (NO raw SQL, NO string interpolation) → JSON rows.

Only `metrics` and `alerts` tables are queryable. Filter keys are whitelisted.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from flask import Blueprint, g, jsonify, request
from sqlalchemy import and_

from backend.extensions import limiter
from backend.models.alert import Alert
from backend.models.camera import Camera
from backend.models.metric import Metric
from backend.services import llm_service
from backend.utils.decorators import token_required

search_bp = Blueprint('search', __name__)


_NL_SYSTEM = (
    "You translate operator questions about a crowd-safety database into a "
    "strict JSON query spec. Output ONLY JSON with keys: "
    "table (\"metrics\"|\"alerts\"), "
    "filters (object), limit (int<=500), order_by (string). "
    "Allowed metrics filters: camera_id, risk_level, min_density, max_density, "
    "min_count, max_count, min_risk, max_risk, since_minutes. "
    "Allowed alerts filters: camera_id, risk_level, trigger_condition, "
    "resolved (bool), acknowledged (bool), since_minutes. "
    "Never include SQL, never guess table columns, never include extra keys. "
    "If the question is ambiguous, pick the most reasonable interpretation."
)

_ALLOWED_METRICS_FILTERS = {
    'camera_id', 'risk_level',
    'min_density', 'max_density',
    'min_count', 'max_count',
    'min_risk', 'max_risk',
    'since_minutes',
}
_ALLOWED_ALERTS_FILTERS = {
    'camera_id', 'risk_level', 'trigger_condition',
    'resolved', 'acknowledged', 'since_minutes',
}


def _apply_metrics_filters(q, f: dict):
    if v := f.get('camera_id'):
        q = q.filter(Metric.camera_id == str(v))
    if v := f.get('risk_level'):
        q = q.filter(Metric.risk_level == str(v).upper())
    if (v := f.get('min_density')) is not None:
        q = q.filter(Metric.density >= float(v))
    if (v := f.get('max_density')) is not None:
        q = q.filter(Metric.density <= float(v))
    if (v := f.get('min_count')) is not None:
        q = q.filter(Metric.count >= int(v))
    if (v := f.get('max_count')) is not None:
        q = q.filter(Metric.count <= int(v))
    if (v := f.get('min_risk')) is not None:
        q = q.filter(Metric.risk_score >= float(v))
    if (v := f.get('max_risk')) is not None:
        q = q.filter(Metric.risk_score <= float(v))
    if (v := f.get('since_minutes')) is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=int(v))
        q = q.filter(Metric.timestamp >= cutoff)
    return q


def _apply_alerts_filters(q, f: dict):
    if v := f.get('camera_id'):
        q = q.filter(Alert.camera_id == str(v))
    if v := f.get('risk_level'):
        q = q.filter(Alert.risk_level == str(v).upper())
    if v := f.get('trigger_condition'):
        q = q.filter(Alert.trigger_condition == str(v))
    if (v := f.get('resolved')) is not None:
        q = q.filter(Alert.resolved == bool(v))
    if (v := f.get('acknowledged')) is not None:
        q = q.filter(Alert.acknowledged == bool(v))
    if (v := f.get('since_minutes')) is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=int(v))
        q = q.filter(Alert.timestamp >= cutoff)
    return q


def _sanitize(spec: dict) -> dict:
    table = (spec.get('table') or '').lower()
    if table not in ('metrics', 'alerts'):
        raise ValueError(f'invalid table: {table}')
    raw_filters = spec.get('filters') or {}
    allowed = _ALLOWED_METRICS_FILTERS if table == 'metrics' else _ALLOWED_ALERTS_FILTERS
    filters = {k: v for k, v in raw_filters.items() if k in allowed}
    limit = int(spec.get('limit') or 100)
    limit = max(1, min(limit, 500))
    return {'table': table, 'filters': filters, 'limit': limit}


@search_bp.route('/nl', methods=['POST'])
@token_required
@limiter.limit('30 per minute')
def nl_search():
    if not llm_service.is_configured():
        return jsonify({'error': 'LLM not configured'}), 503

    data = request.get_json(silent=True) or {}
    question = (data.get('q') or '').strip()
    if not question:
        return jsonify({'error': 'q required'}), 400

    try:
        raw_spec = llm_service.json_response(
            prompt=f'Operator question: "{question}". Return query spec.',
            system=_NL_SYSTEM,
            tier='nano',
            temperature=0.0,
            max_tokens=300,
        )
    except Exception as e:
        return jsonify({'error': f'LLM error: {e}'}), 502

    try:
        spec = _sanitize(raw_spec if isinstance(raw_spec, dict) else {})
    except ValueError as e:
        return jsonify({'error': str(e), 'raw_spec': raw_spec}), 400

    if spec['table'] == 'metrics':
        q = _apply_metrics_filters(Metric.query, spec['filters'])
        rows = q.order_by(Metric.timestamp.desc()).limit(spec['limit']).all()
        results = [r.to_dict() for r in rows]
    else:
        q = _apply_alerts_filters(Alert.query, spec['filters'])
        rows = q.order_by(Alert.timestamp.desc()).limit(spec['limit']).all()
        results = [r.to_dict() for r in rows]

    return jsonify({
        'question': question,
        'spec': spec,
        'count': len(results),
        'results': results,
    })
