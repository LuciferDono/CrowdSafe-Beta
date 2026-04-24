import jwt
from functools import wraps
from flask import request, jsonify, current_app, g
from backend.models.user import User


def _demo_user():
    """Return (and lazily create) the demo admin used when AUTH_DISABLED."""
    from backend.extensions import db

    user = User.query.filter_by(username='admin').first()
    if user is None:
        user = User.query.filter_by(role='admin').first()
    if user is None:
        user = User(
            username='admin',
            email='admin@crowdsafe.local',
            role='admin',
            is_active=True,
        )
        if hasattr(user, 'set_password'):
            user.set_password('admin')
        db.session.add(user)
        db.session.commit()
    return user


def token_required(f):
    """Require valid JWT token for API access (bypassed when AUTH_DISABLED)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_app.config.get('AUTH_DISABLED'):
            g.current_user = _demo_user()
            return f(*args, **kwargs)

        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]

        if not token:
            token = request.cookies.get('access_token')

        if not token:
            return jsonify({'error': 'Authentication token required'}), 401

        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            user = User.query.get(data['user_id'])
            if not user or not user.is_active:
                return jsonify({'error': 'Invalid or inactive user'}), 401
            g.current_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Require specific user role(s) (bypassed when AUTH_DISABLED)."""
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if current_app.config.get('AUTH_DISABLED'):
                return f(*args, **kwargs)
            if g.current_user.role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
