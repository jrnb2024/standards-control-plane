"""Minimal HTTP service surface over consult and audit builders."""

from __future__ import annotations

import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .audit import build_audit_result
from .consult import build_consult_response
from .registry import load_registry


class StandardsControlPlaneServer(ThreadingHTTPServer):
    overlay_paths: tuple[str, ...]
    auth_token: str | None


class StandardsControlPlaneRequestHandler(BaseHTTPRequestHandler):
    server: StandardsControlPlaneServer

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_unauthorized(self) -> None:
        body = json.dumps({"error": "Unauthorized"}, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(401)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("WWW-Authenticate", "Bearer")
        self.end_headers()
        self.wfile.write(body)

    def _overlay_registry(self):
        return load_registry(
            overlay_paths=[Path(path_value) for path_value in self.server.overlay_paths]
        )

    def _is_authorized(self) -> bool:
        expected = self.server.auth_token
        if expected is None:
            return True
        actual = self.headers.get("Authorization", "")
        expected_header = f"Bearer {expected}"
        return secrets.compare_digest(actual, expected_header)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw_body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("request body must be a JSON object")
        return payload

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if parsed.path == "/registry":
            if not self._is_authorized():
                self._send_unauthorized()
                return
            self._send_json(200, self._overlay_registry().to_dict())
            return
        self._send_json(404, {"error": f"Unknown endpoint: {parsed.path}"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/consult", "/audit"} and not self._is_authorized():
            self._send_unauthorized()
            return
        try:
            payload = self._read_json_body()
            registry_snapshot = self._overlay_registry()
            if parsed.path == "/consult":
                self._send_json(
                    200,
                    build_consult_response(payload, registry_snapshot=registry_snapshot),
                )
                return
            if parsed.path == "/audit":
                self._send_json(
                    200,
                    build_audit_result(payload, registry_snapshot=registry_snapshot),
                )
                return
            self._send_json(404, {"error": f"Unknown endpoint: {parsed.path}"})
        except Exception as error:
            self._send_json(400, {"error": str(error)})

    def log_message(self, format: str, *args: object) -> None:
        return


def create_service_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    overlay_paths: list[str] | None = None,
    auth_token: str | None = None,
) -> StandardsControlPlaneServer:
    server = StandardsControlPlaneServer((host, port), StandardsControlPlaneRequestHandler)
    server.overlay_paths = tuple(overlay_paths or [])
    server.auth_token = auth_token
    return server


def serve(
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    overlay_paths: list[str] | None = None,
    auth_token: str | None = None,
) -> None:
    server = create_service_server(
        host=host,
        port=port,
        overlay_paths=overlay_paths,
        auth_token=auth_token,
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()
