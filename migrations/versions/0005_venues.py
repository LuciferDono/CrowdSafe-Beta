"""add venues table + cameras.venue_id

Revision ID: 0005_venues
Revises: 0004_camera_dense_mode
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

revision = '0005_venues'
down_revision = '0004_camera_dense_mode'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if 'venues' not in tables:
        op.create_table(
            'venues',
            sa.Column('id', sa.String(length=50), primary_key=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('venue_type', sa.String(length=30),
                      server_default='generic'),
            sa.Column('location', sa.String(length=200),
                      server_default=''),
            sa.Column('expected_capacity', sa.Integer(),
                      server_default='0'),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('updated_at', sa.DateTime()),
        )

    cols = {c['name'] for c in inspector.get_columns('cameras')}
    if 'venue_id' not in cols:
        with op.batch_alter_table('cameras') as batch:
            batch.add_column(
                sa.Column('venue_id', sa.String(length=50), nullable=True)
            )
            batch.create_foreign_key(
                'fk_cameras_venue_id',
                'venues',
                ['venue_id'], ['id'],
            )
            batch.create_index('ix_cameras_venue_id', ['venue_id'])


def downgrade() -> None:
    with op.batch_alter_table('cameras') as batch:
        batch.drop_index('ix_cameras_venue_id')
        batch.drop_constraint('fk_cameras_venue_id', type_='foreignkey')
        batch.drop_column('venue_id')
    op.drop_table('venues')
