# Finance Tracker

Локальное приложение для учёта личных финансов: доходы, расходы, статистика и графики.
Бэкенд — FastAPI, хранилище — SQLite (локальный файл БД).

## Стек

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — управление зависимостями и окружением
- FastAPI + Uvicorn
- python-dotenv — конфигурация через `.env`
- pytest — тесты (unit и integration)

## Запуск локально

### 1. Установить uv (если ещё нет)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Установить зависимости и создать окружение

Из корня проекта:

```bash
uv sync
```

Команда создаст виртуальное окружение `.venv`, заберёт зависимости из `uv.lock` и установит их (включая dev-зависимости с pytest).

### 3. Создать файл конфигурации

```bash
cp .env.example .env
```

Все настройки приложения — в `.env` в корне проекта:

| Ключ | По умолчанию | Описание |
|---|---|---|
| `FINANCE_TRACKER_DB_PATH` | `~/.local/share/finance-tracker/finance-tracker.db` | путь к файлу SQLite-БД; `~` раскрывается, директория создаётся при старте |
| `FINANCE_TRACKER_HOST` | `127.0.0.1` | хост сервера |
| `FINANCE_TRACKER_PORT` | `8000` | порт сервера |

Переменные окружения ОС на конфигурацию не влияют: единственный источник настроек — файл `.env`. Если какого-то ключа в нём нет, используется значение по умолчанию из кода.

### 4. Запустить сервер

```bash
uv run python src/main.py
```

или так (удобно в разработке, с автоперезагрузкой):

```bash
uv run uvicorn main:app --app-dir src --reload
```

Сервер поднимается на хосте и порте из `.env` (по умолчанию `127.0.0.1:8000`).

### 5. Проверить, что работает

- Health-check: http://127.0.0.1:8000/health
- Swagger UI: http://127.0.0.1:8000/docs

## Тесты

```bash
uv run pytest                     # все тесты
uv run pytest tests/unit          # только unit-тесты
uv run pytest tests/integration   # только интеграционные тесты
```

Структура `tests/unit` и `tests/integration` зеркалит структуру `src`. Сейчас покрыт тестами модуль конфигурации (`tests/unit/core/configuration/test_config.py`).

## Структура проекта

```
finance-tracker/
├── docs/                          # документация и задачи
├── src/
│   ├── main.py                    # точка входа (FastAPI-приложение)
│   └── core/
│       └── configuration/
│           └── config.py          # чтение настроек из .env
├── tests/
│   ├── unit/                      # unit-тесты (зеркалят структуру src)
│   └── integration/               # интеграционные тесты (зеркалят структуру src)
├── .env.example                   # шаблон конфигурации (сам .env в .gitignore)
├── pyproject.toml
├── uv.lock
└── README.md
```

## Планы

- Учёт доходов и расходов в локальной SQLite-БД
- Графики и динамика трат
- Упаковка в десктоп-приложение (ярлык на рабочем столе)
