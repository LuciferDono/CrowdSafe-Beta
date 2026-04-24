"""baseline schema

Revision ID: 0001_baseline
Revises:
Create Date: 2026-04-17
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if 'users' not in existing:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('username', sa.String(50), nullable=False, unique=True),
            sa.Column('email', sa.String(100), nullable=False, unique=True),
            sa.Column('password_hash', sa.String(255), nullable=False, server_default=''),
            sa.Column('full_name', sa.String(100), server_default=''),
            sa.Column('role', sa.String(20), server_default='viewer'),
            sa.Column('is_active', sa.Boolean, server_default=sa.text('1')),
            sa.Column('phone', sa.String(20), server_default=''),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('last_login', sa.DateTime, nullable=True),
        )

    if 'cameras' not in existing:
        op.create_table(
            'cameras',
            sa.Column('id', sa.String(50), primary_key=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('location', sa.String(200), server_default=''),
            sa.Column('source_type', sa.String(20), server_default='file'),
            sa.Column('source_url', sa.Text, server_default=''),
            sa.Column('area_sqm', sa.Float, server_default='100.0'),
            sa.Column('expected_capacity', sa.Integer, server_default='500'),
            sa.Column('calibration_method', sa.String(20), server_default='manual'),
            sa.Column('calibration_data', sa.Text, server_default='{}'),
            sa.Column('roi', sa.Text, server_default='{}'),
            sa.Column('is_active', sa.Boolean, server_default=sa.text('1')),
            sa.Column('status', sa.String(20), server_default='offline'),
            sa.Column('latitude', sa.Float, nullable=True),
            sa.Column('longitude', sa.Float, nullable=True),
            sa.Column('fps_target', sa.Integer, server_default='30'),
            sa.Column('resolution', sa.String(20), server_default='1280x720'),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        )

    if 'metrics' not in existing:
        op.create_table(
            'metrics',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('camera_id', sa.String(50), sa.ForeignKey('cameras.id'), nullable=False),
            sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
            sa.Column('count', sa.Integer, server_default='0'),
            sa.Column('density', sa.Float, server_default='0.0'),
            sa.Column('avg_velocity', sa.Float, server_default='0.0'),
            sa.Column('max_velocity', sa.Float, server_default='0.0'),
            sa.Column('surge_rate', sa.Float, server_default='0.0'),
            sa.Column('flow_in', sa.Integer, server_default='0'),
            sa.Column('flow_out', sa.Integer, server_default='0'),
            sa.Column('risk_score', sa.Float, server_default='0.0'),
            sa.Column('risk_level', sa.String(20), server_default='SAFE'),
            sa.Column('capacity_utilization', sa.Float, server_default='0.0'),
            sa.Column('frame_number', sa.Integer, server_default='0'),
        )
        op.create_index('ix_metrics_camera_id', 'metrics', ['camera_id'])
        op.create_index('ix_metrics_timestamp', 'metrics', ['timestamp'])

    if 'alerts' not in existing:
        op.create_table(
            'alerts',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('alert_id', sa.String(50), nullable=False, unique=True),
            sa.Column('camera_id', sa.String(50), sa.ForeignKey('cameras.id'), nullable=False),
            sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
            sa.Column('risk_level', sa.String(20), nullable=False),
            sa.Column('trigger_condition', sa.String(100), server_default=''),
            sa.Column('message', sa.Text, nullable=False),
            sa.Column('metrics_snapshot', sa.Text, server_default='{}'),
            sa.Column('acknowledged', sa.Boolean, server_default=sa.text('0')),
            sa.Column('acknowledged_by', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
            sa.Column('acknowledged_at', sa.DateTime, nullable=True),
            sa.Column('resolved', sa.Boolean, server_default=sa.text('0')),
            sa.Column('resolved_at', sa.DateTime, nullable=True),
            sa.Column('snapshot_path', sa.String(255), nullable=True),
        )
        op.create_index('ix_alerts_camera_id', 'alerts', ['camera_id'])
        op.create_index('ix_alerts_timestamp', 'alerts', ['timestamp'])

    if 'recordings' not in existing:
        op.create_table(
            'recordings',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('recording_id', sa.String(50), nullable=False, unique=True),
            sa.Column('camera_id', sa.String(50), sa.ForeignKey('cameras.id'), nullable=False),
            sa.Column('filename', sa.String(256), nullable=False),
            sa.Column('filepath', sa.String(512), nullable=False),
            sa.Column('start_time', sa.DateTime, server_default=sa.func.now()),
            sa.Column('end_time', sa.DateTime, nullable=True),
            sa.Column('duration_seconds', sa.Float, server_default='0.0'),
            sa.Column('frame_count', sa.Integer, server_default='0'),
            sa.Column('width', sa.Integer, server_default='0'),
            sa.Column('height', sa.Integer, server_default='0'),
            sa.Column('fps', sa.Float, server_default='0.0'),
            sa.Column('file_size_bytes', sa.BigInteger, server_default='0'),
            sa.Column('thumbnail_path', sa.String(255), nullable=True),
            sa.Column('trigger_type', sa.String(50), server_default='manual'),
        )
        op.create_index('ix_recordings_camera_id', 'recordings', ['camera_id'])

    if 'settings' not in existing:
        op.create_table(
            'settings',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('key', sa.String(100), nullable=False, unique=True),
            sa.Column('value', sa.Text, server_default=''),
            sa.Column('category', sa.String(50), server_default='general'),
            sa.Column('description', sa.Text, server_default=''),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_by', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
        )

    if 'system_logs' not in existing:
        op.create_table(
            'system_logs',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
            sa.Column('level', sa.String(20), server_default='info'),
            sa.Column('component', sa.String(50), server_default=''),
            sa.Column('message', sa.Text, server_default=''),
            sa.Column('details', sa.Text, server_default='{}'),
            sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
        )
        op.create_index('ix_system_logs_timestamp', 'system_logs', ['timestamp'])
        op.create_index('ix_system_logs_level', 'system_logs', ['level'])


def downgrade() -> None:
    # Baseline — no downgrade path (would wipe the world).
    pass
