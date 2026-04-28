from __future__ import annotations

import json

from .conftest import run_scp_mcp_server


def test_stdio_test_lists_empty_tools_and_resources() -> None:
    result = run_scp_mcp_server("--stdio-test")
    assert result.returncode == 0, result.stderr
    assert '"resources": []' in result.stdout
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
    assert payload["resources"] == []
