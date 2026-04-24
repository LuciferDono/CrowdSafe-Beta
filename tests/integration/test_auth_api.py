"""Auth API integration tests."""
from __future__ import annotations

import pytest


@pytest.mark.integration
class TestLogin:
    def test_login_missing_body_returns_400(self, client):
        r = client.post('/api/auth/login', json={})
        assert r.status_code == 400

    def test_login_bad_credentials_returns_401(self, client, admin_user):
        r = client.post('/api/auth/login', json={'username': admin_user.username, 'password': 'wrong'})
        assert r.status_code == 401

    def test_login_happy_path_returns_token(self, client, admin_user):
        r = client.post('/api/auth/login', json={
            'username': admin_user.username,
            'password': 'test-password-123',
        })
        assert r.status_code == 200
        data = r.get_json()
        assert 'access_token' in data
        assert data.get('expires_in', 0) > 0

    def test_login_sets_httponly_cookie(self, client, admin_user):
        r = client.post('/api/auth/login', json={
            'username': admin_user.username,
            'password': 'test-password-123',
        })
        cookie_header = r.headers.get('Set-Cookie', '')
        assert 'access_token=' in cookie_header
        assert 'HttpOnly' in cookie_header


@pytest.mark.integration
class TestMe:
    def test_me_without_token_returns_401(self, unauth_client):
        r = unauth_client.get('/api/auth/me')
        assert r.status_code == 401

    def test_me_with_token_returns_user(self, client, auth_headers, admin_user):
        r = client.get('/api/auth/me', headers=auth_headers)
        assert r.status_code == 200
        body = r.get_json()
        assert body['username'] == admin_user.username
        assert body['role'] == 'admin'


@pytest.mark.integration
class TestLogout:
    def test_logout_clears_cookie(self, client):
        r = client.post('/api/auth/logout')
        assert r.status_code == 200
        cookie_header = r.headers.get('Set-Cookie', '')
        # Either explicit delete or empty value with past expiry.
        assert 'access_token=' in cookie_header
