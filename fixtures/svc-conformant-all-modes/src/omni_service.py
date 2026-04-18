"""Omni service — conformant example declaring all four approved auth modes."""

import secrets

import jwt
from ct_auth.fastapi import ControlTowerAuth
from fastapi import FastAPI, HTTPException, Request

app = FastAPI()
auth = ControlTowerAuth(
    jwks_url="https://ct.example.com/.well-known/jwks.json", audience="omni-service"
)


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "healthy", "version": "1.0.0", "checks": {}}


def _verify_service_token(token: str, jwks_key: str) -> dict[str, object]:
    return jwt.decode(token, jwks_key, algorithms=["RS256"], audience="omni-service")


@app.get("/items")
def items(request: Request, legacy_token: str) -> dict[str, object]:
    authorization = request.headers.get("Authorization", "")
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        return {"ok": True, "mode": "api_key"}
    if secrets.compare_digest(authorization, f"Bearer {legacy_token}"):
        return {"ok": True, "mode": "bearer_legacy"}
    raise HTTPException(status_code=401)
