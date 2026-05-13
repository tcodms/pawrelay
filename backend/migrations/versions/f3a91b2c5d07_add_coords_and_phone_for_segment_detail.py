"""add_coords_and_phone_for_segment_detail

Revision ID: f3a91b2c5d07
Revises: d856dcdf8f32
Create Date: 2026-05-13 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'f3a91b2c5d07'
down_revision = 'd856dcdf8f32'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # relay_segments에 pickup/dropoff 좌표 추가 (카카오맵 마커용)
    op.add_column('relay_segments', sa.Column('pickup_lat', sa.Numeric(9, 6), nullable=True))
    op.add_column('relay_segments', sa.Column('pickup_lng', sa.Numeric(9, 6), nullable=True))
    op.add_column('relay_segments', sa.Column('dropoff_lat', sa.Numeric(9, 6), nullable=True))
    op.add_column('relay_segments', sa.Column('dropoff_lng', sa.Numeric(9, 6), nullable=True))


def downgrade() -> None:
    op.drop_column('relay_segments', 'dropoff_lng')
    op.drop_column('relay_segments', 'dropoff_lat')
    op.drop_column('relay_segments', 'pickup_lng')
    op.drop_column('relay_segments', 'pickup_lat')
