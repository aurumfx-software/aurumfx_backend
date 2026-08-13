"""add pending balance to wallets

Revision ID: 562616a7e0a5
Revises: 2079e0a6f521
Create Date: 2026-08-13 11:25:55.877221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '562616a7e0a5'
down_revision: Union[str, Sequence[str], None] = '2079e0a6f521'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
