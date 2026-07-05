from __future__ import annotations

import subprocess
import time
from pathlib import Path

from standards_control_plane.mcp_server import tools


def _init_adopter_repo(tmp_path: Path) -> Path:
    """Create a mapp-pim-shaped git repo with a services/ change between two commits."""
    repo = tmp_path / "adopter"
    (repo / "services" / "enrichment").mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)

    module = repo / "services" / "enrichment" / "pipeline.py"
    module.write_text("VERSION = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True, text=True
    )

    module.write_text("VERSION = 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "change"], cwd=repo, check=True, capture_output=True, text=True
    )
    return repo


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
        timeout_seconds: float,
        repo_root: Path,
        area_id: str | None,
    ):
        cli_calls["count"] += 1
        return {
            "base_ref": base_ref,
            "head_ref": head_ref,
            "changed_paths": ["docs/DECISIONS.md"],
            "audit_result": {
                "audit_id": f"audit-{cli_calls['count']:03d}",
                "scores": {"governance": 100},
            },
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
        lambda *, base_ref, head_ref, domains, timeout_seconds, repo_root, area_id: {
            "base_ref": base_ref
        },
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
        lambda *, base_ref, head_ref, domains, timeout_seconds, repo_root, area_id: {
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
    expected_key = tools._audit_cache_key(
        resolved_refs["release"],
        resolved_refs["HEAD"],
        tools.project_root().resolve(),
    )
    assert list(tools._AUDIT_CHANGED_CACHE.keys()) == [expected_key]


def test_audit_changed_treats_cache_move_race_as_cache_miss(monkeypatch) -> None:
    original_cache = tools._AUDIT_CHANGED_CACHE
    tools._AUDIT_CHANGED_CACHE.clear()

    class RaceyCache(dict):
        def move_to_end(self, key):  # type: ignore[override]
            raise KeyError(key)

    racey_cache = RaceyCache()
    cache_key = tools._audit_cache_key("a" * 40, "b" * 40, tools.project_root().resolve())
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
        lambda *, base_ref, head_ref, domains, timeout_seconds, repo_root, area_id: {
            "base_ref": base_ref,
            "head_ref": head_ref,
            "changed_paths": ["docs/DECISIONS.md"],
            "audit_result": {"audit_id": "fresh", "scores": {"governance": 100}},
        },
    )

    try:
        response = tools.audit_changed_impl(
            tools.AuditChangedRequest(base_ref="main", head_ref="HEAD"),
        )
    finally:
        monkeypatch.setattr(tools, "_AUDIT_CHANGED_CACHE", original_cache)

    assert isinstance(response, tools.AuditChangedResponse)
    assert response.audit_result["audit_id"] == "fresh"


def test_audit_changed_with_repo_root_audits_external_worktree(monkeypatch, tmp_path) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()
    repo = _init_adopter_repo(tmp_path)
    captured: dict[str, object] = {}

    def _run_cli(
        *,
        base_ref: str,
        head_ref: str,
        domains: list[str],
        timeout_seconds: float,
        repo_root: Path,
        area_id: str | None,
    ):
        captured["repo_root"] = repo_root
        captured["domains"] = domains
        captured["area_id"] = area_id
        return {
            "base_ref": base_ref,
            "head_ref": head_ref,
            "changed_paths": ["services/enrichment/pipeline.py"],
            "audit_result": {"audit_id": "cross-repo", "scores": {"architecture": 100}},
        }

    monkeypatch.setattr(tools, "_run_audit_changed_cli", _run_cli)

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="HEAD~1", head_ref="HEAD", repo_root=str(repo))
    )

    assert isinstance(response, tools.AuditChangedResponse), getattr(response, "message", "")
    assert response.changed_paths == ["services/enrichment/pipeline.py"]
    assert captured["repo_root"] == repo.resolve()
    # services/** paths must resolve to a real domain, not the governance fallback.
    assert "architecture" in captured["domains"]


def test_audit_changed_passes_area_hint_through_to_cli(monkeypatch, tmp_path) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()
    repo = _init_adopter_repo(tmp_path)
    captured: dict[str, object] = {}

    def _run_cli(
        *,
        base_ref: str,
        head_ref: str,
        domains: list[str],
        timeout_seconds: float,
        repo_root: Path,
        area_id: str | None,
    ):
        captured["area_id"] = area_id
        return {
            "base_ref": base_ref,
            "head_ref": head_ref,
            "changed_paths": ["services/enrichment/pipeline.py"],
            "audit_result": {"audit_id": "cross-repo", "scores": {"architecture": 100}},
        }

    monkeypatch.setattr(tools, "_run_audit_changed_cli", _run_cli)

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(
            base_ref="HEAD~1",
            head_ref="HEAD",
            repo_root=str(repo),
            area_hint="enrichment-consumer",
        )
    )

    assert isinstance(response, tools.AuditChangedResponse), getattr(response, "message", "")
    assert captured["area_id"] == "enrichment-consumer"


