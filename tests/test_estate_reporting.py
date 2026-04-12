from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from standards_control_plane.estate_reporting import (
    build_multi_repo_dashboard,
    build_portfolio_trend,
    load_multi_repo_dashboard,
    load_portfolio_history,
    load_portfolio_trend,
    write_multi_repo_outputs,
)
from standards_control_plane.schema_tools import validate_with_schema


def _seed_repo_output(
    root: Path,
    *,
    repo_id: str,
    generated_at: str,
    subsystem_count: int,
    attention_required_count: int,
    warning_count: int,
    open_findings_count: int,
    high_severity_open_findings: int,
) -> Path:
    output_root = root / repo_id / "output"
    dashboard_dir = output_root / "control-tower"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact_version": "0.1.0",
        "generated_at": generated_at,
        "advisory_only": True,
        "summary": {
            "subsystem_count": subsystem_count,
            "healthy_count": 0,
            "monitor_count": 0,
            "attention_required_count": attention_required_count,
            "open_findings_count": open_findings_count,
            "high_severity_open_findings": high_severity_open_findings,
            "warning_count": warning_count,
        },
        "subsystems": [],
    }
    (dashboard_dir / "estate-dashboard.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_root


def _run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(cwd / "src")
    return subprocess.run(
        [sys.executable, "-m", "standards_control_plane.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_build_multi_repo_dashboard_and_trend_are_schema_valid(tmp_path: Path) -> None:
    repo_a_output = _seed_repo_output(
        tmp_path,
        repo_id="repo-a",
        generated_at="2026-04-12T08:00:00Z",
        subsystem_count=2,
        attention_required_count=1,
        warning_count=3,
        open_findings_count=5,
        high_severity_open_findings=2,
    )
    repo_b_output = _seed_repo_output(
        tmp_path,
        repo_id="repo-b",
        generated_at="2026-04-12T09:00:00Z",
        subsystem_count=1,
        attention_required_count=0,
        warning_count=1,
        open_findings_count=2,
        high_severity_open_findings=1,
    )

    dashboard = build_multi_repo_dashboard(
        [repo_b_output, repo_a_output],
        generated_at="2026-04-12T10:00:00Z",
    )
    validate_with_schema(dashboard, "multi-repo-dashboard.schema.json")
    assert [entry["repo_id"] for entry in dashboard["repos"]] == ["repo-a", "repo-b"]
    assert dashboard["repo_count"] == 2
    assert dashboard["summary"] == {
        "subsystem_count": 3,
        "attention_required_count": 1,
        "warning_count": 4,
        "open_findings_count": 7,
        "high_severity_open_findings": 3,
    }

    trend = build_portfolio_trend(
        dashboard,
        history_path_value="estate/portfolio-history.json",
    )
    validate_with_schema(trend, "portfolio-trend.schema.json")
    assert trend["history_count"] == 1
    assert trend["previous"] is None
    assert trend["delta_from_previous"] == {
        "repo_count": 0,
        "subsystem_count": 0,
        "attention_required_count": 0,
        "warning_count": 0,
        "open_findings_count": 0,
        "high_severity_open_findings": 0,
    }


def test_write_multi_repo_outputs_persists_dashboard_history_and_trend(tmp_path: Path) -> None:
    repo_a_output = _seed_repo_output(
        tmp_path,
        repo_id="repo-a",
        generated_at="2026-04-12T08:00:00Z",
        subsystem_count=2,
        attention_required_count=1,
        warning_count=3,
        open_findings_count=5,
        high_severity_open_findings=2,
    )
    repo_b_output = _seed_repo_output(
        tmp_path,
        repo_id="repo-b",
        generated_at="2026-04-12T09:00:00Z",
        subsystem_count=1,
        attention_required_count=0,
        warning_count=1,
        open_findings_count=2,
        high_severity_open_findings=1,
    )

    dashboard_path, history_path, trend_path = write_multi_repo_outputs(
        [repo_a_output, repo_b_output],
        base_output_dir=tmp_path / "aggregate-output",
        generated_at="2026-04-12T10:00:00Z",
    )

    dashboard = load_multi_repo_dashboard(dashboard_path)
    history = load_portfolio_history(history_path)
    trend = load_portfolio_trend(trend_path)
    assert dashboard["summary"]["open_findings_count"] == 7
    assert len(history["snapshots"]) == 1
    assert trend["history_count"] == 1

    repo_b_dashboard = repo_b_output / "control-tower" / "estate-dashboard.json"
    updated_repo_b = json.loads(repo_b_dashboard.read_text(encoding="utf-8"))
    updated_repo_b["summary"]["open_findings_count"] = 4
    updated_repo_b["summary"]["warning_count"] = 2
    repo_b_dashboard.write_text(
        json.dumps(updated_repo_b, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    _, history_path_second, trend_path_second = write_multi_repo_outputs(
        [repo_a_output, repo_b_output],
        base_output_dir=tmp_path / "aggregate-output",
        generated_at="2026-04-12T11:00:00Z",
    )
    history_second = load_portfolio_history(history_path_second)
    trend_second = load_portfolio_trend(trend_path_second)
    assert len(history_second["snapshots"]) == 2
    assert trend_second["previous"]["open_findings_count"] == 7
    assert trend_second["latest"]["open_findings_count"] == 9
    assert trend_second["delta_from_previous"] == {
        "repo_count": 0,
        "subsystem_count": 0,
        "attention_required_count": 0,
        "warning_count": 1,
        "open_findings_count": 2,
        "high_severity_open_findings": 0,
    }


def test_estate_report_cli_prints_and_persists_outputs(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo_a_output = _seed_repo_output(
        tmp_path,
        repo_id="repo-a",
        generated_at="2026-04-12T08:00:00Z",
        subsystem_count=2,
        attention_required_count=1,
        warning_count=3,
        open_findings_count=5,
        high_severity_open_findings=2,
    )

    dashboard_result = _run_cli(
        repo_root,
        "estate-report",
        "--repo-output",
        str(repo_a_output),
    )
    assert dashboard_result.returncode == 0, dashboard_result.stderr
    validate_with_schema(json.loads(dashboard_result.stdout), "multi-repo-dashboard.schema.json")

    original_dashboard = None
    original_history = None
    original_trend = None
    dashboard_file = repo_root / "output" / "estate" / "multi-repo-dashboard.json"
    history_file = repo_root / "output" / "estate" / "portfolio-history.json"
    trend_file = repo_root / "output" / "estate" / "portfolio-trend.json"
    if dashboard_file.exists():
        original_dashboard = dashboard_file.read_text(encoding="utf-8")
    if history_file.exists():
        original_history = history_file.read_text(encoding="utf-8")
    if trend_file.exists():
        original_trend = trend_file.read_text(encoding="utf-8")

    try:
        trend_result = _run_cli(
            repo_root,
            "estate-report",
            "--format",
            "trend",
            "--repo-output",
            str(repo_a_output),
            "--write-output",
        )
        assert trend_result.returncode == 0, trend_result.stderr
        validate_with_schema(json.loads(trend_result.stdout), "portfolio-trend.schema.json")

        persisted_dashboard = _run_cli(repo_root, "estate-report")
        assert persisted_dashboard.returncode == 0, persisted_dashboard.stderr
        validate_with_schema(
            json.loads(persisted_dashboard.stdout),
            "multi-repo-dashboard.schema.json",
        )

        persisted_trend = _run_cli(repo_root, "estate-report", "--format", "trend")
        assert persisted_trend.returncode == 0, persisted_trend.stderr
        validate_with_schema(json.loads(persisted_trend.stdout), "portfolio-trend.schema.json")
    finally:
        if original_dashboard is None:
            dashboard_file.unlink(missing_ok=True)
        else:
            dashboard_file.write_text(original_dashboard, encoding="utf-8")
        if original_history is None:
            history_file.unlink(missing_ok=True)
        else:
            history_file.write_text(original_history, encoding="utf-8")
        if original_trend is None:
            trend_file.unlink(missing_ok=True)
        else:
            trend_file.write_text(original_trend, encoding="utf-8")
