"""Self-hosted service — only implements api_key auth."""

from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/items")
def items(request: Request) -> dict[str, str]:
    return {"api_key": request.headers.get("X-API-Key", "")}
