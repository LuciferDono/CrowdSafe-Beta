import threading
from backend.services.ai_engine import CrowdSafeAI
from backend.services.crowd_analyzer import CrowdAnalyzer
from backend.services.risk_calculator import RiskCalculator
from backend.services.alert_manager import AlertManager
from backend.services.video_processor import VideoProcessor
from backend.utils.logger import get_logger

logger = get_logger('camera_manager')


class CameraManager:
    """Singleton registry mapping camera_id -> VideoProcessor."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._processors = {}
                cls._instance._ai_engine = None
                cls._instance._crowd_analyzer = None
                cls._instance._risk_calculator = None
                cls._instance._alert_manager = None
                cls._instance._app = None
            return cls._instance

    def init_app(self, app):
        self._app = app
        cfg = app.config
        # Build config-like object from Flask config
        _c = type('Cfg', (), {k: cfg[k] for k in cfg if isinstance(cfg[k], (str, int, float, bool))})()
        self._ai_engine = CrowdSafeAI(_c)
        self._crowd_analyzer = CrowdAnalyzer(_c)
        self._risk_calculator = RiskCalculator(_c)
        self._alert_manager = AlertManager(_c)
        logger.info("CameraManager initialized")

    def start_camera(self, camera_id, source_path, area_sqm=100.0, expected_capacity=500):
        if camera_id in self._processors and self._processors[camera_id].is_running:
            return False

        processor = VideoProcessor(
            camera_id=camera_id,
            source_path=source_path,
            ai_engine=self._ai_engine,
            crowd_analyzer=self._crowd_analyzer,
            risk_calculator=self._risk_calculator,
            alert_manager=self._alert_manager,
            app=self._app,
            area_sqm=area_sqm,
            expected_capacity=expected_capacity,
        )
        self._processors[camera_id] = processor
        processor.start()
        logger.info(f"Started processing camera {camera_id}")
        return True

    def stop_camera(self, camera_id):
        proc = self._processors.get(camera_id)
        if proc and proc.is_running:
            proc.stop()
            logger.info(f"Stopped processing camera {camera_id}")
            return True
        return False

    def get_processor(self, camera_id):
        return self._processors.get(camera_id)

    def get_all_status(self):
        return {
            cid: {'running': proc.is_running, 'metrics': proc.latest_metrics}
            for cid, proc in self._processors.items()
        }

    def stop_all(self):
        for proc in self._processors.values():
            if proc.is_running:
                proc.stop()
        self._processors.clear()


camera_manager = CameraManager()
