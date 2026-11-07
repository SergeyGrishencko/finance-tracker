import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Finance Tracker")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    uvicorn.run("finance_tracker.main:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
