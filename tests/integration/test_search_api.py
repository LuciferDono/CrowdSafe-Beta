"""Search API integration tests (LLM fully mocked)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest


@pytest.fixture
def seeded(app, camera):
    from backend.extensions import db
    from backend.models.metric import Metric
    from backend.models.alert import Alert

    with app.app_context():
        base = datetime.now(timezone.utc) - timedelta(minutes=5)
        for i in range(3):
            db.session.add(Metric(
                camera_id=camera.id,
                timestamp=base + timedelta(minutes=i),
                count=5 + i,
                density=0.4 + i * 0.1,
                avg_velocity=1.0,
                surge_rate=0.0,
                risk_score=0.3,
                risk_level='SAFE',
            ))
        import uuid
        aid = f'search-a-{uuid.uuid4().hex[:8]}'
        db.session.add(Alert(alert_id=aid, camera_id=camera.id,
                             risk_level='CRITICAL', message='x',
                             trigger_condition='DENSITY_EXCEEDED'))
        db.session.commit()
        return {'camera_id': camera.id, 'alert_id': aid}


@pytest.mark.integration
class TestNLSearch:
    def test_requires_token(self, unauth_client):
        r = unauth_client.post('/api/search/nl', json={'q': 'x'})
        assert r.status_code == 401

    def test_llm_not_configured(self, client, auth_headers):
        with patch('backend.api.search.llm_service.is_configured', return_value=False):
            r = client.post('/api/search/nl', headers=auth_headers, json={'q': 'x'})
            assert r.status_code == 503

    def test_empty_q(self, client, auth_headers):
        with patch('backend.api.search.llm_service.is_configured', return_value=True):
            r = client.post('/api/search/nl', headers=auth_headers, json={'q': '   '})
            assert r.status_code == 400

    def test_metrics_query(self, client, auth_headers, seeded):
        spec = {'table': 'metrics',
                'filters': {'camera_id': seeded['camera_id'], 'min_density': 0.1},
                'limit': 10}
        with patch('backend.api.search.llm_service.is_configured', return_value=True), \
             patch('backend.api.search.llm_service.json_response', return_value=spec):
            r = client.post('/api/search/nl', headers=auth_headers,
                            json={'q': 'dense moments'})
            assert r.status_code == 200
            body = r.get_json()
            assert body['spec']['table'] == 'metrics'
            assert body['count'] >= 1

    def test_alerts_query(self, client, auth_headers, seeded):
        spec = {'table': 'alerts',
                'filters': {'risk_level': 'critical'},
                'limit': 10}
        with patch('backend.api.search.llm_service.is_configured', return_value=True), \
             patch('backend.api.search.llm_service.json_response', return_value=spec):
            r = client.post('/api/search/nl', headers=auth_headers,
                            json={'q': 'show me critical alerts'})
            assert r.status_code == 200
            body = r.get_json()
            assert body['spec']['table'] == 'alerts'

    def test_bad_table_rejected(self, client, auth_headers):
        spec = {'table': 'secrets', 'filters': {}}
        with patch('backend.api.search.llm_service.is_configured', return_value=True), \
             patch('backend.api.search.llm_service.json_response', return_value=spec):
            r = client.post('/api/search/nl', headers=auth_headers, json={'q': 'q'})
            assert r.status_code == 400

    def test_llm_exception_maps_to_502(self, client, auth_headers):
        with patch('backend.api.search.llm_service.is_configured', return_value=True), \
             patch('backend.api.search.llm_service.json_response',
                   side_effect=RuntimeError('boom')):
            r = client.post('/api/search/nl', headers=auth_headers, json={'q': 'q'})
            assert r.status_code == 502

    def test_non_dict_response_fails_gracefully(self, client, auth_headers):
        with patch('backend.api.search.llm_service.is_configured', return_value=True), \
             patch('backend.api.search.llm_service.json_response', return_value='not-a-dict'):
            r = client.post('/api/search/nl', headers=auth_headers, json={'q': 'q'})
            assert r.status_code == 400

    def test_filter_whitelist_strips_unknown(self, client, auth_headers, seeded):
        spec = {
            'table': 'metrics',
            'filters': {'camera_id': seeded['camera_id'], 'DROP_TABLE': 1, 'evil': 'x'},
            'limit': 5,
        }
        with patch('backend.api.search.llm_service.is_configured', return_value=True), \
             patch('backend.api.search.llm_service.json_response', return_value=spec):
            r = client.post('/api/search/nl', headers=auth_headers, json={'q': 'q'})
            assert r.status_code == 200
            body = r.get_json()
            assert 'DROP_TABLE' not in body['spec']['filters']
            assert 'evil' not in body['spec']['filters']

    def test_limit_clamped(self, client, auth_headers):
        spec = {'table': 'metrics', 'filters': {}, 'limit': 99999}
        with patch('backend.api.search.llm_service.is_configured', return_value=True), \
             patch('backend.api.search.llm_service.json_response', return_value=spec):
            r = client.post('/api/search/nl', headers=auth_headers, json={'q': 'q'})
            assert r.status_code == 200
            assert r.get_json()['spec']['limit'] == 500
