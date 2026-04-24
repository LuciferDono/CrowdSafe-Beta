"""Copilot API integration tests (LLM fully mocked)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.integration
class TestChat:
    def test_requires_token(self, unauth_client):
        r = unauth_client.post('/api/copilot/chat', json={'message': 'hi'})
        assert r.status_code == 401

    def test_llm_not_configured(self, client, auth_headers):
        with patch('backend.api.copilot.llm_service.is_configured', return_value=False):
            r = client.post('/api/copilot/chat', headers=auth_headers,
                            json={'message': 'hi'})
            assert r.status_code == 503

    def test_empty_message(self, client, auth_headers):
        with patch('backend.api.copilot.llm_service.is_configured', return_value=True):
            r = client.post('/api/copilot/chat', headers=auth_headers, json={'message': ''})
            assert r.status_code == 400

    def test_happy_path(self, client, auth_headers):
        fake = MagicMock(text='Stand down.', model='test-model', usage={'prompt_tokens': 1})
        with patch('backend.api.copilot.llm_service.is_configured', return_value=True), \
             patch('backend.api.copilot.llm_service.chat', return_value=fake):
            r = client.post('/api/copilot/chat', headers=auth_headers,
                            json={'message': 'status?', 'include_live': True})
            assert r.status_code == 200
            body = r.get_json()
            assert body['answer'] == 'Stand down.'
            assert body['model'] == 'test-model'

    def test_extra_context_accepted(self, client, auth_headers):
        fake = MagicMock(text='ok', model='m', usage={})
        with patch('backend.api.copilot.llm_service.is_configured', return_value=True), \
             patch('backend.api.copilot.llm_service.chat', return_value=fake):
            r = client.post('/api/copilot/chat', headers=auth_headers, json={
                'message': 'question',
                'include_live': False,
                'context': {'note': 'VIP in section C'},
            })
            assert r.status_code == 200

    def test_llm_exception_maps_to_502(self, client, auth_headers):
        with patch('backend.api.copilot.llm_service.is_configured', return_value=True), \
             patch('backend.api.copilot.llm_service.chat', side_effect=RuntimeError('boom')):
            r = client.post('/api/copilot/chat', headers=auth_headers,
                            json={'message': 'q'})
            assert r.status_code == 502


@pytest.mark.integration
class TestTriage:
    def test_requires_token(self, unauth_client):
        r = unauth_client.post('/api/copilot/triage', json={})
        assert r.status_code == 401

    def test_llm_not_configured(self, client, auth_headers):
        with patch('backend.api.copilot.llm_service.is_configured', return_value=False):
            r = client.post('/api/copilot/triage', headers=auth_headers, json={})
            assert r.status_code == 503

    def test_no_alerts_returns_empty_plan(self, client, auth_headers):
        with patch('backend.api.copilot.llm_service.is_configured', return_value=True):
            r = client.post('/api/copilot/triage', headers=auth_headers,
                            json={'alert_ids': ['does-not-exist']})
            assert r.status_code == 200
            assert r.get_json() == {'plan': []}

    def test_happy_path(self, client, auth_headers, app, camera):
        import uuid
        from backend.extensions import db
        from backend.models.alert import Alert

        aid = f'triage-{uuid.uuid4().hex[:8]}'
        with app.app_context():
            a = Alert(alert_id=aid, camera_id=camera.id, risk_level='WARNING',
                      message='m', trigger_condition='DENSITY_EXCEEDED')
            db.session.add(a)
            db.session.commit()

        with patch('backend.api.copilot.llm_service.is_configured', return_value=True), \
             patch('backend.api.copilot.llm_service.json_response',
                   return_value={'plan': [{'alert_id': aid, 'priority': 1,
                                           'action': 'announce', 'rationale': 'first'}]}):
            r = client.post('/api/copilot/triage', headers=auth_headers, json={})
            assert r.status_code == 200
            body = r.get_json()
            assert body['plan'][0]['alert_id'] == aid

    def test_llm_exception_maps_to_502(self, client, auth_headers, app, camera):
        import uuid
        from backend.extensions import db
        from backend.models.alert import Alert

        aid = f'triage-fail-{uuid.uuid4().hex[:8]}'
        with app.app_context():
            a = Alert(alert_id=aid, camera_id=camera.id, risk_level='WARNING', message='m')
            db.session.add(a)
            db.session.commit()

        with patch('backend.api.copilot.llm_service.is_configured', return_value=True), \
             patch('backend.api.copilot.llm_service.json_response',
                   side_effect=RuntimeError('boom')):
            r = client.post('/api/copilot/triage', headers=auth_headers,
                            json={'alert_ids': [aid]})
            assert r.status_code == 502
