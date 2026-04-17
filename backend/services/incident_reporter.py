"""Auto-draft incident reports for CRITICAL alerts.

Pulls: alert → camera → recent metric history → LLM → written report stored
in ``logs/incidents/<alert_id>.md``. Uses the premium model tier because
these are high-stakes artifacts that may be reviewed post-hoc by regulators.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone

from backend.extensions import db
from backend.models.alert import Alert
from backend.models.camera import Camera
from backend.models.metric import Metric
from backend.services import llm_service
from config import Config

logger = logging.getLogger('incident_reporter')

_SYSTEM = (
    "You draft post-incident reports for a crowd-safety SOC. Tone: factual, "
    "neutral, regulator-ready. Sections (markdown, in this order): "
    "## Summary, ## Timeline, ## Observed Metrics, ## Likely Cause, "
    "## Operator Actions Recommended, ## Follow-up Checklist. Do not invent "
    "facts. If data is missing, say so explicitly."
)


def _incidents_dir() -> str:
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'incidents')
    os.makedirs(base, exist_ok=True)
    return base


def _gather_context(alert: Alert, camera: Camera | None, lookback_minutes: int = 10) -> dict:
    since = (alert.timestamp or datetime.now(timezone.utc)) - timedelta(minutes=lookback_minutes)
    rows = (
        Metric.query.filter(
            Metric.camera_id == alert.camera_id,
            Metric.timestamp >= since,
        )
        .order_by(Metric.timestamp.asc())
        .limit(600)
        .all()
    )
    history = [
        {
            't': m._utc_iso(m.timestamp),
            'count': m.count,
            'density': round(m.density, 3),
            'velocity': round(m.avg_velocity, 2),
            'surge': round(m.surge_rate, 3),
            'risk_score': round(m.risk_score, 3),
            'risk_level': m.risk_level,
        }
        for m in rows
    ]

    return {
        'alert': {
            'alert_id': alert.alert_id,
            'timestamp': alert._utc_iso(alert.timestamp),
            'risk_level': alert.risk_level,
            'trigger': alert.trigger_condition,
            'message': alert.message,
            'metrics_snapshot': alert.metrics_snapshot,
        },
        'camera': {
            'id': camera.id if camera else alert.camera_id,
            'name': camera.name if camera else None,
            'location': camera.location if camera else None,
        },
        'history_minutes': lookback_minutes,
        'history_samples': len(history),
        'history': history,
    }


def draft_report(alert_id: str) -> dict | None:
    """Draft an incident report and persist it. Returns {path, markdown} or None."""
    if not llm_service.is_configured():
        logger.info('LLM not configured; skipping incident report for %s', alert_id)
        return None

    alert = Alert.query.filter_by(alert_id=alert_id).first()
    if not alert:
        logger.warning('draft_report: alert %s not found', alert_id)
        return None

    camera = Camera.query.get(alert.camera_id)
    context = _gather_context(alert, camera)

    prompt = (
        "Draft an incident report from the data below. Stay within the "
        "section structure specified by the system message.\n\n"
        f"DATA:\n{json.dumps(context, default=str)[:12000]}"
    )

    try:
        markdown = llm_service.simple(
            prompt,
            system=_SYSTEM,
            tier='premium',
            temperature=0.2,
            max_tokens=1500,
        )
    except Exception as e:
        logger.warning('incident draft failed for %s: %s', alert_id, e)
        return None

    header = (
        f"# Incident Report — {alert_id}\n\n"
        f"- **Camera:** {context['camera']['name'] or context['camera']['id']}\n"
        f"- **Location:** {context['camera']['location'] or 'n/a'}\n"
        f"- **Timestamp:** {context['alert']['timestamp']}\n"
        f"- **Risk:** {alert.risk_level} / {alert.trigger_condition}\n"
        f"- **Drafted:** {datetime.now(timezone.utc).isoformat()}\n\n---\n\n"
    )
    body = header + markdown.strip() + "\n"

    path = os.path.join(_incidents_dir(), f'{alert_id}.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(body)

    logger.info('Incident report drafted: %s', path)
    return {'path': path, 'markdown': body}


def schedule_if_critical(alert_data: dict, app) -> None:
    """Fire-and-forget hook called from AlertManager on CRITICAL."""
    if (alert_data.get('risk_level') or '').upper() != 'CRITICAL':
        return
    alert_id = alert_data.get('alert_id')
    if not alert_id:
        return

    import threading

    def _run():
        try:
            with app.app_context():
                draft_report(alert_id)
        except Exception as e:
            logger.warning('Background incident draft failed: %s', e)

    threading.Thread(target=_run, name=f'incident-{alert_id}', daemon=True).start()
