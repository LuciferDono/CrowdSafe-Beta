"""create audit_logs (append-only)

Revision ID: 0003_audit_log
Revises: 0002_timescale_hypertables
Create Date: 2026-04-17
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_audit_log'
down_revision = '0002_timescale_hypertables'
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == 'postgresql'


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if 'audit_logs' not in existing:
        op.create_table(
            'audit_logs',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('actor_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('actor_username', sa.String(length=80), nullable=True),
            sa.Column('actor_role', sa.String(length=32), nullable=True),
            sa.Column('action', sa.String(length=80), nullable=False),
            sa.Column('target_type', sa.String(length=80), nullable=True),
            sa.Column('target_id', sa.String(length=120), nullable=True),
            sa.Column('ip', sa.String(length=64), nullable=True),
            sa.Column('user_agent', sa.String(length=255), nullable=True),
            sa.Column('request_id', sa.String(length=64), nullable=True),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='ok'),
            sa.Column('meta', sa.Text(), nullable=False, server_default='{}'),
        )
        op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
        op.create_index('ix_audit_logs_actor_id', 'audit_logs', ['actor_id'])
        op.create_index('ix_audit_logs_actor_username', 'audit_logs', ['actor_username'])
        op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
        op.create_index('ix_audit_logs_target_type', 'audit_logs', ['target_type'])
        op.create_index('ix_audit_logs_target_id', 'audit_logs', ['target_id'])
        op.create_index('ix_audit_logs_status', 'audit_logs', ['status'])

    if _is_postgres():
        conn = bind
        # Append-only enforcement. Any UPDATE or DELETE raises.
        conn.exec_driver_sql("""
            CREATE OR REPLACE FUNCTION audit_logs_deny_mutation()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'audit_logs is append-only: % not permitted', TG_OP;
            END;
            $$ LANGUAGE plpgsql;
        """)
        conn.exec_driver_sql("DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs;")
        conn.exec_driver_sql(
            "CREATE TRIGGER audit_logs_no_update "
            "BEFORE UPDATE ON audit_logs "
            "FOR EACH ROW EXECUTE FUNCTION audit_logs_deny_mutation();"
        )
        conn.exec_driver_sql("DROP TRIGGER IF EXISTS audit_logs_no_delete ON audit_logs;")
        conn.exec_driver_sql(
            "CREATE TRIGGER audit_logs_no_delete "
            "BEFORE DELETE ON audit_logs "
            "FOR EACH ROW EXECUTE FUNCTION audit_logs_deny_mutation();"
        )


def downgrade() -> None:
    if _is_postgres():
        conn = op.get_bind()
        conn.exec_driver_sql("DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs;")
        conn.exec_driver_sql("DROP TRIGGER IF EXISTS audit_logs_no_delete ON audit_logs;")
        conn.exec_driver_sql("DROP FUNCTION IF EXISTS audit_logs_deny_mutation();")

    op.drop_index('ix_audit_logs_status', table_name='audit_logs')
    op.drop_index('ix_audit_logs_target_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_target_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_actor_username', table_name='audit_logs')
    op.drop_index('ix_audit_logs_actor_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_timestamp', table_name='audit_logs')
    op.drop_table('audit_logs')
