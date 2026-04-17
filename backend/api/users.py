from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.models.user import User
from backend.utils.validators import validate_email, validate_username, validate_password
from backend.utils.decorators import role_required
import secrets

users_bp = Blueprint('users', __name__)


@users_bp.route('', methods=['GET'])
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users])


@users_bp.route('', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'viewer')

    if not validate_username(username):
        return jsonify({'error': 'Invalid username (3-50 alphanumeric/underscore)'}), 400
    if not validate_email(email):
        return jsonify({'error': 'Invalid email address'}), 400
    if not validate_password(password):
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if role not in ('admin', 'operator', 'viewer'):
        return jsonify({'error': 'Invalid role'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 409

    user = User(
        username=username,
        email=email,
        full_name=data.get('full_name', ''),
        role=role,
        phone=data.get('phone', ''),
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@users_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    data = request.get_json() or {}
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'email' in data and validate_email(data['email']):
        user.email = data['email']
    if 'role' in data and data['role'] in ('admin', 'operator', 'viewer'):
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = bool(data['is_active'])
    if 'phone' in data:
        user.phone = data['phone']
    db.session.commit()
    return jsonify(user.to_dict())


@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})


@users_bp.route('/<int:user_id>/reset-password', methods=['POST'])
def reset_password(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    temp_password = secrets.token_urlsafe(10)
    user.set_password(temp_password)
    db.session.commit()
    return jsonify({'temporary_password': temp_password})
