"""Общие фикстуры юнит-тестов для работы с тестовой SQLite-БД."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from core.database.db import run_migrations

INSERT_TRANSACTION_SQL = (
    "INSERT INTO transactions (type, amount, category, note, occurred_at) "
    "VALUES (?, ?, ?, ?, ?)"
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Возвращает путь к ещё не созданному файлу тестовой БД во временной директории."""
    return tmp_path / "db.sqlite"


@pytest.fixture
def db_connection(db_path: Path) -> Iterator[sqlite3.Connection]:
    """Открывает подключение к тестовой БД с применёнными миграциями и закрывает его после теста."""
    run_migrations(db_path)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    yield connection
    connection.close()


@pytest.fixture
def query_all(db_connection: sqlite3.Connection) -> Callable[[str, tuple], list[sqlite3.Row]]:
    """Возвращает функцию, выполняющую SELECT-запрос к тестовой БД и возвращающую все строки."""

    def execute_query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Выполняет SELECT-запрос к тестовой БД и возвращает все найденные строки."""
        return db_connection.execute(sql, params).fetchall()

    return execute_query


@pytest.fixture
def insert_transaction(db_connection: sqlite3.Connection) -> Callable[[tuple], None]:
    """Возвращает функцию, добавляющую одну транзакцию в тестовую БД с фиксацией коммита."""

    def execute_insert(params: tuple) -> None:
        """Вставляет строку транзакции в тестовую БД и коммитит изменения."""
        db_connection.execute(INSERT_TRANSACTION_SQL, params)
        db_connection.commit()

    return execute_insert
