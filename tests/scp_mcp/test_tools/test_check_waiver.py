from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from standards_control_plane.mcp_server import tools


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_findings(findings_dir: Path) -> None:
    _write_json(
        findings_dir / "open-findings.json",
        {
            "store_version": "0.1.0",
            "generated_at": "2026-04-28T12:00:00Z",
            "findings": [
                {
                    "finding_id": "F-TEST-001",
                    "rule_id": "ARCH-001",
                    "domain": "architecture",
                    "severity": "high",
                    "summary": "Architecture boundary drift",
                    "status": "open",
                    "area_id": "returns-exceptions",
                }
            ],
        },
    )


def test_check_waiver_returns_active_match(tmp_path: Path) -> None:
    findings_dir = tmp_path / "findings"
    _seed_findings(findings_dir)
    waivers_path = findings_dir / "waivers.json"
    _write_json(
        waivers_path,
        [
            {
                "waiver_id": "waiver-001",
                "finding_id": "F-TEST-001",
                "reason": "Temporary exception",
                "approved_by": "@owner",
                "expires_at": "2026-05-02T00:00:00Z",
                "created_at": "2026-04-28T00:00:00Z",
            }
        ],
    )

    response = tools.check_waiver_impl(
        tools.CheckWaiverRequest(rule_id="ARCH-001", scope="returns-exceptions"),
        waivers_path=waivers_path,
        findings_dir=findings_dir,
        now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )

    assert isinstance(response, tools.CheckWaiverResponse)
    assert [match.waiver_id for match in response.active_waivers] == ["waiver-001"]


def test_check_waiver_ignores_expired_entries(tmp_path: Path) -> None:
    findings_dir = tmp_path / "findings"
    _seed_findings(findings_dir)
    waivers_path = findings_dir / "waivers.json"
    _write_json(
        waivers_path,
        [
            {
                "waiver_id": "waiver-001",
                "finding_id": "F-TEST-001",
                "reason": "Expired exception",
                "approved_by": "@owner",
                "expires_at": "2026-04-28T12:00:00Z",
                "created_at": "2026-04-27T00:00:00Z",
            }
        ],
    )

    response = tools.check_waiver_impl(
        tools.CheckWaiverRequest(rule_id="ARCH-001"),
        waivers_path=waivers_path,
        findings_dir=findings_dir,
        now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )

    assert isinstance(response, tools.CheckWaiverResponse)
    assert response.active_waivers == []


def test_check_waiver_returns_empty_for_unknown_rule(tmp_path: Path) -> None:
    findings_dir = tmp_path / "findings"
    _seed_findings(findings_dir)
    waivers_path = findings_dir / "waivers.json"
    _write_json(waivers_path, [])

    response = tools.check_waiver_impl(
        tools.CheckWaiverRequest(rule_id="ARCH-999"),
        waivers_path=waivers_path,
        findings_dir=findings_dir,
        now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )

    assert isinstance(response, tools.CheckWaiverResponse)
    assert response.active_waivers == []
