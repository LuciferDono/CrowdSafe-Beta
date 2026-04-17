import os
from flask import Blueprint, request, jsonify, send_file
from backend.extensions import db
from backend.models.recording import Recording

recordings_bp = Blueprint('recordings', __name__)


@recordings_bp.route('', methods=['GET'])
def list_recordings():
    camera_id = request.args.get('camera_id')
    query = Recording.query.order_by(Recording.start_time.desc())
    if camera_id:
        query = query.filter_by(camera_id=camera_id)
    limit = request.args.get('limit', 50, type=int)
    recordings = query.limit(limit).all()
    return jsonify([r.to_dict() for r in recordings])


@recordings_bp.route('/<recording_id>', methods=['GET'])
def get_recording(recording_id):
    rec = Recording.query.filter_by(recording_id=recording_id).first()
    if not rec:
        return jsonify({'error': 'Recording not found'}), 404
    return jsonify(rec.to_dict())


@recordings_bp.route('/<recording_id>/download', methods=['GET'])
def download_recording(recording_id):
    rec = Recording.query.filter_by(recording_id=recording_id).first()
    if not rec:
        return jsonify({'error': 'Recording not found'}), 404
    if not os.path.exists(rec.filepath):
        return jsonify({'error': 'File not found on disk'}), 404
    return send_file(rec.filepath, as_attachment=True, download_name=rec.filename)


@recordings_bp.route('/<recording_id>', methods=['DELETE'])
def delete_recording(recording_id):
    rec = Recording.query.filter_by(recording_id=recording_id).first()
    if not rec:
        return jsonify({'error': 'Recording not found'}), 404
    if os.path.exists(rec.filepath):
        os.remove(rec.filepath)
    db.session.delete(rec)
    db.session.commit()
    return jsonify({'message': 'Recording deleted'})
