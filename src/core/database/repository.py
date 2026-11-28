from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from common.enums import StatsGroupBy, TransactionType
from core.database.models import Transaction


@dataclass(frozen=True)
class TransactionFilters:
    """Фильтры выборки транзакций: период, тип операции и категория."""

    date_from: date | None = None
    date_to: date | None = None
    type: TransactionType | None = None
    category: str | None = None


@dataclass(frozen=True)
class StatsEntry:
    """Суммы доходов и расходов за один период группировки."""

    period: str
    income: int
    expense: int


class TransactionRepository:
    """Инкапсулирует все операции с таблицей transactions, скрывая SQL от API-слоя."""

    def __init__(self, session: Session) -> None:
        """Сохраняет сессию БД, через которую выполняются все запросы репозитория."""
        self._session = session

    def add(
        self,
        *,
        type: TransactionType,
        amount: int,
        category: str,
        occurred_at: date,
        note: str = "",
    ) -> Transaction:
        """Сохраняет новую транзакцию и возвращает её с присвоенными id и created_at."""
        transaction = Transaction(
            type=type.value,
            amount=amount,
            category=category,
            note=note,
            occurred_at=occurred_at.isoformat(),
        )
        self._session.add(transaction)
        self._session.commit()
        self._session.refresh(transaction)
        return transaction

    def get(self, transaction_id: int) -> Transaction | None:
        """Возвращает транзакцию по id или None, если записи с таким id нет."""
        return self._session.get(Transaction, transaction_id)

    def list(self, filters: TransactionFilters | None = None) -> Sequence[Transaction]:
        """Возвращает транзакции по фильтрам, отсортированные от свежих к старым."""
        stmt = select(Transaction)
        if filters is not None:
            if filters.date_from is not None:
                stmt = stmt.where(Transaction.occurred_at >= filters.date_from.isoformat())
            if filters.date_to is not None:
                stmt = stmt.where(Transaction.occurred_at <= filters.date_to.isoformat())
            if filters.type is not None:
                stmt = stmt.where(Transaction.type == filters.type.value)
            if filters.category is not None:
                stmt = stmt.where(Transaction.category == filters.category)
        stmt = stmt.order_by(Transaction.occurred_at.desc(), Transaction.id.desc())
        return self._session.scalars(stmt).all()

    def update(
        self,
        transaction_id: int,
        *,
        type: TransactionType | None = None,
        amount: int | None = None,
        category: str | None = None,
        note: str | None = None,
        occurred_at: date | None = None,
    ) -> Transaction | None:
        """Обновляет только переданные поля транзакции либо возвращает None, если её нет."""
        transaction = self.get(transaction_id)
        if transaction is None:
            return None
        if type is not None:
            transaction.type = type.value
        if amount is not None:
            transaction.amount = amount
        if category is not None:
            transaction.category = category
        if note is not None:
            transaction.note = note
        if occurred_at is not None:
            transaction.occurred_at = occurred_at.isoformat()
        self._session.commit()
        self._session.refresh(transaction)
        return transaction

    def delete(self, transaction_id: int) -> bool:
        """Удаляет транзакцию по id и сообщает, существовала ли такая запись."""
        transaction = self.get(transaction_id)
        if transaction is None:
            return False
        self._session.delete(transaction)
        self._session.commit()
        return True

    def summarize(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        group_by: StatsGroupBy = StatsGroupBy.DAY,
    ) -> Sequence[StatsEntry]:
        """Возвращает суммы доходов и расходов за период, сгруппированные по дням или месяцам."""
        period = (
            Transaction.occurred_at
            if group_by is StatsGroupBy.DAY
            else func.substr(Transaction.occurred_at, 1, 7)
        )
        income = func.sum(
            case(
                (Transaction.type == TransactionType.INCOME.value, Transaction.amount),
                else_=0,
            )
        )
        expense = func.sum(
            case(
                (Transaction.type == TransactionType.EXPENSE.value, Transaction.amount),
                else_=0,
            )
        )
        stmt = select(period.label("period"), income.label("income"), expense.label("expense"))
        if date_from is not None:
            stmt = stmt.where(Transaction.occurred_at >= date_from.isoformat())
        if date_to is not None:
            stmt = stmt.where(Transaction.occurred_at <= date_to.isoformat())
        stmt = stmt.group_by(period).order_by(period)
        rows = self._session.execute(stmt).mappings().all()
        return [
            StatsEntry(
                period=str(row["period"]),
                income=int(row["income"]),
                expense=int(row["expense"]),
            )
            for row in rows
        ]
