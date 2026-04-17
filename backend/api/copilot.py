"""LLM operator copilot.

Routes:
  POST /api/copilot/chat    — question + optional context → answer
  POST /api/copilot/triage  — list of alerts → ranked action plan (JSON)
"""
from __future__ import annotations

import json

from flask import Blueprint, g, jsonify, request

from backend.extensions import limiter
from backend.models.alert import Alert
from backend.models.camera import Camera
from backend.services import llm_service
from backend.services.camera_manager import camera_manager
from backend.utils.decorators import token_required

copilot_bp = Blueprint('copilot', __name__)


_CHAT_SYSTEM = (
    "You are CrowdSafe Copilot, an assistant to a live crowd-safety operator. "
    "Be concise, authoritative, and action-oriented. Cite exact numbers from "
    "the provided context. Never invent cameras, metrics, or alerts. When "
    "recommending actions, prefer reversible, graduated responses (announce → "
    "divert → gate → evacuate)."
)

_TRIAGE_SYSTEM = (
    "You are CrowdSafe Triage. Given a list of active alerts, return strict "
    "JSON: {\"plan\":[{\"alert_id\":str,\"priority\":int,\"action\":str,"
    "\"rationale\":str}]}. priority: 1=highest. No extra keys, no prose."
)


def _live_snapshot(limit_cams: int = 16) -> dict:
    """Lightweight current-state snapshot for grounding."""
    status = camera_manager.get_all_status()
    cams = []
    for cam_id, info in list(status.items())[:limit_cams]:
        m = info.get('metrics', {}) or {}
        cams.append({
            'camera_id': cam_id,
            'running': info.get('running', False),
            'count': m.get('count', 0),
            'density': m.get('density', 0),
            'risk_level': m.get('risk_level', 'UNKNOWN'),
            'risk_score': m.get('risk_score', 0),
            'avg_velocity': m.get('avg_velocity', 0),
        })
    active_alerts = (
        Alert.query.filter_by(resolved=False)
        .order_by(Alert.timestamp.desc())
        .limit(20)
        .all()
    )
    return {
        'cameras': cams,
        'active_alerts': [
            {
                'alert_id': a.alert_id,
                'camera_id': a.camera_id,
                'risk_level': a.risk_level,
                'trigger': a.trigger_condition,
                'message': a.message,
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

    include_live = bool(data.get('include_live', True))
    extra_context = data.get('context')

    context_parts: list[str] = []
    if include_live:
        context_parts.append('LIVE STATE:\n' + json.dumps(_live_snapshot(), default=str))
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
                {'role': 'user', 'content': user_content},
            ],
            tier='default',
            temperature=0.2,
            max_tokens=600,
        )
        return jsonify({
            'answer': resp.text,
            'model': resp.model,
            'usage': resp.usage,
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
            .limit(20)
            .all()
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
            'alert_id': a.alert_id,
            'camera': camera_names.get(a.camera_id, a.camera_id),
            'risk_level': a.risk_level,
            'trigger': a.trigger_condition,
            'message': a.message,
            'metrics': a.metrics_snapshot,
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
