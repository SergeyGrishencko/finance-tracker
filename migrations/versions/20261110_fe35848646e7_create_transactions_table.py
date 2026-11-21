"""create transactions table

Revision ID: fe35848646e7
Revises: 
Create Date: 2026-11-10 18:37:57.136529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe35848646e7'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("occurred_at", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.Text(),
            nullable=False,
            server_default=sa.text("(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("type IN ('income', 'expense')"),
        sa.CheckConstraint("amount > 0"),
        sqlite_autoincrement=True,
    )
    op.create_index("idx_transactions_occurred_at", "transactions", ["occurred_at"], unique=False)
    op.create_index("idx_transactions_type", "transactions", ["type"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_transactions_type", table_name="transactions")
    op.drop_index("idx_transactions_occurred_at", table_name="transactions")
    op.drop_table("transactions")
