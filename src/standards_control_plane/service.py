"""FastAPI service surface for the Standards Control Plane."""

from __future__ import annotations

import html
import json
import os
import re
import secrets
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode, urlparse

import httpx
from ct_auth.bff import create_bff_routes
from ct_auth.fastapi import ControlTowerAuth
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from jwt import InvalidTokenError

from .audit import build_audit_result
from .consult import build_consult_response
from .registry import RegistrySnapshot, load_registry
from .resources import project_root

_ESTATE_PROFILE = "estate-read-only/v1"
_ESTATE_AUDIENCE = "scp"
_ESTATE_SUBJECT = "sa:acc-estate-context"
_ESTATE_AUTHORIZED_PARTY = "acc"
_ESTATE_ACTOR_TYPE = "service"
_ESTATE_SCOPES = ["estate:standards:read"]
_ESTATE_BINDING_HEADERS = {
    "active_org_id": "X-Estate-Org-ID",
    "workspace_id": "X-Estate-Workspace-ID",
    "project_id": "X-Estate-Project-ID",
    "repository_id": "X-Estate-Repository-ID",
}
_ESTATE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")


def _strip_trailing_slash(value: str) -> str:
    return value.rstrip("/")


def _package_version() -> str:
    try:
        return _pkg_version("standards-control-plane")
    except PackageNotFoundError:
        return "0.0.0+unknown"


def _release_version() -> str:
    """Release version from version-manifest.json (or build-time env override).

    Build-time `SCP_RELEASE_VERSION` env var (set in Dockerfile via ARG +
    deploy workflow build-arg) takes precedence. Falls back to reading
    version-manifest.json in the package root. Falls back to "unknown" if
    neither resolves.
    """
    env = os.getenv("SCP_RELEASE_VERSION", "").strip()
    if env:
        return env
    # Walk up from this file to find version-manifest.json at repo root.
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "version-manifest.json"
        if candidate.is_file():
            try:
                import json as _json
                with candidate.open("r", encoding="utf-8") as handle:
                    data = _json.load(handle)
                value = data.get("version", "")
                if isinstance(value, str) and value:
                    return value
            except (OSError, ValueError):
                pass
            break
    return "unknown"


def _git_sha() -> str:
    """Git commit SHA of the running build.

    Build-time `SCP_GIT_SHA` env var (set in Dockerfile via ARG + deploy
    workflow build-arg) is authoritative. Falls back to "unknown" — we
    don't shell out to `git rev-parse` at request time because the
    container's /app directory may not have .git available (and we don't
    want to make /health do disk I/O on every request anyway).
    """
    return os.getenv("SCP_GIT_SHA", "").strip() or "unknown"


def _coerce_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return default


def _coerce_feature_flag(value: str | None) -> bool:
    if value is None:
        return False
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    raise ValueError(
        "SCP_ESTATE_READ_ONLY_ENABLED must be an explicit true/false value."
    )


