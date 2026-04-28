from __future__ import annotations

import pytest

from .conftest import resolve_scp_mcp_server, run_scp_mcp_server


@pytest.mark.parametrize(
    ("args", "expected_fragment"),
    [
        (["--help"], "Standards Control Plane MCP server"),
        (["serve", "--help"], "serve"),
        (["keygen", "--help"], "keygen"),
    ],
)
def test_cli_help_exits_zero(args: list[str], expected_fragment: str) -> None:
    assert resolve_scp_mcp_server()
    result = run_scp_mcp_server(*args)
    assert result.returncode == 0, result.stderr
    assert expected_fragment in result.stdout
