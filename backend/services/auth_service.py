import jwt
import datetime
from flask import current_app
from backend.extensions import db
from backend.models.user import User


class AuthService:
    """JWT authentication service."""

    @staticmethod
    def login(username, password):
        """Authenticate user, return tokens."""
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return None, 'Invalid username or password'
        if not user.is_active:
            return None, 'Account is deactivated'

        user.last_login = datetime.datetime.now(datetime.timezone.utc)
        db.session.commit()

        access_token = AuthService._create_token(
            user.id,
            current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            token_type='access'
        )
        refresh_token = AuthService._create_token(
            user.id,
            current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
            token_type='refresh'
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(),
            'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
        }, None

    @staticmethod
    def refresh(refresh_token_str):
        """Refresh an access token."""
        try:
            data = jwt.decode(
                refresh_token_str,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            if data.get('type') != 'refresh':
                return None, 'Invalid token type'

            user = User.query.get(data['user_id'])
            if not user or not user.is_active:
                return None, 'Invalid user'

            new_access = AuthService._create_token(
                user.id,
                current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
                token_type='access'
            )
            return {'access_token': new_access, 'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES']}, None

        except jwt.ExpiredSignatureError:
            return None, 'Refresh token expired'
        except jwt.InvalidTokenError:
            return None, 'Invalid refresh token'

    @staticmethod
    def _create_token(user_id, expires_seconds, token_type='access'):
        payload = {
            'user_id': user_id,
            'type': token_type,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_seconds),
            'iat': datetime.datetime.now(datetime.timezone.utc),
        }
        return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
