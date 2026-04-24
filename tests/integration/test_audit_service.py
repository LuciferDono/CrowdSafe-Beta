"""Audit log service + wiring tests."""
from __future__ import annotations

import uuid

import pytest


@pytest.mark.integration
class TestLogEventDirect:
    def test_writes_row(self, app):
        from backend.extensions import db
        from backend.models.audit_log import AuditLog
        from backend.services.audit_service import log_event

        with app.app_context():
            before = AuditLog.query.count()
            row = log_event(
                'test.direct',
                target_type='unit',
                target_id='x-1',
                meta={'k': 'v'},
            )
            assert row is not None
            assert AuditLog.query.count() == before + 1
            assert row.action == 'test.direct'
            assert row.target_id == 'x-1'
            assert '"k"' in row.meta

    def test_returns_none_on_bad_meta_serializes_anyway(self, app):
        from backend.services.audit_service import log_event

        class _Odd:
            pass

        with app.app_context():
            row = log_event('test.odd_meta', meta={'obj': _Odd()})
            assert row is not None  # serialize_error JSON still writes


@pytest.mark.integration
class TestAuditedDecorator:
    def test_endpoint_creates_audit_row(self, client, admin_user, app, auth_headers):
        from backend.extensions import db
        from backend.models.audit_log import AuditLog

        username = f'audit_t_{uuid.uuid4().hex[:6]}'
        r = client.post('/api/users', json={
            'username': username,
            'email': f'{username}@ex.com',
            'password': 'secret123',
            'role': 'viewer',
        })
        assert r.status_code == 201

        with app.app_context():
            rows = AuditLog.query.filter_by(action='user.create').all()
            assert any(row.status == 'ok' for row in rows)

    def test_404_path_logs_fail_status(self, client, app):
        from backend.models.audit_log import AuditLog

        r = client.put('/api/users/999999', json={'full_name': 'no'})
        assert r.status_code == 404

        with app.app_context():
            rows = AuditLog.query.filter_by(action='user.update').all()
            assert any(row.status == 'fail' for row in rows)


@pytest.mark.integration
class TestAuditReadAPI:
    def test_requires_admin(self, unauth_client):
        r = unauth_client.get('/api/audit')
        assert r.status_code == 401

    def test_admin_can_list(self, client, auth_headers, app):
        from backend.extensions import db
        from backend.services.audit_service import log_event

        with app.app_context():
            log_event('test.read', target_type='unit', target_id='r-1')

        r = client.get('/api/audit?action=test.read', headers=auth_headers)
        assert r.status_code == 200
        rows = r.get_json()
        assert any(row['action'] == 'test.read' for row in rows)

    def test_filters(self, client, auth_headers, app):
        from backend.services.audit_service import log_event

        tag = f'tag-{uuid.uuid4().hex[:6]}'
        with app.app_context():
            log_event('test.filter', target_type='unit', target_id=tag)
            log_event('test.filter', target_type='unit', target_id='other')

        r = client.get(f'/api/audit?action=test.filter&target_id={tag}',
                       headers=auth_headers)
        assert r.status_code == 200
        rows = r.get_json()
        assert all(row['target_id'] == tag for row in rows)

    def test_summary(self, client, auth_headers, app):
        from backend.services.audit_service import log_event

        with app.app_context():
            log_event('test.summary', target_type='unit', target_id='s-1')

        r = client.get('/api/audit/summary?hours=24', headers=auth_headers)
        assert r.status_code == 200
        body = r.get_json()
        assert 'total' in body
        assert 'by_action' in body
        assert body['window_hours'] == 24

    def test_limit_clamped(self, client, auth_headers):
        r = client.get('/api/audit?limit=99999', headers=auth_headers)
        assert r.status_code == 200
        assert len(r.get_json()) <= 500
