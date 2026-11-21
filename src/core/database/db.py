from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy import Engine, create_engine

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"


def build_db_url(db_path: Path) -> str:
    """Собирает URL SQLAlchemy для файла SQLite-БД."""
    return f"sqlite:///{db_path}"


def create_db_engine(db_path: Path) -> Engine:
    """Создаёт движок SQLAlchemy для файла SQLite-БД."""
    return create_engine(build_db_url(db_path))


def run_migrations(db_path: Path) -> None:
    """Применяет все ожидающие миграции Alembic к БД по указанному пути."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    alembic_cfg = AlembicConfig()
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    alembic_cfg.attributes["db_url"] = build_db_url(db_path)
    command.upgrade(alembic_cfg, "head")
