from __future__ import annotations

import json
import subprocess
from pathlib import Path

from standards_control_plane.changed_audit import (
    build_changed_file_audit_result,
    list_changed_files,
)
from standards_control_plane.schema_tools import validate_with_schema


def test_list_changed_files_returns_repo_relative_paths_from_temp_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=repo, check=True)

    tracked = repo / "tracked.txt"
    tracked.write_text("one\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True, text=True
    )

    tracked.write_text("two\n", encoding="utf-8")
    deleted = repo / "deleted.txt"
    deleted.write_text("gone\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt", "deleted.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "second"], cwd=repo, check=True, capture_output=True, text=True)
    deleted.unlink()
    subprocess.run(["git", "rm", "deleted.txt"], cwd=repo, check=True, capture_output=True, text=True)

    changed = list_changed_files(base_ref="HEAD~1", head_ref="HEAD", repo_root=repo)
    assert changed == ["tracked.txt"]


def _init_adopter_repo(tmp_path: Path) -> Path:
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


def test_build_changed_file_audit_result_supports_external_repo_root(tmp_path: Path) -> None:
    repo = _init_adopter_repo(tmp_path)

    result = build_changed_file_audit_result(
        base_ref="HEAD~1",
        head_ref="HEAD",
        domains=["architecture"],
        subsystem="mapp-pim",
        standards_version="2026-04-12",
        repo_root=repo,
    )

    validate_with_schema(result, "changed-audit-result.schema.json")
    assert result["changed_paths"] == ["services/enrichment/pipeline.py"]
    assert result["audit_result"]["scope"]["area_id"] == "mapp-pim-services"


def test_build_changed_file_audit_result_derives_area_id_when_uninferable() -> None:
    # Paths with no ENH spec and no frontend route must fall back to a
    # deterministic subsystem-derived area instead of raising
    # AreaIdInferenceError (paths resolved inside the SCP repo itself).
    result = build_changed_file_audit_result(
        base_ref="base",
        head_ref="head",
        domains=["governance"],
        subsystem="standards-control-plane",
        standards_version="2026-04-12",
        changed_paths=["docs/DECISIONS.md"],
    )

    assert result["audit_result"]["scope"]["area_id"] == "standards-control-plane-docs"


def test_build_changed_file_audit_result_reads_adopter_review_evidence(tmp_path: Path) -> None:
    # Governance audits must resolve review-evidence paths against the
    # external worktree, not the SCP repo (where they don't exist).
    repo = _init_adopter_repo(tmp_path)
    evidence = repo / "docs" / "reviews" / "WP-X" / "review_findings.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("# Review\n\nNo structured block.\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "evidence"], cwd=repo, check=True, capture_output=True, text=True
    )

    result = build_changed_file_audit_result(
        base_ref="HEAD~1",
        head_ref="HEAD",
        domains=["governance"],
        subsystem="mapp-pim",
        standards_version="2026-04-12",
        repo_root=repo,
    )

    assert result["changed_paths"] == ["docs/reviews/WP-X/review_findings.md"]
    assert result["audit_result"]["domain_status"]["governance"]["status"] == "evaluated"


def test_cli_audit_changed_accepts_repo_root(tmp_path: Path, capsys) -> None:
    from standards_control_plane.cli import build_parser

    repo = _init_adopter_repo(tmp_path)
    parser = build_parser()
    args = parser.parse_args(
        [
            "audit-changed",
            "--base-ref",
            "HEAD~1",
            "--head-ref",
            "HEAD",
            "--domains",
            "architecture",
            "--subsystem",
            "mapp-pim",
            "--standards-version",
            "2026-04-12",
            "--repo-root",
            str(repo),
        ]
    )

    assert args.func(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["changed_paths"] == ["services/enrichment/pipeline.py"]


def test_cli_audit_changed_refuses_write_output_for_external_repo_root(
    tmp_path: Path, capsys
) -> None:
    from standards_control_plane.cli import build_parser

    repo = _init_adopter_repo(tmp_path)
    parser = build_parser()
    args = parser.parse_args(
        [
            "audit-changed",
            "--base-ref",
            "HEAD~1",
            "--head-ref",
            "HEAD",
            "--domains",
            "architecture",
            "--subsystem",
            "mapp-pim",
            "--standards-version",
            "2026-04-12",
            "--repo-root",
            str(repo),
            "--write-output",
        ]
    )

    assert args.func(args) == 2
    captured = capsys.readouterr()
    assert "--write-output is not supported with an external --repo-root" in captured.err
    assert captured.out == ""


def test_cli_audit_changed_rejects_repo_root_that_is_not_a_worktree_root(
    tmp_path: Path, capsys
) -> None:
    from standards_control_plane.cli import build_parser

    repo = _init_adopter_repo(tmp_path)
    parser = build_parser()
    args = parser.parse_args(
        [
            "audit-changed",
            "--base-ref",
            "HEAD~1",
            "--head-ref",
            "HEAD",
            "--domains",
            "architecture",
            "--subsystem",
            "mapp-pim",
            "--standards-version",
            "2026-04-12",
            "--repo-root",
            str(repo / "services"),
        ]
    )

    assert args.func(args) == 2
    captured = capsys.readouterr()
    assert "must be the root of a git worktree" in captured.err


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
