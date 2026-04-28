from __future__ import annotations

import hashlib
import subprocess

from standards_control_plane.mcp_server import tools


def test_audit_changed_uses_resolved_refs_for_cache_keys(monkeypatch) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()
    resolved_refs = {
        "main": "a" * 40,
        "HEAD": "b" * 40,
    }
    cli_calls = {"count": 0}

    monkeypatch.setattr(
        tools,
        "_resolve_git_commit",
        lambda ref, *, repo_root, timeout_seconds: resolved_refs[ref],
    )
    monkeypatch.setattr(
        tools,
        "_list_changed_files_with_timeout",
        lambda *, base_ref, head_ref, repo_root, timeout_seconds: ["docs/DECISIONS.md"],
    )

    def _run_cli(*, base_ref: str, head_ref: str, domains: list[str], timeout_seconds: float):
        cli_calls["count"] += 1
        return {
            "base_ref": base_ref,
            "head_ref": head_ref,
            "changed_paths": ["docs/DECISIONS.md"],
            "audit_result": {"audit_id": f"audit-{cli_calls['count']:03d}", "scores": {"governance": 100}},
        }

    monkeypatch.setattr(tools, "_run_audit_changed_cli", _run_cli)

    first = tools.audit_changed_impl(tools.AuditChangedRequest(base_ref="main", head_ref="HEAD"))
    second = tools.audit_changed_impl(tools.AuditChangedRequest(base_ref="main", head_ref="HEAD"))
    resolved_refs["HEAD"] = "c" * 40
    third = tools.audit_changed_impl(tools.AuditChangedRequest(base_ref="main", head_ref="HEAD"))

    assert isinstance(first, tools.AuditChangedResponse)
    assert isinstance(second, tools.AuditChangedResponse)
    assert isinstance(third, tools.AuditChangedResponse)
    assert cli_calls["count"] == 2
    assert first.audit_result["audit_id"] == "audit-001"
    assert second.audit_result["audit_id"] == "audit-001"
    assert third.audit_result["audit_id"] == "audit-002"


def test_audit_changed_returns_timeout_when_diff_enumeration_hangs(monkeypatch) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()

    monkeypatch.setattr(
        tools,
        "_resolve_git_commit",
        lambda ref, *, repo_root, timeout_seconds: f"{ref}-sha",
    )

    def _raise_timeout(*, base_ref: str, head_ref: str, repo_root, timeout_seconds: float):
        raise subprocess.TimeoutExpired(cmd=["git", "diff"], timeout=timeout_seconds)

    monkeypatch.setattr(tools, "_list_changed_files_with_timeout", _raise_timeout)

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="main", head_ref="HEAD")
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E011"


def test_audit_changed_returns_diff_cap_error(monkeypatch) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()

    monkeypatch.setattr(
        tools,
        "_resolve_git_commit",
        lambda ref, *, repo_root, timeout_seconds: f"{ref}-sha",
    )
    monkeypatch.setattr(
        tools,
        "_list_changed_files_with_timeout",
        lambda *, base_ref, head_ref, repo_root, timeout_seconds: [f"file-{index}.txt" for index in range(501)],
    )

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="main", head_ref="HEAD")
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E012"


def test_audit_changed_returns_structured_error_for_invalid_cli_payload(monkeypatch) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()

    monkeypatch.setattr(
        tools,
        "_resolve_git_commit",
        lambda ref, *, repo_root, timeout_seconds: f"{ref}-sha",
    )
    monkeypatch.setattr(
        tools,
        "_list_changed_files_with_timeout",
        lambda *, base_ref, head_ref, repo_root, timeout_seconds: ["docs/DECISIONS.md"],
    )
    monkeypatch.setattr(
        tools,
        "_run_audit_changed_cli",
        lambda *, base_ref, head_ref, domains, timeout_seconds: {"base_ref": base_ref},
    )

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="main", head_ref="HEAD")
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E021"


def test_audit_changed_evicts_old_entries_when_cache_reaches_capacity(monkeypatch) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()
    resolved_refs = {
        "main": "a" * 40,
        "HEAD": "b" * 40,
        "release": "c" * 40,
    }

    monkeypatch.setattr(
        tools,
        "_resolve_git_commit",
        lambda ref, *, repo_root, timeout_seconds: resolved_refs[ref],
    )
    monkeypatch.setattr(
        tools,
        "_list_changed_files_with_timeout",
        lambda *, base_ref, head_ref, repo_root, timeout_seconds: ["docs/DECISIONS.md"],
    )
    monkeypatch.setattr(
        tools,
        "_run_audit_changed_cli",
        lambda *, base_ref, head_ref, domains, timeout_seconds: {
            "base_ref": base_ref,
            "head_ref": head_ref,
            "changed_paths": ["docs/DECISIONS.md"],
            "audit_result": {"audit_id": f"{base_ref}-{head_ref}", "scores": {"governance": 100}},
        },
    )

    first = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="main", head_ref="HEAD"),
        cache_max_entries=1,
    )
    second = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="release", head_ref="HEAD"),
        cache_max_entries=1,
    )

    assert isinstance(first, tools.AuditChangedResponse)
    assert isinstance(second, tools.AuditChangedResponse)
    assert len(tools._AUDIT_CHANGED_CACHE) == 1
    expected_key = hashlib.sha256(f"{resolved_refs['release']}\0{resolved_refs['HEAD']}".encode("utf-8")).hexdigest()
    assert list(tools._AUDIT_CHANGED_CACHE.keys()) == [expected_key]
