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

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'crowdsafe.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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

    # Alerts
    ALERT_COOLDOWN = 60

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
    FORECAST_HORIZON_SECONDS = int(os.environ.get('FORECAST_HORIZON_SECONDS', '60'))

    # Pose fusion
    POSE_ENABLED = os.environ.get('POSE_ENABLED', 'True').lower() == 'true'
    POSE_MODEL = os.environ.get('POSE_MODEL', 'yolo11s-pose.pt')

    # Rate limiting
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')

    # Scene defaults
    PIXELS_PER_METER = 100.0
    SCENE_AREA_SQ_METERS = 100.0

    # Server
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', '5001'))