def _iso_utc(timestamp: float) -> str:
    return (
        datetime.fromtimestamp(timestamp, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sanitize_next(target: str | None) -> str:
    if not target:
        return "/"
    if not target.startswith("/"):
        return "/"
    if target.startswith("//"):
        return "/"
    return target


@dataclass(frozen=True)
class ServiceConfig:
    overlay_paths: tuple[str, ...]
    legacy_auth_token: str | None
    auth_enabled: bool
    ct_base_url: str
    ct_jwks_url: str
    ct_app_id: str
    public_base_url: str | None
    env: str
    estate_read_only_enabled: bool
    ct_issuer: str | None
    access_cookie_name: str = "access_token"
    refresh_cookie_name: str = "refresh_token"
    refresh_cookie_path: str = "/api/auth"
    oauth_state_cookie_name: str = "scp_oauth_state"
    post_login_cookie_name: str = "scp_login_next"

    @classmethod
    def from_env(
        cls,
        *,
        overlay_paths: list[str] | None = None,
        legacy_auth_token: str | None = None,
        env: Mapping[str, str] | None = None,
    ) -> ServiceConfig:
        source = env if env is not None else os.environ
        auth_enabled = _coerce_bool(source.get("AUTH_ENABLED"), default=False)
        estate_read_only_enabled = _coerce_feature_flag(
            source.get("SCP_ESTATE_READ_ONLY_ENABLED")
        )
        ct_base_url = _strip_trailing_slash(
            source.get("CT_BASE_URL", "https://control-tower.brokapps.ai")
        )
        public_base_url_value = _strip_trailing_slash(source.get("PUBLIC_BASE_URL", ""))
        public_base_url = public_base_url_value or None
        config = cls(
            overlay_paths=tuple(overlay_paths or []),
            legacy_auth_token=legacy_auth_token,
            auth_enabled=auth_enabled,
            ct_base_url=ct_base_url,
            ct_jwks_url=source.get(
                "CT_JWKS_URL",
                f"{ct_base_url}/api/v1/.well-known/jwks.json",
            ),
            ct_app_id=source.get("CT_APP_ID", source.get("APP_ID", "scp")),
            public_base_url=public_base_url,
            env=source.get("ENV", source.get("NODE_ENV", "development")).lower(),
            estate_read_only_enabled=estate_read_only_enabled,
            ct_issuer=source.get("CT_ISSUER", "").strip() or None,
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.estate_read_only_enabled:
            if not self.auth_enabled:
                raise ValueError(
                    "SCP Estate read-only profile requires AUTH_ENABLED=true."
                )
            if self.legacy_auth_token is not None:
                raise ValueError(
                    "SCP Estate read-only profile forbids the legacy bearer token."
                )
            if self.ct_app_id != _ESTATE_AUDIENCE:
                raise ValueError("SCP Estate read-only profile requires CT_APP_ID=scp.")
            if not self.ct_issuer:
                raise ValueError(
                    "SCP Estate read-only profile requires an environment-pinned CT_ISSUER."
                )

        if not self.auth_enabled:
            return

        if self.env != "development" and not self.public_base_url:
            raise ValueError(
                "PUBLIC_BASE_URL is required when AUTH_ENABLED=true outside development."
            )

        expected_hosts = {
            "scp": "scp.brokapps.ai",
            "scp-dev": "scp-dev.brokapps.ai",
        }
        expected_host = expected_hosts.get(self.ct_app_id)
        if expected_host and self.public_base_url:
            actual_host = urlparse(self.public_base_url).hostname
            if self.env != "development" and actual_host != expected_host:
                raise ValueError(
                    f"CT_APP_ID={self.ct_app_id} requires PUBLIC_BASE_URL host "
                    f"{expected_host!r}, got {actual_host!r}."
                )

    def public_origin(self, request: Request) -> str:
        if self.public_base_url:
            return self.public_base_url
        return f"{request.url.scheme}://{request.url.netloc}"

    def secure_cookies(self, request: Request) -> bool:
        origin = self.public_origin(request)
        return origin.startswith("https://")

    def auth_mode(self) -> str:
        if self.auth_enabled and self.legacy_auth_token:
            return "oidc+bearer"
        if self.auth_enabled:
            return "oidc"
        if self.legacy_auth_token:
            return "bearer"
        return "none"

    def protected_endpoints(self) -> list[str]:
        protected = ["/registry", "/consult", "/audit"]
        if self.auth_enabled:
            return ["/", "/docs/adoption", *protected]
        return protected


@dataclass
class ServiceState:
    config: ServiceConfig
    registry_snapshot: RegistrySnapshot
    ct_http_client: httpx.AsyncClient | None
    ct_auth: ControlTowerAuth | None
    ct_bff: Any | None
    owns_client: bool

    def artifact_health(self, relative_path: str) -> dict[str, Any]:
        path = project_root() / relative_path
        payload: dict[str, Any] = {
            "path": relative_path,
            "exists": path.exists(),
        }
        if not path.exists():
            return payload
        payload["updated_at"] = _iso_utc(path.stat().st_mtime)
        if path.suffix == ".json":
            try:
                parsed = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return payload
            if isinstance(parsed, dict) and isinstance(parsed.get("generated_at"), str):
                payload["generated_at"] = parsed["generated_at"]
        return payload

    def status_payload(self) -> dict[str, Any]:
        artifacts = {
            "latest_review": self.artifact_health("output/reports/latest-review.md"),
            "ci_output": self.artifact_health("output/ci/latest-ci.json"),
            "control_tower_dashboard": self.artifact_health(
                "output/control-tower/estate-dashboard.json"
            ),
            "portfolio_dashboard": self.artifact_health(
                "output/estate/multi-repo-dashboard.json"
            ),
        }
        missing_artifacts = [
            name for name, details in artifacts.items() if not bool(details["exists"])
        ]
        return {
            "status": "degraded" if missing_artifacts else "ok",
            "service": {
                "name": self.registry_snapshot.name,
                "standards_version": self.registry_snapshot.version,
                "domains": sorted(self.registry_snapshot.domains.keys()),
            },
            "auth": {
                "enabled": self.config.auth_enabled,
                "mode": self.config.auth_mode(),
                "browser_sso": self.config.auth_enabled,
                "legacy_bearer_enabled": self.config.legacy_auth_token is not None,
                "ct_base_url": self.config.ct_base_url if self.config.auth_enabled else None,
                "app_id": self.config.ct_app_id if self.config.auth_enabled else None,
                "protected_endpoints": self.config.protected_endpoints(),
                "estate_read_only_enabled": self.config.estate_read_only_enabled,
                "issuer": self.config.ct_issuer,
            },
            "status_app_integration": {
                "healthy": not missing_artifacts,
                "missing_artifacts": missing_artifacts,
            },
            "artifacts": artifacts,
            "docs": {
                "adoption": "/docs/adoption",
                "readme": (
                    "https://github.com/jrnb2024/standards-control-plane-/blob/main/README.md"
                ),
            },
        }

    def health_payload(self) -> dict[str, object]:
        """SVC-002 health payload with canonical estate string-valued checks.

        SCP is a stateless FastAPI policy/standards engine — ``services.yml``
        declares ``required_infra: []``: no database, cache, queue, or other
        external runtime store. Its only runtime state is the standards/rules
        registry loaded in-memory at startup, plus the CI-produced dashboard/
        report artifacts read from disk. The ``checks`` map therefore reflects
        exactly those real self-checks (no fabricated external dependency),
        each value a canonical estate status string ("ok" | "degraded" |
        "error"). ``status`` is "healthy" iff every check is "ok", else
        "degraded". Auth is intentionally excluded from the checks: it is
        configuration, not a liveness dependency, and /health is
        unauthenticated (SVC-002). Build provenance (release_version, git_sha)
        and registry metadata (standards_version, rules_loaded) are surfaced
        alongside so operators can verify which build/rule-set is serving.
        """
        status_payload = self.status_payload()
        integration = status_payload["status_app_integration"]
        assert isinstance(integration, dict)
        missing_artifacts = integration["missing_artifacts"]
        assert isinstance(missing_artifacts, list)

        registry_loaded = bool(self.registry_snapshot.domains) and bool(
            self.registry_snapshot.version
        )
        checks: dict[str, str] = {
            "rules_registry": "ok" if registry_loaded else "error",
            "required_artifacts": "degraded" if missing_artifacts else "ok",
        }
        status = "healthy" if all(value == "ok" for value in checks.values()) else "degraded"
        return {
            "status": status,
            "version": _package_version(),
            "release_version": _release_version(),
            "git_sha": _git_sha(),
            "standards_version": self.registry_snapshot.version,
            "rules_loaded": sum(
                len(domain.rules) for domain in self.registry_snapshot.domains.values()
            ),
            "checks": checks,
        }


@dataclass(frozen=True)
class EstateRequestBinding:
    active_org_id: str
    workspace_id: str
    project_id: str
    repository_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "active_org_id": self.active_org_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "repository_id": self.repository_id,
        }


@dataclass(frozen=True)
class EstateAuthorization:
    claims: dict[str, Any]
    binding: EstateRequestBinding


def _read_text(relative_path: str) -> str:
    target = project_root() / relative_path
    return target.read_text(encoding="utf-8")


async def _get_claims(request: Request) -> dict[str, Any] | None:
    state: ServiceState = request.app.state.service_state
    if not state.config.auth_enabled or state.ct_auth is None:
        return None
    try:
        return await state.ct_auth(request)
    except HTTPException:
        return None


async def _authorize_api_request(
    request: Request,
) -> dict[str, Any] | EstateAuthorization | None:
    state: ServiceState = request.app.state.service_state
    if state.config.estate_read_only_enabled:
        return await _authorize_estate_api_request(request)
    auth_header = request.headers.get("Authorization", "")
    if state.config.legacy_auth_token is not None:
        if secrets.compare_digest(auth_header, f"Bearer {state.config.legacy_auth_token}"):
            return {"auth_type": "legacy_bearer"}
    claims = await _get_claims(request)
    if claims is not None:
        return claims
    if state.config.auth_enabled or state.config.legacy_auth_token is not None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return None


def _estate_claims_match(claims: Mapping[str, Any], *, issuer: str) -> bool:
    audience = claims.get("aud")
    exact_audience = audience == _ESTATE_AUDIENCE or audience == [_ESTATE_AUDIENCE]
    scopes = claims.get("scopes")
    return bool(
        claims.get("iss") == issuer
        and exact_audience
        and claims.get("sub") == _ESTATE_SUBJECT
        and claims.get("azp") == _ESTATE_AUTHORIZED_PARTY
        and claims.get("actor_type") == _ESTATE_ACTOR_TYPE
        and scopes == _ESTATE_SCOPES
        and isinstance(claims.get("active_org_id"), str)
        and _ESTATE_IDENTIFIER_PATTERN.fullmatch(str(claims["active_org_id"]))
    )


def _estate_request_binding(request: Request) -> EstateRequestBinding:
    values: dict[str, str] = {}
    for field_name, header_name in _ESTATE_BINDING_HEADERS.items():
        value = request.headers.get(header_name, "").strip()
        if not _ESTATE_IDENTIFIER_PATTERN.fullmatch(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_estate_binding",
                    "message": f"{header_name} is required and must be a bounded identifier",
                },
            )
        values[field_name] = value
    return EstateRequestBinding(**values)


async def _authorize_estate_api_request(request: Request) -> EstateAuthorization:
    state: ServiceState = request.app.state.service_state
    claims = await _get_claims(request)
    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "message": "Valid CT service token required"},
        )
    assert state.config.ct_issuer is not None
    if not _estate_claims_match(claims, issuer=state.config.ct_issuer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Estate principal contract mismatch"},
        )
    binding = _estate_request_binding(request)
    if binding.active_org_id != claims["active_org_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Estate organisation binding mismatch"},
        )
    return EstateAuthorization(claims=claims, binding=binding)


