"""Shared pytest fixtures.

Tests use an isolated SQLite database per session. Integration tests reuse a
Flask test client with the normal app factory, so blueprints + extensions are
wired exactly as in production.
"""
from __future__ import annotations

import atexit
import os
import sys
import tempfile

import pytest

# CRITICAL: DATABASE_URL must be set BEFORE any backend import, because
# ``config.Config`` evaluates ``SQLALCHEMY_DATABASE_URI`` at class-body
# (import) time. Setting it inside a fixture is too late — pytest collection
# imports test modules, which pull in ``backend.*``, which imports ``config``,
# which freezes the URI. Anything after that runs against ``instance/crowdsafe.db``
# (the dev DB), silently corrupting test state.
_TMP_DB_FD, _TMP_DB_PATH = tempfile.mkstemp(suffix='.db', prefix='crowdsafe_test_')
os.close(_TMP_DB_FD)


@atexit.register
def _cleanup_tmp_db():  # noqa: D401
    try:
        os.remove(_TMP_DB_PATH)
    except OSError:
        pass


os.environ['DATABASE_URL'] = f'sqlite:///{_TMP_DB_PATH}'

# Tests always run with deterministic secrets + ephemeral SQLite.
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('JWT_SECRET_KEY', 'test-jwt-secret')
os.environ.setdefault('POSE_ENABLED', 'False')
os.environ.setdefault('FORECAST_ENABLED', 'True')
os.environ.setdefault('RATELIMIT_STORAGE_URI', 'memory://')
# Tests assert real auth enforcement; override demo default.
os.environ['AUTH_DISABLED'] = 'False'
# Test suite asserts canonical 300s default; pin to override any .env override.
os.environ['FORECAST_HORIZON_SECONDS'] = '300'

# Ensure project root on sys.path (pytest auto-adds rootdir, but this protects
# against tox/containerized runs that shuffle cwd).
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


@pytest.fixture(scope='session')
def _tmp_db_path():
    return _TMP_DB_PATH


@pytest.fixture(scope='session')
def app(_tmp_db_path):
    from backend import create_app
    from backend.extensions import db

    flask_app = create_app()
    flask_app.config['TESTING'] = True
    flask_app.config['RATELIMIT_ENABLED'] = False

    with flask_app.app_context():
        db.create_all()

    return flask_app


@pytest.fixture
def client(app, auth_token):
    """Authenticated test client.

    Most integration tests target admin-only endpoints, so by default the
    test client sends ``Authorization: Bearer <admin JWT>`` on every request.
    Tests that specifically need to verify anonymous behavior (e.g. the
    ``/api/auth/me`` 401 path) use the ``unauth_client`` fixture instead."""
    c = app.test_client()
    c.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {auth_token}'
    return c


@pytest.fixture
def unauth_client(app):
    """Raw test client with no auth headers preset."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    from backend.extensions import db

    with app.app_context():
        yield db.session
        db.session.rollback()


class _Ref:
    """Plain attribute bag — safe to access outside a SQLAlchemy session."""

    def __init__(self, **attrs):
        self.__dict__.update(attrs)


@pytest.fixture
def admin_user(app):
    from backend.extensions import db
    from backend.models.user import User

    with app.app_context():
        user = User.query.filter_by(username='test_admin').first()
        if user is None:
            user = User(
                username='test_admin',
                email='test_admin@crowdsafe.local',
                full_name='Test Admin',
                role='admin',
                is_active=True,
            )
            user.set_password('test-password-123')
            db.session.add(user)
            db.session.commit()
        return _Ref(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
        )


@pytest.fixture
def auth_token(app, admin_user):
    """Return a valid JWT for the admin_user fixture."""
    import jwt
    from datetime import datetime, timezone, timedelta

    payload = {
        'user_id': admin_user.id,
        'username': admin_user.username,
        'role': admin_user.role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')


@pytest.fixture
def auth_headers(auth_token):
    return {'Authorization': f'Bearer {auth_token}'}


@pytest.fixture
def camera(app):
    from backend.extensions import db
    from backend.models.camera import Camera

    with app.app_context():
        cam = Camera.query.filter_by(id='cam-test-1').first()
        if cam is None:
            cam = Camera(
                id='cam-test-1',
                name='Test Camera 1',
                location='Test Lab',
                source_type='file',
                source_url='',
                area_sqm=100.0,
                expected_capacity=500,
            )
            db.session.add(cam)
            db.session.commit()
        return _Ref(
            id=cam.id,
            name=cam.name,
            area_sqm=cam.area_sqm,
        )
