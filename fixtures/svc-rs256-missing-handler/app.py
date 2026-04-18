"""Service declares mode.service_rs256 but source does not implement RS256 verification."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/items")
def items() -> dict[str, str]:
    return {"items": "none"}
