import re

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username):
    return bool(re.match(r'^[a-zA-Z0-9_]{3,50}$', username))


def validate_password(password):
    return len(password) >= 6


def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def validate_source_type(source_type):
    return source_type in ('rtsp', 'http', 'file', 'usb')


def sanitize_string(s, max_length=500):
    """Basic string sanitization."""
    if not isinstance(s, str):
        return ''
    return s.strip()[:max_length]
