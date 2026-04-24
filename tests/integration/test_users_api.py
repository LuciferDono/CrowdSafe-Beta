"""Users API integration tests."""
from __future__ import annotations

import uuid

import pytest


def _unique(prefix='tuser'):
    return f'{prefix}_{uuid.uuid4().hex[:8]}'


@pytest.mark.integration
class TestListUsers:
    def test_list(self, client, admin_user):
        r = client.get('/api/users')
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)
        assert any(u['username'] == admin_user.username for u in data)


@pytest.mark.integration
class TestCreateUser:
    def test_happy_path(self, client):
        uname = _unique()
        r = client.post('/api/users', json={
            'username': uname,
            'email': f'{uname}@example.com',
            'password': 'secret123',
            'role': 'viewer',
            'full_name': 'Test Viewer',
        })
        assert r.status_code == 201
        assert r.get_json()['username'] == uname

    def test_invalid_username(self, client):
        r = client.post('/api/users', json={
            'username': 'ab',  # too short
            'email': 'a@b.com',
            'password': 'secret123',
        })
        assert r.status_code == 400

    def test_invalid_email(self, client):
        r = client.post('/api/users', json={
            'username': _unique(),
            'email': 'not-an-email',
            'password': 'secret123',
        })
        assert r.status_code == 400

    def test_short_password(self, client):
        r = client.post('/api/users', json={
            'username': _unique(),
            'email': 'x@example.com',
            'password': 'abc',
        })
        assert r.status_code == 400

    def test_invalid_role(self, client):
        r = client.post('/api/users', json={
            'username': _unique(),
            'email': f'{_unique()}@example.com',
            'password': 'secret123',
            'role': 'god',
        })
        assert r.status_code == 400

    def test_duplicate_username(self, client, admin_user):
        r = client.post('/api/users', json={
            'username': admin_user.username,
            'email': f'{_unique()}@example.com',
            'password': 'secret123',
        })
        assert r.status_code == 409

    def test_duplicate_email(self, client, admin_user):
        r = client.post('/api/users', json={
            'username': _unique(),
            'email': admin_user.email,
            'password': 'secret123',
        })
        assert r.status_code == 409


@pytest.mark.integration
class TestUpdateUser:
    def test_not_found(self, client):
        r = client.put('/api/users/999999', json={'full_name': 'X'})
        assert r.status_code == 404

    def test_update_fields(self, client, app):
        from backend.extensions import db
        from backend.models.user import User

        with app.app_context():
            u = User(username=_unique(), email=f'{_unique()}@ex.com', role='viewer')
            u.set_password('secret123')
            db.session.add(u)
            db.session.commit()
            uid = u.id

        r = client.put(f'/api/users/{uid}', json={
            'full_name': 'Updated',
            'email': f'{_unique()}@ex.com',
            'role': 'operator',
            'is_active': False,
            'phone': '+1-555-0100',
        })
        assert r.status_code == 200
        body = r.get_json()
        assert body['full_name'] == 'Updated'
        assert body['role'] == 'operator'
        assert body['is_active'] is False


@pytest.mark.integration
class TestResetPassword:
    def test_not_found(self, client):
        r = client.post('/api/users/999999/reset-password')
        assert r.status_code == 404

    def test_resets(self, client, app):
        from backend.extensions import db
        from backend.models.user import User

        with app.app_context():
            u = User(username=_unique(), email=f'{_unique()}@ex.com', role='viewer')
            u.set_password('orig-password')
            db.session.add(u)
            db.session.commit()
            uid = u.id

        r = client.post(f'/api/users/{uid}/reset-password')
        assert r.status_code == 200
        assert 'temporary_password' in r.get_json()


@pytest.mark.integration
class TestDeleteUser:
    def test_not_found(self, client):
        r = client.delete('/api/users/999999')
        assert r.status_code == 404

    def test_delete(self, client, app):
        from backend.extensions import db
        from backend.models.user import User

        with app.app_context():
            u = User(username=_unique(), email=f'{_unique()}@ex.com', role='viewer')
            u.set_password('secret123')
            db.session.add(u)
            db.session.commit()
            uid = u.id

        r = client.delete(f'/api/users/{uid}')
        assert r.status_code == 200
