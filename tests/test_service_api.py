from __future__ import annotations

import json
import threading
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jwt import encode
from jwt.algorithms import RSAAlgorithm

from standards_control_plane import service as service_module
from standards_control_plane.resources import examples_dir
from standards_control_plane.schema_tools import load_json_file, validate_with_schema
from standards_control_plane.service import create_app


def _write_overlay(root: Path) -> Path:
    architecture = root / "architecture"
    rules_dir = architecture / "rules"
    patterns_dir = architecture / "patterns"
    rules_dir.mkdir(parents=True)
    patterns_dir.mkdir(parents=True)

    (root / "standards-index.json").write_text(
        json.dumps(
            {
                "name": "overlay-registry",
                "version": "2026-04-12",
                "status": "draft",
                "domains": {"architecture": "architecture/index.json"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (rules_dir / "ARCH-001-overlay.md").write_text("# ARCH-001 overlay\n", encoding="utf-8")
    (patterns_dir / "overlay-action-service-pattern.md").write_text(
        "# overlay pattern\n",
        encoding="utf-8",
    )
    (architecture / "index.json").write_text(
        json.dumps(
            {
                "domain": "architecture",
                "version": "2026-04-12",
                "status": "active",
                "rules": [
                    {
                        "rule_id": "ARCH-001",
                        "domain": "architecture",
                        "title": "Overlay boundary severity",
                        "summary": "Overlay raises boundary leaks to critical severity.",
                        "path": "rules/ARCH-001-overlay.md",
                        "severity_default": "critical",
                        "scope": ["frontend", "backend"],
                        "signals": ["cross-boundary import marker"],
                        "exceptions": [],
                        "related_patterns": ["overlay-action-service-pattern"],
                        "version": "2026-04-12",
                        "status": "active",
                    }
                ],
                "patterns": [
                    {
                        "pattern_id": "overlay-action-service-pattern",
                        "domain": "architecture",
                        "title": "Overlay action service pattern",
                        "summary": (
                            "Use the overlay action service for cross-boundary "
                            "orchestration."
                        ),
                        "path": "patterns/overlay-action-service-pattern.md",
                        "tags": ["returns", "triage"],
                        "version": "2026-04-12",
                        "status": "active",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return root


class _FakeControlTower:
    def __init__(self, audience: str) -> None:
        self.audience = audience
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_jwk = json.loads(
            RSAAlgorithm.to_jwk(self.private_key.public_key(), as_dict=False)
        )
        self.public_jwk["kid"] = "scp-test-kid"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self._build_handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def _build_handler(self):
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def _send_json(self, status_code: int, payload: dict[str, object]) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                if parsed.path == "/api/v1/.well-known/jwks.json":
                    self._send_json(200, {"keys": [parent.public_jwk]})
                    return
                if parsed.path == "/api/v1/auth/authorize":
                    params = parse_qs(parsed.query)
                    redirect_uri = params["redirect_uri"][0]
                    state = params["state"][0]
                    self.send_response(302)
                    self.send_header("Location", f"{redirect_uri}?code=test-code&state={state}")
                    self.end_headers()
                    return
                self._send_json(404, {"error": "not_found"})

            def do_POST(self) -> None:
                parsed = urlparse(self.path)
                if parsed.path == "/api/v1/auth/token":
                    payload = parent._token_payload()
                    self._send_json(
                        200,
                        {
                            "access_token": payload,
                            "refresh_token": "refresh-token",
                        },
                    )
                    return
                if parsed.path == "/api/v1/auth/refresh":
                    payload = parent._token_payload()
                    self._send_json(
                        200,
                        {
                            "access_token": payload,
                            "refresh_token": "refresh-token-rotated",
                        },
                    )
                    return
                self._send_json(404, {"error": "not_found"})

            def log_message(self, format: str, *args: object) -> None:  # noqa: A003
                return

        return Handler

    def _token_payload(self, overrides: dict[str, object] | None = None) -> str:
        now = datetime.now(UTC)
        claims: dict[str, object] = {
            "sub": "user-123",
            "email": "user@example.com",
            "display_name": "Example User",
            "roles": ["admin"],
            "iss": "control-tower",
            "aud": self.audience,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=30)).timestamp()),
        }
        if overrides:
            claims.update(overrides)
        return encode(
            claims,
            self.private_key,
            algorithm="RS256",
            headers={"kid": "scp-test-kid"},
        )

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}"

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()


@pytest.fixture
def fake_ct() -> _FakeControlTower:
    server = _FakeControlTower(audience="scp-dev")
    server.start()
    try:
        yield server
    finally:
        server.stop()


def _estate_env(fake_ct: _FakeControlTower, **overrides: str) -> dict[str, str]:
    env = {
        "SCP_ESTATE_READ_ONLY_ENABLED": "true",
        "AUTH_ENABLED": "true",
        "ENV": "development",
        "CT_BASE_URL": fake_ct.base_url,
        "CT_JWKS_URL": f"{fake_ct.base_url}/api/v1/.well-known/jwks.json",
        "CT_APP_ID": "scp",
        "CT_ISSUER": "control-tower",
        "PUBLIC_BASE_URL": "http://testserver",
    }
    env.update(overrides)
    return env


def _estate_claims(**overrides: object) -> dict[str, object]:
    claims: dict[str, object] = {
        "iss": "control-tower",
        "aud": "scp",
        "sub": "sa:acc-estate-context",
        "azp": "acc",
        "actor_type": "service",
        "scopes": ["estate:standards:read"],
        "active_org_id": "org-001",
    }
    claims.update(overrides)
    return claims


def _estate_headers(fake_ct: _FakeControlTower, **overrides: str) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {fake_ct._token_payload(_estate_claims())}",
        "X-Estate-Org-ID": "org-001",
        "X-Estate-Workspace-ID": "workspace-001",
        "X-Estate-Project-ID": "project-001",
        "X-Estate-Repository-ID": "repo-001",
    }
    headers.update(overrides)
    return headers


def test_service_api_serves_frontend_status_and_api_without_auth(tmp_path: Path) -> None:
    overlay_root = _write_overlay(tmp_path / "overlay")
    app = create_app(
        overlay_paths=[str(overlay_root)],
        env={"AUTH_ENABLED": "false", "ENV": "development"},
    )

    with TestClient(app) as client:
        home_page = client.get("/")
        assert home_page.status_code == 200
        assert "Standards Control Plane" in home_page.text
        assert "/status-app/health" in home_page.text
        assert "ADOPT-001 Project Onboarding" in home_page.text

        adoption_page = client.get("/docs/adoption")
        assert adoption_page.status_code == 200
        assert "ADOPT-001 Project Onboarding" in adoption_page.text

        health_payload = client.get("/health").json()
        # SVC-002 shape: status ∈ {healthy, degraded, error} + version + checks.
        # version falls back to "0.0.0+unknown" when the package isn't
        # installed via the wheel (editable or in-tree test run); that's
        # acceptable — SVC-002 only requires a version string, not a
        # specific value.
        assert health_payload["status"] == "healthy"
        assert isinstance(health_payload["version"], str)
        assert health_payload["checks"]["registry"]["status"] == "healthy"
        assert health_payload["checks"]["authentication"]["status"] == "healthy"
        assert health_payload["checks"]["required_artifacts"]["status"] == "healthy"

        status_payload = client.get("/status-app/health").json()
        validate_with_schema(status_payload, "status-app-health.schema.json")
        assert status_payload["service"]["name"] == "standards-control-plane"
        assert status_payload["auth"]["enabled"] is False
        assert status_payload["auth"]["mode"] == "none"

        registry_payload = client.get("/registry").json()
        assert registry_payload["domains"]["architecture"]["rules"][0]["rule_id"] == "ARCH-001"

        consult_request = load_json_file(examples_dir() / "consult-request.json")
        consult_response = client.post("/consult", json=consult_request).json()
        validate_with_schema(consult_response, "consult-response.schema.json")
        assert any(
            item["pattern_id"] == "overlay-action-service-pattern"
            for item in consult_response["approved_patterns"]
        )

        audit_request = load_json_file(examples_dir() / "audit-request.json")
        audit_response = client.post("/audit", json=audit_request).json()
        validate_with_schema(audit_response, "audit-result.schema.json")
        severity_by_id = {
            finding["finding_id"]: finding["severity"]
            for finding in audit_response["findings"]
        }
        assert severity_by_id["F-ARCH-001-returns-exceptions"] == "critical"


def test_service_api_supports_oidc_cookie_auth_and_legacy_bearer(
    tmp_path: Path,
    fake_ct: _FakeControlTower,
) -> None:
    overlay_root = _write_overlay(tmp_path / "overlay")
    app = create_app(
        overlay_paths=[str(overlay_root)],
        auth_token="legacy-token",
        env={
            "AUTH_ENABLED": "true",
            "ENV": "development",
            "CT_BASE_URL": fake_ct.base_url,
            "CT_JWKS_URL": f"{fake_ct.base_url}/api/v1/.well-known/jwks.json",
            "CT_APP_ID": "scp-dev",
            "PUBLIC_BASE_URL": "http://testserver",
        },
    )

    with TestClient(app) as client:
        home = client.get("/", follow_redirects=False)
        assert home.status_code == 302
        assert home.headers["location"] == "/auth/login?next=%2F"

        login = client.get("/auth/login?next=/docs/adoption", follow_redirects=False)
        assert login.status_code == 302
        assert login.headers["location"].startswith(
            f"{fake_ct.base_url}/api/v1/auth/authorize?"
        )
        state = client.cookies.get("scp_oauth_state")
        assert state is not None

        callback = client.get(
            "/auth/callback",
            params={"code": "test-code", "state": state},
            follow_redirects=False,
        )
        assert callback.status_code == 302
        assert callback.headers["location"] == "/docs/adoption"
        assert client.cookies.get("access_token") is not None
        assert client.cookies.get("refresh_token") is not None

        adoption_page = client.get("/docs/adoption")
        assert adoption_page.status_code == 200
        assert "repo-onboarding brief" in adoption_page.text

        me = client.get("/auth/me")
        assert me.status_code == 200
        assert me.json()["email"] == "user@example.com"

        api_me = client.get("/api/auth/me")
        assert api_me.status_code == 200
        assert api_me.json()["email"] == "user@example.com"

        status_payload = client.get("/status-app/health").json()
        validate_with_schema(status_payload, "status-app-health.schema.json")
        assert status_payload["auth"]["enabled"] is True
        assert status_payload["auth"]["mode"] == "oidc+bearer"
        assert status_payload["auth"]["app_id"] == "scp-dev"

        consult_request = load_json_file(examples_dir() / "consult-request.json")
        consult_response = client.post("/consult", json=consult_request)
        assert consult_response.status_code == 200

        logout = client.get("/auth/logout", follow_redirects=False)
        assert logout.status_code == 302
        assert client.cookies.get("access_token") is None

        registry_error = client.get("/registry")
        assert registry_error.status_code == 401

        auth_headers = {"Authorization": "Bearer legacy-token"}
        registry_payload = client.get("/registry", headers=auth_headers).json()
        severity_default = registry_payload["domains"]["architecture"]["rules"][0][
            "severity_default"
        ]
        assert severity_default == "critical"


@pytest.mark.parametrize(
    ("env_overrides", "legacy_token", "message_fragment"),
    [
        ({"AUTH_ENABLED": "false"}, None, "AUTH_ENABLED=true"),
        ({}, "legacy-token", "legacy bearer"),
        ({"CT_APP_ID": "scp-dev"}, None, "CT_APP_ID=scp"),
        ({"CT_ISSUER": ""}, None, "CT_ISSUER"),
        (
            {"SCP_ESTATE_READ_ONLY_ENABLED": "treu"},
            None,
            "SCP_ESTATE_READ_ONLY_ENABLED",
        ),
    ],
)
def test_estate_profile_rejects_unsafe_startup_configuration(
    fake_ct: _FakeControlTower,
    env_overrides: dict[str, str],
    legacy_token: str | None,
    message_fragment: str,
) -> None:
    env = _estate_env(fake_ct, **env_overrides)
    with pytest.raises(ValueError, match=message_fragment):
        create_app(auth_token=legacy_token, env=env)


def test_estate_profile_requires_feature_flag_explicitly() -> None:
    app = create_app(env={"AUTH_ENABLED": "false", "ENV": "development"})
    with TestClient(app):
        assert app.state.service_state.config.estate_read_only_enabled is False


def test_estate_profile_wraps_read_results_with_verified_binding(tmp_path: Path) -> None:
    overlay_root = _write_overlay(tmp_path / "overlay")
    fake_ct = _FakeControlTower(audience="scp")
    fake_ct.start()
    try:
        app = create_app(overlay_paths=[str(overlay_root)], env=_estate_env(fake_ct))
        headers = _estate_headers(fake_ct)
        expected_binding = {
            "active_org_id": "org-001",
            "workspace_id": "workspace-001",
            "project_id": "project-001",
            "repository_id": "repo-001",
        }

        with TestClient(app) as client:
            registry = client.get("/registry", headers=headers)
            assert registry.status_code == 200
            assert registry.json()["profile"] == "estate-read-only/v1"
            assert registry.json()["request_binding"] == expected_binding
            assert registry.json()["authority"] == {
                "mode": "read_only",
                "action_authority": False,
            }
            assert registry.json()["result"]["domains"]["architecture"]["rules"][0][
                "rule_id"
            ] == "ARCH-001"

            consult_request = load_json_file(examples_dir() / "consult-request.json")
            consult = client.post("/consult", headers=headers, json=consult_request)
            assert consult.status_code == 200
            assert consult.json()["request_binding"] == expected_binding
            validate_with_schema(consult.json()["result"], "consult-response.schema.json")

            audit_request = load_json_file(examples_dir() / "audit-request.json")
            audit = client.post("/audit", headers=headers, json=audit_request)
            assert audit.status_code == 200
            assert audit.json()["request_binding"] == expected_binding
            validate_with_schema(audit.json()["result"], "audit-result.schema.json")
    finally:
        fake_ct.stop()


@pytest.mark.parametrize(
    "claim_overrides",
    [
        {"iss": "other-issuer"},
        {"aud": "other-service"},
        {"aud": ["scp", "other-service"]},
        {"sub": "sa:some-other-principal"},
        {"azp": "other-client"},
        {"actor_type": "user"},
        {"scopes": ["other:scope"]},
        {"scopes": ["estate:standards:read", "estate:standards:write"]},
        {"active_org_id": ""},
    ],
)
def test_estate_profile_rejects_identity_drift(
    claim_overrides: dict[str, object],
) -> None:
    estate_ct = _FakeControlTower(audience="scp")
    estate_ct.start()
    try:
        app = create_app(env=_estate_env(estate_ct))
        headers = _estate_headers(estate_ct)
        headers["Authorization"] = (
            f"Bearer {estate_ct._token_payload(_estate_claims(**claim_overrides))}"
        )
        with TestClient(app) as client:
            response = client.get("/registry", headers=headers)
        assert response.status_code in {401, 403}
    finally:
        estate_ct.stop()


@pytest.mark.parametrize(
    ("missing_header", "override", "expected_status"),
    [
        ("X-Estate-Org-ID", None, 400),
        ("X-Estate-Workspace-ID", None, 400),
        ("X-Estate-Project-ID", None, 400),
        ("X-Estate-Repository-ID", None, 400),
        (None, {"X-Estate-Workspace-ID": "workspace-001,workspace-002"}, 400),
        (None, {"X-Estate-Org-ID": "org-other"}, 403),
    ],
)
def test_estate_profile_rejects_missing_or_mismatched_binding(
    missing_header: str | None,
    override: dict[str, str] | None,
    expected_status: int,
) -> None:
    estate_ct = _FakeControlTower(audience="scp")
    estate_ct.start()
    try:
        app = create_app(env=_estate_env(estate_ct))
        headers = _estate_headers(estate_ct)
        if missing_header:
            headers.pop(missing_header)
        if override:
            headers.update(override)
        with TestClient(app) as client:
            response = client.get("/registry", headers=headers)
        assert response.status_code == expected_status
    finally:
        estate_ct.stop()


def test_health_reports_missing_required_artifacts_as_degraded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    estate_ct = _FakeControlTower(audience="scp")
    estate_ct.start()
    try:
        monkeypatch.setattr(service_module, "project_root", lambda: tmp_path)
        app = create_app(env=_estate_env(estate_ct))
        with TestClient(app) as client:
            health = client.get("/health")
            status_health = client.get("/status-app/health")
        assert health.status_code == 200
        assert health.json()["status"] == "degraded"
        assert health.json()["checks"]["required_artifacts"]["status"] == "degraded"
        assert status_health.json()["status"] == "degraded"
        validate_with_schema(status_health.json(), "status-app-health.schema.json")
    finally:
        estate_ct.stop()
