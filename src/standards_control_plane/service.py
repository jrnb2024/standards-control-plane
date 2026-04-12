"""Minimal HTTP service surface over consult and audit builders."""

from __future__ import annotations

import html
import json
import secrets
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .audit import build_audit_result
from .consult import build_consult_response
from .registry import load_registry
from .resources import project_root


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

    def _send_html(self, status_code: int, payload: str) -> None:
        body = payload.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
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

    def _read_text(self, relative_path: str) -> str:
        target = project_root() / relative_path
        return target.read_text(encoding="utf-8")

    def _try_read_text(self, relative_path: str) -> str | None:
        try:
            return self._read_text(relative_path)
        except FileNotFoundError:
            return None

    def _iso_utc(self, timestamp: float) -> str:
        return (
            datetime.fromtimestamp(timestamp, tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

    def _artifact_health(self, relative_path: str) -> dict[str, Any]:
        path = project_root() / relative_path
        payload: dict[str, Any] = {
            "path": relative_path,
            "exists": path.exists(),
        }
        if not path.exists():
            return payload
        payload["updated_at"] = self._iso_utc(path.stat().st_mtime)
        if path.suffix == ".json":
            try:
                parsed = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return payload
            if isinstance(parsed, dict) and isinstance(parsed.get("generated_at"), str):
                payload["generated_at"] = parsed["generated_at"]
        return payload

    def _status_payload(self) -> dict[str, Any]:
        registry_snapshot = self._overlay_registry()
        artifacts = {
            "latest_review": self._artifact_health("output/reports/latest-review.md"),
            "ci_output": self._artifact_health("output/ci/latest-ci.json"),
            "control_tower_dashboard": self._artifact_health(
                "output/control-tower/estate-dashboard.json"
            ),
            "portfolio_dashboard": self._artifact_health(
                "output/estate/multi-repo-dashboard.json"
            ),
        }
        missing_artifacts = [
            name for name, details in artifacts.items() if not bool(details["exists"])
        ]
        return {
            "status": "ok",
            "service": {
                "name": registry_snapshot.name,
                "standards_version": registry_snapshot.version,
                "domains": sorted(registry_snapshot.domains.keys()),
            },
            "auth": {
                "enabled": self.server.auth_token is not None,
                "mode": "bearer" if self.server.auth_token is not None else "none",
                "protected_endpoints": ["/registry", "/consult", "/audit"],
            },
            "status_app_integration": {
                "healthy": not missing_artifacts,
                "missing_artifacts": missing_artifacts,
            },
            "artifacts": artifacts,
            "docs": {
                "adoption": "/docs/adoption",
                "readme": "https://github.com/jrnb2024/standards-control-plane-/blob/main/README.md",
            },
        }

    def _render_landing_page(self) -> str:
        status_payload = self._status_payload()
        auth_mode = status_payload["auth"]["mode"]
        integration = status_payload["status_app_integration"]
        integration_label = "Healthy" if integration["healthy"] else "Degraded"
        artifact_rows = "\n".join(
            (
                "<tr>"
                f"<td>{html.escape(name.replace('_', ' ').title())}</td>"
                f"<td>{'Yes' if details['exists'] else 'No'}</td>"
                "<td>"
                f"{html.escape(str(details.get('generated_at', details.get('updated_at', '-'))))}"
                "</td>"
                f"<td><code>{html.escape(str(details['path']))}</code></td>"
                "</tr>"
            )
            for name, details in status_payload["artifacts"].items()
        )
        domains = ", ".join(status_payload["service"]["domains"])
        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Standards Control Plane</title>
    <style>
      :root {{
        color-scheme: light dark;
        --bg: #0f172a;
        --panel: #111827;
        --panel-2: #1f2937;
        --text: #e5e7eb;
        --muted: #9ca3af;
        --accent: #38bdf8;
        --line: #334155;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system,
          BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: linear-gradient(180deg, #020617 0%, #0f172a 100%);
        color: var(--text);
      }}
      main {{
        width: min(1100px, calc(100% - 32px));
        margin: 0 auto;
        padding: 32px 0 56px;
      }}
      section {{
        padding: 20px 0;
        border-top: 1px solid var(--line);
      }}
      section:first-of-type {{ border-top: 0; padding-top: 0; }}
      .band {{
        background: rgba(15, 23, 42, 0.82);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 16px;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 12px;
      }}
      h1, h2, h3 {{ margin: 0 0 10px; line-height: 1.1; }}
      h1 {{ font-size: 2rem; }}
      h2 {{ font-size: 1.25rem; }}
      p, li {{ color: var(--text); line-height: 1.5; }}
      .muted {{ color: var(--muted); }}
      a {{ color: var(--accent); text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
      code {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        background: rgba(148, 163, 184, 0.12);
        padding: 2px 6px;
        border-radius: 6px;
      }}
      ul {{ margin: 0; padding-left: 18px; }}
      table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
      }}
      th, td {{
        text-align: left;
        padding: 10px 8px;
        border-bottom: 1px solid var(--line);
        vertical-align: top;
      }}
      th {{ color: var(--muted); font-weight: 600; }}
      .pill {{
        display: inline-block;
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 0.85rem;
        color: var(--muted);
      }}
    </style>
  </head>
  <body>
    <main>
      <section>
        <div class="band">
          <span class="pill">Standards Control Plane</span>
          <h1>Consult before coding. Audit before merge.</h1>
          <p class="muted">
            A shared advisory and compliance layer for agent-assisted delivery.
            It serves standards guidance, runs conformance audits, persists
            findings, and emits CI, Control Tower, and portfolio artifacts.
          </p>
        </div>
        <div class="grid">
          <div class="band">
            <h2>What it does</h2>
            <ul>
              <li>Retrieves standards, patterns, and open findings for implementation work.</li>
              <li>Audits repos or changed files and writes structured findings and reports.</li>
              <li>
                Publishes CI, estate, and Control Tower projections from the
                same audit model.
              </li>
            </ul>
          </div>
          <div class="band">
            <h2>How to use it</h2>
            <ul>
              <li>Run <code>consult</code> before implementation.</li>
              <li>Run <code>audit-changed</code> before opening or updating a PR.</li>
              <li>Use overlays for repo-specific standards instead of forking SCP core.</li>
            </ul>
          </div>
          <div class="band">
            <h2>Authentication</h2>
            <p>
              Current mode: <code>{html.escape(auth_mode)}</code>.
              Protected API endpoints are <code>/registry</code>,
              <code>/consult</code>, and <code>/audit</code> when bearer auth
              is configured.
            </p>
            <p class="muted">
              This is service-level API auth. Browser login or SSO is not part of
              the current built-in UI surface.
            </p>
          </div>
        </div>
      </section>
      <section>
        <div class="band">
          <h2>Adoption Guide</h2>
          <p>
            <a href="/docs/adoption">ADOPT-001 Project Onboarding</a> is the
            single repo-onboarding brief. It explains deployment model,
            governance changes, CI wiring, overlay structure, and the expected
            agent workflow for adopters.
          </p>
          <p class="muted">
            Teams should read that guide when integrating SCP into local
            governance docs, PR workflows, and scheduled audit jobs.
          </p>
        </div>
      </section>
      <section>
        <div class="band">
          <h2>Status App Integration</h2>
          <p>
            Integration health: <strong>{html.escape(integration_label)}</strong>.
            Machine-readable status is available at
            <a href="/status-app/health"><code>/status-app/health</code></a>.
          </p>
          <p class="muted">
            Standards version:
            <code>{html.escape(status_payload['service']['standards_version'])}</code>.
            Active domains: <code>{html.escape(domains)}</code>.
          </p>
          <table>
            <thead>
              <tr>
                <th>Artifact</th>
                <th>Present</th>
                <th>Freshness</th>
                <th>Path</th>
              </tr>
            </thead>
            <tbody>
              {artifact_rows}
            </tbody>
          </table>
        </div>
      </section>
      <section>
        <div class="band">
          <h2>Core Endpoints</h2>
          <ul>
            <li><a href="/health"><code>/health</code></a> — service liveness</li>
            <li>
              <a href="/status-app/health"><code>/status-app/health</code></a>
              — status integration health
            </li>
            <li><a href="/registry"><code>/registry</code></a> — standards registry snapshot</li>
            <li><code>POST /consult</code> — consult guidance</li>
            <li><code>POST /audit</code> — audit execution</li>
          </ul>
        </div>
      </section>
    </main>
  </body>
</html>
"""

    def _render_adoption_page(self) -> str:
        adoption_body = self._try_read_text("docs/adoption/ADOPT-001-project-onboarding.md")
        if adoption_body is None:
            adoption_text = html.escape(
                "ADOPT-001 Project Onboarding has not been written into this repo yet."
            )
        else:
            adoption_text = html.escape(adoption_body)
        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ADOPT-001 Project Onboarding</title>
    <style>
      body {{
        margin: 0;
        font-family: Inter, ui-sans-serif, system-ui, sans-serif;
        background: #0f172a;
        color: #e5e7eb;
      }}
      main {{
        width: min(1100px, calc(100% - 32px));
        margin: 0 auto;
        padding: 24px 0 40px;
      }}
      a {{ color: #38bdf8; text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
      pre {{
        white-space: pre-wrap;
        word-break: break-word;
        line-height: 1.5;
        background: #111827;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        overflow: auto;
      }}
      .band {{
        background: #111827;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
      }}
    </style>
  </head>
  <body>
    <main>
      <div class="band">
        <a href="/">Back to service home</a>
        <h1>ADOPT-001 Project Onboarding</h1>
        <p>
          This is the repo-onboarding brief for teams integrating Standards
          Control Plane into local governance, CI, and agent workflows.
        </p>
      </div>
      <pre>{adoption_text}</pre>
    </main>
  </body>
</html>
"""

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
        if parsed.path == "/":
            self._send_html(200, self._render_landing_page())
            return
        if parsed.path == "/docs/adoption":
            self._send_html(200, self._render_adoption_page())
            return
        if parsed.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if parsed.path == "/status-app/health":
            self._send_json(200, self._status_payload())
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
