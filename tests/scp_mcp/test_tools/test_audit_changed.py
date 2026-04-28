from __future__ import annotations

import subprocess

from standards_control_plane.mcp_server import tools


def test_audit_changed_returns_cli_payload(monkeypatch) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()

    monkeypatch.setattr(
        tools,
        "list_changed_files",
        lambda *, base_ref, head_ref: ["docs/DECISIONS.md"],
    )
    monkeypatch.setattr(
        tools,
        "_run_audit_changed_cli",
        lambda *, base_ref, head_ref, domains, timeout_seconds: {
            "base_ref": base_ref,
            "head_ref": head_ref,
            "changed_paths": ["docs/DECISIONS.md"],
            "audit_result": {"audit_id": "audit-001", "scores": {"governance": 100}},
        },
    )

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="main", head_ref="HEAD")
    )

    assert isinstance(response, tools.AuditChangedResponse)
    assert response.base_ref == "main"
    assert response.audit_result["audit_id"] == "audit-001"


def test_audit_changed_returns_timeout_circuit_breaker(monkeypatch) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()

    monkeypatch.setattr(
        tools,
        "list_changed_files",
        lambda *, base_ref, head_ref: ["docs/DECISIONS.md"],
    )

    def _raise_timeout(*, base_ref: str, head_ref: str, domains: list[str], timeout_seconds: int):
        raise subprocess.TimeoutExpired(cmd=["audit-changed"], timeout=timeout_seconds)

    monkeypatch.setattr(tools, "_run_audit_changed_cli", _raise_timeout)

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="main", head_ref="HEAD")
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E011"


def test_audit_changed_returns_diff_cap_error(monkeypatch) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()

    monkeypatch.setattr(
        tools,
        "list_changed_files",
        lambda *, base_ref, head_ref: [f"file-{index}.txt" for index in range(501)],
    )

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="main", head_ref="HEAD")
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E012"
