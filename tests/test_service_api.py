from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

from standards_control_plane.resources import examples_dir
from standards_control_plane.schema_tools import load_json_file, validate_with_schema
from standards_control_plane.service import create_service_server


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


def _get_json(url: str, *, headers: dict[str, str] | None = None) -> dict[str, object]:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request) as response:
        payload = json.loads(response.read().decode("utf-8"))
    assert isinstance(payload, dict)
    return payload


def _post_json(
    url: str,
    payload: dict[str, object],
    *,
    headers: dict[str, str] | None = None,
) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    with urllib.request.urlopen(request) as response:
        body = json.loads(response.read().decode("utf-8"))
    assert isinstance(body, dict)
    return body


def _get_http_error(url: str, *, headers: dict[str, str] | None = None) -> urllib.error.HTTPError:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        urllib.request.urlopen(request)
    except urllib.error.HTTPError as error:
        return error
    raise AssertionError("Expected HTTPError")


def _post_http_error(
    url: str,
    payload: dict[str, object],
    *,
    headers: dict[str, str] | None = None,
) -> urllib.error.HTTPError:
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers=request_headers,
    )
    try:
        urllib.request.urlopen(request)
    except urllib.error.HTTPError as error:
        return error
    raise AssertionError("Expected HTTPError")


def test_service_api_serves_health_registry_consult_and_audit(tmp_path: Path) -> None:
    overlay_root = _write_overlay(tmp_path / "overlay")
    server = create_service_server(port=0, overlay_paths=[str(overlay_root)])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{server.server_port}"
        assert _get_json(f"{base_url}/health") == {"status": "ok"}

        registry_payload = _get_json(f"{base_url}/registry")
        assert registry_payload["domains"]["architecture"]["rules"][0]["rule_id"] == "ARCH-001"

        consult_request = load_json_file(examples_dir() / "consult-request.json")
        consult_response = _post_json(f"{base_url}/consult", consult_request)
        validate_with_schema(consult_response, "consult-response.schema.json")
        assert any(
            item["pattern_id"] == "overlay-action-service-pattern"
            for item in consult_response["approved_patterns"]
        )

        audit_request = load_json_file(examples_dir() / "audit-request.json")
        audit_response = _post_json(f"{base_url}/audit", audit_request)
        validate_with_schema(audit_response, "audit-result.schema.json")
        severity_by_id = {
            finding["finding_id"]: finding["severity"]
            for finding in audit_response["findings"]
        }
        assert severity_by_id["F-ARCH-001-returns-exceptions"] == "critical"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_service_api_optionally_requires_bearer_auth(tmp_path: Path) -> None:
    overlay_root = _write_overlay(tmp_path / "overlay")
    server = create_service_server(
        port=0,
        overlay_paths=[str(overlay_root)],
        auth_token="test-token",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{server.server_port}"
        assert _get_json(f"{base_url}/health") == {"status": "ok"}

        registry_error = _get_http_error(f"{base_url}/registry")
        assert registry_error.code == 401

        consult_request = load_json_file(examples_dir() / "consult-request.json")
        consult_error = _post_http_error(f"{base_url}/consult", consult_request)
        assert consult_error.code == 401

        audit_request = load_json_file(examples_dir() / "audit-request.json")
        audit_error = _post_http_error(f"{base_url}/audit", audit_request)
        assert audit_error.code == 401

        auth_headers = {"Authorization": "Bearer test-token"}
        registry_payload = _get_json(f"{base_url}/registry", headers=auth_headers)
        severity_default = registry_payload["domains"]["architecture"]["rules"][0][
            "severity_default"
        ]
        assert severity_default == "critical"

        consult_response = _post_json(
            f"{base_url}/consult",
            consult_request,
            headers=auth_headers,
        )
        validate_with_schema(consult_response, "consult-response.schema.json")

        audit_response = _post_json(
            f"{base_url}/audit",
            audit_request,
            headers=auth_headers,
        )
        validate_with_schema(audit_response, "audit-result.schema.json")
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
