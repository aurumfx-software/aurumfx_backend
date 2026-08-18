"""update kyc for front and back documents

Revision ID: 6d1c2617fa40
Revises: eb9b2c434204
Create Date: 2026-08-18 18:22:47.219911

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d1c2617fa40'
down_revision: Union[str, Sequence[str], None] = 'eb9b2c434204'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "user_kyc",
        sa.Column(
            "front_file_name",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "user_kyc",
        sa.Column(
            "front_file_url",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "user_kyc",
        sa.Column(
            "back_file_name",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "user_kyc",
        sa.Column(
            "back_file_url",
            sa.Text(),
            nullable=True,
        ),
    )

    # Existing records
    op.execute(
        """
        UPDATE user_kyc
        SET
            front_file_name = file_name,
            front_file_url = file_url
        WHERE front_file_name IS NULL
        """
    )

    op.alter_column(
        "user_kyc",
        "front_file_name",
        nullable=False,
    )

    op.alter_column(
        "user_kyc",
        "front_file_url",
        nullable=False,
    )

    op.drop_column(
        "user_kyc",
        "file_name",
    )

    op.drop_column(
        "user_kyc",
        "file_url",
    )


def downgrade():

    op.add_column(
        "user_kyc",
        sa.Column(
            "file_name",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "user_kyc",
        sa.Column(
            "file_url",
            sa.Text(),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE user_kyc
        SET
            file_name = front_file_name,
            file_url = front_file_url
        """
    )

    op.drop_column(
        "user_kyc",
        "front_file_name",
    )

    op.drop_column(
        "user_kyc",
        "front_file_url",
    )

    op.drop_column(
        "user_kyc",
        "back_file_name",
    )

    op.drop_column(
        "user_kyc",
        "back_file_url",
    )
