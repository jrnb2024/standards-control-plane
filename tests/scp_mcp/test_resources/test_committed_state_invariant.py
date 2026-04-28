from __future__ import annotations

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

    assert [decision["decision_id"] for decision in before["decisions"]] == ["D-024", "D-028"]
    assert after == before
