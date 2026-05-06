"""add waypoint_id to relay_segments

Revision ID: d3f81a2b9c05
Revises: c7f20a1b9e34
Create Date: 2026-05-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd3f81a2b9c05'
down_revision: Union[str, None] = 'c7f20a1b9e34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('relay_segments', sa.Column('waypoint_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        'fk_relay_segments_waypoint_id',
        'relay_segments', 'waypoints',
        ['waypoint_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_relay_segments_waypoint_id', 'relay_segments', type_='foreignkey')
    op.drop_column('relay_segments', 'waypoint_id')
