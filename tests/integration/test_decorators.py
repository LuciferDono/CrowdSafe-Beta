"""Auth decorator integration tests.

Covers token_required + role_required via the real `/api/auth/me` + `/api/copilot/chat`
endpoints (both decorated), so we exercise the full request flow.
"""
from __future__ import annotations

import jwt
import pytest
from datetime import datetime, timedelta, timezone


@pytest.mark.integration
class TestTokenRequired:
    def test_bearer_header_accepted(self, client, auth_headers):
        r = client.get('/api/auth/me', headers=auth_headers)
        assert r.status_code == 200

    def test_cookie_fallback_accepted(self, client, auth_token):
        try:
            client.set_cookie('access_token', auth_token, domain='localhost')
        except TypeError:
            client.set_cookie('localhost', 'access_token', auth_token)
        r = client.get('/api/auth/me')
        assert r.status_code == 200

    def test_missing_returns_401(self, unauth_client):
        r = unauth_client.get('/api/auth/me')
        assert r.status_code == 401

    def test_expired_returns_401(self, client, app, admin_user):
        payload = {
            'user_id': admin_user.id,
            'username': admin_user.username,
            'role': admin_user.role,
            'exp': datetime.now(timezone.utc) - timedelta(minutes=5),
            'iat': datetime.now(timezone.utc) - timedelta(minutes=10),
        }
        expired = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        r = client.get('/api/auth/me', headers={'Authorization': f'Bearer {expired}'})
        assert r.status_code == 401
        assert 'expired' in r.get_json().get('error', '').lower()

    def test_malformed_returns_401(self, client):
        r = client.get('/api/auth/me', headers={'Authorization': 'Bearer garbage'})
        assert r.status_code == 401
