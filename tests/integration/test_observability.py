"""Observability wiring tests: /metrics endpoint + Sentry init guard."""
from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.mark.integration
class TestPrometheusEndpoint:
    def test_metrics_endpoint_serves_text(self, client):
        r = client.get('/metrics')
        assert r.status_code == 200
        body = r.get_data(as_text=True)
        # prometheus_client default content-type.
        assert 'text/plain' in r.headers.get('Content-Type', '')
        # At least the app_info metric should be present.
        assert 'crowdsafe_app_info' in body

    def test_custom_metrics_exposed(self, client):
        r = client.get('/metrics')
        body = r.get_data(as_text=True)
        # All registered custom metrics should show up (even at zero).
        for name in (
            'crowdsafe_cameras_active',
            'crowdsafe_alerts_total',
            'crowdsafe_dense_count_invocations_total',
            'crowdsafe_audit_events_total',
        ):
            assert name in body, f'missing metric {name}'


@pytest.mark.integration
class TestRecordHelpers:
    def test_record_alert_bumps_counter(self, client):
        from backend.observability import record_alert

        before = client.get('/metrics').get_data(as_text=True)
        record_alert('WARNING')
        after = client.get('/metrics').get_data(as_text=True)

        # Counter should have WARNING label populated after the call.
        assert 'crowdsafe_alerts_total{level="WARNING"}' in after
        # And its value should have increased (text comparison is enough).
        assert after != before

    def test_record_audit_event_bumps_counter(self, client):
        from backend.observability import record_audit_event

        record_audit_event('test.metric')
        body = client.get('/metrics').get_data(as_text=True)
        assert 'crowdsafe_audit_events_total{action="test.metric"}' in body

    def test_set_risk_score_emits_gauge(self, client):
        from backend.observability import set_risk_score

        set_risk_score('cam-X', 0.42)
        body = client.get('/metrics').get_data(as_text=True)
        assert 'crowdsafe_risk_score{camera_id="cam-X"} 0.42' in body

    def test_set_cameras_active_emits_gauge(self, client):
        from backend.observability import set_cameras_active

        set_cameras_active(7)
        body = client.get('/metrics').get_data(as_text=True)
        assert 'crowdsafe_cameras_active 7.0' in body


@pytest.mark.integration
class TestSentryInit:
    def test_no_dsn_skips_init(self, app):
        from backend.observability import init_sentry

        app.config['SENTRY_DSN'] = ''
        assert init_sentry(app) is False

    def test_dsn_triggers_init(self, app):
        from backend import observability

        app.config['SENTRY_DSN'] = 'https://pub@sentry.io/1'
        with patch('sentry_sdk.init') as mocked_init:
            assert observability.init_sentry(app) is True
            assert mocked_init.called

    def test_init_swallows_errors(self, app):
        from backend import observability

        app.config['SENTRY_DSN'] = 'https://pub@sentry.io/1'
        with patch('sentry_sdk.init', side_effect=RuntimeError('boom')):
            assert observability.init_sentry(app) is False


class TestScrubPII:
    def test_jwt_in_message_redacted(self):
        from backend.observability import scrub_pii

        # Realistic JWT shape: three dot-separated base64url-ish segments
        # starting with eyJ (the literal {" header prefix).
        jwt = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIxMjM0NQ_abcdef.dBjftJeZ4CVP_abc'
        event = {'message': f'failed with token {jwt} in request'}
        out = scrub_pii(event, {})
        assert '[jwt-redacted]' in out['message']
        assert jwt not in out['message']

    def test_bearer_header_redacted(self):
        from backend.observability import scrub_pii

        event = {
            'request': {
                'headers': {
                    'Authorization': 'Bearer s3cret.token.value',
                    'X-API-Key': 'abc-def',
                    'User-Agent': 'pytest',
                },
                'cookies': {
                    'access_token': 'jwt-here',
                    'session': 'sess-id',
                    'pref': 'dark',
                },
            }
        }
        out = scrub_pii(event, {})
        headers = out['request']['headers']
        assert headers['Authorization'] == '[redacted]'
        assert headers['X-API-Key'] == '[redacted]'
        assert headers['User-Agent'] == 'pytest'

        cookies = out['request']['cookies']
        assert cookies['access_token'] == '[redacted]'
        assert cookies['session'] == '[redacted]'
        assert cookies['pref'] == 'dark'
