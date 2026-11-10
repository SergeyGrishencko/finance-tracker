from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from core.database.db import run_migrations

INSERT_SQL = (
    "INSERT INTO transactions (type, amount, category, note, occurred_at) "
    "VALUES (?, ?, ?, ?, ?)"
)


def connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def query_all(db_path: Path, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    connection = connect(db_path)
    try:
        return connection.execute(sql, params).fetchall()
    finally:
        connection.close()


def insert(db_path: Path, params: tuple) -> None:
    connection = connect(db_path)
    try:
        connection.execute(INSERT_SQL, params)
        connection.commit()
    finally:
        connection.close()


def test_run_migrations_creates_file_in_missing_nested_dir(tmp_path: Path) -> None:
    db_path = tmp_path / "finance" / "tracker" / "db.sqlite"

    run_migrations(db_path)

    assert db_path.is_file()


@pytest.mark.parametrize(
    ("object_name", "object_kind"),
    [
        pytest.param("transactions", "table", id="transactions-table"),
        pytest.param("idx_transactions_occurred_at", "index", id="occurred-at-index"),
        pytest.param("idx_transactions_type", "index", id="type-index"),
    ],
)
def test_run_migrations_creates_schema_objects(
    tmp_path: Path, object_name: str, object_kind: str
) -> None:
    db_path = tmp_path / "db.sqlite"
    run_migrations(db_path)

    found = query_all(db_path, "SELECT type FROM sqlite_master WHERE name = ?", (object_name,))

    assert [row["type"] for row in found] == [object_kind]


def test_run_migrations_stamps_alembic_version(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    run_migrations(db_path)

    tables = query_all(
        db_path,
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'alembic_version'",
    )

    assert len(tables) == 1


def test_run_migrations_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"

    run_migrations(db_path)
    run_migrations(db_path)

    tables = query_all(
        db_path,
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'transactions'",
    )
    assert len(tables) == 1


@pytest.mark.parametrize(
    "invalid_type",
    [
        pytest.param("transfer", id="unknown-type"),
        pytest.param("INCOME", id="wrong-case"),
        pytest.param("", id="empty"),
        pytest.param(None, id="null"),
    ],
)
def test_insert_rejects_invalid_type(tmp_path: Path, invalid_type: str | None) -> None:
    db_path = tmp_path / "db.sqlite"
    run_migrations(db_path)

    with pytest.raises(sqlite3.IntegrityError):
        insert(db_path, (invalid_type, 1050, "Зарплата", "", "2026-11-09"))


@pytest.mark.parametrize(
    "invalid_amount",
    [
        pytest.param(0, id="zero"),
        pytest.param(-1050, id="negative"),
        pytest.param(None, id="null"),
    ],
)
def test_insert_rejects_non_positive_amount(tmp_path: Path, invalid_amount: int | None) -> None:
    db_path = tmp_path / "db.sqlite"
    run_migrations(db_path)

    with pytest.raises(sqlite3.IntegrityError):
        insert(db_path, ("income", invalid_amount, "Зарплата", "", "2026-11-09"))


@pytest.mark.parametrize(
    "field_index",
    [
        pytest.param(2, id="null-category"),
        pytest.param(4, id="null-occurred-at"),
    ],
)
def test_insert_rejects_null_required_fields(tmp_path: Path, field_index: int) -> None:
    db_path = tmp_path / "db.sqlite"
    run_migrations(db_path)

    params = ["income", 1050, "Зарплата", "", "2026-11-09"]
    params[field_index] = None

    with pytest.raises(sqlite3.IntegrityError):
        insert(db_path, tuple(params))


def test_insert_stores_amount_in_kopecks(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    run_migrations(db_path)
    insert(db_path, ("expense", 1050, "Кафе", "", "2026-11-09"))

    amount = query_all(db_path, "SELECT amount FROM transactions")[0]["amount"]

    assert amount == 1050
    assert isinstance(amount, int)


def test_insert_fills_created_at_automatically(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    run_migrations(db_path)
    insert(db_path, ("income", 1050, "Зарплата", "", "2026-11-09"))

    created_at = query_all(db_path, "SELECT created_at FROM transactions")[0]["created_at"]

    assert isinstance(created_at, str)
    assert created_at.startswith("20")


def test_insert_returns_row_with_all_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    run_migrations(db_path)
    insert(db_path, ("expense", 4200, "Продукты", "Пятёрочка", "2026-11-08"))

    row = dict(query_all(db_path, "SELECT * FROM transactions")[0])

    assert row == {
        "id": 1,
        "type": "expense",
        "amount": 4200,
        "category": "Продукты",
        "note": "Пятёрочка",
        "occurred_at": "2026-11-08",
        "created_at": row["created_at"],
    }
