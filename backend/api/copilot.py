"""LLM operator copilot.

Routes:
  POST /api/copilot/chat    — question + optional context → answer
  POST /api/copilot/triage  — list of alerts → ranked action plan (JSON)
"""
from __future__ import annotations

import json

from flask import Blueprint, jsonify, request
from sqlalchemy import text

from backend.extensions import db, limiter
from backend.models.alert import Alert
from backend.models.camera import Camera
from backend.models.metric import Metric
from backend.services import llm_service
from backend.services.camera_manager import camera_manager
from backend.utils.decorators import token_required

copilot_bp = Blueprint('copilot', __name__)


_CHAT_SYSTEM = """\
You are CrowdSafe Copilot — an AI assistant embedded in a live crowd-safety operations platform.

You have access to TWO data sources in every query:
1. LIVE STATE — current metrics per camera (count, density, risk_level, density_trend, recent_counts)
2. HISTORICAL ANALYTICS — popular_times_by_camera: average crowd by hour-of-day from all recorded sessions

HOW TO USE EACH:
- "When does it get crowded?" / "Peak hours?" → use popular_times_by_camera. Cite the top hours and avg counts.
- "Is density trending up or down?" → use density_trend field + recent_counts array to describe the direction.
- "Current state?" / "What's happening now?" → use live state metrics.
- Data is limited (e.g. one camera, few samples)? Say "Based on available data from [camera]..." and still give a useful answer. Never flat-out refuse.

STYLE RULES:
- Concise, authoritative, action-oriented. No hedging, no disclaimers about future prediction.
- Cite exact numbers from context. Never invent cameras, metrics, or alerts.
- When recommending action: announce → divert → gate → evacuate (graduated responses).
- If genuinely no data exists for a question, say "Insufficient data recorded yet" — one sentence, move on.
"""

_TRIAGE_SYSTEM = (
    "You are CrowdSafe Triage. Given a list of active alerts, return strict "
    "JSON: {\"plan\":[{\"alert_id\":str,\"priority\":int,\"action\":str,"
    "\"rationale\":str}]}. priority: 1=highest. No extra keys, no prose."
)


def _compute_trend(densities: list[float]) -> str:
    """Classify density direction from a time-ordered list (oldest first)."""
    if len(densities) < 4:
        return 'insufficient_data'
    half = len(densities) // 2
    old_avg = sum(densities[:half]) / half
    new_avg = sum(densities[half:]) / (len(densities) - half)
    if old_avg == 0:
        return 'stable'
    ratio = new_avg / old_avg
    if ratio > 1.12:
        return 'increasing'
    if ratio < 0.88:
        return 'decreasing'
    return 'stable'


def _popular_times(camera_id: str) -> list[dict]:
    """Top-5 busiest hours for a camera, from all historical metrics."""
    rows = db.session.execute(text("""
        SELECT
            CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
            AVG("count")  AS avg_count,
            COUNT(*)      AS samples
        FROM metrics
        WHERE camera_id = :cid
        GROUP BY hour
        ORDER BY avg_count DESC
        LIMIT 5
    """), {'cid': camera_id}).fetchall()

    def _label(h):
        return f"{h % 12 or 12}{'AM' if h < 12 else 'PM'}"

    return [
        {
            'hour':      int(r[0]),
            'label':     _label(int(r[0])),
            'avg_count': round(float(r[1] or 0), 1),
            'samples':   int(r[2] or 0),
        }
        for r in rows
    ]


