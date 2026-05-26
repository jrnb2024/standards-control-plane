"""Tests for standards_control_plane.scp_cli (WP-SCP-026 026B).

Unit tests use monkeypatching of subprocess.Popen to avoid real scp-mcp-server
startup. Integration paths (subprocess-actually-runs) live in
tests/scp_mcp/test_stdio_handshake.py via the existing harness.
"""

from __future__ import annotations

import io
import json
import subprocess
from typing import Any
from unittest.mock import MagicMock

import pytest

from standards_control_plane import scp_cli


def _mock_popen_returning(
    monkeypatch: pytest.MonkeyPatch,
    *,
    stdout: str,
    stderr: str = "",
    returncode: int = 0,
    raise_timeout: bool = False,
) -> MagicMock:
    """Patch subprocess.Popen to return a controlled handle."""
    handle = MagicMock()
    if raise_timeout:
        handle.communicate.side_effect = subprocess.TimeoutExpired(
            cmd="scp-mcp-server", timeout=25
        )
    else:
        handle.communicate.return_value = (stdout, stderr)
    handle.returncode = returncode
    factory = MagicMock(return_value=handle)
    monkeypatch.setattr(scp_cli.subprocess, "Popen", factory)
    return factory


def _tool_call_response_frame(consult_response_dict: dict[str, Any]) -> str:
    """Build a JSON-RPC tools/call response frame wrapping the given dict."""
    return json.dumps({
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "content": [
                {"type": "text", "text": json.dumps(consult_response_dict)},
            ]
        },
    })


def _stdout_with_handshake_then_tool_call(consult_response_dict: dict[str, Any]) -> str:
    """Simulate the MCP server's stdout: initialize_result + tools/call response."""
    init_result = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"protocolVersion": "2024-11-05", "capabilities": {}},
    })
    return init_result + "\n" + _tool_call_response_frame(consult_response_dict) + "\n"


@pytest.fixture
def sample_consult_response() -> dict[str, Any]:
    return {
        "schema_version": "scp-mcp.v1",
        "request_id": "abc-123",
        "domains": ["auth"],
        "approved_patterns": [],
        "open_findings": [],
        "historical_reviews": [],
        "applicable_rules": [
            {"rule_id": "SCP-R-001", "reason": "auth domain governance"}
        ],
        "guidance": ["consult before authoring"],
        "risks": [],
        "confidence": 0.9,
        "confidence_class": "high",
    }


