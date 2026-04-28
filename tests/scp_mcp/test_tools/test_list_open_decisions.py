from __future__ import annotations

from pathlib import Path

from standards_control_plane.mcp_server import tools


def _write_decisions_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Decisions",
                "",
                "| ID | Date | Decision | Status | Rationale |",
                "|----|------|----------|--------|-----------|",
                "| D-100 | 2026-04-27 | Ship the thing | ACCEPTED | Needed for delivery |",
                "| D-101 | 2026-04-28 | Guard the thing | ACCEPTED | Needed for safety |",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_list_open_decisions_reads_table_rows(tmp_path: Path) -> None:
    decisions_path = tmp_path / "DECISIONS.md"
    _write_decisions_fixture(decisions_path)

    response = tools.list_open_decisions_impl(
        tools.ListOpenDecisionsRequest(),
        decisions_path=decisions_path,
    )

    assert isinstance(response, tools.ListOpenDecisionsResponse)
    assert [decision.decision_id for decision in response.decisions] == ["D-100", "D-101"]


def test_list_open_decisions_filters_by_since(tmp_path: Path) -> None:
    decisions_path = tmp_path / "DECISIONS.md"
    _write_decisions_fixture(decisions_path)

    response = tools.list_open_decisions_impl(
        tools.ListOpenDecisionsRequest(since="2026-04-28T00:00:00Z"),
        decisions_path=decisions_path,
    )

    assert isinstance(response, tools.ListOpenDecisionsResponse)
    assert [decision.decision_id for decision in response.decisions] == ["D-101"]


def test_list_open_decisions_returns_structured_error_for_malformed_dates(tmp_path: Path) -> None:
    decisions_path = tmp_path / "DECISIONS.md"
    decisions_path.write_text(
        "\n".join(
            [
                "# Decisions",
                "",
                "| ID | Date | Decision | Status | Rationale |",
                "|----|------|----------|--------|-----------|",
                "| D-100 | TBD | Ship the thing | ACCEPTED | Needed for delivery |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    response = tools.list_open_decisions_impl(
        tools.ListOpenDecisionsRequest(since="2026-04-28T00:00:00Z"),
        decisions_path=decisions_path,
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E021"
