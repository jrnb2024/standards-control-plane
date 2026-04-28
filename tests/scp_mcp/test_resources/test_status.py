from __future__ import annotations

from pathlib import Path

from .conftest import commit_file


def test_status_resource_parses_markdown_and_filters_wp_merges(resource_repo: Path, fixed_now) -> None:
    from standards_control_plane.mcp_server.resources import ScpCommittedResourceCatalog

    commit_file(
        resource_repo,
        "docs/STATUS.md",
        "\n".join(
            [
                "# Status",
                "",
                "**Last Updated:** 2026-04-29",
                "**Current Branch:** `feature/wp-scp-021d-fix-round-1`",
                "**Current Work Package:** `WP-SCP-022`",
                "**Current State:** Fix round active",
                "",
                "## Summary",
                "",
                "- correctness fixes committed",
                "- governance checks expanded",
                "",
            ]
        ),
        "WP-SCP-022 slice test",
    )
    commit_file(
        resource_repo,
        "docs/notes.txt",
        "non-WP commit\n",
        "docs: ignore for status history",
    )

    catalog = ScpCommittedResourceCatalog(repo_root=resource_repo, now_func=lambda: fixed_now)
    payload = catalog.read_static("scp://status")

    assert payload["schema_version"] == "1.0.0"
    assert payload["key_id"] == "scp-mcp-2026-04"
    assert payload["status"] == {
        "last_updated": "2026-04-29",
        "current_branch": "`feature/wp-scp-021d-fix-round-1`",
        "current_work_package": "`WP-SCP-022`",
        "current_state": "Fix round active",
        "summary": ["correctness fixes committed", "governance checks expanded"],
    }
    assert [entry["subject"] for entry in payload["recent_wp_merges"]] == ["WP-SCP-022 slice test"]
