from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "8998fe4ba54f"
down_revision: Union[str, Sequence[str], None] = "83b1dd3c1e69"


def upgrade() -> None:
    op.add_column(
        "investments",
        sa.Column(
            "reject_reason",
            sa.String(length=500),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("investments", "reject_reason")