from __future__ import annotations

import json
from pathlib import Path

import pytest

from standards_control_plane.audit import build_audit_result
from standards_control_plane.findings import persist_audit_findings
from standards_control_plane.resources import examples_dir
from standards_control_plane.schema_tools import load_json_file, validate_with_schema
from standards_control_plane.scoring import finding_penalty, score_findings


def _write_waivers(path: Path, payload: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _example_request(*, standards_version: str = "2026-04-11") -> dict[str, object]:
    request = load_json_file(examples_dir() / "audit-request.json")
    request["standards_version"] = standards_version
    return request


def test_build_audit_result_applies_active_waiver_and_updates_score(tmp_path: Path) -> None:
    waivers_path = _write_waivers(
        tmp_path / "waivers.json",
        [
            {
                "waiver_id": "W-0001",
                "finding_id": "F-ARCH-002-returns-exceptions",
                "reason": "Temporary exception during migration",
                "approved_by": "team-lead",
                "expires_at": "2026-06-30T00:00:00Z",
                "created_at": "2026-04-11T16:20:00Z",
            }
        ],
    )

    result = build_audit_result(_example_request(), waivers_path=waivers_path)

    validate_with_schema(result, "audit-result.schema.json")
    statuses = {finding["finding_id"]: finding["status"] for finding in result["findings"]}
    assert statuses == {
        "F-ARCH-001-returns-exceptions": "open",
        "F-ARCH-002-returns-exceptions": "waived",
        "F-ARCH-003-returns-exceptions": "open",
    }
    assert result["waivers_applied"] == [
        {
            "waiver_id": "W-0001",
            "finding_id": "F-ARCH-002-returns-exceptions",
            "reason": "Temporary exception during migration",
            "approved_by": "team-lead",
            "expires_at": "2026-06-30T00:00:00Z",
            "created_at": "2026-04-11T16:20:00Z",
        }
    ]
    assert result["summary"] == {
        "high_severity_count": 1,
        "medium_severity_count": 1,
        "low_severity_count": 0,
        "waived_count": 1,
    }
    assert result["scores"] == {"architecture": 55, "governance": 100}
    assert result["recommended_actions"] == [
        "Route cross-boundary work through the approved integration seam instead of importing bounded implementation modules directly.",
        "Move remote-access setup behind the approved service abstraction for the subsystem.",
    ]


def test_build_audit_result_treats_missing_waivers_file_as_empty(tmp_path: Path) -> None:
    result = build_audit_result(_example_request(), waivers_path=tmp_path / "missing-waivers.json")
    assert result == load_json_file(examples_dir() / "audit-result.json")


def test_build_audit_result_orders_applied_waivers_deterministically(tmp_path: Path) -> None:
    waivers_path = _write_waivers(
        tmp_path / "waivers.json",
        [
            {
                "waiver_id": "W-0007",
                "finding_id": "F-ARCH-003-returns-exceptions",
                "reason": "Later in file",
                "approved_by": "team-lead",
                "expires_at": "2026-06-30T00:00:00Z",
                "created_at": "2026-04-11T16:30:00Z",
            },
            {
                "waiver_id": "W-0006",
                "finding_id": "F-ARCH-001-returns-exceptions",
                "reason": "Earlier finding id",
                "approved_by": "team-lead",
                "expires_at": "2026-06-30T00:00:00Z",
                "created_at": "2026-04-11T16:25:00Z",
            },
        ],
    )

    result = build_audit_result(_example_request(), waivers_path=waivers_path)
    assert [waiver["finding_id"] for waiver in result["waivers_applied"]] == [
        "F-ARCH-001-returns-exceptions",
        "F-ARCH-003-returns-exceptions",
    ]


def test_build_audit_result_ignores_expired_waiver(tmp_path: Path) -> None:
    waivers_path = _write_waivers(
        tmp_path / "waivers.json",
        [
            {
                "waiver_id": "W-0002",
                "finding_id": "F-ARCH-002-returns-exceptions",
                "reason": "Expired exception",
                "approved_by": "team-lead",
                "expires_at": "2026-04-10T23:59:59Z",
                "created_at": "2026-04-10T12:00:00Z",
            }
        ],
    )

    result = build_audit_result(_example_request(), waivers_path=waivers_path)
    statuses = {finding["finding_id"]: finding["status"] for finding in result["findings"]}
    assert statuses["F-ARCH-002-returns-exceptions"] == "open"
    assert result["waivers_applied"] == []
    assert result["scores"] == {"architecture": 25, "governance": 100}


def test_build_audit_result_rejects_overlapping_active_waivers(tmp_path: Path) -> None:
    waivers_path = _write_waivers(
        tmp_path / "waivers.json",
        [
            {
                "waiver_id": "W-0003",
                "finding_id": "F-ARCH-002-returns-exceptions",
                "reason": "Migration",
                "approved_by": "team-lead",
                "expires_at": "2026-06-30T00:00:00Z",
                "created_at": "2026-04-11T16:20:00Z",
            },
            {
                "waiver_id": "W-0004",
                "finding_id": "F-ARCH-002-returns-exceptions",
                "reason": "Second active waiver",
                "approved_by": "director",
                "expires_at": "2026-07-15T00:00:00Z",
                "created_at": "2026-04-11T16:25:00Z",
            },
        ],
    )

    with pytest.raises(ValueError, match="Multiple active waivers"):
        build_audit_result(_example_request(), waivers_path=waivers_path)


def test_waived_finding_reopens_after_waiver_expiry(tmp_path: Path) -> None:
    findings_dir = tmp_path / "findings"
    waivers_path = _write_waivers(
        tmp_path / "waivers.json",
        [
            {
                "waiver_id": "W-0005",
                "finding_id": "F-ARCH-002-returns-exceptions",
                "reason": "Short-lived exception",
                "approved_by": "team-lead",
                "expires_at": "2026-04-11T23:59:59Z",
                "created_at": "2026-04-11T16:20:00Z",
            }
        ],
    )

    first_result = build_audit_result(
        _example_request(standards_version="2026-04-11"),
        waivers_path=waivers_path,
    )
    first_open, first_history = persist_audit_findings(first_result, findings_dir=findings_dir)
    assert [finding.finding_id for finding in first_open.findings] == [
        "F-ARCH-001-returns-exceptions",
        "F-ARCH-003-returns-exceptions",
    ]
    first_history_by_id = {finding.finding_id: finding for finding in first_history.findings}
    assert first_history_by_id["F-ARCH-002-returns-exceptions"].status == "waived"

    second_result = build_audit_result(
        _example_request(standards_version="2026-04-12"),
        waivers_path=waivers_path,
    )
    second_open, second_history = persist_audit_findings(second_result, findings_dir=findings_dir)
    assert [finding.finding_id for finding in second_open.findings] == [
        "F-ARCH-001-returns-exceptions",
        "F-ARCH-002-returns-exceptions",
        "F-ARCH-003-returns-exceptions",
    ]
    second_history_by_id = {finding.finding_id: finding for finding in second_history.findings}
    assert second_history_by_id["F-ARCH-002-returns-exceptions"].status == "open"
    assert second_history_by_id["F-ARCH-002-returns-exceptions"].updated_at == "2026-04-12T00:00:00Z"


def test_score_findings_ignores_non_open_statuses_and_clamps_to_zero() -> None:
    findings = [
        {"severity": "critical", "status": "open"},
        {"severity": "high", "status": "open"},
        {"severity": "medium", "status": "waived"},
        {"severity": "low", "status": "resolved"},
        {"severity": "critical", "status": "open"},
    ]
    assert finding_penalty(findings[0]) == 40
    assert finding_penalty(findings[2]) == 0
    assert score_findings(findings) == 0
