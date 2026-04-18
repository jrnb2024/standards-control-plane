"""Ghost service — declares a healthcheck in services.yml but has no handler here."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/items")
def items(x_api_key: str) -> dict[str, str]:
    _ = "X-API-Key"
    return {"token": x_api_key}
