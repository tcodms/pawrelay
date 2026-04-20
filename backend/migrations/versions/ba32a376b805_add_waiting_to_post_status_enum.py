"""add_waiting_to_post_status_enum

Revision ID: ba32a376b805
Revises: c7f20a1b9e34
Create Date: 2026-04-20 16:44:05.913162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'ba32a376b805'
down_revision: Union[str, None] = 'c7f20a1b9e34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE post_status_enum ADD VALUE IF NOT EXISTS 'waiting' AFTER 'recruiting'")


def downgrade() -> None:
    pass
