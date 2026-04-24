import os
import secrets
import sys
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _require_or_generate(env_key: str, *, prod_only: bool = True) -> str:
    """Return env var; in prod require it set, in dev generate ephemeral."""
    val = os.environ.get(env_key)
    if val:
        return val
    is_prod = os.environ.get('FLASK_ENV', 'development').lower() == 'production'
    if is_prod and prod_only:
        sys.stderr.write(
            f"FATAL: {env_key} must be set in production. "
            f"Generate via: python -c 'import secrets;print(secrets.token_urlsafe(64))'\n"
        )
        sys.exit(1)
    ephemeral = secrets.token_urlsafe(64)
    sys.stderr.write(
        f"WARNING: {env_key} unset, using ephemeral key (dev only). "
        f"Sessions invalidate on restart.\n"
    )
    return ephemeral


class Config:
    SECRET_KEY = _require_or_generate('SECRET_KEY')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # Demo/dev: disable auth entirely (default True — this is a project, not prod)
    AUTH_DISABLED = os.environ.get('AUTH_DISABLED', 'True').lower() == 'true'

    # Database
    _raw_db_url = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'crowdsafe.db')}"
    )
    # Normalize legacy scheme (heroku/render ship "postgres://", SQLA 2.x needs "postgresql://")
    if _raw_db_url.startswith('postgres://'):
        _raw_db_url = 'postgresql://' + _raw_db_url[len('postgres://'):]
    SQLALCHEMY_DATABASE_URI = _raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pool tuning only when talking to a real server (Postgres).
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': int(os.environ.get('DB_POOL_SIZE', '10')),
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '20')),
            'pool_pre_ping': True,
            'pool_recycle': 1800,
        }

    # Paths
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    RECORDING_FOLDER = os.path.join(BASE_DIR, 'recordings')
    MODEL_FOLDER = os.path.join(BASE_DIR, 'models')

    # YOLO / AI
    YOLO_MODEL = os.environ.get('MODEL_PATH', 'yolo11s.pt')
    YOLO_CONFIDENCE = float(os.environ.get('YOLO_CONFIDENCE', '0.25'))
    YOLO_IOU = float(os.environ.get('YOLO_IOU', '0.5'))
    YOLO_IMGSZ = int(os.environ.get('YOLO_IMGSZ', '960'))
    YOLO_MIN_BOX_AREA = int(os.environ.get('YOLO_MIN_BOX_AREA', '100'))
    YOLO_MAX_BOX_RATIO = float(os.environ.get('YOLO_MAX_BOX_RATIO', '5.0'))
    DENSE_CROWD_THRESHOLD = 50
    GRID_SIZE = 50
    OCCLUSION_FACTOR = 1.3

    # ML / Crowd Analysis
    PROXIMITY_THRESHOLD_PX = 80
    CLUSTER_MIN_SAMPLES = 2
    CLUSTER_EPS_PX = 120
    ANOMALY_VELOCITY_ZSCORE = 2.0
    COHERENCE_WINDOW = 10

    # Processing
    PROCESS_FPS = 15
    FRAME_SKIP = 2

    # Risk thresholds
    DENSITY_SAFE = 2.0
    DENSITY_CAUTION = 4.0
    DENSITY_WARNING = 6.0
    DENSITY_CRITICAL = 6.0
    VELOCITY_STAGNANT = 0.2
    VELOCITY_SLOW = 0.5
    VELOCITY_NORMAL = 1.0
    SURGE_WARNING = 0.5
    SURGE_CRITICAL = 0.8
    RISK_WARNING = 0.50
    RISK_CRITICAL = 0.75

    # Risk weights
    RISK_WEIGHT_DENSITY = 0.4
    RISK_WEIGHT_SURGE = 0.3
    RISK_WEIGHT_VELOCITY = 0.3

    # Risk amplifiers (env-tunable per deployment — stadium vs temple vs transit)
    # Crush escalation: pose-fusion crush_risk bumps base risk up; at cutoffs
    # it overrides the classification directly.
    RISK_CRUSH_AMPLIFIER = float(os.environ.get('RISK_CRUSH_AMPLIFIER', '0.4'))
    RISK_CRUSH_CRITICAL_THRESHOLD = float(os.environ.get('RISK_CRUSH_CRITICAL_THRESHOLD', '0.6'))
    RISK_CRUSH_WARNING_THRESHOLD = float(os.environ.get('RISK_CRUSH_WARNING_THRESHOLD', '0.3'))
    # Large-crowd multiplier: bumps risk score once count crosses the floor.
    RISK_LARGE_CROWD_COUNT = int(os.environ.get('RISK_LARGE_CROWD_COUNT', '100'))
    RISK_LARGE_CROWD_BUMP = float(os.environ.get('RISK_LARGE_CROWD_BUMP', '1.15'))

    # Alerts
    ALERT_COOLDOWN = 60
    # Hysteresis — N consecutive frames above threshold to escalate,
    # M below to de-escalate. CRITICAL escalates instantly because a
    # genuine stampede signal (fallen/compressed bodies) is not flicker.
    ALERT_HYSTERESIS_WARNING_ENTER = int(os.environ.get('ALERT_HYSTERESIS_WARNING_ENTER', '3'))
    ALERT_HYSTERESIS_CRITICAL_ENTER = int(os.environ.get('ALERT_HYSTERESIS_CRITICAL_ENTER', '1'))
    ALERT_HYSTERESIS_EXIT = int(os.environ.get('ALERT_HYSTERESIS_EXIT', '5'))

    # Telegram
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

    # JWT
    JWT_SECRET_KEY = _require_or_generate('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '86400'))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', '604800'))

    # OpenRouter LLM
    OR_API_KEY = os.environ.get('OR_API_KEY', '')
    OR_BASE_URL = os.environ.get('OR_BASE_URL', 'https://openrouter.ai/api/v1')
    OR_MODEL_DEFAULT = os.environ.get('OR_MODEL_DEFAULT', 'google/gemini-2.5-flash')
    OR_MODEL_PREMIUM = os.environ.get('OR_MODEL_PREMIUM', 'anthropic/claude-sonnet-4.6')
    OR_MODEL_VISION = os.environ.get('OR_MODEL_VISION', 'qwen/qwen3-vl-30b-a3b-instruct')
    OR_MODEL_NANO = os.environ.get('OR_MODEL_NANO', 'openai/gpt-5-nano')
    OR_SITE_URL = os.environ.get('OR_SITE_URL', 'https://github.com/LuciferDono/CrowdSafe-Beta')
    OR_APP_NAME = os.environ.get('OR_APP_NAME', 'CrowdSafe-Beta')

    # HuggingFace
    HF_TOKEN = os.environ.get('HF_TOKEN', '')

    # Admin defaults (first boot only)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')

    # Forecasting
    FORECAST_ENABLED = os.environ.get('FORECAST_ENABLED', 'True').lower() == 'true'
    # Default 300s (5 min) — evacuation-actionable horizon.
    FORECAST_HORIZON_SECONDS = int(os.environ.get('FORECAST_HORIZON_SECONDS', '300'))
    FORECAST_HORIZON_MAX = int(os.environ.get('FORECAST_HORIZON_MAX', '900'))
    FORECAST_HORIZON_MIN = int(os.environ.get('FORECAST_HORIZON_MIN', '30'))
    FORECAST_LOOKBACK_MAX = int(os.environ.get('FORECAST_LOOKBACK_MAX', '1800'))
    FORECAST_STEP_MAX = int(os.environ.get('FORECAST_STEP_MAX', '60'))

    # Historical pattern-of-life baseline (compare live metrics against
    # same-weekday-same-hour averages over past N weeks).
    BASELINE_ENABLED = os.environ.get('BASELINE_ENABLED', 'True').lower() == 'true'
    BASELINE_LOOKBACK_WEEKS = int(os.environ.get('BASELINE_LOOKBACK_WEEKS', '4'))
    BASELINE_HOUR_WINDOW = int(os.environ.get('BASELINE_HOUR_WINDOW', '1'))

    # Multi-camera wave correlation (stampede propagation detection)
    CORRELATION_ENABLED = os.environ.get('CORRELATION_ENABLED', 'True').lower() == 'true'
    CORRELATION_WINDOW_SECONDS = int(os.environ.get('CORRELATION_WINDOW_SECONDS', '300'))
    CORRELATION_MAX_LAG_SECONDS = int(os.environ.get('CORRELATION_MAX_LAG_SECONDS', '30'))
    CORRELATION_MIN_PEARSON = float(os.environ.get('CORRELATION_MIN_PEARSON', '0.5'))

    # Heatmap sample persistence (per-zone spatial density)
    HEATMAP_ENABLED = os.environ.get('HEATMAP_ENABLED', 'True').lower() == 'true'
    HEATMAP_SAMPLE_INTERVAL_S = float(os.environ.get('HEATMAP_SAMPLE_INTERVAL_S', '10'))
    HEATMAP_GRID_ROWS = int(os.environ.get('HEATMAP_GRID_ROWS', '16'))
    HEATMAP_GRID_COLS = int(os.environ.get('HEATMAP_GRID_COLS', '16'))
    HEATMAP_RETENTION_HOURS = int(os.environ.get('HEATMAP_RETENTION_HOURS', '72'))

    # Pose fusion
    POSE_ENABLED = os.environ.get('POSE_ENABLED', 'True').lower() == 'true'
    POSE_MODEL = os.environ.get('POSE_MODEL', 'yolo11s-pose.pt')

    # CSRNet dense crowd counting (kicks in when YOLO saturates)
    DENSE_COUNT_ENABLED = os.environ.get('DENSE_COUNT_ENABLED', 'False').lower() == 'true'
    DENSE_COUNT_MODEL_REPO = os.environ.get('DENSE_COUNT_MODEL_REPO', '')
    DENSE_COUNT_MODEL_FILE = os.environ.get('DENSE_COUNT_MODEL_FILE', '')
    DENSE_COUNT_THRESHOLD = int(os.environ.get('DENSE_COUNT_THRESHOLD', '40'))
    DENSE_COUNT_INTERVAL = int(os.environ.get('DENSE_COUNT_INTERVAL', '15'))  # every N frames
    # Strict mode: refuse to run CSRNet on random-init weights.
    # Defaults True in production so meaningless counts can never ship.
    DENSE_COUNT_STRICT = os.environ.get(
        'DENSE_COUNT_STRICT',
        'True' if os.environ.get('FLASK_ENV', 'development').lower() == 'production' else 'False'
    ).lower() == 'true'

    # Rate limiting
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')

    # Observability
    SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
    SENTRY_TRACES_SAMPLE_RATE = float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1'))
    SENTRY_ENVIRONMENT = os.environ.get('SENTRY_ENVIRONMENT', os.environ.get('FLASK_ENV', 'development'))
    METRICS_ENABLED = os.environ.get('METRICS_ENABLED', 'True').lower() == 'true'

    # Scene defaults
    PIXELS_PER_METER = 100.0
    SCENE_AREA_SQ_METERS = 100.0

    # Server
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', '5001'))
