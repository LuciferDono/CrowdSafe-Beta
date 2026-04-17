from flask_socketio import join_room, leave_room, emit
from backend.extensions import socketio


@socketio.on('connect')
def handle_connect():
    emit('system_notification', {'type': 'info', 'message': 'Connected to CrowdSafe'})


@socketio.on('disconnect')
def handle_disconnect():
    pass


@socketio.on('subscribe_camera')
def handle_subscribe(data):
    camera_id = data.get('camera_id')
    if camera_id:
        join_room(f'camera_{camera_id}')


@socketio.on('unsubscribe_camera')
def handle_unsubscribe(data):
    camera_id = data.get('camera_id')
    if camera_id:
        leave_room(f'camera_{camera_id}')


@socketio.on('get_metrics')
def handle_get_metrics(data):
    camera_id = data.get('camera_id')
    if camera_id:
        from backend.services.camera_manager import camera_manager
        proc = camera_manager.get_processor(camera_id)
        if proc and proc.is_running:
            emit('metrics_update', proc.latest_metrics)
