from __future__ import annotations

from sqlalchemy import CheckConstraint, Index, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей проекта."""


class Transaction(Base):
    """Финансовая операция: доход или расход (сумма в копейках)."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("type IN ('income', 'expense')"),
        CheckConstraint("amount > 0"),
        Index("idx_transactions_occurred_at", "occurred_at"),
        Index("idx_transactions_type", "type"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(Text)
    amount: Mapped[int]
    category: Mapped[str] = mapped_column(Text)
    note: Mapped[str] = mapped_column(Text, server_default="")
    occurred_at: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(
        Text,
        server_default=text("(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"),
    )
