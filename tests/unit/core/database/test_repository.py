from __future__ import annotations

import sqlite3
from datetime import date
from typing import Protocol

import pytest
from sqlalchemy.orm import Session

from common.enums import StatsGroupBy, TransactionType
from core.database.repository import (
    StatsEntry,
    TransactionFilters,
    TransactionRepository,
)


class RowQuery(Protocol):
    """Селект-хелпер тестовой БД: выполняет SQL-запрос и возвращает все найденные строки."""

    def __call__(self, sql: str, params: tuple = ...) -> list[sqlite3.Row]:
        """Выполняет SELECT-запрос к тестовой БД и возвращает все найденные строки."""
        ...


@pytest.fixture
def repository(db_session: Session) -> TransactionRepository:
    """Создаёт репозиторий транзакций поверх открытой сессии тестовой БД."""
    return TransactionRepository(db_session)


def seed_transactions(repository: TransactionRepository) -> None:
    """Наполняет тестовую БД фиксированным набором из четырёх транзакций ноября 2026."""
    transactions = [
        (TransactionType.INCOME, 100000, "Зарплата", date(2026, 11, 1)),
        (TransactionType.EXPENSE, 4200, "Продукты", date(2026, 11, 5)),
        (TransactionType.EXPENSE, 1500, "Кафе", date(2026, 11, 10)),
        (TransactionType.INCOME, 50000, "Фриланс", date(2026, 11, 20)),
    ]
    for type, amount, category, occurred_at in transactions:
        repository.add_transaction(
            type=type, amount=amount, category=category, occurred_at=occurred_at
        )


def test_add_transaction_returns_transaction_with_generated_fields(
    repository: TransactionRepository,
) -> None:
    transaction = repository.add_transaction(
        type=TransactionType.EXPENSE,
        amount=4200,
        category="Продукты",
        note="Пятёрочка",
        occurred_at=date(2026, 11, 8),
    )

    assert isinstance(transaction.id, int)
    assert transaction.type == "expense"
    assert transaction.amount == 4200
    assert transaction.category == "Продукты"
    assert transaction.note == "Пятёрочка"
    assert transaction.occurred_at == "2026-11-08"
    assert transaction.created_at


def test_add_transaction_persists_row_in_database(
    repository: TransactionRepository, query_all: RowQuery
) -> None:
    repository.add_transaction(
        type=TransactionType.INCOME,
        amount=1050,
        category="Зарплата",
        note="Аванс",
        occurred_at=date(2026, 11, 9),
    )

    rows = query_all("SELECT * FROM transactions")

    assert [dict(row) for row in rows] == [
        {
            "id": 1,
            "type": "income",
            "amount": 1050,
            "category": "Зарплата",
            "note": "Аванс",
            "occurred_at": "2026-11-09",
            "created_at": rows[0]["created_at"],
        }
    ]


def test_get_transaction_by_id_returns_none_when_missing(repository: TransactionRepository) -> None:
    assert repository.get_transaction_by_id(1) is None


def test_get_transaction_by_id_returns_matching_transaction(
    repository: TransactionRepository,
) -> None:
    added = repository.add_transaction(
        type=TransactionType.EXPENSE,
        amount=1500,
        category="Кафе",
        occurred_at=date(2026, 11, 10),
    )

    found = repository.get_transaction_by_id(added.id)

    assert found is not None
    assert found.id == added.id
    assert found.amount == 1500
    assert found.category == "Кафе"


def test_get_transactions_by_filters_returns_empty_result_without_data(
    repository: TransactionRepository,
) -> None:
    assert repository.get_transactions_by_filters() == []


def test_get_transactions_by_filters_orders_transactions_newest_first(
    repository: TransactionRepository,
) -> None:
    seed_transactions(repository)

    amounts = [transaction.amount for transaction in repository.get_transactions_by_filters()]

    assert amounts == [50000, 1500, 4200, 100000]


def test_get_transactions_by_filters_orders_same_day_transactions_by_id_desc(
    repository: TransactionRepository,
) -> None:
    repository.add_transaction(
        type=TransactionType.EXPENSE, amount=100, category="Кафе", occurred_at=date(2026, 11, 5)
    )
    repository.add_transaction(
        type=TransactionType.EXPENSE,
        amount=200,
        category="Продукты",
        occurred_at=date(2026, 11, 5),
    )

    amounts = [transaction.amount for transaction in repository.get_transactions_by_filters()]

    assert amounts == [200, 100]


@pytest.mark.parametrize(
    ("filters", "expected_amounts"),
    [
        pytest.param(TransactionFilters(), [50000, 1500, 4200, 100000], id="no-filters"),
        pytest.param(TransactionFilters(type=TransactionType.EXPENSE), [1500, 4200], id="by-type"),
        pytest.param(TransactionFilters(category="Продукты"), [4200], id="by-category"),
        pytest.param(
            TransactionFilters(date_from=date(2026, 11, 5)), [50000, 1500, 4200], id="by-date-from"
        ),
        pytest.param(
            TransactionFilters(date_to=date(2026, 11, 5)), [4200, 100000], id="by-date-to"
        ),
        pytest.param(
            TransactionFilters(date_from=date(2026, 11, 5), date_to=date(2026, 11, 10)),
            [1500, 4200],
            id="by-period",
        ),
        pytest.param(
            TransactionFilters(type=TransactionType.INCOME, category="Фриланс"),
            [50000],
            id="by-type-and-category",
        ),
    ],
)
def test_get_transactions_by_filters_applies_filters(
    repository: TransactionRepository,
    filters: TransactionFilters,
    expected_amounts: list[int],
) -> None:
    seed_transactions(repository)

    amounts = [
        transaction.amount for transaction in repository.get_transactions_by_filters(filters)
    ]

    assert amounts == expected_amounts


