from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.models.setting import Setting

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('', methods=['GET'])
def list_settings():
    settings = Setting.query.all()
    result = {}
    for s in settings:
        cat = s.category or 'general'
        if cat not in result:
            result[cat] = {}
        result[cat][s.key] = s.value
    return jsonify(result)


@settings_bp.route('/<category>', methods=['GET'])
def get_category(category):
    settings = Setting.query.filter_by(category=category).all()
    return jsonify({s.key: s.value for s in settings})


@settings_bp.route('/<category>/<key>', methods=['PUT'])
def update_setting(category, key):
    data = request.get_json() or {}
    value = str(data.get('value', ''))

    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
        setting.category = category
    else:
        setting = Setting(key=key, value=value, category=category)
        db.session.add(setting)
    db.session.commit()
    return jsonify(setting.to_dict())


@settings_bp.route('/risk-thresholds', methods=['POST'])
def update_risk_thresholds():
    data = request.get_json() or {}
    updated = {}
    for key, value in data.items():
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = Setting(key=key, value=str(value), category='risk')
            db.session.add(setting)
        updated[key] = value
    db.session.commit()
    return jsonify({'status': 'updated', 'thresholds': updated})
