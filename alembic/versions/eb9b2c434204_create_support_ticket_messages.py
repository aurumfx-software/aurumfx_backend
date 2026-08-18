"""create support ticket messages

Revision ID: eb9b2c434204
Revises: fc4efbed992c
Create Date: 2026-08-18 15:08:45.684942
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "eb9b2c434204"
down_revision: Union[str, Sequence[str], None] = "fc4efbed992c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "support_ticket_messages",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "ticket_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "user_id",
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
            "sender_type",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["support_tickets.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_support_ticket_messages_id",
        "support_ticket_messages",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_support_ticket_messages_ticket_id",
        "support_ticket_messages",
        ["ticket_id"],
        unique=False,
    )

    op.create_index(
        "ix_support_ticket_messages_user_id",
        "support_ticket_messages",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_support_ticket_messages_user_id",
        table_name="support_ticket_messages",
    )

    op.drop_index(
        "ix_support_ticket_messages_ticket_id",
        table_name="support_ticket_messages",
    )

    op.drop_index(
        "ix_support_ticket_messages_id",
        table_name="support_ticket_messages",
    )

    op.drop_table("support_ticket_messages")