def test_get_transactions_by_filters_returns_empty_result_when_filters_match_nothing(
    repository: TransactionRepository,
) -> None:
    seed_transactions(repository)

    transactions = repository.get_transactions_by_filters(
        TransactionFilters(category="Путешествия")
    )

    assert transactions == []


def test_update_transaction_changes_provided_fields_and_keeps_the_rest(
    repository: TransactionRepository,
) -> None:
    added = repository.add_transaction(
        type=TransactionType.EXPENSE,
        amount=4200,
        category="Продукты",
        note="Пятёрочка",
        occurred_at=date(2026, 11, 5),
    )

    updated = repository.update_transaction(added.id, amount=5000, note="Вкусвилл")

    assert updated is not None
    assert updated.amount == 5000
    assert updated.note == "Вкусвилл"
    assert updated.type == "expense"
    assert updated.category == "Продукты"
    assert updated.occurred_at == "2026-11-05"


def test_update_transaction_converts_type_and_date_to_storage_format(
    repository: TransactionRepository,
) -> None:
    added = repository.add_transaction(
        type=TransactionType.EXPENSE,
        amount=4200,
        category="Продукты",
        occurred_at=date(2026, 11, 5),
    )

    updated = repository.update_transaction(
        added.id, type=TransactionType.INCOME, occurred_at=date(2026, 12, 1)
    )

    assert updated is not None
    assert updated.type == "income"
    assert updated.occurred_at == "2026-12-01"


def test_update_transaction_returns_none_when_missing(repository: TransactionRepository) -> None:
    assert repository.update_transaction(999, amount=1) is None


def test_update_transaction_persists_changes_in_database(
    repository: TransactionRepository, query_all: RowQuery
) -> None:
    added = repository.add_transaction(
        type=TransactionType.EXPENSE,
        amount=4200,
        category="Продукты",
        occurred_at=date(2026, 11, 5),
    )

    repository.update_transaction(added.id, amount=5000)

    row = query_all("SELECT amount FROM transactions WHERE id = ?", (added.id,))[0]

    assert row["amount"] == 5000


def test_delete_transaction_removes_transaction_and_returns_true(
    repository: TransactionRepository, query_all: RowQuery
) -> None:
    added = repository.add_transaction(
        type=TransactionType.EXPENSE,
        amount=1500,
        category="Кафе",
        occurred_at=date(2026, 11, 10),
    )

    deleted = repository.delete_transaction(added.id)

    assert deleted is True
    assert repository.get_transactions_by_filters() == []
    assert query_all("SELECT id FROM transactions") == []


def test_delete_transaction_returns_false_when_missing(repository: TransactionRepository) -> None:
    assert repository.delete_transaction(999) is False


def test_summarize_groups_amounts_by_day(repository: TransactionRepository) -> None:
    seed_transactions(repository)

    entries = repository.summarize()

    assert entries == [
        StatsEntry(period="2026-11-01", income=100000, expense=0),
        StatsEntry(period="2026-11-05", income=0, expense=4200),
        StatsEntry(period="2026-11-10", income=0, expense=1500),
        StatsEntry(period="2026-11-20", income=50000, expense=0),
    ]


def test_summarize_groups_amounts_by_month(repository: TransactionRepository) -> None:
    seed_transactions(repository)
    repository.add_transaction(
        type=TransactionType.INCOME,
        amount=30000,
        category="Зарплата",
        occurred_at=date(2026, 10, 28),
    )
    repository.add_transaction(
        type=TransactionType.EXPENSE,
        amount=900,
        category="Продукты",
        occurred_at=date(2026, 10, 30),
    )

    entries = repository.summarize(group_by=StatsGroupBy.MONTH)

    assert entries == [
        StatsEntry(period="2026-10", income=30000, expense=900),
        StatsEntry(period="2026-11", income=150000, expense=5700),
    ]


def test_summarize_sums_both_types_within_one_day(repository: TransactionRepository) -> None:
    repository.add_transaction(
        type=TransactionType.INCOME,
        amount=100000,
        category="Зарплата",
        occurred_at=date(2026, 11, 5),
    )
    repository.add_transaction(
        type=TransactionType.EXPENSE,
        amount=4200,
        category="Продукты",
        occurred_at=date(2026, 11, 5),
    )

    entries = repository.summarize()

    assert entries == [StatsEntry(period="2026-11-05", income=100000, expense=4200)]


def test_summarize_applies_period_bounds(repository: TransactionRepository) -> None:
    seed_transactions(repository)

    entries = repository.summarize(date_from=date(2026, 11, 5), date_to=date(2026, 11, 10))

    assert entries == [
        StatsEntry(period="2026-11-05", income=0, expense=4200),
        StatsEntry(period="2026-11-10", income=0, expense=1500),
    ]


def test_summarize_returns_empty_result_without_data(repository: TransactionRepository) -> None:
    assert repository.summarize() == []
