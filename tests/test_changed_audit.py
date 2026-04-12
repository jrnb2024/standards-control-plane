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
