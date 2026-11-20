"""page predictions

Revision ID: 630a76eed6b0
Revises: 6bb35f14b90b
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "630a76eed6b0"
down_revision: str | None = "6bb35f14b90b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "pages", sa.Column("predictions", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("pages", "predictions")
