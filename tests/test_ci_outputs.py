from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from standards_control_plane.ci_outputs import (
    build_ci_output,
    load_ci_output,
    render_ci_markdown,
    write_ci_outputs,
)
from standards_control_plane.resources import examples_dir, output_dir
from standards_control_plane.schema_tools import load_json_file, validate_with_schema


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src")
    return subprocess.run(
        [sys.executable, "-m", "standards_control_plane.cli", *args],
        cwd=root,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _example_audit_result() -> dict[str, object]:
    payload = load_json_file(examples_dir() / "audit-result.json")
    assert isinstance(payload, dict)
    return payload


def test_build_ci_output_warns_on_threshold_findings_and_regressions() -> None:
    audit_result = _example_audit_result()
    audit_result["regressions"] = ["Returns exceptions architecture regression remains unresolved."]

    ci_output = build_ci_output(audit_result)
    validate_with_schema(ci_output, "ci-output.schema.json")

    assert ci_output["outcome"] == "pass_with_warnings"
    assert ci_output["warning_count"] == 2
    assert ci_output["warnings"][0]["warning_id"] == "WARN-FINDING-F-ARCH-001-returns-exceptions"
    assert ci_output["warnings"][1]["warning_id"] == "WARN-REGRESSION-001"


def test_write_ci_outputs_writes_deterministic_json_and_markdown(tmp_path: Path) -> None:
    audit_result = _example_audit_result()

    json_path, markdown_path = write_ci_outputs(audit_result, base_output_dir=tmp_path)
    first_json = json_path.read_text(encoding="utf-8")
    first_markdown = markdown_path.read_text(encoding="utf-8")

    assert load_ci_output(json_path)["warning_count"] == 1
    assert render_ci_markdown(load_ci_output(json_path)) == first_markdown

    write_ci_outputs(audit_result, base_output_dir=tmp_path)

    assert json_path.read_text(encoding="utf-8") == first_json
    assert markdown_path.read_text(encoding="utf-8") == first_markdown


def test_write_ci_outputs_captures_changed_audit_source_metadata(tmp_path: Path) -> None:
    audit_result = _example_audit_result()

    json_path, _ = write_ci_outputs(
        audit_result,
        source_mode="audit_changed",
        base_ref="origin/main",
        head_ref="HEAD",
        changed_paths=[
            "fixtures/returns-pilot/docs/enhancements/ENH-042-returns-exceptions.md",
            "fixtures/returns-pilot/frontend/app/exceptions/page.tsx",
        ],
        base_output_dir=tmp_path,
    )
    payload = load_ci_output(json_path)

    assert payload["source"] == {
        "mode": "audit_changed",
        "base_ref": "origin/main",
        "head_ref": "HEAD",
        "changed_paths": [
            "fixtures/returns-pilot/docs/enhancements/ENH-042-returns-exceptions.md",
            "fixtures/returns-pilot/frontend/app/exceptions/page.tsx",
        ],
    }


def test_audit_write_output_emits_ci_artifacts_and_ci_cli_reads_them() -> None:
    ci_dir = output_dir() / "ci"
    json_path = ci_dir / "latest-ci.json"
    markdown_path = ci_dir / "latest-ci.md"
    original_json = json_path.read_text(encoding="utf-8") if json_path.exists() else None
    original_markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else None

    try:
        audit_run = _run_cli("audit", "--request", "examples/audit-request.json", "--write-output")
        assert audit_run.returncode == 0, audit_run.stderr
        assert json_path.exists()
        assert markdown_path.exists()

        json_result = _run_cli("ci", "--format", "json")
        assert json_result.returncode == 0, json_result.stderr
        payload = json.loads(json_result.stdout)
        validate_with_schema(payload, "ci-output.schema.json")
        assert payload["warning_count"] == 1

        markdown_result = _run_cli("ci")
        assert markdown_result.returncode == 0, markdown_result.stderr
        assert markdown_result.stdout.startswith("# Standards Control Plane — CI Summary")
        assert "**Outcome:** pass_with_warnings" in markdown_result.stdout
    finally:
        if original_json is None:
            json_path.unlink(missing_ok=True)
        else:
            json_path.write_text(original_json, encoding="utf-8")
        if original_markdown is None:
            markdown_path.unlink(missing_ok=True)
        else:
            markdown_path.write_text(original_markdown, encoding="utf-8")


def test_ci_cli_fails_when_latest_artifact_is_missing() -> None:
    json_path = output_dir() / "ci" / "latest-ci.json"
    original_json = json_path.read_text(encoding="utf-8") if json_path.exists() else None

    try:
        json_path.unlink(missing_ok=True)
        missing_ci = _run_cli("ci", "--format", "json")
        assert missing_ci.returncode == 1
        assert "CI artifact not found" in missing_ci.stderr
    finally:
        if original_json is not None:
            json_path.write_text(original_json, encoding="utf-8")
