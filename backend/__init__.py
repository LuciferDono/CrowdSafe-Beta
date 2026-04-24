from flask import Flask
from config import Config
from backend.extensions import db, socketio, limiter, migrate
import os
import secrets
import stat


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
    migrate.init_app(
        app,
        db,
        directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations'),
        render_as_batch=True,
    )
    socketio.init_app(app, async_mode='threading', cors_allowed_origins='*')
    limiter.init_app(app)

    # Setup logging
    from backend.utils.logger import setup_logging
    setup_logging(app)

    # Observability — Sentry first (before blueprints), Prometheus after
    # (needs the app object to wire its /metrics route).
    from backend.observability import init_sentry, init_prometheus
    init_sentry(app)
    init_prometheus(app)

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
    from backend.api.copilot import copilot_bp
    from backend.api.forecast import forecast_bp
    from backend.api.search import search_bp
    from backend.api.audit import audit_bp
    from backend.api.correlation import correlation_bp
    from backend.api.venues import venues_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(cameras_bp, url_prefix='/api/cameras')
    app.register_blueprint(metrics_bp, url_prefix='/api/metrics')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(recordings_bp, url_prefix='/api/recordings')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(system_bp, url_prefix='/api/system')
    app.register_blueprint(copilot_bp, url_prefix='/api/copilot')
    app.register_blueprint(forecast_bp, url_prefix='/api/forecast')
    app.register_blueprint(search_bp, url_prefix='/api/search')
    app.register_blueprint(audit_bp, url_prefix='/api/audit')
    app.register_blueprint(correlation_bp, url_prefix='/api/correlation')
    app.register_blueprint(venues_bp, url_prefix='/api/venues')

    # Register websocket events
    from backend.websockets import events  # noqa: F401

    # Schema bootstrap: SQLite (dev) uses create_all, Postgres relies on alembic.
    with app.app_context():
        import backend.models  # noqa: F401
        _bootstrap_schema(app)
        _ensure_defaults(app)

    return app


def _bootstrap_schema(app) -> None:
    """Ensure tables exist. Behavior depends on dialect.

    - SQLite (dev): run create_all(); keeps the zero-config dev loop working.
    - Postgres (prod): rely on `alembic upgrade head`. Log a warning if the
      alembic_version table is missing so operators catch the mistake early.
    """
    from sqlalchemy import inspect

    engine = db.engine
    dialect = engine.dialect.name

    if dialect == 'sqlite':
        db.create_all()
        return

    inspector = inspect(engine)
    if 'alembic_version' not in inspector.get_table_names():
        app.logger.warning(
            "Postgres target has no alembic_version table. "
            "Run `alembic upgrade head` before serving traffic."
        )
        db.create_all()  # last-resort safety net; not the canonical path


def _ensure_defaults(app):
    """Create default admin user and settings if they don't exist."""
    from backend.models.user import User
    from backend.models.setting import Setting

    admin_username = app.config.get('ADMIN_USERNAME', 'admin')
    if User.query.filter_by(username=admin_username).first() is None:
        configured_pwd = app.config.get('ADMIN_PASSWORD', '') or ''
        generated = not configured_pwd
        password = configured_pwd if configured_pwd else secrets.token_urlsafe(24)

        admin = User(
            username=admin_username,
            email=f'{admin_username}@crowdsafe.local',
            full_name='Administrator',
            role='admin',
            is_active=True,
        )
        admin.set_password(password)
        db.session.add(admin)

        if generated:
            _write_first_boot_credentials(app, admin_username, password)
            app.logger.warning(
                "First-boot admin credentials written to logs/FIRST_BOOT_CREDENTIALS.txt. "
                "Login, change the password immediately, then delete the file."
            )

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


def _write_first_boot_credentials(app, username: str, password: str) -> None:
    """Write generated admin credentials to a restricted-permission file."""
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    path = os.path.join(logs_dir, 'FIRST_BOOT_CREDENTIALS.txt')

    content = (
        "CrowdSafe First-Boot Admin Credentials\n"
        "======================================\n"
        f"Username: {username}\n"
        f"Password: {password}\n\n"
        "ACTION REQUIRED:\n"
        "  1. Log in immediately.\n"
        "  2. Change the password.\n"
        "  3. Delete this file.\n"
    )

    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception:
        os.close(fd)
        raise

    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
