from __future__ import annotations

import json
from pathlib import Path

from standards_control_plane.mcp_server import tools


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_check_finding_returns_matching_record(tmp_path: Path) -> None:
    findings_dir = tmp_path / "findings"
    _write_json(
        findings_dir / "open-findings.json",
        {
            "store_version": "0.1.0",
            "generated_at": "2026-04-28T12:00:00Z",
            "findings": [
                {
                    "finding_id": "F-LOOKUP-001",
                    "rule_id": "GOV-001",
                    "domain": "governance",
                    "severity": "high",
                    "summary": "Scope mismatch",
                    "status": "open",
                    "area_id": "mcp-slice",
                }
            ],
        },
    )

    response = tools.check_finding_impl(
        tools.CheckFindingRequest(finding_id="F-LOOKUP-001"),
        findings_dir=findings_dir,
    )

    assert isinstance(response, tools.CheckFindingResponse)
    assert response.finding["rule_id"] == "GOV-001"


def test_check_finding_returns_not_found_error(tmp_path: Path) -> None:
    findings_dir = tmp_path / "findings"
    _write_json(findings_dir / "open-findings.json", {"findings": []})

    response = tools.check_finding_impl(
        tools.CheckFindingRequest(finding_id="F-LOOKUP-404"),
        findings_dir=findings_dir,
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E022"
