import uvicorn
from fastapi import FastAPI

from core.configuration.config import Config
from core.database.db import run_migrations

app = FastAPI(title="Finance Tracker")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    config = Config.load()
    run_migrations(config.db_path)
    uvicorn.run("main:app", host=config.host, port=config.port)


if __name__ == "__main__":
    main()
