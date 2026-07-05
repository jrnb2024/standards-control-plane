from __future__ import annotations

import subprocess
import time

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

    def _run_cli(
        *,
        base_ref: str,
        head_ref: str,
        domains: list[str],
        repo_root,
        subsystem,
        area_hint,
        timeout_seconds: float,
    ):
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
        lambda *, base_ref, head_ref, domains, repo_root, subsystem, area_hint, timeout_seconds: {"base_ref": base_ref},
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
        lambda *, base_ref, head_ref, domains, repo_root, subsystem, area_hint, timeout_seconds: {
            "base_ref": base_ref,
            "head_ref": head_ref,
            "changed_paths": ["docs/DECISIONS.md"],
            "audit_result": {"audit_id": f"{base_ref}-{head_ref}", "scores": {"governance": 100}},
        },
    )

    repo_root = str(tools.project_root())
    first = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="main", head_ref="HEAD", repo_root=repo_root),
        cache_max_entries=1,
    )
    second = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="release", head_ref="HEAD", repo_root=repo_root),
        cache_max_entries=1,
    )

    assert isinstance(first, tools.AuditChangedResponse)
    assert isinstance(second, tools.AuditChangedResponse)
    assert len(tools._AUDIT_CHANGED_CACHE) == 1
    expected_key = tools._audit_cache_key(
        resolved_refs["release"],
        resolved_refs["HEAD"],
        repo_root=tools.project_root(),
        subsystem=tools.project_root().name,
        area_hint=None,
    )
    assert list(tools._AUDIT_CHANGED_CACHE.keys()) == [expected_key]


def test_audit_changed_treats_cache_move_race_as_cache_miss(monkeypatch) -> None:
    original_cache = tools._AUDIT_CHANGED_CACHE
    tools._AUDIT_CHANGED_CACHE.clear()

    class RaceyCache(dict):
        def move_to_end(self, key):  # type: ignore[override]
            raise KeyError(key)

    racey_cache = RaceyCache()
    cache_key = tools._audit_cache_key(
        "a" * 40,
        "b" * 40,
        repo_root=tools.project_root(),
        subsystem=tools.project_root().name,
        area_hint=None,
    )
    cached_response = tools.AuditChangedResponse(
        base_ref="main",
        head_ref="HEAD",
        changed_paths=["docs/DECISIONS.md"],
        audit_result={"audit_id": "stale", "scores": {"governance": 100}},
    )
    racey_cache[cache_key] = (time.time() + 60, cached_response)

    monkeypatch.setattr(tools, "_AUDIT_CHANGED_CACHE", racey_cache)
    monkeypatch.setattr(
        tools,
        "_resolve_git_commit",
        lambda ref, *, repo_root, timeout_seconds: {"main": "a" * 40, "HEAD": "b" * 40}[ref],
    )
    monkeypatch.setattr(
        tools,
        "_list_changed_files_with_timeout",
        lambda *, base_ref, head_ref, repo_root, timeout_seconds: ["docs/DECISIONS.md"],
    )
    monkeypatch.setattr(
        tools,
        "_run_audit_changed_cli",
        lambda *, base_ref, head_ref, domains, repo_root, subsystem, area_hint, timeout_seconds: {
            "base_ref": base_ref,
            "head_ref": head_ref,
            "changed_paths": ["docs/DECISIONS.md"],
            "audit_result": {"audit_id": "fresh", "scores": {"governance": 100}},
        },
    )

    try:
        response = tools.audit_changed_impl(
            tools.AuditChangedRequest(
                base_ref="main",
                head_ref="HEAD",
                repo_root=str(tools.project_root()),
            ),
        )
    finally:
        monkeypatch.setattr(tools, "_AUDIT_CHANGED_CACHE", original_cache)

    assert isinstance(response, tools.AuditChangedResponse)
    assert response.audit_result["audit_id"] == "fresh"
