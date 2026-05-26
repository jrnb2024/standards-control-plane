"""SCP design-time consult CLI shim.

Thin wrapper over ``scp-mcp-server`` stdio + JSON-RPC translation, registered as
the ``scp-cli`` console-script entry-point. Per D-054 (Shape C, 2026-05-25),
this preserves the MCP-as-protocol narrative — the CLI delegates to the same
MCP tool that agent runtimes use directly.

Latency: cold-start adds ~500ms (Python import + MCP handshake). Design-time
use only; not suitable for hot loops. See ADOPT-001 §13.

Output contract:
- stdout: JSON list containing one element, the ConsultRulesResponse dict.
  Single-element list shape matches ACC's RI canary
  (ri-est-p-ws-2/.acc/mcp_server.py:333-335) which checks isinstance(parsed,
  list) and returns CLI_OUTPUT_NOT_LIST on a non-list.
- stderr: SCP-CLI-EnnN error codes on failure. Subprocess incidental stderr
  is swallowed (only echoed truncated/sanitised in E002 detail field on
  scp-mcp-server nonzero exit).

Exit codes:
- 0: success
- 2: subprocess timeout after retries (SCP-CLI-E001)
- 3: scp-mcp-server nonzero exit (SCP-CLI-E002)
- 4: MCP protocol / response parse error (SCP-CLI-E003)
- 5: input validation regex fail (SCP-CLI-E005)
- 6: stdout size cap exceeded (SCP-CLI-E004)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Any

_SUBPROCESS_TIMEOUT_SECONDS = 12
_MAX_RETRIES_ON_TIMEOUT = 2
_MAX_STDOUT_BYTES = 10 * 1024 * 1024
_READ_CHUNK_BYTES = 64 * 1024
_DOMAIN_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")
_SUBSYSTEM_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")
# area_id is a logical path-shaped identifier (e.g. "src/auth/oauth.py"), NOT
# a filesystem path. It is serialised as a JSON string into the MCP payload
# and never reaches os.path. Permissive `.` + `/` is intentional; the `..`
# substring is allowed because it would only be visible inside consult_rules
# response assembly which does not perform path resolution.
_AREA_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-./]{1,128}$")
_MCP_PROTOCOL_VERSION = "2024-11-05"
# Strips C0 controls + DEL so a hostile/buggy server cannot inject ANSI
# escapes into the operator's terminal via stderr-detail echoing. Excludes
# \r \n \t — those are escaped to literal `\r` `\n` `\t` separately so log
# lines stay parseable without losing the signal that they were there.
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class _CliError(Exception):
    exit_code: int = 1


class _Timeout(_CliError):
    exit_code = 2


class _NonzeroExit(_CliError):
    exit_code = 3


class _ProtocolError(_CliError):
    exit_code = 4


class _OutputCapped(_CliError):
    exit_code = 6


class _ValidationError(_CliError):
    exit_code = 5


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scp-cli",
        description="SCP design-time consult CLI (delegates to scp-mcp-server stdio)",
    )
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    consult = subparsers.add_parser("consult", help="Consult SCP rules for a domain")
    consult.add_argument("--domain", required=True, help="Domain name (e.g. auth, governance)")
    consult.add_argument("--subsystem", help="Optional subsystem narrower than domain")
    consult.add_argument(
        "--area-id",
        dest="area_id",
        help="Optional area_id (path-shaped identifier for the consult scope)",
    )
    args = parser.parse_args(argv)
    if args.cmd == "consult":
        return _consult(args)
    return 1


def _consult(args: argparse.Namespace) -> int:
    try:
        _validate(args)
    except _ValidationError as exc:
        return exc.exit_code

    arguments: dict[str, Any] = {"domain": args.domain}
    if args.subsystem:
        arguments["subsystem"] = args.subsystem
    if args.area_id:
        arguments["area_id"] = args.area_id

    for attempt in range(_MAX_RETRIES_ON_TIMEOUT):
        try:
            result = _invoke_mcp(arguments)
        except _Timeout:
            if attempt + 1 == _MAX_RETRIES_ON_TIMEOUT:
                print(
                    "SCP-CLI-E001: scp-mcp-server timeout after "
                    f"{_MAX_RETRIES_ON_TIMEOUT} attempts ({_SUBPROCESS_TIMEOUT_SECONDS}s each)",
                    file=sys.stderr,
                )
                return _Timeout.exit_code
            continue
        except _CliError as exc:
            return exc.exit_code
        else:
            print(json.dumps([result]))
            return 0

    # Defensive: the loop returns inside on success or final-timeout. If the
    # loop ever exits normally (would require zero iterations, impossible
    # given _MAX_RETRIES_ON_TIMEOUT > 0), surface as timeout.
    return _Timeout.exit_code


def _validate(args: argparse.Namespace) -> None:
    if not _DOMAIN_REGEX.match(args.domain):
        print("SCP-CLI-E005: --domain failed validation regex", file=sys.stderr)
        raise _ValidationError()
    if args.subsystem and not _SUBSYSTEM_REGEX.match(args.subsystem):
        print("SCP-CLI-E005: --subsystem failed validation regex", file=sys.stderr)
        raise _ValidationError()
    if args.area_id and not _AREA_ID_REGEX.match(args.area_id):
        print("SCP-CLI-E005: --area-id failed validation regex", file=sys.stderr)
        raise _ValidationError()


def _invoke_mcp(arguments: dict[str, Any]) -> dict[str, Any]:
    """Subprocess scp-mcp-server stdio; do MCP handshake + tools/call.

    Returns the parsed ConsultRulesResponse dict. Raises _Timeout /
    _NonzeroExit / _ProtocolError / _OutputCapped on failure (caller maps
    to exit code; stderr emission happens here). The subprocess is always
    cleaned up via context-manager — on any exception (KeyboardInterrupt,
    OSError, etc.) Popen.__exit__ waits/kills as needed.

    Output-size cap is enforced AFTER communicate() returns. communicate()
    does buffer all stdout in memory before returning, so the cap is
    defense-in-depth against a bug in our own scp-mcp-server (which we
    fully control). A truly adversarial subprocess could OOM scp-cli before
    the cap fires; the threat model assumes scp-mcp-server is trusted code
    we wrote. If true streaming becomes required, replace communicate() with
    a per-chunk read loop and adjust test mocks accordingly.
    """
    safe_env = _scrub_env()
    payload = _build_payload(arguments)

    with subprocess.Popen(  # noqa: S603 — list-form, shell=False, scrubbed env
        [sys.executable, "-m", "standards_control_plane.mcp_server.cli", "serve"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=safe_env,
    ) as proc:
        try:
            stdout, stderr = proc.communicate(payload, timeout=_SUBPROCESS_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            raise _Timeout()

        if len(stdout) > _MAX_STDOUT_BYTES:
            print(
                f"SCP-CLI-E004: scp-mcp-server stdout exceeded {_MAX_STDOUT_BYTES} bytes",
                file=sys.stderr,
            )
            raise _OutputCapped()

        if proc.returncode != 0:
            sanitised = _sanitise_for_stderr(stderr, max_len=200)
            print(
                f"SCP-CLI-E002: scp-mcp-server exit {proc.returncode}: {sanitised}",
                file=sys.stderr,
            )
            raise _NonzeroExit()

        return _extract_tool_call_result(stdout)


def _build_payload(arguments: dict[str, Any]) -> str:
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": _MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "scp-cli", "version": "1.0"},
        },
    }
    initialized = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }
    tool_call = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "consult_rules", "arguments": arguments},
    }
    return (
        json.dumps(init_req) + "\n"
        + json.dumps(initialized) + "\n"
        + json.dumps(tool_call) + "\n"
    )


def _scrub_env() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
    }


def _extract_tool_call_result(stdout: str) -> dict[str, Any]:
    tool_call_response: dict[str, Any] | None = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            frame = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Validate frame shape: must be a JSON-RPC response (id=2 AND has
        # result OR error). Guards against a hostile/buggy server emitting a
        # bare {id:2} frame that lacks both fields.
        if frame.get("id") == 2 and ("result" in frame or "error" in frame):
            tool_call_response = frame
            break

    if tool_call_response is None:
        print("SCP-CLI-E003: no tools/call response in MCP frames", file=sys.stderr)
        raise _ProtocolError()

    if "error" in tool_call_response:
        err = tool_call_response["error"]
        msg = _sanitise_for_stderr(str(err.get("message", "")), max_len=200)
        print(
            f"SCP-CLI-E003: MCP error: code={err.get('code')} msg={msg}",
            file=sys.stderr,
        )
        raise _ProtocolError()

    result = tool_call_response.get("result")
    if not isinstance(result, dict) or "content" not in result:
        print(
            "SCP-CLI-E003: malformed tools/call response: missing 'result.content'",
            file=sys.stderr,
        )
        raise _ProtocolError()

    content = result["content"]
    if not isinstance(content, list) or not content:
        print(
            "SCP-CLI-E003: malformed tools/call response: 'result.content' empty/non-list",
            file=sys.stderr,
        )
        raise _ProtocolError()

    first = content[0]
    if not isinstance(first, dict) or first.get("type") != "text":
        print(
            "SCP-CLI-E003: malformed tools/call response: content[0] not type=text",
            file=sys.stderr,
        )
        raise _ProtocolError()

    text_payload = first.get("text", "")
    if not isinstance(text_payload, str):
        print(
            "SCP-CLI-E003: malformed tools/call response: content[0].text not a string",
            file=sys.stderr,
        )
        raise _ProtocolError()

    try:
        parsed = json.loads(text_payload)
    except json.JSONDecodeError as exc:
        print(
            f"SCP-CLI-E003: tools/call text payload not JSON: {exc}",
            file=sys.stderr,
        )
        raise _ProtocolError() from exc

    if not isinstance(parsed, dict):
        print(
            f"SCP-CLI-E003: parsed tool result is not a dict: got {type(parsed).__name__}",
            file=sys.stderr,
        )
        raise _ProtocolError()

    return parsed


def _sanitise_for_stderr(s: str, *, max_len: int) -> str:
    """Make subprocess stderr safe to echo: strip C0/DEL controls, escape
    whitespace, truncate. Prevents ANSI escape injection corrupting the
    operator's terminal and hides log-injection newlines that could split
    SCP-CLI-EnnN error lines.
    """
    if not s:
        return "<empty>"
    stripped = _CONTROL_CHAR_RE.sub("", s)
    trimmed = stripped[:max_len]
    return trimmed.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")


if __name__ == "__main__":
    sys.exit(main())
