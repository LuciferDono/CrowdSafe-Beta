"""Venue API — group cameras into logical venues and expose rollup risk."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.extensions import db
from backend.models.venue import Venue
from backend.services.audit_service import audited
from backend.services.venue_service import (
    aggregate_all_venues,
    aggregate_venue_risk,
)
from backend.utils.decorators import role_required, token_required

venues_bp = Blueprint('venues', __name__)


@venues_bp.route('', methods=['GET'])
@token_required
def list_venues():
    venues = Venue.query.all()
    return jsonify([v.to_dict() for v in venues])


@venues_bp.route('/<venue_id>', methods=['GET'])
@token_required
def get_venue(venue_id):
    v = Venue.query.filter_by(id=venue_id).first()
    if v is None:
        return jsonify({'error': 'Venue not found'}), 404
    return jsonify(v.to_dict())


@venues_bp.route('', methods=['POST'])
@role_required('admin')
@audited('venue.create', target_type='venue', target_id_from='id')
def create_venue():
    data = request.get_json() or {}
    vid = str(data.get('id', '')).strip()
    name = str(data.get('name', '')).strip()
    if not vid or not name:
        return jsonify({'error': 'id and name required'}), 400
    if Venue.query.filter_by(id=vid).first():
        return jsonify({'error': 'Venue already exists'}), 409

    v = Venue(
        id=vid,
        name=name,
        venue_type=data.get('venue_type', 'generic'),
        location=data.get('location', ''),
        expected_capacity=int(data.get('expected_capacity', 0) or 0),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        is_active=bool(data.get('is_active', True)),
    )
    db.session.add(v)
    db.session.commit()
    return jsonify(v.to_dict()), 201


@venues_bp.route('/<venue_id>', methods=['PUT'])
@role_required('admin')
@audited('venue.update', target_type='venue', target_id_from='venue_id')
def update_venue(venue_id):
    v = Venue.query.filter_by(id=venue_id).first()
    if v is None:
        return jsonify({'error': 'Venue not found'}), 404
    data = request.get_json() or {}
    for field in ('name', 'venue_type', 'location'):
        if field in data:
            setattr(v, field, data[field])
    if 'expected_capacity' in data:
        v.expected_capacity = int(data['expected_capacity'] or 0)
    for field in ('latitude', 'longitude'):
        if field in data:
            setattr(v, field, data[field])
    if 'is_active' in data:
        v.is_active = bool(data['is_active'])
    db.session.commit()
    return jsonify(v.to_dict())


@venues_bp.route('/<venue_id>', methods=['DELETE'])
@role_required('admin')
@audited('venue.delete', target_type='venue', target_id_from='venue_id')
def delete_venue(venue_id):
    v = Venue.query.filter_by(id=venue_id).first()
    if v is None:
        return jsonify({'error': 'Venue not found'}), 404
    db.session.delete(v)
    db.session.commit()
    return jsonify({'status': 'deleted', 'id': venue_id})


@venues_bp.route('/<venue_id>/risk', methods=['GET'])
@token_required
def get_venue_risk(venue_id):
    block = aggregate_venue_risk(venue_id)
    if block is None:
        return jsonify({'error': 'Venue not found'}), 404
    return jsonify(block)


@venues_bp.route('/risk', methods=['GET'])
@token_required
def get_all_venues_risk():
    return jsonify(aggregate_all_venues())
