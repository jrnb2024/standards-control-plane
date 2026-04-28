from __future__ import annotations

from standards_control_plane.mcp_server import tools


def test_consult_rules_happy_path() -> None:
    response = tools.consult_rules_impl(
        tools.ConsultRulesRequest(
            domain="service-lifecycle",
            subsystem="service-lifecycle",
            area_id="svc-platform",
        )
    )

    assert isinstance(response, tools.ConsultRulesResponse)
    assert response.schema_version == "1.0.0"
    assert response.domains == ["service-lifecycle"]
    assert {"SVC-001", "SVC-002", "SVC-003"}.issubset(
        {rule.rule_id for rule in response.applicable_rules}
    )


def test_consult_rules_returns_missing_domain_error() -> None:
    response = tools.consult_rules_impl(
        tools.ConsultRulesRequest(domain="   ", subsystem="service-lifecycle", area_id="svc-platform")
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E021"


def test_consult_rules_returns_invalid_subsystem_error() -> None:
    response = tools.consult_rules_impl(
        tools.ConsultRulesRequest(
            domain="governance",
            subsystem="Bad Subsystem!",
            area_id="mcp-slice",
        )
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E021"
