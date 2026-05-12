"""fix_relay_segments_waypoint_fk

Revision ID: d856dcdf8f32
Revises: 4fcd2a6fff38
Create Date: 2026-05-12 20:59:04.934017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'd856dcdf8f32'
down_revision: Union[str, None] = '4fcd2a6fff38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('fk_relay_segments_waypoint_id', 'relay_segments', type_='foreignkey')
    op.create_foreign_key('fk_relay_segments_waypoint_id', 'relay_segments', 'waypoints', ['waypoint_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_relay_segments_waypoint_id', 'relay_segments', type_='foreignkey')
    op.create_foreign_key('fk_relay_segments_waypoint_id', 'relay_segments', 'waypoints', ['waypoint_id'], ['id'], ondelete='SET NULL')
