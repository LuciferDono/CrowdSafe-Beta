"""add cameras.dense_mode

Revision ID: 0004_camera_dense_mode
Revises: 0003_audit_log
Create Date: 2026-04-17
"""
from alembic import op
import sqlalchemy as sa

revision = '0004_camera_dense_mode'
down_revision = '0003_audit_log'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c['name'] for c in inspector.get_columns('cameras')}
    if 'dense_mode' in cols:
        return
    # batch_alter_table keeps SQLite happy while remaining no-op-ish on PG.
    with op.batch_alter_table('cameras') as batch:
        batch.add_column(
            sa.Column(
                'dense_mode',
                sa.String(length=10),
                nullable=False,
                server_default='auto',
            )
        )


def downgrade() -> None:
    with op.batch_alter_table('cameras') as batch:
        batch.drop_column('dense_mode')
