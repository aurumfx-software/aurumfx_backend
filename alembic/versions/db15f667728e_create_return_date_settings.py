"""create return date settings

Revision ID: db15f667728e
Revises: e98d9382b009
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "db15f667728e"
down_revision: Union[str, Sequence[str], None] = "e98d9382b009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "return_date_settings",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False
        ),

        sa.Column(
            "from_day",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "to_day",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "payout_day",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "status",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true()
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now()
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("return_date_settings")