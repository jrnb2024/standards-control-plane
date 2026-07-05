from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from standards_control_plane.changed_audit import (
    RepoRootResolutionError,
    build_changed_file_audit_result,
    list_changed_files,
    resolve_audit_repo_root,
)
from standards_control_plane.schema_tools import validate_with_schema


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo(repo: Path, *, second_commit: bool = True) -> None:
    """Initialise a temp git repo with a base commit and (optionally) a head
    commit that adds an ENH spec so area_id can be inferred from the diff."""
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init")
    _git(repo, "config", "user.name", "Adopter")
    _git(repo, "config", "user.email", "adopter@example.com")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "base")
    if not second_commit:
        return
    enh_dir = repo / "docs" / "enhancements"
    enh_dir.mkdir(parents=True)
    (enh_dir / "ENH-001-pim-enrichment.md").write_text("# spec\n", encoding="utf-8")
    _git(repo, "add", "docs/enhancements/ENH-001-pim-enrichment.md")
    _git(repo, "commit", "-m", "add enh spec")


def test_list_changed_files_returns_repo_relative_paths_from_temp_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=repo, check=True)

    tracked = repo / "tracked.txt"
    tracked.write_text("one\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True, text=True)

    tracked.write_text("two\n", encoding="utf-8")
    deleted = repo / "deleted.txt"
    deleted.write_text("gone\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt", "deleted.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "second"], cwd=repo, check=True, capture_output=True, text=True)
    deleted.unlink()
    subprocess.run(["git", "rm", "deleted.txt"], cwd=repo, check=True, capture_output=True, text=True)

    changed = list_changed_files(base_ref="HEAD~1", head_ref="HEAD", repo_root=repo)
    assert changed == ["tracked.txt"]


def test_build_changed_file_audit_result_accepts_explicit_changed_paths() -> None:
    result = build_changed_file_audit_result(
        base_ref="base",
        head_ref="head",
        domains=["governance", "architecture"],
        subsystem="returns",
        standards_version="2026-04-11",
        changed_paths=[
            "fixtures/returns-pilot/docs/enhancements/ENH-042-returns-exceptions.md",
            "fixtures/returns-pilot/frontend/app/exceptions/page.tsx",
        ],
    )
    validate_with_schema(result, "changed-audit-result.schema.json")
    assert result["changed_paths"] == [
        "fixtures/returns-pilot/docs/enhancements/ENH-042-returns-exceptions.md",
        "fixtures/returns-pilot/frontend/app/exceptions/page.tsx",
    ]
    assert result["audit_result"]["scope"]["area_id"] == "returns-exceptions"


def test_build_changed_file_audit_result_audits_cwd_repo_not_scp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression for WP-SCP-038 defect 1: run audit-changed from a SECOND git
    repo and assert the changed_paths (and inferred area) come from THAT repo,
    not from the standards-control-plane checkout. Under the old
    project_root() default the diff resolved against SCP and this file — which
    exists only in the adopter repo — would never appear."""
    adopter = tmp_path / "adopter-repo"
    _init_repo(adopter)
    monkeypatch.chdir(adopter)

    result = build_changed_file_audit_result(
        base_ref="HEAD~1",
        head_ref="HEAD",
        domains=["governance"],
        subsystem="pim",
        standards_version="2026-04-11",
    )

    assert result["changed_paths"] == ["docs/enhancements/ENH-001-pim-enrichment.md"]
    assert result["audit_result"]["scope"]["area_id"] == "pim-enrichment"


def test_resolve_audit_repo_root_rejects_non_git_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    monkeypatch.chdir(plain)

    with pytest.raises(RepoRootResolutionError):
        build_changed_file_audit_result(
            base_ref="HEAD~1",
            head_ref="HEAD",
            domains=["governance"],
            subsystem="pim",
            standards_version="2026-04-11",
        )


def test_resolve_audit_repo_root_rejects_cwd_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Standing in repo A but pointing --repo-root at repo B must fail loudly —
    the exact wrong-repo footgun (and content extraction would read the wrong
    tree)."""
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    _init_repo(repo_a)
    _init_repo(repo_b)
    monkeypatch.chdir(repo_a)

    with pytest.raises(RepoRootResolutionError):
        build_changed_file_audit_result(
            base_ref="HEAD~1",
            head_ref="HEAD",
            domains=["governance"],
            subsystem="pim",
            standards_version="2026-04-11",
            repo_root=repo_b,
        )


def test_resolve_audit_repo_root_rejects_missing_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "single-commit"
    _init_repo(repo, second_commit=False)
    monkeypatch.chdir(repo)

    with pytest.raises(RepoRootResolutionError):
        build_changed_file_audit_result(
            base_ref="HEAD~5",
            head_ref="HEAD",
            domains=["governance"],
            subsystem="pim",
            standards_version="2026-04-11",
        )


def test_resolve_audit_repo_root_returns_toplevel_from_subdir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resolution normalises to the git toplevel even when invoked from a
    subdirectory, and the cwd/root match check passes."""
    repo = tmp_path / "adopter-repo"
    _init_repo(repo)
    subdir = repo / "docs" / "enhancements"
    monkeypatch.chdir(subdir)

    resolved = resolve_audit_repo_root(base_ref="HEAD~1", head_ref="HEAD")
    assert resolved == repo.resolve()


def test_build_changed_file_audit_result_explicit_changed_paths_honours_repo_root(
    tmp_path: Path,
) -> None:
    """The explicit-changed_paths branch (no git diff) must extract file content
    from an explicit repo_root, not the SCP checkout. The ENH spec exists ONLY
    under `other`, so a correct extraction infers its area; falling back to
    project_root() would raise FileNotFoundError instead."""
    other = tmp_path / "other-repo"
    enh_dir = other / "docs" / "enhancements"
    enh_dir.mkdir(parents=True)
    (enh_dir / "ENH-001-pim-enrichment.md").write_text("# spec\n", encoding="utf-8")

    result = build_changed_file_audit_result(
        base_ref="base",
        head_ref="head",
        domains=["governance"],
        subsystem="pim",
        standards_version="2026-04-11",
        changed_paths=["docs/enhancements/ENH-001-pim-enrichment.md"],
        repo_root=other,
    )

    assert result["changed_paths"] == ["docs/enhancements/ENH-001-pim-enrichment.md"]
    assert result["audit_result"]["scope"]["area_id"] == "pim-enrichment"
