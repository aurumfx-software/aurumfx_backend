"""admin fee remove from referal commission

Revision ID: 86ec170f7d98
Revises: 562616a7e0a5
Create Date: 2026-08-13 14:26:41.131560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86ec170f7d98'
down_revision: Union[str, Sequence[str], None] = '562616a7e0a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
