"""WP-SCP-023 023D / D-043: scp.consult_scorecard MCP method tests.

Verifies that the read-only consult method:
- Reads `output/scorecards/index.json` correctly.
- Filters by repo_filter / since_emitted_at.
- NEVER returns waiver content (`reason` / `approved_by` / `waiver_id`)
  per WP-SCP-023 plan-doc invariant 2.
- Handles failure modes (missing index, malformed index, malformed
  rows) loudly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from standards_control_plane.mcp_server import tools


REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def empty_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    index = {
        "schema_version": "0.1",
        "aggregated_at": "1970-01-01T00:00:00Z",
        "aggregator_run_id": 0,
        "adopters": [],
    }
    out_dir = tmp_path / "output" / "scorecards"
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "index.json"
    p.write_text(json.dumps(index), encoding="utf-8")
    monkeypatch.setattr(tools, "project_root", lambda: tmp_path)
    return p


@pytest.fixture
def single_verified_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    index = {
        "schema_version": "0.1",
        "aggregated_at": "2026-05-03T06:00:00Z",
        "aggregator_run_id": 99999,
        "adopters": [
            {
                "repo": "jrnb2024/example-adopter",
                "status": "verified",
                "last_emit_run_id": 12345,
                "last_emit_commit": "1111111111111111111111111111111111111111",
                "last_emit_emitted_at": "2026-05-03T05:30:00Z",
                "verdict": "allow",
                "rule_counts": {
                    "SCP-R-001": {"raw_findings": 0, "denies": 0, "waived": 0, "rule_config_disabled": False}
                },
                "waivers_aggregate": {"active_count": 0, "by_rule_id": {}, "expiring_within_30d": 0},
                "rule_config_aggregate": {"disabled_rules": [], "expiring_within_30d": 0},
                "scp_version": "1.2.0",
                "ref": "main",
            }
        ],
    }
    out_dir = tmp_path / "output" / "scorecards"
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "index.json"
    p.write_text(json.dumps(index), encoding="utf-8")
    monkeypatch.setattr(tools, "project_root", lambda: tmp_path)
    return p


@pytest.fixture
def multi_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    index = {
        "schema_version": "0.1",
        "aggregated_at": "2026-05-03T06:00:00Z",
        "aggregator_run_id": 99999,
        "adopters": [
            {
                "repo": "jrnb2024/adopter-a",
                "status": "verified",
                "last_emit_run_id": 1,
                "last_emit_commit": "a" * 40,
                "last_emit_emitted_at": "2026-05-03T05:30:00Z",
                "verdict": "allow",
                "rule_counts": {},
                "waivers_aggregate": {"active_count": 0, "by_rule_id": {}, "expiring_within_30d": 0},
                "rule_config_aggregate": {"disabled_rules": [], "expiring_within_30d": 0},
                "scp_version": "1.2.0",
                "ref": "main",
            },
            {
                "repo": "jrnb2024/adopter-b",
                "status": "verification_failure",
                "last_emit_run_id": 2,
                "last_emit_commit": "b" * 40,
                "error": "gh attestation verify failed: signing-workflow mismatch",
            },
            {
                "repo": "jrnb2024/adopter-c",
                "status": "unreachable",
                "error": "gh run list exited 1: rate limit",
            },
        ],
    }
    out_dir = tmp_path / "output" / "scorecards"
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "index.json"
    p.write_text(json.dumps(index), encoding="utf-8")
    monkeypatch.setattr(tools, "project_root", lambda: tmp_path)
    return p


def test_empty_index_returns_empty_adopters(empty_index: Path) -> None:
    response = tools.consult_scorecard_impl(tools.ConsultScorecardRequest())
    assert isinstance(response, tools.ConsultScorecardResponse)
    assert response.aggregated_at == "1970-01-01T00:00:00Z"
    assert response.aggregator_run_id == 0
    assert response.adopters == []


def test_single_verified_returns_full_row(single_verified_index: Path) -> None:
    response = tools.consult_scorecard_impl(tools.ConsultScorecardRequest())
    assert isinstance(response, tools.ConsultScorecardResponse)
    assert len(response.adopters) == 1
    row = response.adopters[0]
    assert row.repo == "jrnb2024/example-adopter"
    assert row.status == "verified"
    assert row.verdict == "allow"
    assert row.scp_version == "1.2.0"
    assert row.last_emit_emitted_at == "2026-05-03T05:30:00Z"
    assert len(row.rule_counts) == 1
    assert row.rule_counts[0].rule_id == "SCP-R-001"


def test_repo_filter(multi_index: Path) -> None:
    response = tools.consult_scorecard_impl(
        tools.ConsultScorecardRequest(repo_filter="jrnb2024/adopter-b")
    )
    assert isinstance(response, tools.ConsultScorecardResponse)
    assert len(response.adopters) == 1
    assert response.adopters[0].repo == "jrnb2024/adopter-b"
    assert response.adopters[0].status == "verification_failure"


def test_since_emitted_at_filter_keeps_recent(multi_index: Path) -> None:
    # Filter to emits >= 2026-05-03T05:00:00Z; only adopter-a has an
    # emitted_at, and it's 05:30 ≥ 05:00 → kept.
    response = tools.consult_scorecard_impl(
        tools.ConsultScorecardRequest(since_emitted_at="2026-05-03T05:00:00Z")
    )
    assert isinstance(response, tools.ConsultScorecardResponse)
    repos = {a.repo for a in response.adopters}
    assert "jrnb2024/adopter-a" in repos
    # adopter-b has no emitted_at → kept (don't silently drop on
    # missing timestamp; the helper returns True when emit_at is None)
    assert "jrnb2024/adopter-b" in repos


def test_missing_index_returns_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools, "project_root", lambda: tmp_path)
    response = tools.consult_scorecard_impl(tools.ConsultScorecardRequest())
    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-SCORECARD-001"


def test_malformed_index_returns_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out_dir = tmp_path / "output" / "scorecards"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.json").write_text("{ malformed json", encoding="utf-8")
    monkeypatch.setattr(tools, "project_root", lambda: tmp_path)
    response = tools.consult_scorecard_impl(tools.ConsultScorecardRequest())
    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-SCORECARD-002"


def test_response_excludes_waiver_content(multi_index: Path) -> None:
    """Per WP-SCP-023 plan-doc invariant 2: the MCP response NEVER
    carries waiver content (`reason` / `approved_by` / `waiver_id`
    strings). The Pydantic model excludes these fields by construction;
    this test serializes the response + scans for the forbidden keys to
    catch a future schema-drift mistake.
    """
    response = tools.consult_scorecard_impl(tools.ConsultScorecardRequest())
    assert isinstance(response, tools.ConsultScorecardResponse)
    raw = response.model_dump_json()
    for forbidden in ('"reason"', '"approved_by"', '"waiver_id"'):
        assert forbidden not in raw, (
            f"WP-SCP-023 plan-doc invariant 2 violation: "
            f"consult_scorecard response contains forbidden key {forbidden}"
        )


def test_invalid_repo_filter_rejected_by_pydantic() -> None:
    """The Pydantic model's `pattern` constraint rejects malformed
    repo filters at request-build time (no impl call needed)."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        tools.ConsultScorecardRequest(repo_filter="not a valid repo")


def test_unknown_schema_version_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Closes 023D R1 COR-MAJ-001: index with unknown schema_version
    must be rejected (not silently processed)."""
    index = {
        "schema_version": "999.0",
        "aggregated_at": "2026-05-03T06:00:00Z",
        "aggregator_run_id": 1,
        "adopters": [],
    }
    out_dir = tmp_path / "output" / "scorecards"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.json").write_text(json.dumps(index), encoding="utf-8")
    monkeypatch.setattr(tools, "project_root", lambda: tmp_path)
    response = tools.consult_scorecard_impl(tools.ConsultScorecardRequest())
    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-SCORECARD-004"


def test_register_tools_includes_consult_scorecard() -> None:
    """The new method is registered on the FastMCP server."""

    class _ServerStub:
        def __init__(self) -> None:
            self.registered: list[str] = []

        def tool(self, *, name: str, structured_output: bool = False):
            def decorator(fn):
                self.registered.append(name)
                return fn
            return decorator

    stub = _ServerStub()
    tools.register_tools(stub)  # type: ignore[arg-type]
    assert "consult_scorecard" in stub.registered
