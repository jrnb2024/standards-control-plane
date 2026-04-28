from __future__ import annotations

from standards_control_plane.mcp_server.resources import TEMPLATE_RESOURCE_URIS

from .conftest import list_server_resource_templates, read_server_resource


def test_per_id_resource_templates_are_registered(resource_server) -> None:
    assert list_server_resource_templates(resource_server) == sorted(TEMPLATE_RESOURCE_URIS)


def test_per_id_resources_route_to_expected_payloads(resource_server) -> None:
    rule = read_server_resource(resource_server, "scp://rule/GOV-001")
    waiver = read_server_resource(resource_server, "scp://waiver/W-001")
    expired_waiver = read_server_resource(resource_server, "scp://waiver/W-002")
    finding = read_server_resource(resource_server, "scp://finding/F-OPEN-001")
    decision = read_server_resource(resource_server, "scp://decision/D-1000")

    assert rule["schema_version"] == "1.0.0"
    assert rule["key_id"] == "scp-mcp-2026-04"
    assert rule["rule"]["rule_id"] == "GOV-001"
    assert rule["rule"]["body_markdown"].startswith("# GOV-001")
    assert waiver["schema_version"] == "1.0.0"
    assert waiver["key_id"] == "scp-mcp-2026-04"
    assert waiver["waiver"]["waiver_id"] == "W-001"
    assert waiver["waiver"]["active"] is True
    assert expired_waiver["waiver"]["waiver_id"] == "W-002"
    assert expired_waiver["waiver"]["active"] is False
    assert finding["schema_version"] == "1.0.0"
    assert finding["key_id"] == "scp-mcp-2026-04"
    assert finding["finding"]["finding_id"] == "F-OPEN-001"
    assert decision["schema_version"] == "1.0.0"
    assert decision["key_id"] == "scp-mcp-2026-04"
    assert decision["decision"]["decision_id"] == "D-1000"
