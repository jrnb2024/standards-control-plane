from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from standards_control_plane.ci_outputs import build_ci_output, write_ci_outputs
from standards_control_plane.control_tower import (
    load_control_tower_surface,
    load_estate_dashboard,
    write_control_tower_outputs,
)
from standards_control_plane.findings import load_findings_store
from standards_control_plane.reports import write_audit_reports
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


def test_write_control_tower_outputs_writes_surface_subsystem_and_dashboard(tmp_path: Path) -> None:
    audit_result = _example_audit_result()
    open_store = load_findings_store(output_dir() / "findings" / "open-findings.json")
    history_store = load_findings_store(output_dir() / "findings" / "findings-history.json")
    ci_output = build_ci_output(audit_result)

    write_audit_reports(
        audit_result,
        open_store=open_store,
        history_store=history_store,
        base_output_dir=tmp_path,
    )
    write_ci_outputs(audit_result, base_output_dir=tmp_path)
    surface_json_path, subsystem_path, dashboard_path = write_control_tower_outputs(
        audit_result,
        open_store=open_store,
        ci_output=ci_output,
        base_output_dir=tmp_path,
    )

    surface = load_control_tower_surface(surface_json_path)
    subsystem_entry = load_json_file(subsystem_path)
    dashboard = load_estate_dashboard(dashboard_path)

    validate_with_schema(surface, "control-tower-surface.schema.json")
    validate_with_schema(subsystem_entry, "control-tower-subsystem.schema.json")
    validate_with_schema(dashboard, "estate-dashboard.schema.json")

    assert subsystem_entry["status"] == "attention_required"
    assert subsystem_entry["open_findings_count"] == 3
    assert subsystem_entry["high_severity_open_findings"] == 2
    assert subsystem_entry["warning_count"] == 1
    assert subsystem_entry["report_path"] == "reports/subsystems/returns-review.md"
    assert subsystem_entry["ci_artifact_path"] == "ci/latest-ci.json"
    assert dashboard["summary"] == {
        "subsystem_count": 1,
        "healthy_count": 0,
        "monitor_count": 0,
        "attention_required_count": 1,
        "open_findings_count": 3,
        "high_severity_open_findings": 2,
        "warning_count": 1,
    }


def test_estate_dashboard_rollup_includes_existing_subsystem_entries(tmp_path: Path) -> None:
    existing_dir = tmp_path / "control-tower" / "subsystems"
    existing_dir.mkdir(parents=True, exist_ok=True)
    seeded_entry = {
        "artifact_version": "0.1.0",
        "latest_audit_id": "audit-labeller-2026-04-11",
        "subsystem": "labeller",
        "area_id": "labeller-workqueue",
        "generated_at": "2026-04-11T00:00:00Z",
        "status": "monitor",
        "domains_evaluated": ["governance"],
        "scores": {"governance": 80},
        "worst_score": 80,
        "open_findings_count": 1,
        "high_severity_open_findings": 0,
        "warning_count": 0,
        "report_path": "reports/subsystems/labeller-review.md",
        "ci_artifact_path": "ci/latest-ci.json",
        "ci_summary_path": "ci/latest-ci.md",
        "area_summary_path": "findings/area-summaries/labeller.json",
        "top_open_findings": [
            {
                "finding_id": "F-LAB-001",
                "severity": "medium",
                "title": "Labeller review evidence is incomplete",
                "summary": "Labeller requires follow-up evidence.",
            }
        ],
    }
    validate_with_schema(seeded_entry, "control-tower-subsystem.schema.json")
    (existing_dir / "labeller.json").write_text(
        json.dumps(seeded_entry, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    audit_result = _example_audit_result()
    open_store = load_findings_store(output_dir() / "findings" / "open-findings.json")
    ci_output = build_ci_output(audit_result)
    _, _, dashboard_path = write_control_tower_outputs(
        audit_result,
        open_store=open_store,
        ci_output=ci_output,
        base_output_dir=tmp_path,
    )
    dashboard = load_estate_dashboard(dashboard_path)

    assert [entry["subsystem"] for entry in dashboard["subsystems"]] == ["labeller", "returns"]
    assert dashboard["summary"]["subsystem_count"] == 2
    assert dashboard["summary"]["monitor_count"] == 1
    assert dashboard["summary"]["attention_required_count"] == 1


def test_control_tower_cli_prints_dashboard_and_fails_when_missing() -> None:
    control_tower_dir = output_dir() / "control-tower"
    dashboard_path = control_tower_dir / "estate-dashboard.json"
    surface_path = control_tower_dir / "surface.json"
    subsystem_dir = control_tower_dir / "subsystems"
    original_dashboard = (
        dashboard_path.read_text(encoding="utf-8") if dashboard_path.exists() else None
    )
    original_surface = surface_path.read_text(encoding="utf-8") if surface_path.exists() else None
    original_subsystems: dict[str, str] = {}
    if subsystem_dir.exists():
        for path in subsystem_dir.glob("*.json"):
            original_subsystems[path.name] = path.read_text(encoding="utf-8")

    try:
        audit_run = _run_cli("audit", "--request", "examples/audit-request.json", "--write-output")
        assert audit_run.returncode == 0, audit_run.stderr

        dashboard_result = _run_cli("control-tower")
        assert dashboard_result.returncode == 0, dashboard_result.stderr
        payload = json.loads(dashboard_result.stdout)
        validate_with_schema(payload, "estate-dashboard.schema.json")
        assert payload["summary"]["subsystem_count"] >= 1

        surface_result = _run_cli("control-tower", "--format", "surface")
        assert surface_result.returncode == 0, surface_result.stderr
        validate_with_schema(json.loads(surface_result.stdout), "control-tower-surface.schema.json")

        dashboard_path.unlink(missing_ok=True)
        missing_dashboard = _run_cli("control-tower")
        assert missing_dashboard.returncode == 1
        assert "Control Tower dashboard not found" in missing_dashboard.stderr
    finally:
        if original_dashboard is None:
            dashboard_path.unlink(missing_ok=True)
        else:
            dashboard_path.write_text(original_dashboard, encoding="utf-8")
        if original_surface is None:
            surface_path.unlink(missing_ok=True)
        else:
            surface_path.write_text(original_surface, encoding="utf-8")
        if subsystem_dir.exists():
            for path in subsystem_dir.glob("*.json"):
                if path.name not in original_subsystems:
                    path.unlink()
        if original_subsystems:
            subsystem_dir.mkdir(parents=True, exist_ok=True)
            for name, content in original_subsystems.items():
                (subsystem_dir / name).write_text(content, encoding="utf-8")
        elif subsystem_dir.exists() and not any(subsystem_dir.iterdir()):
            subsystem_dir.rmdir()
