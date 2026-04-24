"""AuthService unit/integration tests."""
from __future__ import annotations

import jwt
import pytest

from backend.services.auth_service import AuthService


@pytest.mark.integration
class TestLogin:
    def test_invalid_credentials_return_error(self, app, admin_user):
        with app.app_context():
            out, err = AuthService.login(admin_user.username, 'wrong')
            assert out is None
            assert err == 'Invalid username or password'

    def test_happy_path_returns_tokens(self, app, admin_user):
        with app.app_context():
            out, err = AuthService.login(admin_user.username, 'test-password-123')
            assert err is None
            assert out['access_token']
            assert out['refresh_token']
            assert out['user']['username'] == admin_user.username

    def test_inactive_user_blocked(self, app, admin_user):
        from backend.extensions import db
        from backend.models.user import User

        with app.app_context():
            u = User.query.get(admin_user.id)
            u.is_active = False
            db.session.commit()
            try:
                out, err = AuthService.login(admin_user.username, 'test-password-123')
                assert out is None
                assert err == 'Account is deactivated'
            finally:
                u.is_active = True
                db.session.commit()


@pytest.mark.integration
class TestRefresh:
    def test_valid_refresh_returns_new_access(self, app, admin_user):
        with app.app_context():
            out, _ = AuthService.login(admin_user.username, 'test-password-123')
            refreshed, err = AuthService.refresh(out['refresh_token'])
            assert err is None
            assert refreshed['access_token']

    def test_access_token_rejected_as_refresh(self, app, admin_user):
        with app.app_context():
            out, _ = AuthService.login(admin_user.username, 'test-password-123')
            refreshed, err = AuthService.refresh(out['access_token'])
            assert refreshed is None
            assert 'token type' in err.lower()

    def test_garbage_rejected(self, app):
        with app.app_context():
            refreshed, err = AuthService.refresh('not-a-valid-jwt')
            assert refreshed is None
            assert err == 'Invalid refresh token'
