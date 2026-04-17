from flask import Flask
from config import Config
from backend.extensions import db, socketio
import os


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static'),
    )
    app.config.from_object(config_class)

    # Ensure directories exist
    for folder in [app.config['UPLOAD_FOLDER'], app.config['RECORDING_FOLDER'],
                   app.config['MODEL_FOLDER'],
                   os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')]:
        os.makedirs(folder, exist_ok=True)

    # Init extensions
    db.init_app(app)
    socketio.init_app(app, async_mode='threading', cors_allowed_origins='*')

    # Setup logging
    from backend.utils.logger import setup_logging
    setup_logging(app)

    # Register blueprints
    from backend.api.pages import pages_bp
    from backend.api.auth import auth_bp
    from backend.api.cameras import cameras_bp
    from backend.api.metrics import metrics_bp
    from backend.api.alerts import alerts_bp
    from backend.api.recordings import recordings_bp
    from backend.api.settings_api import settings_bp
    from backend.api.users import users_bp
    from backend.api.system import system_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(cameras_bp, url_prefix='/api/cameras')
    app.register_blueprint(metrics_bp, url_prefix='/api/metrics')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(recordings_bp, url_prefix='/api/recordings')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(system_bp, url_prefix='/api/system')

    # Register websocket events
    from backend.websockets import events  # noqa: F401

    # Create tables and default admin
    with app.app_context():
        import backend.models  # noqa: F401
        db.create_all()
        _ensure_defaults(app)

    return app


def _ensure_defaults(app):
    """Create default admin user and settings if they don't exist."""
    from backend.models.user import User
    from backend.models.setting import Setting

    if User.query.filter_by(username='admin').first() is None:
        admin = User(
            username='admin',
            email='admin@crowdsafe.local',
            full_name='Administrator',
            role='admin',
            is_active=True,
        )
        admin.set_password('admin123')
        db.session.add(admin)

    defaults = [
        ('general', 'app_name', 'CrowdSafe'),
        ('general', 'timezone', 'UTC'),
        ('general', 'theme', 'dark'),
        ('risk', 'density_warning', '4.0'),
        ('risk', 'density_critical', '6.0'),
        ('risk', 'velocity_stagnant', '0.2'),
        ('risk', 'weight_density', '0.4'),
        ('risk', 'weight_surge', '0.3'),
        ('risk', 'weight_velocity', '0.3'),
        ('alerts', 'cooldown_seconds', '60'),
        ('alerts', 'email_enabled', 'false'),
        ('alerts', 'sms_enabled', 'false'),
        ('alerts', 'telegram_enabled', 'true'),
        ('alerts', 'telegram_bot_token', ''),
        ('alerts', 'telegram_chat_id', ''),
        ('ai', 'model', 'yolo11n.pt'),
        ('ai', 'confidence', '0.5'),
        ('ai', 'iou', '0.7'),
    ]
    for cat, key, val in defaults:
        if Setting.query.filter_by(key=key).first() is None:
            db.session.add(Setting(category=cat, key=key, value=val))

    db.session.commit()
