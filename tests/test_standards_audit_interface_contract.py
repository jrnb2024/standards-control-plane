from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest

from standards_control_plane import cli as audit_cli
from standards_control_plane.cli import build_parser
from standards_control_plane.schema_tools import load_json_file, validate_with_schema

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "interfaces" / "standards-audit-cli-v1.json"
SUBSYSTEM_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"


def _audit_parser() -> argparse.ArgumentParser:
    parser = build_parser()
    subcommands = next(action for action in parser._actions if action.dest == "command")
    return subcommands.choices["audit"]


def _option(parser: argparse.ArgumentParser, destination: str) -> argparse.Action:
    return next(action for action in parser._actions if action.dest == destination)


def _run_audit_cli(*arguments: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    entry_module = "standards_control_plane.cli"
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", entry_module, *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )


def _valid_audit_result() -> dict[str, object]:
    return {
        "audit_id": "audit-returns-2026-04-11",
        "scope": {
            "paths": ["fixtures/returns-pilot"],
            "subsystem": "returns",
            "area_id": "returns-exceptions",
        },
        "domain_status": {"governance": {"status": "evaluated"}},
        "scores": {"governance": 100},
        "summary": {
            "high_severity_count": 0,
            "medium_severity_count": 0,
            "low_severity_count": 0,
            "waived_count": 0,
        },
        "findings": [],
        "waivers_applied": [],
        "drift": [],
        "regressions": [],
        "recommended_actions": [],
        "generated_at": "2026-04-11T00:00:00Z",
    }


def test_standards_audit_cli_contract_matches_parser_schemas_and_read_only_result() -> None:
    contract = load_json_file(CONTRACT_PATH)

    assert contract["scope"] == "audit"
    assert contract["executable"] == "standards-control-plane"
    assert contract["entry_point"] == "standards_control_plane.cli:main"
    assert contract["subcommand"] == "audit"
    assert contract["request_schema"] == "schemas/audit-request.schema.json"
    assert contract["result_schema"] == "schemas/audit-result.schema.json"
    assert set(contract["arguments"]) == {"--request", "--overlay", "--write-output"}
    assert contract["stdout"]["media_type"] == "application/json"
    assert contract["stdout"]["schema"] == contract["result_schema"]
    assert set(contract["exit_codes"]) == {"0", "1", "2"}
    assert contract["exit_codes"]["0"]["meaning"] == "audit completed successfully"
    assert contract["exit_codes"]["0"]["findings_do_not_change_exit_code"] is True
    assert contract["side_effects"]["default"] == "none"
    assert contract["side_effects"]["--write-output"]["enabled_when"] == "present"
    assert contract["request_constraints"]["scope.subsystem"] == {
        "type": "string",
        "pattern": SUBSYSTEM_PATTERN,
        "maxLength": 128,
    }
    assert contract["side_effects"]["--write-output"]["path_policy"] == (
        "writer-owned; paths are not fixed by this contract"
    )

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["scripts"][contract["executable"]] == contract["entry_point"]

    request_schema_path = ROOT / contract["request_schema"]
    result_schema_path = ROOT / contract["result_schema"]
    assert request_schema_path.is_file()
    assert result_schema_path.is_file()

    audit = _audit_parser()
    request_option = _option(audit, "request")
    overlay_option = _option(audit, "overlay")
    write_output_option = _option(audit, "write_output")

    assert request_option.option_strings == ["--request"]
    assert request_option.required is True
    assert request_option.nargs is None
    assert contract["arguments"]["--request"]["required"] == request_option.required
    assert contract["arguments"]["--request"]["repeatable"] is False
    assert overlay_option.option_strings == ["--overlay"]
    assert overlay_option.required is False
    assert overlay_option.nargs is None
    assert type(overlay_option).__name__ == "_AppendAction"
    assert contract["arguments"]["--overlay"]["required"] == overlay_option.required
    assert contract["arguments"]["--overlay"]["repeatable"] is True
    assert write_output_option.option_strings == ["--write-output"]
    assert write_output_option.required is False
    assert write_output_option.nargs == 0
    assert write_output_option.default is False
    assert contract["arguments"]["--write-output"]["required"] == write_output_option.required
    assert contract["arguments"]["--write-output"]["repeatable"] is False

    request_path = ROOT / "examples" / "audit-request.json"
    parsed = build_parser().parse_args(
        [
            "audit",
            "--request",
            str(request_path),
            "--overlay",
            "overlay-one",
            "--overlay",
            "overlay-two",
        ]
    )
    assert parsed.command == "audit"
    assert parsed.request == str(request_path)
    assert parsed.overlay == ["overlay-one", "overlay-two"]
    assert parsed.write_output is False
    write_enabled = build_parser().parse_args(
        ["audit", "--request", str(request_path), "--write-output"]
    )
    assert write_enabled.write_output is True

    request = load_json_file(request_path)
    validate_with_schema(request, Path(contract["request_schema"]).name)

    completed = _run_audit_cli(
        "audit",
        "--request",
        str(request_path),
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    result = json.loads(completed.stdout)
    assert isinstance(result, dict)
    validate_with_schema(result, Path(contract["result_schema"]).name)
    assert result["audit_id"]


@pytest.mark.parametrize(
    "subsystem",
    [
        "../outside",
        "safe/../../outside",
        r"safe\..\outside",
        ".",
        "..",
        "safe subsystem",
        "/absolute/path",
        "a" * 129,
    ],
)
def test_request_schema_rejects_unsafe_subsystem(subsystem: str) -> None:
    request = load_json_file(ROOT / "examples" / "audit-request.json")
    request["scope"]["subsystem"] = subsystem

    with pytest.raises(ValueError, match="audit-request.schema.json validation failed"):
        validate_with_schema(request, "audit-request.schema.json")


def test_console_script_rejects_traversal_without_writing_outside_isolated_root(
    tmp_path: Path,
) -> None:
    isolated_root = tmp_path / "isolated"
    outside_root = tmp_path / "outside"
    isolated_root.mkdir()
    outside_root.mkdir()
    request_path = isolated_root / "traversal.json"
    request = load_json_file(ROOT / "examples" / "audit-request.json")
    request["scope"]["subsystem"] = "../outside/escaped"
    request_path.write_text(json.dumps(request), encoding="utf-8")

    completed = _run_audit_cli("audit", "--request", str(request_path), cwd=isolated_root)

    assert completed.returncode == 1
    assert completed.stdout == ""
    assert not any(outside_root.iterdir())
    assert sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")) == [
        Path("isolated"),
        Path("isolated/traversal.json"),
        Path("outside"),
    ]


def test_console_script_malformed_request_exits_one(tmp_path: Path) -> None:
    request_path = tmp_path / "malformed.json"
    request_path.write_text(
        json.dumps(
            {
                "mode": "audit",
                "domains": ["governance"],
                "scope": {"paths": ["fixtures/returns-pilot"], "subsystem": "returns"},
            }
        ),
        encoding="utf-8",
    )

    completed = _run_audit_cli("audit", "--request", str(request_path), cwd=tmp_path)

    assert completed.returncode == 1
    assert completed.stdout == ""


def test_console_script_argparse_misuse_exits_two(tmp_path: Path) -> None:
    completed = _run_audit_cli("audit", cwd=tmp_path)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "the following arguments are required: --request" in completed.stderr


def test_default_audit_mode_makes_no_persistence_calls_or_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_path = ROOT / "examples" / "audit-request.json"
    result = _valid_audit_result()
    monkeypatch.setattr(audit_cli, "build_audit_result", lambda *args, **kwargs: result)
    monkeypatch.setattr(audit_cli, "_print_json", lambda payload: None)
    for function_name in (
        "persist_audit_findings",
        "write_audit_reports",
        "write_false_positive_summary",
        "write_ci_outputs",
        "write_control_tower_outputs",
    ):
        monkeypatch.setattr(
            audit_cli,
            function_name,
            lambda *args, _name=function_name, **kwargs: pytest.fail(
                f"default audit unexpectedly called {_name}"
            ),
        )

    assert (
        audit_cli.cmd_audit(
            SimpleNamespace(request=str(request_path), overlay=None, write_output=False)
        )
        == 0
    )


def test_write_output_delegates_to_production_writers_without_path_claims(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request_path = ROOT / "examples" / "audit-request.json"
    result = _valid_audit_result()
    open_store = object()
    history_store = object()
    ci_path = tmp_path / "latest-ci.json"
    ci_output = {"source": {"mode": "audit"}}
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(audit_cli, "build_audit_result", lambda *args, **kwargs: result)
    monkeypatch.setattr(audit_cli, "_print_json", lambda payload: None)
    monkeypatch.setattr(
        audit_cli,
        "persist_audit_findings",
        lambda payload: (calls.append(("persist", payload)) or (open_store, history_store)),
    )
    monkeypatch.setattr(
        audit_cli,
        "write_audit_reports",
        lambda payload, **kwargs: calls.append(("reports", (payload, kwargs))),
    )
    monkeypatch.setattr(
        audit_cli,
        "write_false_positive_summary",
        lambda payload: calls.append(("false_positive", payload)),
    )
    monkeypatch.setattr(
        audit_cli,
        "write_ci_outputs",
        lambda payload, **kwargs: (
            calls.append(("ci", (payload, kwargs)))
            or (ci_path, tmp_path / "latest-ci.md")
        ),
    )
    monkeypatch.setattr(
        audit_cli,
        "load_ci_output",
        lambda path: calls.append(("load_ci", path)) or ci_output,
    )
    monkeypatch.setattr(
        audit_cli,
        "write_control_tower_outputs",
        lambda payload, **kwargs: calls.append(("control_tower", (payload, kwargs))),
    )

    assert (
        audit_cli.cmd_audit(
            SimpleNamespace(request=str(request_path), overlay=None, write_output=True)
        )
        == 0
    )

    assert calls == [
        ("persist", result),
        (
            "reports",
            (result, {"open_store": open_store, "history_store": history_store}),
        ),
        ("false_positive", history_store),
        ("ci", (result, {"source_mode": "audit"})),
        ("load_ci", ci_path),
        (
            "control_tower",
            (result, {"open_store": open_store, "ci_output": ci_output}),
        ),
    ]