def test_happy_path_emits_list_wrapping_consult_response(
    monkeypatch: pytest.MonkeyPatch,
    sample_consult_response: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _mock_popen_returning(
        monkeypatch,
        stdout=_stdout_with_handshake_then_tool_call(sample_consult_response),
    )
    exit_code = scp_cli.main(["consult", "--domain", "auth"])
    assert exit_code == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert isinstance(parsed, list), "RI canary expects list output"
    assert len(parsed) == 1
    assert parsed[0]["applicable_rules"][0]["rule_id"] == "SCP-R-001"


def test_domain_regex_validation_rejects_path_injection(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    factory = _mock_popen_returning(monkeypatch, stdout="")
    exit_code = scp_cli.main(["consult", "--domain", "../etc/passwd"])
    assert exit_code == 5
    assert factory.call_count == 0, "subprocess must not start on regex fail"
    err = capsys.readouterr().err
    assert "SCP-CLI-E005" in err


def test_domain_regex_validation_rejects_shell_meta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory = _mock_popen_returning(monkeypatch, stdout="")
    for hostile in ["auth;ls", "auth$(id)", "auth`whoami`", "auth|nc", "auth&", ""]:
        exit_code = scp_cli.main(["consult", "--domain", hostile])
        assert exit_code == 5, f"hostile value passed regex: {hostile!r}"
    assert factory.call_count == 0


def test_subsystem_regex_validation(
    monkeypatch: pytest.MonkeyPatch,
    sample_consult_response: dict[str, Any],
) -> None:
    _mock_popen_returning(
        monkeypatch,
        stdout=_stdout_with_handshake_then_tool_call(sample_consult_response),
    )
    bad = scp_cli.main(["consult", "--domain", "auth", "--subsystem", "bad;val"])
    assert bad == 5
    good = scp_cli.main(["consult", "--domain", "auth", "--subsystem", "oauth"])
    assert good == 0


def test_area_id_regex_allows_slashes_and_dots(
    monkeypatch: pytest.MonkeyPatch,
    sample_consult_response: dict[str, Any],
) -> None:
    _mock_popen_returning(
        monkeypatch,
        stdout=_stdout_with_handshake_then_tool_call(sample_consult_response),
    )
    exit_code = scp_cli.main([
        "consult", "--domain", "auth", "--area-id", "src/auth/oauth.py"
    ])
    assert exit_code == 0


def test_timeout_retries_then_returns_2(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    factory = _mock_popen_returning(
        monkeypatch, stdout="", raise_timeout=True
    )
    exit_code = scp_cli.main(["consult", "--domain", "auth"])
    assert exit_code == 2
    assert factory.call_count == scp_cli._MAX_RETRIES_ON_TIMEOUT
    err = capsys.readouterr().err
    assert "SCP-CLI-E001" in err


def test_nonzero_subprocess_exit_returns_3(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _mock_popen_returning(
        monkeypatch,
        stdout="",
        stderr="ImportError: no module named foo",
        returncode=1,
    )
    exit_code = scp_cli.main(["consult", "--domain", "auth"])
    assert exit_code == 3
    err = capsys.readouterr().err
    assert "SCP-CLI-E002" in err
    assert "ImportError" in err


def test_stderr_newline_sanitised(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _mock_popen_returning(
        monkeypatch,
        stdout="",
        stderr="line1\nline2\rinjected: FAKE\n",
        returncode=1,
    )
    scp_cli.main(["consult", "--domain", "auth"])
    err = capsys.readouterr().err
    error_line = next(line for line in err.splitlines() if "SCP-CLI-E002" in line)
    assert "\n" not in error_line.replace("\\n", "")
    assert "\\n" in error_line


def test_stderr_truncated_to_200_chars(monkeypatch: pytest.MonkeyPatch) -> None:
    long_stderr = "X" * 500
    _mock_popen_returning(monkeypatch, stdout="", stderr=long_stderr, returncode=1)
    sanitised = scp_cli._sanitise_for_stderr(long_stderr, max_len=200)
    assert len(sanitised) == 200


def test_malformed_response_missing_tools_call_frame(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    init_only = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}) + "\n"
    _mock_popen_returning(monkeypatch, stdout=init_only)
    exit_code = scp_cli.main(["consult", "--domain", "auth"])
    assert exit_code == 4
    err = capsys.readouterr().err
    assert "SCP-CLI-E003" in err
    assert "no tools/call response" in err


def test_malformed_response_mcp_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    err_frame = json.dumps({
        "jsonrpc": "2.0",
        "id": 2,
        "error": {"code": -32601, "message": "Method not found"},
    })
    _mock_popen_returning(monkeypatch, stdout=err_frame + "\n")
    exit_code = scp_cli.main(["consult", "--domain", "auth"])
    assert exit_code == 4
    err = capsys.readouterr().err
    assert "SCP-CLI-E003" in err
    assert "-32601" in err


def test_malformed_response_missing_content(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bad_result = json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"foo": "bar"}})
    _mock_popen_returning(monkeypatch, stdout=bad_result + "\n")
    assert scp_cli.main(["consult", "--domain", "auth"]) == 4
    assert "missing 'result.content'" in capsys.readouterr().err


def test_malformed_response_content_not_text_type(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bad = json.dumps({
        "jsonrpc": "2.0",
        "id": 2,
        "result": {"content": [{"type": "image", "data": "..."}]},
    })
    _mock_popen_returning(monkeypatch, stdout=bad + "\n")
    assert scp_cli.main(["consult", "--domain", "auth"]) == 4
    assert "not type=text" in capsys.readouterr().err


def test_malformed_response_text_not_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bad = json.dumps({
        "jsonrpc": "2.0",
        "id": 2,
        "result": {"content": [{"type": "text", "text": "{not valid json"}]},
    })
    _mock_popen_returning(monkeypatch, stdout=bad + "\n")
    assert scp_cli.main(["consult", "--domain", "auth"]) == 4
    assert "not JSON" in capsys.readouterr().err


def test_argparse_missing_subcommand_returns_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        scp_cli.main([])
    assert exc_info.value.code != 0


def test_argparse_missing_domain(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        scp_cli.main(["consult"])
    assert exc_info.value.code != 0


def test_env_scrubbed_drops_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GH_TOKEN", "supersecret")
    monkeypatch.setenv("SCP_FEDERATION_APP_PRIVATE_KEY", "-----BEGIN PRIVATE-----")
    env = scp_cli._scrub_env()
    assert "GH_TOKEN" not in env
    assert "SCP_FEDERATION_APP_PRIVATE_KEY" not in env
    assert "PATH" in env


def test_jsonrpc_payload_includes_initialize_and_tool_call(
    monkeypatch: pytest.MonkeyPatch,
    sample_consult_response: dict[str, Any],
) -> None:
    captured: dict[str, Any] = {}
    handle = MagicMock()
    handle.communicate.return_value = (
        _stdout_with_handshake_then_tool_call(sample_consult_response), ""
    )
    handle.returncode = 0

    def _capture_popen(*args: Any, **kwargs: Any) -> MagicMock:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return handle

    def _capture_communicate(payload: str, timeout: float) -> tuple[str, str]:
        captured["payload"] = payload
        return (_stdout_with_handshake_then_tool_call(sample_consult_response), "")

    handle.communicate.side_effect = _capture_communicate
    monkeypatch.setattr(scp_cli.subprocess, "Popen", _capture_popen)

    scp_cli.main(["consult", "--domain", "auth"])
    payload = captured["payload"]
    assert "\"method\": \"initialize\"" in payload
    assert "notifications/initialized" in payload
    assert "\"method\": \"tools/call\"" in payload
    assert "\"name\": \"consult_rules\"" in payload


def test_stdin_argument_order_initialize_then_initialized_then_tool_call(
    monkeypatch: pytest.MonkeyPatch,
    sample_consult_response: dict[str, Any],
) -> None:
    captured_payload: dict[str, str] = {}
    handle = MagicMock()

    def _capture_communicate(payload: str, timeout: float) -> tuple[str, str]:
        captured_payload["p"] = payload
        return (_stdout_with_handshake_then_tool_call(sample_consult_response), "")

    handle.communicate.side_effect = _capture_communicate
    handle.returncode = 0
    monkeypatch.setattr(scp_cli.subprocess, "Popen", MagicMock(return_value=handle))

    scp_cli.main(["consult", "--domain", "auth"])
    lines = [l for l in captured_payload["p"].splitlines() if l.strip()]
    assert len(lines) == 3
    assert json.loads(lines[0])["method"] == "initialize"
    assert json.loads(lines[1])["method"] == "notifications/initialized"
    assert json.loads(lines[2])["method"] == "tools/call"
