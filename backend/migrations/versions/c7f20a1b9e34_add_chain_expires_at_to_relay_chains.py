"""add chain_expires_at to relay_chains

Revision ID: c7f20a1b9e34
Revises: b4e91c3a7d02
Create Date: 2026-04-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7f20a1b9e34'
down_revision: Union[str, None] = 'b4e91c3a7d02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('relay_chains', sa.Column('chain_expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('relay_chains', 'chain_expires_at')