def _estate_response(
    state: ServiceState,
    authorization: dict[str, Any] | EstateAuthorization | None,
    result: Any,
) -> Any:
    if not state.config.estate_read_only_enabled:
        return result
    if not isinstance(authorization, EstateAuthorization):
        raise RuntimeError("Estate response requires verified Estate authorization")
    return {
        "profile": _ESTATE_PROFILE,
        "request_binding": authorization.binding.to_dict(),
        "authority": {
            "mode": "read_only",
            "action_authority": False,
        },
        "result": result,
    }


def _render_home_content() -> tuple[str, str]:
    """Render docs/home/HOME.md to (toc_html, sectioned_body_html).

    Reads the canonical home markdown, renders to HTML using the markdown
    package, then post-processes to wrap each ``<h2>``-rooted section in
    a ``<details>`` block so the page rolls up rather than dumping the
    whole document at once. Returns the rendered TOC HTML separately so
    the layout can place it in a sticky sidebar.
    """
    try:
        source = _read_text("docs/home/HOME.md")
    except FileNotFoundError:
        return ("", "<p>Home content unavailable.</p>")

    try:
        import markdown as _md
    except ImportError:
        # Graceful fallback: dump the markdown as escaped text so the
        # service still renders something meaningful when the markdown
        # package is not installed (e.g. minimal-deps installs).
        escaped = html.escape(source)
        return ("", f"<pre>{escaped}</pre>")

    md_proc = _md.Markdown(
        extensions=["toc", "tables", "fenced_code", "attr_list"],
        extension_configs={
            "toc": {
                # Default baselevel=1 keeps the markdown's own heading
                # levels: H1 = page title, H2 = collapsible section,
                # H3 = sub-section. Setting baselevel>1 demotes every
                # heading and breaks the post-processor below.
                "permalink": True,
                "permalink_title": "Link to this section",
                # Only include H2 + H3 in the TOC sidebar (skip H1 title
                # which is the page itself; skip H4 sub-headings as
                # noise in nav).
                "toc_depth": "2-3",
            },
        },
    )
    body_html = md_proc.convert(source)
    toc_html = md_proc.toc

    # Split on <h2> opening tags so each section becomes its own
    # collapsible <details> block. parts[0] is the page lead (before any
    # H2); parts[odd] are H2 tags; parts[even>0] are section bodies.
    parts = re.split(r'(<h2[^>]*>.*?</h2>)', body_html, flags=re.DOTALL)
    if len(parts) < 3:
        return (toc_html, body_html)

    rebuilt: list[str] = [parts[0]]
    for i in range(1, len(parts), 2):
        h2_tag = parts[i]
        section_body = parts[i + 1] if i + 1 < len(parts) else ""
        heading_match = re.search(
            r'<h2(?:\s+id="([^"]+)")?[^>]*>(.*?)</h2>',
            h2_tag,
            re.DOTALL,
        )
        anchor_id = heading_match.group(1) if heading_match and heading_match.group(1) else ""
        heading_inner = heading_match.group(2) if heading_match else "Section"
        is_first = i == 1
        details_attrs = " open" if is_first else ""
        details_id = f' id="{anchor_id}"' if anchor_id else ""
        rebuilt.append(f'<details class="section"{details_attrs}{details_id}>')
        rebuilt.append(
            f'<summary class="section-summary"><span class="section-h2">{heading_inner}</span></summary>'
        )
        rebuilt.append(f'<div class="section-body">{section_body}</div>')
        rebuilt.append("</details>")
    return (toc_html, "".join(rebuilt))


