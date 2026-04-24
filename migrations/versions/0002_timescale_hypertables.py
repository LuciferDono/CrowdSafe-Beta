"""enable TimescaleDB + convert metrics to hypertable

Revision ID: 0002_timescale_hypertables
Revises: 0001_baseline
Create Date: 2026-04-17
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_timescale_hypertables'
down_revision = '0001_baseline'
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == 'postgresql'


def upgrade() -> None:
    # TimescaleDB features only land on Postgres. SQLite dev skips this cleanly.
    if not _is_postgres():
        return

    conn = op.get_bind()
    conn.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;')

    # Metrics: high-write time-series → hypertable with 1-day chunks.
    conn.exec_driver_sql(
        "SELECT create_hypertable('metrics', 'timestamp', "
        "chunk_time_interval => INTERVAL '1 day', "
        "if_not_exists => TRUE, migrate_data => TRUE);"
    )

    # Compress old chunks aggressively — metrics are append-only.
    conn.exec_driver_sql(
        "ALTER TABLE metrics SET ("
        "timescaledb.compress, "
        "timescaledb.compress_segmentby = 'camera_id', "
        "timescaledb.compress_orderby = 'timestamp DESC'"
        ");"
    )
    conn.exec_driver_sql(
        "SELECT add_compression_policy('metrics', INTERVAL '7 days', if_not_exists => TRUE);"
    )

    # Retention: drop raw chunks older than 90 days (operators keep alerts separately).
    conn.exec_driver_sql(
        "SELECT add_retention_policy('metrics', INTERVAL '90 days', if_not_exists => TRUE);"
    )

    # System logs: same pattern, shorter retention.
    conn.exec_driver_sql(
        "SELECT create_hypertable('system_logs', 'timestamp', "
        "chunk_time_interval => INTERVAL '7 days', "
        "if_not_exists => TRUE, migrate_data => TRUE);"
    )
    conn.exec_driver_sql(
        "SELECT add_retention_policy('system_logs', INTERVAL '30 days', if_not_exists => TRUE);"
    )


def downgrade() -> None:
    if not _is_postgres():
        return
    conn = op.get_bind()
    # Remove policies but keep tables + TimescaleDB extension in place.
    conn.exec_driver_sql("SELECT remove_retention_policy('metrics', if_exists => TRUE);")
    conn.exec_driver_sql("SELECT remove_compression_policy('metrics', if_exists => TRUE);")
    conn.exec_driver_sql("SELECT remove_retention_policy('system_logs', if_exists => TRUE);")
