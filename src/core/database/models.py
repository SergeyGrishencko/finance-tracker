from __future__ import annotations

from enum import Enum

from sqlalchemy import CheckConstraint, Dialect, Index, Text, TypeDecorator, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей проекта."""


class TransactionType(Enum):
    """Тип финансовой операции: доход или расход."""

    INCOME = "income"
    EXPENSE = "expense"


class TransactionTypeText(TypeDecorator[TransactionType]):
    """TEXT-колонка, которая хранит TransactionType и отклоняет любые другие значения."""

    impl = Text
    cache_ok = True

    def process_bind_param(
        self, value: TransactionType | str | None, dialect: Dialect
    ) -> str | None:
        """Подготавливает значение для записи: enum или валидная строка, иначе LookupError."""
        if value is None:
            return None
        if isinstance(value, TransactionType):
            return value.value
        if isinstance(value, str):
            try:
                return TransactionType(value).value
            except ValueError as exc:
                raise LookupError(f"недопустимый тип операции: {value!r}") from exc
        raise LookupError(f"недопустимый тип операции: {value!r}")

    def process_result_value(self, value: str | None, dialect: Dialect) -> TransactionType | None:
        """Восстанавливает TransactionType из текстового значения, прочитанного из БД."""
        if value is None:
            return None
        return TransactionType(value)


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
    type: Mapped[TransactionType] = mapped_column(TransactionTypeText)
    amount: Mapped[int]
    category: Mapped[str] = mapped_column(Text)
    note: Mapped[str] = mapped_column(Text, server_default="")
    occurred_at: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(
        Text,
        server_default=text("(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"),
    )