def _render_landing_page(
    state: ServiceState,
    *,
    claims: dict[str, Any] | None,
) -> str:
    status_payload = state.status_payload()
    integration = status_payload["status_app_integration"]
    integration_label = "Healthy" if integration["healthy"] else "Degraded"
    integration_class = "ok" if integration["healthy"] else "degraded"
    standards_version = html.escape(status_payload["service"]["standards_version"])
    auth_mode = html.escape(state.config.auth_mode())
    app_id = html.escape(state.config.ct_app_id)

    if claims is not None:
        email = html.escape(str(claims.get("email", claims.get("sub", "unknown"))))
        auth_top = (
            f'<span class="pill pill-ok" title="Auth mode: {auth_mode} | App: {app_id}">'
            f"Signed in: {email}</span>"
            '<a class="top-link" href="/auth/logout">Sign out</a>'
        )
    elif state.config.auth_enabled:
        auth_top = (
            f'<span class="pill" title="Auth mode: {auth_mode} | App: {app_id}">'
            f"Auth: {auth_mode}</span>"
            '<a class="top-link" href="/auth/login">Sign in</a>'
        )
    else:
        auth_top = (
            f'<span class="pill" title="App: {app_id}">Auth: {auth_mode}</span>'
        )

    toc_html, body_html = _render_home_content()

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Standards Control Plane</title>
    <style>
      :root {{
        color-scheme: dark;
        --bg: #0b1120;
        --bg-2: #0f172a;
        --panel: #111827;
        --panel-2: #1e293b;
        --text: #e5e7eb;
        --muted: #94a3b8;
        --accent: #38bdf8;
        --accent-dim: rgba(56, 189, 248, 0.18);
        --line: #1f2937;
        --line-strong: #334155;
        --ok: #34d399;
        --warn: #fbbf24;
        --err: #f87171;
      }}
      * {{ box-sizing: border-box; }}
      html, body {{ margin: 0; padding: 0; }}
      body {{
        font-family: Inter, ui-sans-serif, system-ui, -apple-system,
          BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: var(--bg);
        color: var(--text);
        line-height: 1.55;
      }}
      a {{ color: var(--accent); text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
      code {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.88em;
        background: rgba(148, 163, 184, 0.14);
        padding: 1px 6px;
        border-radius: 4px;
      }}
      pre {{
        background: #020617;
        border: 1px solid var(--line-strong);
        border-radius: 6px;
        padding: 14px 16px;
        overflow-x: auto;
        font-size: 0.85rem;
        line-height: 1.5;
      }}
      pre code {{
        background: transparent;
        padding: 0;
        font-size: inherit;
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.92rem;
        margin: 12px 0 18px;
      }}
      th, td {{
        text-align: left;
        padding: 9px 12px;
        border-bottom: 1px solid var(--line-strong);
        vertical-align: top;
      }}
      th {{
        color: var(--muted);
        font-weight: 600;
        background: rgba(148, 163, 184, 0.04);
      }}
      tr:last-child td {{ border-bottom: 0; }}
      blockquote {{
        margin: 12px 0;
        padding: 8px 16px;
        border-left: 3px solid var(--accent);
        background: var(--accent-dim);
        color: var(--text);
      }}

      /* Top bar */
      .top-bar {{
        position: sticky;
        top: 0;
        z-index: 10;
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 12px 24px;
        background: rgba(11, 17, 32, 0.92);
        border-bottom: 1px solid var(--line);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
      }}
      .brand {{
        font-weight: 600;
        letter-spacing: 0.01em;
        color: var(--text);
      }}
      .brand-sub {{
        color: var(--muted);
        font-size: 0.85rem;
        margin-left: 6px;
      }}
      .top-spacer {{ flex: 1; }}
      .pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        border: 1px solid var(--line-strong);
        border-radius: 999px;
        padding: 4px 12px;
        font-size: 0.8rem;
        color: var(--muted);
        background: rgba(15, 23, 42, 0.5);
      }}
      .pill-ok {{ color: var(--ok); border-color: rgba(52, 211, 153, 0.4); }}
      .pill-warn {{ color: var(--warn); border-color: rgba(251, 191, 36, 0.4); }}
      .pill-err {{ color: var(--err); border-color: rgba(248, 113, 113, 0.4); }}
      .pill::before {{
        content: "●";
        font-size: 0.65em;
        color: var(--muted);
      }}
      .pill-ok::before {{ color: var(--ok); }}
      .pill-warn::before {{ color: var(--warn); }}
      .pill-err::before {{ color: var(--err); }}
      .top-link {{
        font-size: 0.85rem;
        color: var(--accent);
      }}

      /* Two-column layout */
      .layout {{
        display: grid;
        grid-template-columns: 280px minmax(0, 1fr);
        gap: 0;
        min-height: calc(100vh - 56px);
      }}
      .sidebar {{
        position: sticky;
        top: 56px;
        height: calc(100vh - 56px);
        overflow-y: auto;
        padding: 24px 16px 32px;
        border-right: 1px solid var(--line);
        background: var(--bg-2);
      }}
      .sidebar-title {{
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.72rem;
        color: var(--muted);
        margin: 4px 12px 12px;
      }}
      .sidebar nav.toc > ul,
      .sidebar nav.toc ul {{
        list-style: none;
        margin: 0;
        padding: 0;
      }}
      .sidebar nav.toc li {{
        margin: 0;
      }}
      .sidebar nav.toc li > a {{
        display: block;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.86rem;
        color: var(--muted);
        line-height: 1.35;
      }}
      .sidebar nav.toc li > a:hover {{
        color: var(--text);
        background: rgba(56, 189, 248, 0.08);
        text-decoration: none;
      }}
      .sidebar nav.toc ul ul li > a {{
        padding-left: 28px;
        font-size: 0.82rem;
        color: var(--muted);
      }}
      .sidebar nav.toc ul ul ul li > a {{
        padding-left: 44px;
        font-size: 0.78rem;
      }}
      .sidebar-quick {{
        margin-top: 20px;
        padding: 12px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: rgba(15, 23, 42, 0.5);
      }}
      .sidebar-quick h4 {{
        margin: 0 0 8px;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted);
      }}
      .sidebar-quick ul {{
        list-style: none;
        margin: 0;
        padding: 0;
      }}
      .sidebar-quick li {{
        font-size: 0.82rem;
        line-height: 1.6;
      }}
      .sidebar-quick li code {{ font-size: 0.78rem; }}

      /* Main content */
      .content {{
        padding: 28px 40px 56px;
        max-width: 920px;
      }}
      .content h1 {{
        font-size: 2rem;
        margin: 0 0 8px;
        line-height: 1.15;
        letter-spacing: -0.01em;
      }}
      .content > p:first-of-type {{
        font-size: 1.05rem;
        color: var(--text);
        margin: 0 0 20px;
      }}
      .content h2 {{
        font-size: 1.35rem;
        margin: 0;
        line-height: 1.25;
        letter-spacing: -0.005em;
      }}
      .content h3 {{
        font-size: 1.08rem;
        margin: 22px 0 8px;
        color: var(--text);
      }}
      .content h4 {{ font-size: 0.95rem; margin: 18px 0 6px; color: var(--muted); }}
      .content p {{ margin: 0 0 12px; }}
      .content ul, .content ol {{ margin: 0 0 14px; padding-left: 22px; }}
      .content li {{ margin: 4px 0; }}
      .content hr {{
        border: 0;
        height: 1px;
        background: var(--line);
        margin: 28px 0;
      }}

      /* Collapsible sections */
      details.section {{
        border: 1px solid var(--line);
        border-radius: 10px;
        background: rgba(15, 23, 42, 0.5);
        margin: 14px 0;
        overflow: hidden;
      }}
      details.section[open] {{
        background: var(--panel);
      }}
      details.section > summary.section-summary {{
        list-style: none;
        cursor: pointer;
        padding: 14px 20px;
        user-select: none;
        display: flex;
        align-items: center;
        gap: 12px;
        background: var(--panel);
        border-bottom: 1px solid transparent;
        transition: background 0.15s;
      }}
      details.section[open] > summary.section-summary {{
        border-bottom-color: var(--line);
      }}
      details.section > summary.section-summary:hover {{
        background: var(--panel-2);
      }}
      details.section > summary.section-summary::-webkit-details-marker {{ display: none; }}
      details.section > summary.section-summary::before {{
        content: "▸";
        color: var(--accent);
        font-size: 0.9rem;
        transition: transform 0.15s;
        display: inline-block;
        width: 1em;
      }}
      details.section[open] > summary.section-summary::before {{
        content: "▾";
      }}
      .section-h2 {{
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text);
      }}
      .section-body {{
        padding: 18px 22px 22px;
      }}
      .section-body > :first-child {{ margin-top: 0; }}
      .section-body > :last-child {{ margin-bottom: 0; }}

      /* Permalink anchors emitted by toc extension */
      .headerlink {{
        margin-left: 8px;
        opacity: 0;
        font-size: 0.85em;
        color: var(--accent);
        transition: opacity 0.15s;
      }}
      h1:hover .headerlink,
      h2:hover .headerlink,
      h3:hover .headerlink,
      h4:hover .headerlink,
      .section-h2:hover .headerlink {{
        opacity: 1;
      }}

      /* Responsive: collapse sidebar on narrow viewports */
      @media (max-width: 960px) {{
        .layout {{ grid-template-columns: 1fr; }}
        .sidebar {{
          position: static;
          height: auto;
          border-right: 0;
          border-bottom: 1px solid var(--line);
          padding: 18px 20px;
        }}
        .content {{ padding: 24px 20px 48px; }}
      }}
    </style>
  </head>
  <body>
    <header class="top-bar">
      <span class="brand">Standards Control Plane <span class="brand-sub">v{standards_version}</span></span>
      <span class="top-spacer"></span>
      <span class="pill pill-{integration_class}">{integration_label}</span>
      {auth_top}
    </header>
    <div class="layout">
      <aside class="sidebar">
        <div class="sidebar-title">Contents</div>
        {toc_html}
        <div class="sidebar-quick">
          <h4>Quick links</h4>
          <ul>
            <li><a href="/docs/adoption">ADOPT-001 Project Onboarding</a></li>
            <li><a href="/health"><code>/health</code></a></li>
            <li><a href="/status-app/health"><code>/status-app/health</code></a></li>
            <li><a href="/registry"><code>/registry</code></a></li>
            <li><a href="/auth/me"><code>/auth/me</code></a></li>
          </ul>
        </div>
      </aside>
      <main class="content">
        {body_html}
      </main>
    </div>
  </body>
