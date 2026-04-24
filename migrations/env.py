"""Alembic migration environment.

Pulls the database URL from the Flask config so that local dev (SQLite) and
production (Postgres + TimescaleDB) share one migration path.
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make the project root importable so we can load Flask config + models.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from config import Config  # noqa: E402
from backend.extensions import db  # noqa: E402
import backend.models  # noqa: F401,E402 — register all models on metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject runtime DB URL (env-driven via Config).
config.set_main_option('sqlalchemy.url', Config.SQLALCHEMY_DATABASE_URI)

target_metadata = db.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
