from __future__ import annotations


def test_findings_open_returns_only_unwaived_open_findings(resource_catalog) -> None:
    payload = resource_catalog.read_static("scp://findings/open")
    finding_ids = [finding["finding_id"] for finding in payload["findings"]]

    assert finding_ids == ["F-OPEN-001", "F-OPEN-003"]
