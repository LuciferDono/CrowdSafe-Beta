import time
import json
from datetime import datetime, timezone, timedelta
from backend.extensions import db, socketio
from backend.models.alert import Alert
from backend.models.camera import Camera
from backend.models.setting import Setting
from backend.services.telegram_service import send_alert as telegram_send
from backend.services.alert_narrator import narrate as vlm_narrate
from backend.services.incident_reporter import schedule_if_critical
from backend.utils.helpers import generate_id
from backend.utils.logger import get_logger

logger = get_logger('alert_manager')

# Risk levels ranked; anything >= CAUTION rank triggers an alert.
_LEVEL_RANK = {'SAFE': 0, 'CAUTION': 1, 'WARNING': 2, 'CRITICAL': 3}


class AlertManager:
    """Threshold-based alert creation with hysteresis, cooldown, escalation."""

    def __init__(self, config):
        self.config = config
        self._last_alert_time = {}  # key -> timestamp
        # Hysteresis state per camera:
        #   effective_level: last confirmed level (after debounce)
        #   above_streak / below_streak: consecutive frames biasing up/down
        self._hyst_state: dict[str, dict] = {}

    def _apply_hysteresis(self, camera_id: str, observed: str) -> str:
        """Debounce flicker around thresholds. Returns the *effective* level
        to act on. Upgrade to CRITICAL is near-instant; upgrade to WARNING
        needs multiple frames; downgrade always requires a streak."""
        st = self._hyst_state.setdefault(
            camera_id,
            {'effective_level': 'SAFE', 'above_streak': 0, 'below_streak': 0},
        )
        effective = st['effective_level']
        obs_rank = _LEVEL_RANK.get(observed, 0)
        eff_rank = _LEVEL_RANK.get(effective, 0)

        warning_enter = getattr(self.config, 'ALERT_HYSTERESIS_WARNING_ENTER', 3)
        critical_enter = getattr(self.config, 'ALERT_HYSTERESIS_CRITICAL_ENTER', 1)
        exit_streak = getattr(self.config, 'ALERT_HYSTERESIS_EXIT', 5)

        if obs_rank > eff_rank:
            # Escalation candidate
            st['above_streak'] += 1
            st['below_streak'] = 0
            needed = critical_enter if observed == 'CRITICAL' else warning_enter
            if st['above_streak'] >= needed:
                st['effective_level'] = observed
                st['above_streak'] = 0
        elif obs_rank < eff_rank:
            # De-escalation candidate
            st['below_streak'] += 1
            st['above_streak'] = 0
            if st['below_streak'] >= exit_streak:
                st['effective_level'] = observed
                st['below_streak'] = 0
        else:
            st['above_streak'] = 0
            st['below_streak'] = 0

        return st['effective_level']

    def reset_hysteresis(self, camera_id: str | None = None) -> None:
        """Test hook / operator hook. Drop debounce state."""
        if camera_id is None:
            self._hyst_state.clear()
        else:
            self._hyst_state.pop(camera_id, None)

    def check_and_alert(self, camera_id, metrics, app, frame_jpeg=None):
        """Check metrics against thresholds, create alerts if needed."""
        observed_level = metrics.get('risk_level', 'SAFE')
        risk_level = self._apply_hysteresis(camera_id, observed_level)
        # Surface the debounced level so downstream UI reflects what the
        # alerting system actually reacted to.
        metrics['risk_level_effective'] = risk_level

        if risk_level not in ('CAUTION', 'WARNING', 'CRITICAL'):
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
        elif risk_level == 'WARNING':
            message = (f"WARNING: Elevated crowd density. "
                       f"{count} people, density {density:.2f} p/m\u00b2, "
                       f"risk {risk_score:.0%} at {time_str}")
        else:
            message = (f"CAUTION: Crowd density increasing. "
                       f"{count} people, density {density:.2f} p/m\u00b2, "
                       f"risk {risk_score:.0%} at {time_str}")

        try:
            with app.app_context():
                # Get camera name and location
                cam = Camera.query.get(camera_id)
                camera_name = cam.name if cam else camera_id
                camera_location = cam.location if cam else ''

                narrative = None
                try:
                    narrative = vlm_narrate(metrics, frame_jpeg, camera_name=camera_name)
                except Exception as e:
                    logger.debug(f"VLM narration skipped: {e}")

                final_message = f"{narrative} — {message}" if narrative else message

                alert = Alert(
                    alert_id=generate_id('ALT'),
                    camera_id=camera_id,
                    risk_level=risk_level,
                    trigger_condition=trigger,
                    message=final_message,
                    metrics_snapshot=json.dumps(metrics, default=str),
                )
                db.session.add(alert)
                db.session.commit()

                try:
                    from backend.observability import record_alert
                    record_alert(risk_level)
                except Exception:
                    pass

                alert_data = alert.to_dict()
                # Add camera info for Telegram
                alert_data['camera_name'] = camera_name
                alert_data['camera_location'] = camera_location
                alert_data['narrative'] = narrative
                socketio.emit('alert', alert_data)
                socketio.emit('alert', alert_data, room=f'camera_{camera_id}')

                # Telegram notification
                self._send_telegram(alert_data, frame_jpeg)

                # Auto incident report (CRITICAL only, background thread)
                try:
                    schedule_if_critical(alert_data, app)
                except Exception as e:
                    logger.debug(f"Incident reporter skipped: {e}")

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
