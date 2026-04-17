"""Background cleanup tasks for data retention."""
from datetime import datetime, timezone, timedelta
from backend.extensions import db
from backend.models.metric import Metric
from backend.models.system_log import SystemLog
from backend.utils.logger import get_logger

logger = get_logger('cleanup')


def cleanup_old_metrics(app, days=30):
    """Delete metrics older than N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with app.app_context():
        deleted = Metric.query.filter(Metric.timestamp < cutoff).delete()
        db.session.commit()
        logger.info(f"Cleaned up {deleted} metrics older than {days} days")


def cleanup_old_logs(app, days=90):
    """Delete system logs older than N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with app.app_context():
        deleted = SystemLog.query.filter(SystemLog.timestamp < cutoff).delete()
        db.session.commit()
        logger.info(f"Cleaned up {deleted} logs older than {days} days")
