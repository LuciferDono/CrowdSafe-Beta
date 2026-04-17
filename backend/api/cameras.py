import os
import cv2
from flask import Blueprint, request, jsonify, Response, current_app
from werkzeug.utils import secure_filename
from backend.extensions import db
from backend.models.camera import Camera
from backend.models.recording import Recording
from backend.services.camera_manager import camera_manager
from backend.utils.helpers import generate_id
from backend.utils.validators import allowed_video_file, sanitize_string

cameras_bp = Blueprint('cameras', __name__)


@cameras_bp.route('', methods=['GET'])
def list_cameras():
    cameras = Camera.query.order_by(Camera.created_at.desc()).all()
    result = []
    for cam in cameras:
        d = cam.to_dict()
        proc = camera_manager.get_processor(cam.id)
        d['is_processing'] = proc.is_running if proc else False
        d['current_metrics'] = proc.latest_metrics if proc and proc.is_running else {}
        result.append(d)
    return jsonify(result)


@cameras_bp.route('', methods=['POST'])
def create_camera():
    data = request.get_json() or {}
    cam_id = generate_id('CAM')
    cam = Camera(
        id=cam_id,
        name=sanitize_string(data.get('name', f'Camera {cam_id[:6]}'), 100),
        location=sanitize_string(data.get('location', ''), 200),
        source_type=data.get('source_type', 'file'),
        source_url=data.get('source_url', ''),
        area_sqm=float(data.get('area_sqm', 100.0)),
        expected_capacity=int(data.get('expected_capacity', 500)),
        fps_target=int(data.get('fps_target', 30)),
        resolution=data.get('resolution', '1280x720'),
    )
    db.session.add(cam)
    db.session.commit()
    return jsonify(cam.to_dict()), 201


@cameras_bp.route('/<camera_id>', methods=['GET'])
def get_camera(camera_id):
    cam = db.session.get(Camera, camera_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404
    d = cam.to_dict()
    proc = camera_manager.get_processor(cam.id)
    d['is_processing'] = proc.is_running if proc else False
    d['current_metrics'] = proc.latest_metrics if proc and proc.is_running else {}
    return jsonify(d)


@cameras_bp.route('/<camera_id>', methods=['PUT'])
def update_camera(camera_id):
    cam = db.session.get(Camera, camera_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404
    data = request.get_json() or {}
    for field in ['name', 'location', 'source_type', 'source_url', 'resolution']:
        if field in data:
            setattr(cam, field, sanitize_string(str(data[field]), 200))
    for field in ['area_sqm']:
        if field in data:
            setattr(cam, field, float(data[field]))
    for field in ['expected_capacity', 'fps_target']:
        if field in data:
            setattr(cam, field, int(data[field]))
    if 'is_active' in data:
        cam.is_active = bool(data['is_active'])
    db.session.commit()
    return jsonify(cam.to_dict())


@cameras_bp.route('/<camera_id>', methods=['DELETE'])
def delete_camera(camera_id):
    cam = db.session.get(Camera, camera_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404
    camera_manager.stop_camera(camera_id)
    db.session.delete(cam)
    db.session.commit()
    return jsonify({'message': 'Camera deleted'})


@cameras_bp.route('/<camera_id>/upload', methods=['POST'])
def upload_video(camera_id):
    cam = db.session.get(Camera, camera_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    file = request.files['video']
    if file.filename == '' or not allowed_video_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: mp4, avi, mov, mkv, webm'}), 400

    filename = secure_filename(f"{camera_id}_{file.filename}")
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    cap = cv2.VideoCapture(filepath)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0
    cap.release()

    rec = Recording(
        recording_id=generate_id('REC'),
        camera_id=camera_id,
        filename=filename,
        filepath=filepath,
        duration_seconds=duration,
        frame_count=frame_count,
        width=width,
        height=height,
        fps=fps,
        file_size_bytes=os.path.getsize(filepath),
        trigger_type='manual',
    )
    db.session.add(rec)
    cam.source_url = filepath
    cam.source_type = 'file'
    db.session.commit()
    return jsonify(rec.to_dict()), 201


@cameras_bp.route('/<camera_id>/test', methods=['POST'])
def test_camera(camera_id):
    cam = db.session.get(Camera, camera_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404
    source = cam.source_url
    if not source:
        return jsonify({'connection_status': 'error', 'message': 'No source configured'}), 400
    cap = cv2.VideoCapture(source)
    ok = cap.isOpened()
    cap.release()
    status = 'ok' if ok else 'error'
    return jsonify({'connection_status': status, 'message': 'Connection successful' if ok else 'Cannot open source'})


@cameras_bp.route('/<camera_id>/start', methods=['POST'])
def start_processing(camera_id):
    cam = db.session.get(Camera, camera_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404
    source = cam.source_url
    if not source or (cam.source_type == 'file' and not os.path.exists(source)):
        return jsonify({'error': 'No video source configured. Upload a video first.'}), 400
    if camera_manager._app is None:
        camera_manager.init_app(current_app._get_current_object())
    started = camera_manager.start_camera(cam.id, source, cam.area_sqm, cam.expected_capacity)
    if started:
        cam.status = 'processing'
        db.session.commit()
        return jsonify({'status': 'started', 'camera_id': cam.id})
    return jsonify({'status': 'already_running', 'camera_id': cam.id})


@cameras_bp.route('/<camera_id>/stop', methods=['POST'])
def stop_processing(camera_id):
    cam = db.session.get(Camera, camera_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404
    # Get processor before stopping to capture recording ID
    proc = camera_manager.get_processor(camera_id)
    camera_manager.stop_camera(camera_id)
    cam.status = 'offline'
    db.session.commit()
    recording_id = proc.last_recording_id if proc else None
    return jsonify({'status': 'stopped', 'camera_id': cam.id, 'recording_id': recording_id})


@cameras_bp.route('/<camera_id>/stream')
def stream(camera_id):
    proc = camera_manager.get_processor(camera_id)
    if not proc or not proc.is_running:
        return jsonify({'error': 'Camera not processing'}), 404
    proc.show_heatmap = request.args.get('heatmap') == '1'
    return Response(proc.generate_mjpeg(), mimetype='multipart/x-mixed-replace; boundary=frame')
