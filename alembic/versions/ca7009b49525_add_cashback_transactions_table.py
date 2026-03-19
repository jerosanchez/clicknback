"""add cashback_transactions table

Revision ID: ca7009b49525
Revises: 8497bfcea306
Create Date: 2026-03-18 18:23:04.589455

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ca7009b49525"
down_revision: Union[str, Sequence[str], None] = "8497bfcea306"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "cashback_transactions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("purchase_id", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "status",
            sa.String(),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchases.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("purchase_id"),
    )
    op.create_index(
        op.f("ix_cashback_transactions_id"),
        "cashback_transactions",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_cashback_transactions_status",
        "cashback_transactions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_cashback_transactions_user_id",
        "cashback_transactions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_cashback_transactions_user_id", table_name="cashback_transactions"
    )
    op.drop_index("ix_cashback_transactions_status", table_name="cashback_transactions")
    op.drop_index(
        op.f("ix_cashback_transactions_id"), table_name="cashback_transactions"
    )
    op.drop_table("cashback_transactions")
