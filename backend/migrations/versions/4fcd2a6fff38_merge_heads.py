"""merge_heads

Revision ID: 4fcd2a6fff38
Revises: ba32a376b805, e1f92c3b4d06
Create Date: 2026-05-12 20:58:19.029280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '4fcd2a6fff38'
down_revision: Union[str, None] = ('ba32a376b805', 'e1f92c3b4d06')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
