import time
import platform
from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.models.camera import Camera
from backend.models.alert import Alert
from backend.models.metric import Metric
from backend.models.system_log import SystemLog
from backend.services.camera_manager import camera_manager

system_bp = Blueprint('system', __name__)

_start_time = time.time()


@system_bp.route('/health', methods=['GET'])
def health():
    uptime = int(time.time() - _start_time)
    return jsonify({
        'status': 'ok',
        'service': 'CrowdSafe',
        'uptime_seconds': uptime,
        'platform': platform.system(),
    })


@system_bp.route('/stats', methods=['GET'])
def stats():
    camera_count = Camera.query.count()
    alert_count = Alert.query.count()
    unack_alerts = Alert.query.filter_by(acknowledged=False).count()
    metric_count = Metric.query.count()
    active = camera_manager.get_all_status()
    active_count = sum(1 for v in active.values() if v['running'])

    total_people = 0
    for v in active.values():
        if v['running']:
            total_people += v['metrics'].get('count', 0)

    return jsonify({
        'cameras_total': camera_count,
        'cameras_active': active_count,
        'alerts_total': alert_count,
        'alerts_unacknowledged': unack_alerts,
        'metrics_recorded': metric_count,
        'total_people_detected': total_people,
    })


@system_bp.route('/logs', methods=['GET'])
def logs():
    level = request.args.get('level')
    component = request.args.get('component')
    limit = request.args.get('limit', 100, type=int)

    query = SystemLog.query.order_by(SystemLog.timestamp.desc())
    if level:
        query = query.filter_by(level=level)
    if component:
        query = query.filter_by(component=component)
    return jsonify([l.to_dict() for l in query.limit(limit).all()])
