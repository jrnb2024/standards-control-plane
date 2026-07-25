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


def test_cli_refuses_estate_profile_when_feature_flag_is_off() -> None:
    result = run_scp_mcp_server("serve", "--profile", "estate-read-only")

    assert result.returncode == 2
    assert "SCP_ESTATE_READ_ONLY_ENABLED=true" in result.stderr
