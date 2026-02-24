"""Add merchants table

Revision ID: de09c6256aea
Revises: a5c9d5ac614e
Create Date: 2026-02-24 18:43:31.126553

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "de09c6256aea"
down_revision: Union[str, Sequence[str], None] = "a5c9d5ac614e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "merchants",
        sa.Column("id", sa.String(), primary_key=True, nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("default_cashback_percentage", sa.Float(), nullable=False),
        sa.Column(
            "active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("merchants")
