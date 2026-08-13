"""remove admin_fee from walet table

Revision ID: e819a4ea779a
Revises: 7bc4786aaad6
Create Date: 2026-08-13 17:52:02.574758

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e819a4ea779a'
down_revision: Union[str, Sequence[str], None] = '7bc4786aaad6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
