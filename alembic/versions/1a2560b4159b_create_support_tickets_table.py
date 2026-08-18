"""create support tickets table

Revision ID: 1a2560b4159b
Revises: 1885ac4c2398
Create Date: 2026-08-18 09:52:30.267593
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1a2560b4159b"
down_revision: Union[str, Sequence[str], None] = "1885ac4c2398"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "support_tickets",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "ticket_number",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "subject",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "attachment",
            sa.String(),
            nullable=True,
        ),

        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default="OPEN",
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),

        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_number"),
    )

    op.create_index(
        "ix_support_tickets_id",
        "support_tickets",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_support_tickets_ticket_number",
        "support_tickets",
        ["ticket_number"],
        unique=True,
    )

    op.create_index(
        "ix_support_tickets_user_id",
        "support_tickets",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_support_tickets_user_id",
        table_name="support_tickets",
    )

    op.drop_index(
        "ix_support_tickets_ticket_number",
        table_name="support_tickets",
    )

    op.drop_index(
        "ix_support_tickets_id",
        table_name="support_tickets",
    )

    op.drop_table("support_tickets")