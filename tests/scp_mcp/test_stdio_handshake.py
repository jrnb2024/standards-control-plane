from __future__ import annotations

import asyncio
import json

from standards_control_plane.mcp_server.resources import STATIC_RESOURCE_URIS
from standards_control_plane.mcp_server.server import ScpMcpServer

from .conftest import run_scp_mcp_server


def test_stdio_test_lists_tools_and_resources() -> None:
    result = run_scp_mcp_server("--stdio-test")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert {tool["name"] for tool in payload["tools"]} == {
        "consult_rules",
        "check_waiver",
        "list_open_decisions",
        "check_finding",
        "audit_changed",
        "resolve_domain",
        "propose",
        "consult_scorecard",
    }
    assert {resource["uri"] for resource in payload["resources"]} == set(STATIC_RESOURCE_URIS)


def test_server_instructions_describe_registered_surface() -> None:
    instructions = ScpMcpServer().instructions

    assert "consult_rules" in instructions
    assert "scp://rules/registry" in instructions
    assert "docs/integrations/mcp-error-codes.md" in instructions


def test_estate_read_only_profile_lists_only_bounded_read_tools() -> None:
    payload = asyncio.run(ScpMcpServer(profile="estate-read-only").handshake_payload())

    assert {tool["name"] for tool in payload["tools"]} == {
        "consult_rules",
        "check_waiver",
        "list_open_decisions",
        "check_finding",
        "resolve_domain",
        "consult_scorecard",
    }
    assert "propose" not in {tool["name"] for tool in payload["tools"]}
    assert "audit_changed" not in {tool["name"] for tool in payload["tools"]}
    assert payload["server"]["profile"] == "estate-read-only"
    assert {resource["uri"] for resource in payload["resources"]} == set(STATIC_RESOURCE_URIS)
    assert "no action authority" in ScpMcpServer(profile="estate-read-only").instructions
