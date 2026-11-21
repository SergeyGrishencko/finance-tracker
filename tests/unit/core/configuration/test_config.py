from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.configuration.config import Config

DEFAULT_CONFIG = Config(
    db_path=Path("~/.local/share/finance-tracker/finance-tracker.db").expanduser(),
    host="127.0.0.1",
    port=8000,
)


def write_env(tmp_path: Path, content: str) -> Path:
    env_path = tmp_path / ".env"
    env_path.write_text(content, encoding="utf-8")
    return env_path


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        pytest.param(
            "FINANCE_TRACKER_DB_PATH=/tmp/finance/db.sqlite\n"
            "FINANCE_TRACKER_HOST=0.0.0.0\n"
            "FINANCE_TRACKER_PORT=9000\n",
            Config(db_path=Path("/tmp/finance/db.sqlite"), host="0.0.0.0", port=9000),
            id="all-values-from-file",
        ),
        pytest.param(
            "FINANCE_TRACKER_HOST=0.0.0.0\n",
            Config(
                db_path=DEFAULT_CONFIG.db_path,
                host="0.0.0.0",
                port=DEFAULT_CONFIG.port,
            ),
            id="partial-file-uses-defaults",
        ),
        pytest.param(
            "",
            DEFAULT_CONFIG,
            id="empty-file-uses-defaults",
        ),
        pytest.param(
            "\n".join(
                f"{key}="
                for key in (
                    "FINANCE_TRACKER_DB_PATH",
                    "FINANCE_TRACKER_HOST",
                    "FINANCE_TRACKER_PORT",
                )
            ),
            DEFAULT_CONFIG,
            id="blank-values-use-defaults",
        ),
    ],
)
def test_load(tmp_path: Path, content: str, expected: Config) -> None:
    env_path = write_env(tmp_path, content)

    assert Config.load(env_path) == expected


def test_load_missing_file_uses_defaults(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"

    assert Config.load(env_path) == DEFAULT_CONFIG


@pytest.mark.parametrize(
    ("port_value", "expected_port"),
    [
        pytest.param("1", 1, id="min-port"),
        pytest.param("8000", 8000, id="default-port"),
        pytest.param("65535", 65535, id="max-port"),
    ],
)
def test_load_converts_port_to_int(tmp_path: Path, port_value: str, expected_port: int) -> None:
    env_path = write_env(tmp_path, f"FINANCE_TRACKER_PORT={port_value}\n")

    assert Config.load(env_path).port == expected_port


@pytest.mark.parametrize(
    "port_value",
    [
        pytest.param("abc", id="letters"),
        pytest.param("12.5", id="float"),
        pytest.param("8 000", id="space-inside"),
    ],
)
def test_load_invalid_port_raises(tmp_path: Path, port_value: str) -> None:
    env_path = write_env(tmp_path, f"FINANCE_TRACKER_PORT={port_value}\n")

    with pytest.raises(ValueError):
        Config.load(env_path)


def test_load_expands_user_in_db_path(tmp_path: Path) -> None:
    env_path = write_env(tmp_path, "FINANCE_TRACKER_DB_PATH=~/data/ft.db\n")

    assert Config.load(env_path).db_path == Path.home() / "data" / "ft.db"


@pytest.mark.parametrize(
    "env_var",
    [
        pytest.param("FINANCE_TRACKER_DB_PATH", id="db-path"),
        pytest.param("FINANCE_TRACKER_HOST", id="host"),
        pytest.param("FINANCE_TRACKER_PORT", id="port"),
    ],
)
def test_load_ignores_os_environ(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, env_var: str
) -> None:
    monkeypatch.setenv(env_var, "spoiled-value")
    env_path = write_env(
        tmp_path,
        "FINANCE_TRACKER_DB_PATH=/tmp/finance/db.sqlite\n"
        "FINANCE_TRACKER_HOST=0.0.0.0\n"
        "FINANCE_TRACKER_PORT=9000\n",
    )
    expected = Config(db_path=Path("/tmp/finance/db.sqlite"), host="0.0.0.0", port=9000)

    assert Config.load(env_path) == expected


@pytest.mark.parametrize(
    "rel_path",
    [
        pytest.param("db.sqlite", id="flat"),
        pytest.param("finance/db.sqlite", id="one-level"),
        pytest.param("finance/tracker/data/db.sqlite", id="nested"),
    ],
)
def test_create_db_dir_creates_parent_dirs(tmp_path: Path, rel_path: str) -> None:
    config = Config(db_path=tmp_path / rel_path, host="127.0.0.1", port=8000)

    config.create_db_dir()

    assert config.db_path.parent.is_dir()
    assert not config.db_path.exists()


def test_create_db_dir_idempotent_for_existing_dir(tmp_path: Path) -> None:
    config = Config(db_path=tmp_path / "db.sqlite", host="127.0.0.1", port=8000)
    config.create_db_dir()

    config.create_db_dir()

    assert config.db_path.parent.is_dir()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("db_path", Path("/other/db.sqlite"), id="db-path"),
        pytest.param("host", "0.0.0.0", id="host"),
        pytest.param("port", 9999, id="port"),
    ],
)
def test_config_is_frozen(field: str, value: object) -> None:
    config = Config(db_path=Path("/tmp/db.sqlite"), host="127.0.0.1", port=8000)

    with pytest.raises(FrozenInstanceError):
        setattr(config, field, value)
