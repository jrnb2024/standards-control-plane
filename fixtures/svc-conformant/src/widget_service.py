"""Conformant widget service — exercises user_oidc + bearer_legacy markers."""
import secrets

from ct_auth.fastapi import ControlTowerAuth
from fastapi import FastAPI, HTTPException, Request

app = FastAPI()
auth = ControlTowerAuth(jwks_url="https://ct.example.com/.well-known/jwks.json", audience="widget")


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "healthy", "version": "1.0.0", "checks": {}}


@app.get("/items")
def items(request: Request, legacy_token: str) -> dict[str, object]:
    authorization = request.headers.get("Authorization", "")
    if secrets.compare_digest(authorization, f"Bearer {legacy_token}"):
        return {"ok": True}
    raise HTTPException(status_code=401)
