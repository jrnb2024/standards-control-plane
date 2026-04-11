from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from standards_control_plane.audit import build_audit_result
from standards_control_plane.findings import load_findings_store
from standards_control_plane.reports import write_audit_reports
from standards_control_plane.resources import examples_dir, output_dir
from standards_control_plane.schema_tools import load_json_file, validate_with_schema


def _current_reporting_state() -> tuple[dict[str, object], object, object]:
    audit_result = build_audit_result(load_json_file(examples_dir() / "audit-request.json"))
    open_store = load_findings_store(output_dir() / "findings" / "open-findings.json")
    history_store = load_findings_store(output_dir() / "findings" / "findings-history.json")
    return audit_result, open_store, history_store


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


def test_write_audit_reports_generates_markdown_and_area_summary(tmp_path: Path) -> None:
    audit_result, open_store, history_store = _current_reporting_state()

    latest_path, subsystem_path, summary_path = write_audit_reports(
        audit_result,
        open_store=open_store,
        history_store=history_store,
        base_output_dir=tmp_path,
    )

    latest_review = latest_path.read_text(encoding="utf-8")
    subsystem_review = subsystem_path.read_text(encoding="utf-8")
    summary = load_json_file(summary_path)

    assert latest_review.startswith("# Standards Control Plane — Latest Review")
    assert "**Generated at:** 2026-04-11T00:00:00Z" in latest_review
    assert "## Top Open High-Severity Issues" in latest_review
    assert "evidence: fixtures/returns-pilot/frontend/app/exceptions/page.tsx" in latest_review
    assert "## Regressions" in latest_review
    assert "## Notable Improvements" in latest_review
    assert "`F-2026-00031`" in latest_review
    assert subsystem_review.startswith("# Standards Control Plane — Returns Review")

    validate_with_schema(summary, "area-summary.schema.json")
    assert summary == {
        "area_id": "returns-exceptions",
        "subsystem": "returns",
        "scores": {
            "governance": 100,
            "architecture": 25,
        },
        "open_findings_count": 3,
        "updated_at": "2026-04-11T00:00:00Z",
    }


def test_write_audit_reports_is_deterministic(tmp_path: Path) -> None:
    audit_result, open_store, history_store = _current_reporting_state()

    write_audit_reports(
        audit_result,
        open_store=open_store,
        history_store=history_store,
        base_output_dir=tmp_path,
    )
    first_latest = (tmp_path / "reports" / "latest-review.md").read_text(encoding="utf-8")
    first_subsystem = (
        tmp_path / "reports" / "subsystems" / "returns-review.md"
    ).read_text(encoding="utf-8")
    first_summary = (
        tmp_path / "findings" / "area-summaries" / "returns.json"
    ).read_text(encoding="utf-8")

    write_audit_reports(
        audit_result,
        open_store=open_store,
        history_store=history_store,
        base_output_dir=tmp_path,
    )

    assert (tmp_path / "reports" / "latest-review.md").read_text(encoding="utf-8") == first_latest
    assert (
        tmp_path / "reports" / "subsystems" / "returns-review.md"
    ).read_text(encoding="utf-8") == first_subsystem
    assert (
        tmp_path / "findings" / "area-summaries" / "returns.json"
    ).read_text(encoding="utf-8") == first_summary


def test_report_cli_prints_fresh_review_and_rejects_stale_output() -> None:
    latest_path = output_dir() / "reports" / "latest-review.md"
    subsystem_path = output_dir() / "reports" / "subsystems" / "returns-review.md"
    summary_path = output_dir() / "findings" / "area-summaries" / "returns.json"
    open_path = output_dir() / "findings" / "open-findings.json"

    original_latest = latest_path.read_text(encoding="utf-8") if latest_path.exists() else None
    original_subsystem = (
        subsystem_path.read_text(encoding="utf-8") if subsystem_path.exists() else None
    )
    original_summary = summary_path.read_text(encoding="utf-8") if summary_path.exists() else None
    original_open = open_path.read_text(encoding="utf-8")

    try:
        audit_run = _run_cli("audit", "--request", "examples/audit-request.json", "--write-output")
        assert audit_run.returncode == 0, audit_run.stderr

        fresh_report = _run_cli("report")
        assert fresh_report.returncode == 0, fresh_report.stderr
        assert fresh_report.stdout.strip() == latest_path.read_text(encoding="utf-8").strip()

        open_payload = json.loads(open_path.read_text(encoding="utf-8"))
        open_payload["findings"] = open_payload["findings"][:-1]
        open_path.write_text(json.dumps(open_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        stale_report = _run_cli("report")
        assert stale_report.returncode == 1
        assert "refresh it with `audit --write-output`" in stale_report.stderr
    finally:
        open_path.write_text(original_open, encoding="utf-8")
        if original_latest is None:
            latest_path.unlink(missing_ok=True)
        else:
            latest_path.write_text(original_latest, encoding="utf-8")
        if original_subsystem is None:
            subsystem_path.unlink(missing_ok=True)
        else:
            subsystem_path.write_text(original_subsystem, encoding="utf-8")
        if original_summary is None:
            summary_path.unlink(missing_ok=True)
        else:
            summary_path.write_text(original_summary, encoding="utf-8")


def test_report_cli_fails_when_latest_review_is_missing() -> None:
    latest_path = output_dir() / "reports" / "latest-review.md"
    original_latest = latest_path.read_text(encoding="utf-8") if latest_path.exists() else None
    try:
        latest_path.unlink(missing_ok=True)
        missing_report = _run_cli("report")
        assert missing_report.returncode == 1
        assert "Report file not found" in missing_report.stderr
    finally:
        if original_latest is not None:
            latest_path.write_text(original_latest, encoding="utf-8")


def test_report_cli_fails_explicitly_when_findings_store_is_invalid() -> None:
    open_path = output_dir() / "findings" / "open-findings.json"
    original_open = open_path.read_text(encoding="utf-8")
    try:
        open_path.write_text("{not valid json\n", encoding="utf-8")
        invalid_report = _run_cli("report")
        assert invalid_report.returncode == 1
        assert "Unable to validate report freshness" in invalid_report.stderr
    finally:
        open_path.write_text(original_open, encoding="utf-8")
