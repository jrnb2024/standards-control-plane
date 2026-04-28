from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from .conftest import create_resource_repo


def test_findings_open_returns_only_unwaived_open_findings(resource_catalog) -> None:
    payload = resource_catalog.read_static("scp://findings/open")
    finding_ids = [finding["finding_id"] for finding in payload["findings"]]

    assert payload["schema_version"] == "1.0.0"
    assert payload["key_id"] == "scp-mcp-2026-04"
    assert finding_ids == ["F-OPEN-001", "F-OPEN-003"]


def test_findings_open_ignores_waivers_file_even_when_entries_look_like_findings(tmp_path: Path, fixed_now) -> None:
    from standards_control_plane.mcp_server.resources import ScpCommittedResourceCatalog

    resource_repo = create_resource_repo(
        tmp_path,
        extra_files={
            "output/findings/waivers.json": json.dumps(
                [
                    {
                        "waiver_id": "W-001",
                        "finding_id": "F-OPEN-002",
                        "rule_id": "ARCH-001",
                        "reason": "Temporary exception",
                        "approved_by": "@owner",
                        "expires_at": "2026-05-10T00:00:00Z",
                    },
                    {
                        "waiver_id": "W-LOOKALIKE",
                        "finding_id": "F-WAIVER-ONLY",
                        "rule_id": "ARCH-001",
                        "domain": "architecture",
                        "severity": "high",
                        "summary": "Should never be treated as a finding",
                        "status": "open",
                        "reason": "Still a waiver",
                        "approved_by": "@owner",
                        "expires_at": "2026-05-10T00:00:00Z",
                    },
                ],
                indent=2,
            )
            + "\n"
        },
    )
    catalog = ScpCommittedResourceCatalog(repo_root=resource_repo, now_func=lambda: fixed_now)

    payload = catalog.read_static("scp://findings/open")

    assert [finding["finding_id"] for finding in payload["findings"]] == ["F-OPEN-001", "F-OPEN-003"]
    with pytest.raises(KeyError, match="unknown finding resource"):
        catalog.read_finding("F-WAIVER-ONLY")


def test_snapshot_uses_one_timestamp_for_waivers_and_findings(tmp_path: Path) -> None:
    from standards_control_plane.mcp_server.resources import ScpCommittedResourceCatalog

    expiry = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    resource_repo = create_resource_repo(
        tmp_path,
        extra_files={
            "output/findings/waivers.json": json.dumps(
                [
                    {
                        "waiver_id": "W-BOUNDARY",
                        "finding_id": "F-OPEN-002",
                        "rule_id": "ARCH-001",
                        "reason": "Boundary test",
                        "approved_by": "@owner",
                        "expires_at": expiry.isoformat().replace("+00:00", "Z"),
                    }
                ],
                indent=2,
            )
            + "\n"
        },
    )

    call_times = [
        expiry - timedelta(seconds=1),
        expiry + timedelta(seconds=1),
    ]

    def now_func() -> datetime:
        index = min(now_func.calls, len(call_times) - 1)
        now = call_times[index]
        now_func.calls += 1
        return now

    now_func.calls = 0
    catalog = ScpCommittedResourceCatalog(repo_root=resource_repo, now_func=now_func)

    waivers = catalog.read_static("scp://waivers")
    findings = catalog.read_static("scp://findings/open")

    assert now_func.calls == 1
    assert [waiver["waiver_id"] for waiver in waivers["waivers"]] == ["W-BOUNDARY"]
    assert [finding["finding_id"] for finding in findings["findings"]] == ["F-OPEN-001", "F-OPEN-003"]
