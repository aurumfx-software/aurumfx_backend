"""separate bank and nominee status

Revision ID: b96ce8351d5a
Revises: ca1de0a66631
Create Date: 2026-09-02 12:55:35.252147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b96ce8351d5a'
down_revision: Union[str, Sequence[str], None] = 'ca1de0a66631'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    # 1. Add new columns as nullable first
    op.add_column(
        "user_bank_details",
        sa.Column("bank_status", sa.String(), nullable=True),
    )

    op.add_column(
        "user_bank_details",
        sa.Column("bank_rejection_reason", sa.String(), nullable=True),
    )

    op.add_column(
        "user_bank_details",
        sa.Column("nominee_status", sa.String(), nullable=True),
    )

    op.add_column(
        "user_bank_details",
        sa.Column("nominee_rejection_reason", sa.String(), nullable=True),
    )

    # 2. Copy existing generic status/rejection data
    #    into both bank and nominee status fields.
    op.execute(
        """
        UPDATE user_bank_details
        SET
            bank_status = COALESCE(status, 'PENDING'),
            bank_rejection_reason = rejection_reason,
            nominee_status = COALESCE(status, 'PENDING'),
            nominee_rejection_reason = rejection_reason
        """
    )

    # 3. Make the new status columns NOT NULL
    op.alter_column(
        "user_bank_details",
        "bank_status",
        existing_type=sa.String(),
        nullable=False,
    )

    op.alter_column(
        "user_bank_details",
        "nominee_status",
        existing_type=sa.String(),
        nullable=False,
    )

    # 4. Remove old columns
    op.drop_column(
        "user_bank_details",
        "status",
    )

    op.drop_column(
        "user_bank_details",
        "rejection_reason",
    )

def downgrade() -> None:
    # Restore old columns
    op.add_column(
        "user_bank_details",
        sa.Column("status", sa.String(), nullable=True),
    )

    op.add_column(
        "user_bank_details",
        sa.Column("rejection_reason", sa.String(), nullable=True),
    )

    # Use bank status/reason when reverting
    op.execute(
        """
        UPDATE user_bank_details
        SET
            status = bank_status,
            rejection_reason = bank_rejection_reason
        """
    )

    # Remove new columns
    op.drop_column(
        "user_bank_details",
        "nominee_rejection_reason",
    )

    op.drop_column(
        "user_bank_details",
        "nominee_status",
    )

    op.drop_column(
        "user_bank_details",
        "bank_rejection_reason",
    )

    op.drop_column(
        "user_bank_details",
        "bank_status",
    )

    # Make restored columns NOT NULL if required
    op.alter_column(
        "user_bank_details",
        "status",
        existing_type=sa.String(),
        nullable=False,
    )


