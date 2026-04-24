from flask import Blueprint, g, request, jsonify
from datetime import datetime, timezone
import os
from backend.extensions import db
from backend.models.alert import Alert
from backend.services.audit_service import audited
from backend.utils.decorators import role_required, token_required

alerts_bp = Blueprint('alerts', __name__)


@alerts_bp.route('', methods=['GET'])
@token_required
def list_alerts():
    camera_id = request.args.get('camera_id')
    risk_level = request.args.get('risk_level')
    resolved = request.args.get('resolved')
    limit = request.args.get('limit', 50, type=int)

    query = Alert.query.order_by(Alert.timestamp.desc())
    if camera_id:
        query = query.filter_by(camera_id=camera_id)
    if risk_level:
        query = query.filter_by(risk_level=risk_level.upper())
    if resolved is not None:
        query = query.filter_by(resolved=(resolved.lower() == 'true'))

    alerts = query.limit(limit).all()
    return jsonify([a.to_dict() for a in alerts])


@alerts_bp.route('/<alert_id>', methods=['GET'])
@token_required
def get_alert(alert_id):
    alert = Alert.query.filter_by(alert_id=alert_id).first()
    if not alert:
        alert = db.session.get(Alert, alert_id) if alert_id.isdigit() else None
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    return jsonify(alert.to_dict())


@alerts_bp.route('/<alert_id>/acknowledge', methods=['POST'])
@role_required('admin', 'operator')
@audited('alert.acknowledge', target_type='alert', target_id_from='alert_id')
def acknowledge_alert(alert_id):
    alert = Alert.query.filter_by(alert_id=alert_id).first()
    if not alert and alert_id.isdigit():
        alert = db.session.get(Alert, int(alert_id))
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    alert.acknowledged = True
    alert.acknowledged_by = getattr(g.current_user, 'id', None)
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(alert.to_dict())


@alerts_bp.route('/<alert_id>/resolve', methods=['POST'])
@role_required('admin', 'operator')
@audited('alert.resolve', target_type='alert', target_id_from='alert_id')
def resolve_alert(alert_id):
    alert = Alert.query.filter_by(alert_id=alert_id).first()
    if not alert and alert_id.isdigit():
        alert = db.session.get(Alert, int(alert_id))
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    alert.resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    if not alert.acknowledged:
        alert.acknowledged = True
        alert.acknowledged_by = getattr(g.current_user, 'id', None)
        alert.acknowledged_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(alert.to_dict())


@alerts_bp.route('/unacknowledged/count', methods=['GET'])
@token_required
def unacknowledged_count():
    count = Alert.query.filter_by(acknowledged=False).count()
    return jsonify({'count': count})


@alerts_bp.route('/<alert_id>/report', methods=['GET'])
@token_required
def get_incident_report(alert_id):
    """Return the auto-drafted incident markdown. 404 if not yet generated."""
    base = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'logs', 'incidents',
    )
    path = os.path.join(base, f'{alert_id}.md')
    if not os.path.exists(path):
        return jsonify({'error': 'Report not available yet'}), 404
    with open(path, 'r', encoding='utf-8') as f:
        return jsonify({'alert_id': alert_id, 'markdown': f.read()})


@alerts_bp.route('/<alert_id>/report/regenerate', methods=['POST'])
@role_required('admin', 'operator')
def regenerate_incident_report(alert_id):
    from backend.services.incident_reporter import draft_report

    result = draft_report(alert_id)
    if not result:
        return jsonify({'error': 'Unable to draft report'}), 503
    return jsonify({'alert_id': alert_id, **result})


@alerts_bp.route('/statistics', methods=['GET'])
@token_required
def statistics():
    from sqlalchemy import func
    total = Alert.query.count()
    by_level = dict(db.session.query(Alert.risk_level, func.count(Alert.id))
                    .group_by(Alert.risk_level).all())
    unresolved = Alert.query.filter_by(resolved=False).count()
    return jsonify({
        'total_alerts': total,
        'unresolved': unresolved,
        'by_level': by_level,
    })
