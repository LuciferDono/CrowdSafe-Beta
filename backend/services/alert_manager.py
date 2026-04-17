import time
import json
from datetime import datetime, timezone, timedelta
from backend.extensions import db, socketio
from backend.models.alert import Alert
from backend.models.camera import Camera
from backend.models.setting import Setting
from backend.services.telegram_service import send_alert as telegram_send
from backend.utils.helpers import generate_id
from backend.utils.logger import get_logger

logger = get_logger('alert_manager')


class AlertManager:
    """Threshold-based alert creation with cooldown and escalation."""

    def __init__(self, config):
        self.config = config
        self._last_alert_time = {}  # key -> timestamp

    def check_and_alert(self, camera_id, metrics, app, frame_jpeg=None):
        """Check metrics against thresholds, create alerts if needed."""
        risk_level = metrics.get('risk_level', 'SAFE')
        if risk_level not in ('WARNING', 'CRITICAL'):
            return None

        # Cooldown
        now = time.time()
        key = f"{camera_id}_{risk_level}"
        last = self._last_alert_time.get(key, 0)
        cooldown = getattr(self.config, 'ALERT_COOLDOWN', 60)
        if now - last < cooldown:
            return None
        self._last_alert_time[key] = now

        count = metrics.get('count', 0)
        density = metrics.get('density', 0)
        risk_score = metrics.get('risk_score', 0)
        velocity = metrics.get('avg_velocity', 0)

        # Determine trigger condition
        trigger = 'risk_threshold'
        if density > 6:
            trigger = 'extreme_density'
        elif metrics.get('surge_rate', 0) > 0.8:
            trigger = 'sudden_surge'
        elif velocity < 0.2 and density > 4:
            trigger = 'stagnation_with_density'

        # IST timestamp
        IST = timezone(timedelta(hours=5, minutes=30))
        ist_now = datetime.now(IST)
        time_str = ist_now.strftime('%d %b %Y, %I:%M:%S %p IST')

        if risk_level == 'CRITICAL':
            message = (f"CRITICAL: Dangerous crowd conditions! "
                       f"{count} people, density {density:.2f} p/m\u00b2, "
                       f"velocity {velocity:.2f} m/s, risk {risk_score:.0%} "
                       f"at {time_str}")
        else:
            message = (f"WARNING: Elevated crowd density. "
                       f"{count} people, density {density:.2f} p/m\u00b2, "
                       f"risk {risk_score:.0%} at {time_str}")

        try:
            with app.app_context():
                # Get camera name and location
                cam = Camera.query.get(camera_id)
                camera_name = cam.name if cam else camera_id
                camera_location = cam.location if cam else ''

                alert = Alert(
                    alert_id=generate_id('ALT'),
                    camera_id=camera_id,
                    risk_level=risk_level,
                    trigger_condition=trigger,
                    message=message,
                    metrics_snapshot=json.dumps(metrics, default=str),
                )
                db.session.add(alert)
                db.session.commit()

                alert_data = alert.to_dict()
                # Add camera info for Telegram
                alert_data['camera_name'] = camera_name
                alert_data['camera_location'] = camera_location
                socketio.emit('alert', alert_data)
                socketio.emit('alert', alert_data, room=f'camera_{camera_id}')

                # Telegram notification
                self._send_telegram(alert_data, frame_jpeg)

                logger.info(f"Alert created: {alert.alert_id} - {risk_level} for camera {camera_id}")
                return alert_data
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None

    def _send_telegram(self, alert_data, frame_jpeg=None):
        """Send alert via Telegram if enabled in settings."""
        try:
            enabled = Setting.query.filter_by(key='telegram_enabled').first()
            if not enabled or enabled.value != 'true':
                return
            token_row = Setting.query.filter_by(key='telegram_bot_token').first()
            chat_row = Setting.query.filter_by(key='telegram_chat_id').first()
            bot_token = (token_row.value if token_row else '') or self.config.TELEGRAM_BOT_TOKEN
            chat_id = (chat_row.value if chat_row else '') or self.config.TELEGRAM_CHAT_ID
            if bot_token and chat_id:
                telegram_send(alert_data, bot_token, chat_id, frame_jpeg)
        except Exception as e:
            logger.error(f"Telegram dispatch error: {e}")
