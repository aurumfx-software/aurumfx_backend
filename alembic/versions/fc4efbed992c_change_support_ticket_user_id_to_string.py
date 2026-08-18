"""change support ticket user id to string

Revision ID: fc4efbed992c
Revises: 1a2560b4159b
Create Date: 2026-08-18 12:56:42.552965
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fc4efbed992c"
down_revision: Union[str, Sequence[str], None] = "1a2560b4159b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove old foreign key
    op.drop_constraint(
        "support_tickets_user_id_fkey",
        "support_tickets",
        type_="foreignkey",
    )

    # Change user_id from INTEGER to VARCHAR
    op.alter_column(
        "support_tickets",
        "user_id",
        existing_type=sa.Integer(),
        type_=sa.String(),
        existing_nullable=False,
    )

    # Create foreign key to users.user_id
    op.create_foreign_key(
        "support_tickets_user_id_fkey",
        "support_tickets",
        "users",
        ["user_id"],
        ["user_id"],
    )


def downgrade() -> None:
    # Remove new foreign key
    op.drop_constraint(
        "support_tickets_user_id_fkey",
        "support_tickets",
        type_="foreignkey",
    )

    # Change user_id back to INTEGER
    op.alter_column(
        "support_tickets",
        "user_id",
        existing_type=sa.String(),
        type_=sa.Integer(),
        existing_nullable=False,
    )

    # Restore old foreign key
    op.create_foreign_key(
        "support_tickets_user_id_fkey",
        "support_tickets",
        "users",
        ["user_id"],
        ["id"],
    )