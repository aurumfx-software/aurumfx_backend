"""add nominee aadhar front and back documents

Revision ID: de04f8f7ff22
Revises: 6d1c2617fa40
Create Date: 2026-08-19 12:19:38.075562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de04f8f7ff22'
down_revision: Union[str, Sequence[str], None] = '6d1c2617fa40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("nominee_aadhar_front", sa.String(), nullable=True)
    )

    op.add_column(
        "users",
        sa.Column("nominee_aadhar_back", sa.String(), nullable=True)
    )


def downgrade():
    op.drop_column("users", "nominee_aadhar_back")
    op.drop_column("users", "nominee_aadhar_front")
