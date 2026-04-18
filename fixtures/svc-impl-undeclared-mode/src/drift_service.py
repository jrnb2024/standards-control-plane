"""Drift service — declares api_key but also wires ControlTowerAuth (user_oidc)."""

from ct_auth.fastapi import ControlTowerAuth
from fastapi import FastAPI, Request

app = FastAPI()
auth = ControlTowerAuth(jwks_url="https://ct.example.com/.well-known/jwks.json", audience="drift")


@app.get("/items")
def items(request: Request) -> dict[str, str]:
    _api_key = request.headers.get("X-API-Key", "")
    return {"api_key": _api_key}
