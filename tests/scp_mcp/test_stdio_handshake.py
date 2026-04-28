from __future__ import annotations

import json

from standards_control_plane.mcp_server.resources import STATIC_RESOURCE_URIS

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
    }
    assert {resource["uri"] for resource in payload["resources"]} == set(STATIC_RESOURCE_URIS)
