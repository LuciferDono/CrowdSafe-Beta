import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(app):
    """Configure structured logging with file rotation."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    fmt = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
    )

    # App log
    app_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'), maxBytes=100_000_000, backupCount=10
    )
    app_handler.setFormatter(fmt)
    app_handler.setLevel(logging.INFO)
    app.logger.addHandler(app_handler)

    # Error log
    err_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'), maxBytes=100_000_000, backupCount=10
    )
    err_handler.setFormatter(fmt)
    err_handler.setLevel(logging.ERROR)
    app.logger.addHandler(err_handler)

    app.logger.setLevel(logging.INFO)


def get_logger(name):
    """Get a named logger."""
    return logging.getLogger(name)