def _live_snapshot(limit_cams: int = 16) -> dict:
    """Enriched snapshot: live state + density trends + historical peak hours."""
    status = camera_manager.get_all_status()
    cam_ids = list(status.keys())[:limit_cams]

    # Fetch camera names
    cam_names = {c.id: c.name for c in Camera.query.filter(Camera.id.in_(cam_ids)).all()}

    cams = []
    for cam_id in cam_ids:
        info = status[cam_id]
        m = info.get('metrics', {}) or {}

        # Last 20 metrics for trend computation (oldest first)
        recent = (Metric.query
                  .filter_by(camera_id=cam_id)
                  .order_by(Metric.timestamp.desc())
                  .limit(20).all())
        densities = [r.density for r in reversed(recent)]
        counts    = [r.count   for r in reversed(recent)]

        cams.append({
            'camera_id':      cam_id,
            'name':           cam_names.get(cam_id, cam_id),
            'running':        info.get('running', False),
            'count':          m.get('count', 0),
            'density':        m.get('density', 0),
            'risk_level':     m.get('risk_level', 'UNKNOWN'),
            'risk_score':     round(m.get('risk_score', 0), 3),
            'avg_velocity':   m.get('avg_velocity', 0),
            'density_trend':  _compute_trend(densities),
            'recent_counts':  counts[-5:],   # last 5 readings, oldest→newest
        })

    # Historical peak hours per camera
    popular_times_by_camera = {
        cam_id: _popular_times(cam_id)
        for cam_id in cam_ids
    }

    active_alerts = (
        Alert.query.filter_by(resolved=False)
        .order_by(Alert.timestamp.desc())
        .limit(20).all()
    )

    return {
        'cameras': cams,
        'popular_times_by_camera': popular_times_by_camera,
        'active_alerts': [
            {
                'alert_id':  a.alert_id,
                'camera_id': a.camera_id,
                'risk_level': a.risk_level,
                'trigger':   a.trigger_condition,
                'message':   a.message,
            }
            for a in active_alerts
        ],
    }


@copilot_bp.route('/chat', methods=['POST'])
@token_required
@limiter.limit('30 per minute')
def chat():
    if not llm_service.is_configured():
        return jsonify({'error': 'LLM not configured (OR_API_KEY missing)'}), 503

    data = request.get_json(silent=True) or {}
    question = (data.get('message') or '').strip()
    if not question:
        return jsonify({'error': 'message required'}), 400

    include_live  = bool(data.get('include_live', True))
    extra_context = data.get('context')

    context_parts: list[str] = []
    if include_live:
        context_parts.append('LIVE STATE + HISTORICAL:\n' + json.dumps(_live_snapshot(), default=str))
    if extra_context:
        context_parts.append('USER CONTEXT:\n' + json.dumps(extra_context, default=str)[:4000])

    user_content = (
        '\n\n'.join(context_parts)
        + ('\n\n' if context_parts else '')
        + f'OPERATOR: {question}'
    )

    try:
        resp = llm_service.chat(
            messages=[
                {'role': 'system', 'content': _CHAT_SYSTEM},
                {'role': 'user',   'content': user_content},
            ],
            tier='default',
            temperature=0.2,
            max_tokens=600,
        )
        return jsonify({
            'answer': resp.text,
            'model':  resp.model,
            'usage':  resp.usage,
        })
    except Exception as e:
        return jsonify({'error': f'LLM error: {e}'}), 502


@copilot_bp.route('/triage', methods=['POST'])
@token_required
@limiter.limit('15 per minute')
def triage():
    if not llm_service.is_configured():
        return jsonify({'error': 'LLM not configured'}), 503

    data = request.get_json(silent=True) or {}
    alert_ids = data.get('alert_ids') or []
    if alert_ids:
        alerts = Alert.query.filter(Alert.alert_id.in_(alert_ids)).all()
    else:
        alerts = (
            Alert.query.filter_by(resolved=False)
            .order_by(Alert.timestamp.desc())
            .limit(20).all()
        )

    if not alerts:
        return jsonify({'plan': []})

    camera_names = {
        c.id: c.name for c in Camera.query.filter(
            Camera.id.in_([a.camera_id for a in alerts])
        ).all()
    }

    payload = [
        {
            'alert_id':  a.alert_id,
            'camera':    camera_names.get(a.camera_id, a.camera_id),
            'risk_level': a.risk_level,
            'trigger':   a.trigger_condition,
            'message':   a.message,
            'metrics':   a.metrics_snapshot,
        }
        for a in alerts
    ]

    try:
        result = llm_service.json_response(
            prompt=json.dumps({'alerts': payload}, default=str),
            system=_TRIAGE_SYSTEM,
            tier='nano',
            temperature=0.0,
            max_tokens=800,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'LLM error: {e}'}), 502
