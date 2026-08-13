"""remove plan_id from adminfee settings

Revision ID: 66f285f06ce7
Revises: 86ec170f7d98
Create Date: 2026-08-13 16:04:05.092341

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66f285f06ce7'
down_revision: Union[str, Sequence[str], None] = '86ec170f7d98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
