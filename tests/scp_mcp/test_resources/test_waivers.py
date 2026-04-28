from __future__ import annotations


def test_waivers_resource_filters_expired_waivers(resource_catalog) -> None:
    payload = resource_catalog.read_static("scp://waivers")

    assert payload["schema_version"] == "1.0.0"
    assert [waiver["waiver_id"] for waiver in payload["waivers"]] == ["W-001"]
