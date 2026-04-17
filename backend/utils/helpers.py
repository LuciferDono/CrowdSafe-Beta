import uuid
import os


def generate_id(prefix=''):
    """Generate a short unique ID with optional prefix."""
    uid = uuid.uuid4().hex[:12].upper()
    return f"{prefix}{uid}" if prefix else uid


def ensure_dir(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)
    return path
