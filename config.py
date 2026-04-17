import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'crowdsafe-dev-key-change-in-prod')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

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
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-prod')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '86400'))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', '604800'))

    # Scene defaults
    PIXELS_PER_METER = 100.0
    SCENE_AREA_SQ_METERS = 100.0

    # Server
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', '5001'))
