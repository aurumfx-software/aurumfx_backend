"""add admin_fee from walet table

Revision ID: 5c3f45ed2a95
Revises: e819a4ea779a
Create Date: 2026-08-13 17:58:28.774001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c3f45ed2a95'
down_revision: Union[str, Sequence[str], None] = 'e819a4ea779a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
