"""add district column to users

Revision ID: dd5429552986
Revises: b96ce8351d5a
Create Date: 2026-09-03 13:56:42.160091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd5429552986'
down_revision: Union[str, Sequence[str], None] = 'b96ce8351d5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("district", sa.String(), nullable=True)
    )


def downgrade():
    op.drop_column("users", "district")