def test_audit_changed_passes_area_hint_without_repo_root(monkeypatch) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()
    captured: dict[str, object] = {}

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

    def _run_cli(*, base_ref, head_ref, domains, timeout_seconds, repo_root, area_id):
        captured["area_id"] = area_id
        captured["repo_root"] = repo_root
        return {
            "base_ref": base_ref,
            "head_ref": head_ref,
            "changed_paths": ["docs/DECISIONS.md"],
            "audit_result": {"audit_id": "self", "scores": {"governance": 100}},
        }

    monkeypatch.setattr(tools, "_run_audit_changed_cli", _run_cli)

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="main", head_ref="HEAD", area_hint="mcp-plane")
    )

    assert isinstance(response, tools.AuditChangedResponse)
    assert captured["area_id"] == "mcp-plane"
    assert captured["repo_root"] == tools.project_root().resolve()


def test_audit_changed_rejects_nonexistent_repo_root(tmp_path) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(repo_root=str(tmp_path / "does-not-exist"))
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E021"


def test_audit_changed_rejects_repo_root_that_is_not_a_worktree_root(tmp_path) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()
    repo = _init_adopter_repo(tmp_path)

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(repo_root=str(repo / "services"))
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E021"


def test_audit_cache_key_distinguishes_repo_roots(tmp_path) -> None:
    key_a = tools._audit_cache_key("a" * 40, "b" * 40, tmp_path / "repo-a")
    key_b = tools._audit_cache_key("a" * 40, "b" * 40, tmp_path / "repo-b")

    assert key_a != key_b


def test_audit_cache_key_distinguishes_area_hints(tmp_path) -> None:
    # area_hint changes scope.area_id and every finding identity, so two
    # audits differing only by hint must not share a cache entry.
    key_none = tools._audit_cache_key("a" * 40, "b" * 40, tmp_path, None)
    key_hint = tools._audit_cache_key("a" * 40, "b" * 40, tmp_path, "enrichment")

    assert key_none != key_hint


def test_audit_changed_does_not_cache_external_repo_root_results(monkeypatch, tmp_path) -> None:
    # External worktrees are live editing surfaces: evaluators read working-tree
    # content, so a cached verdict keyed on commit SHAs would go stale the
    # moment the agent edits a file without committing.
    tools._AUDIT_CHANGED_CACHE.clear()
    repo = _init_adopter_repo(tmp_path)
    cli_calls = {"count": 0}

    def _run_cli(*, base_ref, head_ref, domains, timeout_seconds, repo_root, area_id):
        cli_calls["count"] += 1
        return {
            "base_ref": base_ref,
            "head_ref": head_ref,
            "changed_paths": ["services/enrichment/pipeline.py"],
            "audit_result": {
                "audit_id": f"run-{cli_calls['count']}",
                "scores": {"architecture": 100},
            },
        }

    monkeypatch.setattr(tools, "_run_audit_changed_cli", _run_cli)

    request = tools.AuditChangedRequest(base_ref="HEAD~1", head_ref="HEAD", repo_root=str(repo))
    first = tools.audit_changed_impl(request)
    second = tools.audit_changed_impl(request)

    assert isinstance(first, tools.AuditChangedResponse)
    assert isinstance(second, tools.AuditChangedResponse)
    assert cli_calls["count"] == 2
    assert len(tools._AUDIT_CHANGED_CACHE) == 0


def test_audit_changed_treats_blank_area_hint_as_absent(monkeypatch) -> None:
    tools._AUDIT_CHANGED_CACHE.clear()
    captured: dict[str, object] = {}

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

    def _run_cli(*, base_ref, head_ref, domains, timeout_seconds, repo_root, area_id):
        captured["area_id"] = area_id
        return {
            "base_ref": base_ref,
            "head_ref": head_ref,
            "changed_paths": ["docs/DECISIONS.md"],
            "audit_result": {"audit_id": "self", "scores": {"governance": 100}},
        }

    monkeypatch.setattr(tools, "_run_audit_changed_cli", _run_cli)

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="main", head_ref="HEAD", area_hint="   ")
    )

    assert isinstance(response, tools.AuditChangedResponse)
    assert captured["area_id"] is None


def test_audit_changed_end_to_end_against_external_repo(tmp_path) -> None:
    """Acceptance: a diff in an external worktree naming services/ paths yields a
    real audit result (findings or a clean pass), not SCP-MCP-E021."""
    tools._AUDIT_CHANGED_CACHE.clear()
    repo = _init_adopter_repo(tmp_path)

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(base_ref="HEAD~1", head_ref="HEAD", repo_root=str(repo))
    )

    assert isinstance(response, tools.AuditChangedResponse), getattr(response, "message", "")
    assert response.changed_paths == ["services/enrichment/pipeline.py"]
    audit_result = response.audit_result
    assert audit_result["scope"]["area_id"]
    assert "architecture" in audit_result["domain_status"]
    assert isinstance(audit_result["findings"], list)
    # Resolution legibility: services/** resolved via the glob tier, so the
    # response must say which domains ran and at what confidence.
    assert "architecture" in response.domains_evaluated
    assert response.resolve_confidence == 0.75
