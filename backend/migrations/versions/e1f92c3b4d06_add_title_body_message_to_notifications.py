"""add title, body, message to notifications

Revision ID: e1f92c3b4d06
Revises: d3f81a2b9c05
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1f92c3b4d06"
down_revision: Union[str, None] = "d3f81a2b9c05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("title", sa.String(100), nullable=True))
    op.add_column("notifications", sa.Column("body", sa.String(255), nullable=True))
    op.add_column("notifications", sa.Column("message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("notifications", "message")
    op.drop_column("notifications", "body")
    op.drop_column("notifications", "title")
