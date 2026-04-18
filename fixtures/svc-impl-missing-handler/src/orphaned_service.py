"""Orphaned service — declares mode.user_oidc but has no CT OIDC implementation."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/items")
def items() -> dict[str, str]:
    return {"items": "none"}
