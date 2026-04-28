from __future__ import annotations

import subprocess
from pathlib import Path


def test_uncommitted_edits_are_not_visible(resource_repo: Path, fixed_now) -> None:
    from standards_control_plane.mcp_server.resources import ScpCommittedResourceCatalog

    catalog = ScpCommittedResourceCatalog(repo_root=resource_repo, now_func=lambda: fixed_now)
    before = catalog.read_static("scp://decisions")

    (resource_repo / "docs" / "DECISIONS.md").write_text(
        "\n".join(
            [
                "# Decisions",
                "",
                "| ID | Date | Decision | Status | Rationale |",
                "|----|------|----------|--------|-----------|",
                "| D-999 | 2026-04-28 | Uncommitted | ACCEPTED | Should stay hidden |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    after = catalog.read_static("scp://decisions")

    assert [decision["decision_id"] for decision in before["decisions"]] == ["D-024", "D-028", "D-1000"]
    assert after == before


def test_staged_edits_are_not_visible(resource_repo: Path, fixed_now) -> None:
    from standards_control_plane.mcp_server.resources import ScpCommittedResourceCatalog

    catalog = ScpCommittedResourceCatalog(repo_root=resource_repo, now_func=lambda: fixed_now)
    before = catalog.read_static("scp://decisions")

    decisions_path = resource_repo / "docs" / "DECISIONS.md"
    decisions_path.write_text(
        "\n".join(
            [
                "# Decisions",
                "",
                "| ID | Date | Decision | Status | Rationale |",
                "|----|------|----------|--------|-----------|",
                "| D-2000 | 2026-04-28 | Staged only | ACCEPTED | Must stay hidden |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "docs/DECISIONS.md"],
        cwd=resource_repo,
        check=True,
        capture_output=True,
        text=True,
    )

    after = catalog.read_static("scp://decisions")

    assert after == before


def test_uncommitted_waiver_edits_are_not_visible(resource_repo: Path, fixed_now) -> None:
    from standards_control_plane.mcp_server.resources import ScpCommittedResourceCatalog

    catalog = ScpCommittedResourceCatalog(repo_root=resource_repo, now_func=lambda: fixed_now)
    before = catalog.read_static("scp://waivers")

    (resource_repo / "output" / "findings" / "waivers.json").write_text("[]\n", encoding="utf-8")

    after = catalog.read_static("scp://waivers")

    assert after == before
