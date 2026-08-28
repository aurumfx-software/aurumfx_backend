"""add building_no and street to users

Revision ID: b0c3794e3c4a
Revises: 55f66dd4cc48
Create Date: 2026-08-28 13:48:00.358568

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0c3794e3c4a'
down_revision: Union[str, Sequence[str], None] = '55f66dd4cc48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("building_no", sa.String(), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("street", sa.String(), nullable=True)
    )


def downgrade():
    op.drop_column("users", "street")
    op.drop_column("users", "building_no")
