import os
import cv2
from flask import Blueprint, request, jsonify, Response, current_app
from werkzeug.utils import secure_filename
from backend.extensions import db
from backend.models.camera import Camera
from backend.models.recording import Recording
from backend.services.audit_service import audited
from backend.services.camera_manager import camera_manager
from backend.services.heatmap_service import latest_sample, recent_samples
from backend.utils.decorators import role_required, token_required
from backend.utils.helpers import generate_id
from backend.utils.validators import allowed_video_file, sanitize_string

cameras_bp = Blueprint('cameras', __name__)


@cameras_bp.route('', methods=['GET'])
@token_required
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
@role_required('admin')
@audited('camera.create', target_type='camera')
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
@token_required
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
@role_required('admin', 'operator')
@audited('camera.update', target_type='camera', target_id_from='camera_id')
def update_camera(camera_id):
    cam = db.session.get(Camera, camera_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404
    data = request.get_json() or {}
    for field in ['name', 'location', 'source_type', 'source_url', 'resolution']:
        if field in data:
            setattr(cam, field, sanitize_string(str(data[field]), 200))
    if 'dense_mode' in data:
        val = str(data['dense_mode']).lower()
        if val in ('auto', 'always', 'never'):
            cam.dense_mode = val
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
@role_required('admin')
@audited('camera.delete', target_type='camera', target_id_from='camera_id')
def delete_camera(camera_id):
    cam = db.session.get(Camera, camera_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404
    camera_manager.stop_camera(camera_id)
    db.session.delete(cam)
    db.session.commit()
    return jsonify({'message': 'Camera deleted'})


@cameras_bp.route('/<camera_id>/upload', methods=['POST'])
@role_required('admin', 'operator')
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
@role_required('admin', 'operator')
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
@role_required('admin', 'operator')
@audited('camera.start', target_type='camera', target_id_from='camera_id')
def start_processing(camera_id):
    cam = db.session.get(Camera, camera_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404
    source = cam.source_url
    if not source or (cam.source_type == 'file' and not os.path.exists(source)):
        return jsonify({'error': 'No video source configured. Upload a video first.'}), 400
    if camera_manager._app is None:
        camera_manager.init_app(current_app._get_current_object())
    started = camera_manager.start_camera(
        cam.id, source, cam.area_sqm, cam.expected_capacity,
        dense_mode=cam.dense_mode or 'auto',
    )
    if started:
        cam.status = 'processing'
        db.session.commit()
        return jsonify({'status': 'started', 'camera_id': cam.id})
    return jsonify({'status': 'already_running', 'camera_id': cam.id})


@cameras_bp.route('/<camera_id>/stop', methods=['POST'])
@role_required('admin', 'operator')
@audited('camera.stop', target_type='camera', target_id_from='camera_id')
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
@token_required
def stream(camera_id):
    proc = camera_manager.get_processor(camera_id)
    if not proc or not proc.is_running:
        return jsonify({'error': 'Camera not processing'}), 404
    proc.show_heatmap = request.args.get('heatmap') == '1'
    return Response(proc.generate_mjpeg(), mimetype='multipart/x-mixed-replace; boundary=frame')


@cameras_bp.route('/<camera_id>/heatmap', methods=['GET'])
@token_required
def get_heatmap(camera_id):
    """Return recent persisted heatmap samples.

    Query params:
      - ``limit`` (default 20, max 200) — number of samples, newest first.
      - ``include_grid`` (default 1) — set ``0`` to omit the grid payload
        (useful for listings that just want timestamps + counts).
    """
    cam = db.session.get(Camera, camera_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404

    try:
        limit = max(1, min(int(request.args.get('limit', 20)), 200))
    except (TypeError, ValueError):
        limit = 20
    include_grid = request.args.get('include_grid', '1') != '0'

    return jsonify({
        'camera_id': camera_id,
        'samples': recent_samples(camera_id, limit=limit, include_grid=include_grid),
    })


@cameras_bp.route('/<camera_id>/heatmap/current', methods=['GET'])
@token_required
def get_heatmap_current(camera_id):
    """Return the most recent heatmap sample for the camera."""
    cam = db.session.get(Camera, camera_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404
    sample = latest_sample(camera_id)
    if sample is None:
        return jsonify({'error': 'No heatmap samples yet'}), 404
    return jsonify(sample)


@cameras_bp.route('/<camera_id>/popular-times', methods=['GET'])
@token_required
def popular_times(camera_id):
    """Aggregate historical metrics by hour-of-day for a Google-Maps-style popular times chart."""
    cam = db.session.get(Camera, camera_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404

    from sqlalchemy import text
    rows = db.session.execute(text("""
        SELECT
            CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
            AVG("count")        AS avg_count,
            AVG(density)        AS avg_density,
            AVG(risk_score)     AS avg_risk_score,
            COUNT(*)            AS sample_count
        FROM metrics
        WHERE camera_id = :cid
        GROUP BY hour
        ORDER BY hour
    """), {'cid': camera_id}).fetchall()

    if not rows:
        return jsonify({'camera_id': camera_id, 'hours': [], 'peak_hour': None, 'total_samples': 0})

    hour_map = {
        int(r[0]): {
            'avg_count':      float(r[1] or 0),
            'avg_density':    float(r[2] or 0),
            'avg_risk_score': float(r[3] or 0),
            'sample_count':   int(r[4] or 0),
        }
        for r in rows
    }

    max_count = max((v['avg_count'] for v in hour_map.values()), default=1) or 1

    def _label(h):
        suffix = 'AM' if h < 12 else 'PM'
        return f"{h % 12 or 12}{suffix}"

    hours_out = []
    for h in range(24):
        d = hour_map.get(h, {})
        avg_count = d.get('avg_count', 0)
        hours_out.append({
            'hour':               h,
            'label':              _label(h),
            'avg_count':          round(avg_count, 1),
            'avg_density':        round(d.get('avg_density', 0), 3),
            'avg_risk_score':     round(d.get('avg_risk_score', 0), 3),
            'relative_intensity': round(avg_count / max_count, 3),
            'sample_count':       d.get('sample_count', 0),
            'has_data':           h in hour_map,
        })

    # Peak within visible display window (6 AM–11 PM); fall back to global peak
    display_map = {h: v for h, v in hour_map.items() if 6 <= h <= 23}
    peak_hour = (max(display_map, key=lambda h: display_map[h]['avg_count'])
                 if display_map
                 else (max(hour_map, key=lambda h: hour_map[h]['avg_count']) if hour_map else None))
    total_samples = sum(v['sample_count'] for v in hour_map.values())

    return jsonify({
        'camera_id':     camera_id,
        'hours':         hours_out,
        'peak_hour':     peak_hour,
        'total_samples': total_samples,
    })
