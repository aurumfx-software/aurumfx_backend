"""add bank status to users

Revision ID: e34cb2854b32
Revises: de04f8f7ff22
Create Date: 2026-08-19 15:48:02.990189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e34cb2854b32'
down_revision: Union[str, Sequence[str], None] = 'de04f8f7ff22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "bank_status",
            sa.String(),
            nullable=False,
            server_default="PENDING"
        )
    )


def downgrade():
    op.drop_column("users", "bank_status")