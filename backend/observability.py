"""Observability wiring: Sentry error tracking + Prometheus metrics.

Both are opt-in:

- **Sentry** only initializes when ``SENTRY_DSN`` is set. No DSN, no init,
  no background threads. ``scrub_pii`` strips JWTs + API keys from events
  before they leave the process (defense in depth — keys should never
  reach Sentry anyway).
- **Prometheus** exposes ``/metrics`` via prometheus_flask_exporter when
  ``METRICS_ENABLED`` is true (default). Custom gauges/counters track
  crowd-safety signals that generic HTTP metrics miss: active cameras,
  alert counts by severity, risk-score gauge per camera, dense-count
  invocations.

Failures here are non-fatal. Audit, request handling, and video
processing must never break because observability is misconfigured.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger('observability')

_JWT_RE = re.compile(r'eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}')
_BEARER_RE = re.compile(r'(?i)bearer\s+[A-Za-z0-9_\-.]+')
_SENSITIVE_HEADER_RE = re.compile(r'(?i)(x-api-key|authorization|cookie)')

_metrics: Any = None
cameras_active_gauge: Any = None
alerts_total_counter: Any = None
risk_score_gauge: Any = None
dense_invocations_counter: Any = None
audit_events_counter: Any = None


def scrub_pii(event: dict, _hint: dict) -> dict | None:
    """Sentry before_send: strip JWTs and auth headers. Returns None to drop."""
    try:
        request = event.get('request') or {}
        headers = request.get('headers') or {}
        for k in list(headers.keys()):
            if _SENSITIVE_HEADER_RE.match(k or ''):
                headers[k] = '[redacted]'

        cookies = request.get('cookies') or {}
        for k in list(cookies.keys()):
            if k.lower() in ('access_token', 'refresh_token', 'session'):
                cookies[k] = '[redacted]'

        msg = event.get('message')
        if isinstance(msg, str):
            event['message'] = _scrub_str(msg)

        for entry in (event.get('breadcrumbs') or {}).get('values', []) or []:
            if isinstance(entry.get('message'), str):
                entry['message'] = _scrub_str(entry['message'])

        return event
    except Exception:
        return event  # never break delivery on scrub failure


def _scrub_str(s: str) -> str:
    s = _JWT_RE.sub('[jwt-redacted]', s)
    s = _BEARER_RE.sub('Bearer [redacted]', s)
    return s


def init_sentry(app) -> bool:
    """Initialize Sentry if DSN configured. Returns True if active."""
    dsn = app.config.get('SENTRY_DSN') or ''
    if not dsn:
        return False
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[FlaskIntegration(), SqlalchemyIntegration()],
            traces_sample_rate=float(app.config.get('SENTRY_TRACES_SAMPLE_RATE', 0.1)),
            environment=app.config.get('SENTRY_ENVIRONMENT', 'development'),
            send_default_pii=False,
            before_send=scrub_pii,
        )
        app.logger.info('Sentry initialized (env=%s)',
                        app.config.get('SENTRY_ENVIRONMENT'))
        return True
    except Exception as e:
        app.logger.warning('Sentry init failed: %s', e)
        return False


def init_prometheus(app) -> bool:
    """Initialize Prometheus /metrics endpoint + custom gauges/counters."""
    global _metrics, cameras_active_gauge, alerts_total_counter
    global risk_score_gauge, dense_invocations_counter, audit_events_counter

    if not app.config.get('METRICS_ENABLED', True):
        return False
    try:
        from prometheus_flask_exporter import PrometheusMetrics
        from prometheus_client import Counter, Gauge

        _metrics = PrometheusMetrics(
            app,
            defaults_prefix='crowdsafe',
            group_by='endpoint',
        )
        _metrics.info(
            'crowdsafe_app_info',
            'CrowdSafe application info',
            version=app.config.get('APP_VERSION', '0.1.0'),
        )

        # Idempotent custom metric registration — prometheus_client raises on
        # duplicate names, which blows up test suites that call create_app()
        # multiple times. ``_already_registered`` catches re-init safely.
        cameras_active_gauge = _get_or_create(
            Gauge, 'crowdsafe_cameras_active',
            'Number of cameras currently processing video',
        )
        alerts_total_counter = _get_or_create(
            Counter, 'crowdsafe_alerts_total',
            'Total alerts emitted, labelled by severity',
            ['level'],
        )
        risk_score_gauge = _get_or_create(
            Gauge, 'crowdsafe_risk_score',
            'Latest risk score (0..1) per camera',
            ['camera_id'],
        )
        dense_invocations_counter = _get_or_create(
            Counter, 'crowdsafe_dense_count_invocations_total',
            'Times CSRNet dense counting was invoked',
        )
        audit_events_counter = _get_or_create(
            Counter, 'crowdsafe_audit_events_total',
            'Audit log entries written, labelled by action',
            ['action'],
        )
        app.logger.info('Prometheus /metrics enabled')
        return True
    except Exception as e:
        app.logger.warning('Prometheus init failed: %s', e)
        return False


def _get_or_create(cls, name: str, doc: str, labels: list | None = None):
    """Idempotent metric registration — survive repeated create_app() calls."""
    from prometheus_client import REGISTRY
    existing = REGISTRY._names_to_collectors.get(name)
    if existing is not None:
        return existing
    if labels:
        return cls(name, doc, labels)
    return cls(name, doc)


def record_alert(level: str) -> None:
    """Bump alert counter. Safe when prometheus not initialized."""
    if alerts_total_counter is None:
        return
    try:
        alerts_total_counter.labels(level=(level or 'unknown')).inc()
    except Exception:
        pass


def record_audit_event(action: str) -> None:
    if audit_events_counter is None:
        return
    try:
        audit_events_counter.labels(action=(action or 'unknown')).inc()
    except Exception:
        pass


def record_dense_invocation() -> None:
    if dense_invocations_counter is None:
        return
    try:
        dense_invocations_counter.inc()
    except Exception:
        pass


def set_cameras_active(n: int) -> None:
    if cameras_active_gauge is None:
        return
    try:
        cameras_active_gauge.set(n)
    except Exception:
        pass


def set_risk_score(camera_id: str, score: float) -> None:
    if risk_score_gauge is None:
        return
    try:
        risk_score_gauge.labels(camera_id=str(camera_id)).set(float(score))
    except Exception:
        pass
