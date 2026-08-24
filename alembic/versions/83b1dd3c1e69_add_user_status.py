"""add user status

Revision ID: YOUR_REVISION_ID
Revises: YOUR_PREVIOUS_REVISION
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "83b1dd3c1e69"
down_revision: Union[str, Sequence[str], None] = "db15f667728e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.add_column(
        "users",
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default="ACTIVE",
        ),
    )

    op.create_index(
        "ix_users_status",
        "users",
        ["status"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_users_status",
        table_name="users",
    )

    op.drop_column(
        "users",
        "status",
    )