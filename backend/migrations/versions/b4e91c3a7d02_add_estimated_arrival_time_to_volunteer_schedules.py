"""add estimated_arrival_time to volunteer_schedules

Revision ID: b4e91c3a7d02
Revises: 3289b011bcb8
Create Date: 2026-04-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4e91c3a7d02'
down_revision: Union[str, None] = '3289b011bcb8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('volunteer_schedules', sa.Column('estimated_arrival_time', sa.String(length=5), nullable=True))
    op.create_check_constraint(
        "ck_volunteer_schedules_estimated_arrival_time_hhmm",
        "volunteer_schedules",
        "estimated_arrival_time IS NULL OR estimated_arrival_time ~ '^(?:[01][0-9]|2[0-3]):[0-5][0-9]$'",
    )


def downgrade() -> None:
    bind = op.get_bind()
    exists = bind.execute(sa.text(
        "SELECT 1 FROM information_schema.table_constraints "
        "WHERE constraint_name = 'ck_volunteer_schedules_estimated_arrival_time_hhmm'"
    )).scalar()
    if exists:
        op.drop_constraint("ck_volunteer_schedules_estimated_arrival_time_hhmm", "volunteer_schedules")
    op.drop_column('volunteer_schedules', 'estimated_arrival_time')
