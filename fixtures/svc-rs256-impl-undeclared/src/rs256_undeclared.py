"""Service declares only api_key, but code decodes tokens with RS256."""

import jwt
from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/items")
def items(request: Request) -> dict[str, str]:
    api_key = request.headers.get("X-API-Key", "")
    authorization = request.headers.get("Authorization", "")
    _decoded = jwt.decode(
        authorization.removeprefix("Bearer "),
        "key-placeholder",
        algorithms=["RS256"],
    )
    return {"api_key": api_key}
