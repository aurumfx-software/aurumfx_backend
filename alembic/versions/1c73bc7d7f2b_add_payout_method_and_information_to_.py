"""add payout method and information to payout history

Revision ID: 1c73bc7d7f2b
Revises: 52e3d94f3db7
Create Date: 2026-08-15 20:24:51.403153

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c73bc7d7f2b'
down_revision: Union[str, Sequence[str], None] = 'e26d8fa59045'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'payout_history',
        sa.Column('payout_method', sa.String(), nullable=True)
    )

    op.add_column(
        'payout_history',
        sa.Column('payout_information', sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('payout_history', 'payout_information')
    op.drop_column('payout_history', 'payout_method')