"""
CrowdSafe Telegram Alert Service.

Sends alert notifications to Telegram via Bot API.
Uses only Python stdlib (urllib) - zero extra dependencies.
"""

import json
import threading
import urllib.request
import urllib.error
from backend.utils.logger import get_logger

logger = get_logger('telegram')

TELEGRAM_MSG_API = 'https://api.telegram.org/bot{token}/sendMessage'
TELEGRAM_PHOTO_API = 'https://api.telegram.org/bot{token}/sendPhoto'


def send_alert(alert_data, bot_token, chat_id, frame_jpeg=None):
    """Send an alert notification to Telegram in a background thread."""
    if not bot_token or not chat_id:
        return

    thread = threading.Thread(
        target=_send, args=(alert_data, bot_token, chat_id, frame_jpeg),
        daemon=True,
    )
    thread.start()


def _format_ist(timestamp_str):
    """Convert ISO timestamp to human-readable IST format."""
    from datetime import datetime, timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    try:
        if isinstance(timestamp_str, str):
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = timestamp_str
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ist_dt = dt.astimezone(IST)
        return ist_dt.strftime('%d %b %Y, %I:%M:%S %p IST')
    except (ValueError, TypeError, AttributeError):
        return str(timestamp_str)


def _build_caption(alert_data):
    """Build the alert caption text."""
    risk_level = alert_data.get('risk_level', 'UNKNOWN')
    icon = '\U0001F534' if risk_level == 'CRITICAL' else '\U0001F7E0'
    camera_name = alert_data.get('camera_name', '')
    camera_location = alert_data.get('camera_location', '')
    camera_id = alert_data.get('camera_id', 'N/A')
    message = alert_data.get('message', '')
    trigger = alert_data.get('trigger_condition', '')
    timestamp = alert_data.get('timestamp', '')

    # Build human-readable location line
    place = camera_name or camera_id
    if camera_location:
        place += f' - {camera_location}'

    # Format timestamp to IST
    time_str = _format_ist(timestamp)

    metrics = {}
    snapshot = alert_data.get('metrics_snapshot')
    if snapshot:
        if isinstance(snapshot, str):
            metrics = json.loads(snapshot)
        else:
            metrics = snapshot

    count = metrics.get('count', 0)
    density = metrics.get('density', 0)
    velocity = metrics.get('avg_velocity', 0)
    risk_score = metrics.get('risk_score', 0)
    pressure = metrics.get('crowd_pressure', 0)
    coherence = metrics.get('flow_coherence', 0)

    return (
        f"{icon} *CrowdSafe Alert*\n"
        f"*Level:* {risk_level}\n"
        f"*Location:* {place}\n"
        f"*Trigger:* {trigger.replace('_', ' ').title()}\n\n"
        f"{message}\n\n"
        f"*People:* {count}\n"
        f"*Density:* {density:.2f} p/m\u00b2\n"
        f"*Velocity:* {velocity:.2f} m/s\n"
        f"*Risk Score:* {risk_score:.0%}\n"
        f"*Pressure:* {pressure:.2f}\n"
        f"*Coherence:* {coherence:.2f}\n"
        f"\n\U0001F552 {time_str}"
    )


def _send(alert_data, bot_token, chat_id, frame_jpeg=None):
    """Send the alert with photo if available, otherwise text only."""
    try:
        caption = _build_caption(alert_data)

        if frame_jpeg:
            _send_photo(bot_token, chat_id, frame_jpeg, caption)
        else:
            _send_text(bot_token, chat_id, caption)

        logger.info(f"Telegram alert sent: {alert_data.get('alert_id')}")

    except urllib.error.HTTPError as e:
        logger.error(f"Telegram HTTP error {e.code}: {e.read().decode()}")
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")


def _send_text(bot_token, chat_id, text):
    """Send a text-only message."""
    payload = json.dumps({
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
    }).encode('utf-8')

    url = TELEGRAM_MSG_API.format(token=bot_token)
    req = urllib.request.Request(
        url, data=payload,
        headers={'Content-Type': 'application/json'},
    )
    urllib.request.urlopen(req, timeout=10)


def _send_photo(bot_token, chat_id, jpeg_bytes, caption):
    """Send a photo with caption using multipart/form-data."""
    boundary = '----CrowdSafeAlertBoundary'

    body = b''
    # chat_id field
    body += f'--{boundary}\r\n'.encode()
    body += b'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
    body += f'{chat_id}\r\n'.encode()
    # parse_mode field
    body += f'--{boundary}\r\n'.encode()
    body += b'Content-Disposition: form-data; name="parse_mode"\r\n\r\n'
    body += b'Markdown\r\n'
    # caption field
    body += f'--{boundary}\r\n'.encode()
    body += b'Content-Disposition: form-data; name="caption"\r\n\r\n'
    body += caption.encode('utf-8') + b'\r\n'
    # photo file
    body += f'--{boundary}\r\n'.encode()
    body += b'Content-Disposition: form-data; name="photo"; filename="alert.jpg"\r\n'
    body += b'Content-Type: image/jpeg\r\n\r\n'
    body += jpeg_bytes + b'\r\n'
    # closing boundary
    body += f'--{boundary}--\r\n'.encode()

    url = TELEGRAM_PHOTO_API.format(token=bot_token)
    req = urllib.request.Request(
        url, data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    )
    urllib.request.urlopen(req, timeout=15)
