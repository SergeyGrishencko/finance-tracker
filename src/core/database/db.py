from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    amount INTEGER NOT NULL CHECK (amount > 0),
    category TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_transactions_occurred_at
    ON transactions (occurred_at);

CREATE INDEX IF NOT EXISTS idx_transactions_type
    ON transactions (type);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    """Открывает соединение с SQLite-БД и настраивает доступ к колонкам по имени."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path) -> None:
    """Создаёт директорию и файл БД со схемой; безопасен при повторном запуске."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(db_path)
    try:
        connection.executescript(SCHEMA)
        connection.commit()
    finally:
        connection.close()
