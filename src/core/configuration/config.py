from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"

DEFAULTS = {
    "FINANCE_TRACKER_DB_PATH": "~/.local/share/finance-tracker/finance-tracker.db",
    "FINANCE_TRACKER_HOST": "127.0.0.1",
    "FINANCE_TRACKER_PORT": "8000",
}


@dataclass(frozen=True)
class Config:
    """Иммутабельные настройки приложения: путь к БД, хост и порт сервера."""

    db_path: Path
    host: str
    port: int

    @classmethod
    def load(cls, env_path: Path = ENV_PATH) -> Config:
        """Читает настройки из .env-файла, подставляя дефолты для отсутствующих ключей."""
        file_values = {
            key: value
            for key, value in dotenv_values(env_path).items()
            if value
        }
        values = {**DEFAULTS, **file_values}
        return cls(
            db_path=Path(values["FINANCE_TRACKER_DB_PATH"]).expanduser(),
            host=str(values["FINANCE_TRACKER_HOST"]),
            port=int(values["FINANCE_TRACKER_PORT"]),
        )

    def create_db_dir(self) -> None:
        """Создаёт родительскую директорию файла БД, если её ещё нет."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
