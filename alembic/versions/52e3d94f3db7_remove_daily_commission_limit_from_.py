"""remove daily commission limit from investment plan table

Revision ID: 52e3d94f3db7
Revises: 7dd41e336f06
Create Date: 2026-08-14 15:19:07.093316

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52e3d94f3db7'
down_revision: Union[str, Sequence[str], None] = '7dd41e336f06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("investment_plans", "daily_commission_limit")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "investment_plans",
        sa.Column(
            "daily_commission_limit",
            sa.Numeric(18, 2),
            nullable=True,
        ),
    )
