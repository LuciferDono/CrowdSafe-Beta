from flask import Blueprint, request, jsonify, make_response
from backend.services.auth_service import AuthService
from backend.utils.decorators import token_required
from flask import g

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    result, error = AuthService.login(username, password)
    if error:
        return jsonify({'error': error}), 401

    resp = make_response(jsonify(result))
    resp.set_cookie('access_token', result['access_token'],
                    httponly=True, samesite='Lax', max_age=result['expires_in'])
    return resp


@auth_bp.route('/logout', methods=['POST'])
def logout():
    resp = make_response(jsonify({'message': 'Logged out'}))
    resp.delete_cookie('access_token')
    return resp


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token', '')
    if not refresh_token:
        return jsonify({'error': 'Refresh token required'}), 400

    result, error = AuthService.refresh(refresh_token)
    if error:
        return jsonify({'error': error}), 401
    return jsonify(result)


@auth_bp.route('/me', methods=['GET'])
@token_required
def me():
    return jsonify(g.current_user.to_dict())
