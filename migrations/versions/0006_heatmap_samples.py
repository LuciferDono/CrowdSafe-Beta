"""add heatmap_samples table

Revision ID: 0006_heatmap_samples
Revises: 0005_venues
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

revision = '0006_heatmap_samples'
down_revision = '0005_venues'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if 'heatmap_samples' in tables:
        return

    op.create_table(
        'heatmap_samples',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('camera_id', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('grid_rows', sa.Integer(), nullable=False),
        sa.Column('grid_cols', sa.Integer(), nullable=False),
        sa.Column('grid_data', sa.Text(), nullable=False),
        sa.Column('person_count', sa.Integer(), server_default='0'),
        sa.Column('peak_density', sa.Float(), server_default='0'),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id']),
    )
    op.create_index(
        'ix_heatmap_samples_camera_id', 'heatmap_samples', ['camera_id']
    )
    op.create_index(
        'ix_heatmap_samples_timestamp', 'heatmap_samples', ['timestamp']
    )


def downgrade() -> None:
    op.drop_index('ix_heatmap_samples_timestamp', table_name='heatmap_samples')
    op.drop_index('ix_heatmap_samples_camera_id', table_name='heatmap_samples')
    op.drop_table('heatmap_samples')
