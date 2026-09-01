"""add approval status updated at to investments

Revision ID: 3c9a588663ac
Revises: b0c3794e3c4a
Create Date: 2026-09-01 09:43:24.645889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c9a588663ac'
down_revision: Union[str, Sequence[str], None] = 'b0c3794e3c4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "investments",
        sa.Column(
            "approval_status_updated_at",
            sa.DateTime(timezone=True),
            nullable=True
        )
    )


def downgrade():
    op.drop_column(
        "investments",
        "approval_status_updated_at"
    )