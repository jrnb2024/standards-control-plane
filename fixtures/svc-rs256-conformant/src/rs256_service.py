"""RS256 service — conformant; verifies S2S tokens with RS256."""

import jwt
from fastapi import FastAPI, Header, HTTPException

app = FastAPI()


def _verify(token: str, jwks_key: str) -> dict[str, object]:
    return jwt.decode(token, jwks_key, algorithms=["RS256"], audience="rs256-service")


@app.get("/items")
def items(authorization: str = Header(...)) -> dict[str, str]:
    try:
        _verify(authorization.removeprefix("Bearer "), "key-placeholder")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401) from exc
    return {"ok": "true"}
