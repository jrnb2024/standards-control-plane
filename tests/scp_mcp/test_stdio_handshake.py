from __future__ import annotations

import asyncio
import json

import pytest

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


@pytest.mark.parametrize("gated_tool", ["propose", "audit_changed"])
def test_estate_read_only_profile_rejects_gated_tool_invocation(gated_tool: str) -> None:
    # The listing test above only proves propose/audit_changed are ABSENT from
    # the estate handshake surface. This proves they are also unreachable at
    # CALL time: register_tools(profile="estate-read-only") never binds them, so
    # FastMCP's dispatcher rejects the invocation as an unknown tool BEFORE any
    # implementation runs. The regex is load-bearing — a *registered* action
    # tool invoked with empty args raises a *different* ToolError ("Error
    # executing tool ...: validation error"), so if the estate profile ever
    # leaked action authority by registering these tools, this test would fail
    # on the mismatched message rather than pass on a validation error.
    from mcp.server.fastmcp.exceptions import ToolError

    server = ScpMcpServer(profile="estate-read-only").server

    with pytest.raises(ToolError, match=rf"Unknown tool: {gated_tool}"):
        asyncio.run(server.call_tool(gated_tool, {}))


def test_legacy_profile_still_dispatches_gated_tools() -> None:
    # Counterpart / anti-vacuity guard for the estate rejection test above:
    # confirms propose and audit_changed ARE reachable under the default legacy
    # profile, so the estate rejection is a profile-scoped restriction rather
    # than these tools being globally unregistered (which would make the
    # rejection test pass for the wrong reason).
    from mcp.server.fastmcp.exceptions import ToolError

    server = ScpMcpServer(profile="legacy").server

    for legacy_tool in ("propose", "audit_changed"):
        # Empty args reach the tool and fail argument validation — proving the
        # tool is bound and dispatched, not rejected as unknown.
        with pytest.raises(ToolError, match=rf"Error executing tool {legacy_tool}"):
            asyncio.run(server.call_tool(legacy_tool, {}))
