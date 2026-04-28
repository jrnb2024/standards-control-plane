from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from standards_control_plane.mcp_server import tools


def test_propose_writes_incrementing_stub_file(tmp_path: Path) -> None:
    proposals_root = tmp_path / "docs" / "reviews" / "proposals"

    response = tools.propose_impl(
        tools.ProposeRequest(title="Add MCP policy", body="Queue this for later adjudication."),
        proposals_root=proposals_root,
        now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )

    assert isinstance(response, tools.ProposeResponse)
    assert response.proposal_id == "PROP-001"
    assert (proposals_root / "PROP-001.md").exists()


def test_propose_rejects_duplicate_normalised_content(tmp_path: Path) -> None:
    proposals_root = tmp_path / "docs" / "reviews" / "proposals"
    first = tools.propose_impl(
        tools.ProposeRequest(title="Add MCP policy", body="Queue this for later adjudication."),
        proposals_root=proposals_root,
        now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )
    assert isinstance(first, tools.ProposeResponse)

    duplicate = tools.propose_impl(
        tools.ProposeRequest(
            title="Add   MCP   policy",
            body="Queue this   for later adjudication.",
        ),
        proposals_root=proposals_root,
        now=datetime(2026, 4, 28, 12, 5, tzinfo=timezone.utc),
    )

    assert isinstance(duplicate, tools.ErrorResponse)
    assert duplicate.error_code == "SCP-MCP-E020"
