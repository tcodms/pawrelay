"""add_kakao_openchat_url_to_transport_posts

Revision ID: a2b83c4d6e08
Revises: f3a91b2c5d07
Create Date: 2026-05-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a2b83c4d6e08'
down_revision = 'f3a91b2c5d07'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('transport_posts', sa.Column('kakao_openchat_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('transport_posts', 'kakao_openchat_url')