</html>
"""


def _render_adoption_page() -> str:
    try:
        adoption_body = _read_text("docs/adoption/ADOPT-001-project-onboarding.md")
    except FileNotFoundError:
        adoption_body = "ADOPT-001 Project Onboarding has not been written into this repo yet."
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


async def _ct_token_exchange(
    request: Request,
    *,
    code: str,
    redirect_uri: str,
) -> dict[str, Any]:
    state: ServiceState = request.app.state.service_state
    if state.ct_http_client is None:
        raise RuntimeError("CT HTTP client is unavailable")
    response = await state.ct_http_client.post(
        f"{state.config.ct_base_url}/api/v1/auth/token",
        json={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": state.config.ct_app_id,
            "redirect_uri": redirect_uri,
        },
        headers={"Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest"},
    )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="OAuth token exchange failed")
    payload = response.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=502, detail="OAuth token exchange failed")
    return payload


def _set_auth_cookies(
    response: RedirectResponse | JSONResponse,
    request: Request,
    config: ServiceConfig,
    *,
    access_token: str,
    refresh_token: str | None,
) -> None:
    secure = config.secure_cookies(request)
    response.set_cookie(
        key=config.access_cookie_name,
        value=access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
        max_age=3600,
    )
    if refresh_token:
        response.set_cookie(
            key=config.refresh_cookie_name,
            value=refresh_token,
            httponly=True,
            secure=secure,
            samesite="lax",
            path=config.refresh_cookie_path,
            max_age=604800,
        )


def _clear_auth_cookies(
    response: RedirectResponse | JSONResponse,
    config: ServiceConfig,
) -> None:
    response.delete_cookie(key=config.access_cookie_name, path="/")
    response.delete_cookie(key=config.refresh_cookie_name, path=config.refresh_cookie_path)
    response.delete_cookie(key=config.refresh_cookie_name, path="/auth")
    response.delete_cookie(key=config.oauth_state_cookie_name, path="/auth")
    response.delete_cookie(key=config.post_login_cookie_name, path="/auth")


async def _require_html_session(request: Request) -> dict[str, Any] | None:
    state: ServiceState = request.app.state.service_state
    claims = await _get_claims(request)
    if state.config.auth_enabled and claims is None:
        return None
    return claims


def create_app(
    *,
    overlay_paths: list[str] | None = None,
    auth_token: str | None = None,
    env: Mapping[str, str] | None = None,
    ct_http_client: httpx.AsyncClient | None = None,
) -> FastAPI:
    config = ServiceConfig.from_env(
        overlay_paths=overlay_paths,
        legacy_auth_token=auth_token,
        env=env,
    )
    if env is not None and "ENV" in env:
        # Keep the shared CT SDK on the same environment contract as this app
        # when tests or embedded callers inject an env mapping instead of
        # relying on the process environment.
        os.environ["ENV"] = config.env
    registry_snapshot = load_registry(
        overlay_paths=[Path(path_value) for path_value in config.overlay_paths]
    )
    owns_client = ct_http_client is None
    shared_ct_http_client = (
        ct_http_client if ct_http_client is not None else httpx.AsyncClient(timeout=10.0)
    )
    ct_bff = (
        create_bff_routes(
            config.ct_base_url,
            cookie_name=config.access_cookie_name,
            refresh_cookie_name=config.refresh_cookie_name,
            cookie_path="/",
            refresh_cookie_path=config.refresh_cookie_path,
            secure_cookies=(config.env != "development"),
            oauth_client_id=config.ct_app_id,
            http_client=shared_ct_http_client,
            include_me=True,
            jwks_url=config.ct_jwks_url,
        )
        if config.auth_enabled
        else None
    )
    service_state = ServiceState(
        config=config,
        registry_snapshot=registry_snapshot,
        ct_http_client=shared_ct_http_client,
        ct_auth=ControlTowerAuth(
            jwks_url=config.ct_jwks_url,
            audience=config.ct_app_id,
        )
        if config.auth_enabled
        else None,
        ct_bff=ct_bff,
        owns_client=owns_client,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.service_state = service_state
        try:
            yield
        finally:
            state: ServiceState = app.state.service_state
            if state.ct_bff is not None:
                await state.ct_bff.close()
            if state.owns_client and state.ct_http_client is not None:
                await state.ct_http_client.aclose()

    app = FastAPI(title="Standards Control Plane", lifespan=lifespan)
    if service_state.ct_bff is not None:
        app.include_router(service_state.ct_bff.router, prefix="/api/auth")

    @app.get("/", response_class=HTMLResponse, response_model=None)
    async def home(request: Request):
        claims = await _require_html_session(request)
        if request.app.state.service_state.config.auth_enabled and claims is None:
            return RedirectResponse(
                url=f"/auth/login?{urlencode({'next': request.url.path})}",
                status_code=302,
            )
        return HTMLResponse(_render_landing_page(request.app.state.service_state, claims=claims))

    @app.get("/docs/adoption", response_class=HTMLResponse, response_model=None)
    async def adoption(request: Request):
        claims = await _require_html_session(request)
        if request.app.state.service_state.config.auth_enabled and claims is None:
            return RedirectResponse(
                url=f"/auth/login?{urlencode({'next': request.url.path})}",
                status_code=302,
            )
        return HTMLResponse(_render_adoption_page())

    @app.get("/health")
    async def health(request: Request) -> dict[str, object]:
        # SVC-002 shape: status must be healthy|degraded|error, plus version,
        # plus a checks map. The static evaluator checks path presence only,
        # so SCP's genuine compliance here is proven by dogfood review and
        # by this handler shape — not by the auto-check alone.
        #
        # release_version + git_sha let operators verify which build is
        # actually serving traffic (vs the static "version": "0.1.0" from
        # pyproject which never moves). Sourced from SCP_RELEASE_VERSION +
        # SCP_GIT_SHA env vars injected at container build time (Dockerfile
        # ARG → ENV). Falls back to version-manifest.json + "unknown".
        state: ServiceState = request.app.state.service_state
        return state.health_payload()

    @app.get("/status-app/health")
    async def status_app_health(request: Request) -> JSONResponse:
        return JSONResponse(request.app.state.service_state.status_payload())

    @app.get("/auth/login")
    async def auth_login(request: Request, next: str = "/") -> RedirectResponse:
        state: ServiceState = request.app.state.service_state
        if not state.config.auth_enabled:
            return RedirectResponse(url=_sanitize_next(next), status_code=302)
        oauth_state = secrets.token_urlsafe(24)
        redirect_target = _sanitize_next(next)
        callback_base = state.config.public_origin(request)
        params = urlencode(
            {
                "response_type": "code",
                "client_id": state.config.ct_app_id,
                "redirect_uri": f"{callback_base}/auth/callback",
                "state": oauth_state,
                "scope": "openid profile",
            }
        )
        response = RedirectResponse(
            url=f"{state.config.ct_base_url}/api/v1/auth/authorize?{params}",
            status_code=302,
        )
        secure = state.config.secure_cookies(request)
        response.set_cookie(
            key=state.config.oauth_state_cookie_name,
            value=oauth_state,
            httponly=True,
            secure=secure,
            samesite="lax",
            path="/auth",
            max_age=300,
        )
        response.set_cookie(
            key=state.config.post_login_cookie_name,
            value=redirect_target,
            httponly=True,
            secure=secure,
            samesite="lax",
            path="/auth",
            max_age=300,
        )
        return response

    @app.get("/auth/callback")
    async def auth_callback(
        request: Request,
        code: str | None = None,
        state: str | None = None,
    ) -> RedirectResponse:
        service_state = request.app.state.service_state
        if not service_state.config.auth_enabled:
            return RedirectResponse(url="/", status_code=302)
        saved_state = request.cookies.get(service_state.config.oauth_state_cookie_name)
        next_target = _sanitize_next(
            request.cookies.get(service_state.config.post_login_cookie_name, "/")
        )
        if not code or not state or not saved_state or state != saved_state:
            raise HTTPException(status_code=400, detail="Invalid OAuth callback")
        callback_base = service_state.config.public_origin(request)
        token_payload = await _ct_token_exchange(
            request,
            code=code,
            redirect_uri=f"{callback_base}/auth/callback",
        )
        access_token = str(token_payload.get("access_token", "")).strip()
        refresh_token = str(token_payload.get("refresh_token", "")).strip()
        if not access_token:
            raise HTTPException(status_code=502, detail="OAuth token exchange failed")
        response = RedirectResponse(url=next_target, status_code=302)
        _set_auth_cookies(
            response,
            request,
            service_state.config,
            access_token=access_token,
            refresh_token=refresh_token or None,
        )
        response.delete_cookie(service_state.config.oauth_state_cookie_name, path="/auth")
        response.delete_cookie(service_state.config.post_login_cookie_name, path="/auth")
        return response

    @app.get("/auth/me")
    async def auth_me(request: Request) -> JSONResponse:
        claims = await _get_claims(request)
        if claims is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return JSONResponse(claims)

    @app.get("/auth/logout")
    async def auth_logout(request: Request) -> RedirectResponse:
        response = RedirectResponse(url="/", status_code=302)
        _clear_auth_cookies(response, request.app.state.service_state.config)
        return response

    @app.get("/registry")
    async def registry(request: Request) -> JSONResponse:
        authorization = await _authorize_api_request(request)
        state = request.app.state.service_state
        return JSONResponse(
            _estate_response(state, authorization, state.registry_snapshot.to_dict())
        )

    @app.post("/consult")
    async def consult(request: Request) -> JSONResponse:
        authorization = await _authorize_api_request(request)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="request body must be a JSON object")
        state = request.app.state.service_state
        result = build_consult_response(
            payload,
            registry_snapshot=state.registry_snapshot,
        )
        return JSONResponse(_estate_response(state, authorization, result))

    @app.post("/audit")
    async def audit(request: Request) -> JSONResponse:
        authorization = await _authorize_api_request(request)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="request body must be a JSON object")
        state = request.app.state.service_state
        result = build_audit_result(
            payload,
            registry_snapshot=state.registry_snapshot,
        )
        return JSONResponse(_estate_response(state, authorization, result))

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(
        request: Request,
        error: HTTPException,
    ) -> JSONResponse | HTMLResponse:
        if request.url.path in {"/", "/docs/adoption"} and error.status_code == 401:
            return RedirectResponse(
                url=f"/auth/login?{urlencode({'next': request.url.path})}",
                status_code=302,
            )
        detail = error.detail
        if isinstance(detail, dict):
            payload = detail
        else:
            payload = {"error": str(detail)}
        return JSONResponse(payload, status_code=error.status_code)

    @app.exception_handler(InvalidTokenError)
    async def _token_error_handler(
        request: Request,
        error: InvalidTokenError,
    ) -> JSONResponse:
        return JSONResponse({"error": str(error)}, status_code=401)

    return app


def serve(
    *,
    host: str = "127.0.0.1",
    port: int = 3787,
    overlay_paths: list[str] | None = None,
    auth_token: str | None = None,
) -> None:
    import uvicorn

    app = create_app(overlay_paths=overlay_paths, auth_token=auth_token)
    uvicorn.run(app, host=host, port=port, log_level="warning")
