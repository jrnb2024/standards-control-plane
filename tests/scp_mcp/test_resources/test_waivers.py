from __future__ import annotations


def test_waivers_resource_filters_expired_waivers(resource_catalog) -> None:
    payload = resource_catalog.read_static("scp://waivers")

    assert payload["schema_version"] == "1.0.0"
    assert payload["key_id"] == "scp-mcp-2026-04"
    assert [waiver["waiver_id"] for waiver in payload["waivers"]] == ["W-001"]
    assert payload["waivers"][0]["active"] is True
