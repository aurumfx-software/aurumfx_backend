"""admin fee add walet table

Revision ID: 7bc4786aaad6
Revises: 66f285f06ce7
Create Date: 2026-08-13 16:53:20.709881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bc4786aaad6'
down_revision: Union[str, Sequence[str], None] = '66f285f06ce7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
