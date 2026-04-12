"""Portfolio-style reporting across repo-local SCP outputs."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .control_tower import estate_dashboard_path as control_tower_estate_dashboard_path
from .control_tower import load_estate_dashboard
from .resources import output_dir
from .schema_tools import load_json_file, validate_with_schema

ARTIFACT_VERSION = "0.1.0"
ESTATE_DIRNAME = "estate"
MULTI_REPO_DASHBOARD_FILENAME = "multi-repo-dashboard.json"
PORTFOLIO_HISTORY_FILENAME = "portfolio-history.json"
PORTFOLIO_TREND_FILENAME = "portfolio-trend.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _estate_dir(base_output_dir: Path | None = None) -> Path:
    root = base_output_dir or output_dir()
    return root / ESTATE_DIRNAME


def multi_repo_dashboard_path(base_output_dir: Path | None = None) -> Path:
    return _estate_dir(base_output_dir) / MULTI_REPO_DASHBOARD_FILENAME


def portfolio_history_path(base_output_dir: Path | None = None) -> Path:
    return _estate_dir(base_output_dir) / PORTFOLIO_HISTORY_FILENAME


def portfolio_trend_path(base_output_dir: Path | None = None) -> Path:
    return _estate_dir(base_output_dir) / PORTFOLIO_TREND_FILENAME


def _relative_output_path(path: Path, base_output_dir: Path | None = None) -> str:
    root = (base_output_dir or output_dir()).resolve()
    return path.resolve().relative_to(root).as_posix()


def _stage_json(target_path: Path, payload: dict[str, Any], schema_name: str) -> Path:
    validate_with_schema(payload, schema_name)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=target_path.parent,
        delete=False,
        prefix=f".{target_path.name}.",
        suffix=".tmp",
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        return Path(handle.name)


def _cleanup(path: Path | None) -> None:
    if path is not None and path.exists():
        path.unlink()


def _stage_backup(target_path: Path) -> Path | None:
    if not target_path.exists():
        return None
    with NamedTemporaryFile(
        mode="wb",
        dir=target_path.parent,
        delete=False,
        prefix=f".{target_path.name}.",
        suffix=".bak",
    ) as handle:
        handle.write(target_path.read_bytes())
        return Path(handle.name)


def _write_artifacts_atomic(targets: list[tuple[Path, dict[str, Any], str]]) -> None:
    staged: list[tuple[Path, Path]] = []
    backups: list[tuple[Path, Path | None]] = []
    for target_path, payload, schema_name in targets:
        staged_path = _stage_json(target_path, payload, schema_name)
        staged.append((target_path, staged_path))
        backups.append((target_path, _stage_backup(target_path)))

    try:
        for target_path, staged_path in staged:
            os.replace(staged_path, target_path)
    except Exception:
        for target_path, backup_path in backups:
            if backup_path is not None:
                os.replace(backup_path, target_path)
            elif target_path.exists():
                target_path.unlink()
        raise
    finally:
        for _, staged_path in staged:
            _cleanup(staged_path)
        for _, backup_path in backups:
            _cleanup(backup_path)


def _repo_id(output_root: Path) -> str:
    if output_root.name == "output" and output_root.parent.name:
        return output_root.parent.name
    return output_root.name or output_root.resolve().name


def build_repo_dashboard_entry(repo_output_root: Path) -> dict[str, Any]:
    output_root = repo_output_root.resolve()
    dashboard_path = control_tower_estate_dashboard_path(output_root)
    dashboard = load_estate_dashboard(dashboard_path)
    summary = dashboard["summary"]
    entry = {
        "repo_id": _repo_id(output_root),
        "output_root": str(output_root),
        "dashboard_path": str(dashboard_path.resolve()),
        "generated_at": dashboard["generated_at"],
        "subsystem_count": int(summary["subsystem_count"]),
        "attention_required_count": int(summary["attention_required_count"]),
        "warning_count": int(summary["warning_count"]),
        "open_findings_count": int(summary["open_findings_count"]),
        "high_severity_open_findings": int(summary["high_severity_open_findings"]),
    }
    validate_with_schema(
        {
            "artifact_version": ARTIFACT_VERSION,
            "generated_at": dashboard["generated_at"],
            "advisory_only": True,
            "repo_count": 1,
            "summary": {
                "subsystem_count": entry["subsystem_count"],
                "attention_required_count": entry["attention_required_count"],
                "warning_count": entry["warning_count"],
                "open_findings_count": entry["open_findings_count"],
                "high_severity_open_findings": entry["high_severity_open_findings"],
            },
            "repos": [entry],
        },
        "multi-repo-dashboard.schema.json",
    )
    return entry


def build_multi_repo_dashboard(
    repo_output_roots: list[Path],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if not repo_output_roots:
        raise ValueError("At least one repo output root is required")

    repo_entries = sorted(
        (build_repo_dashboard_entry(path) for path in repo_output_roots),
        key=lambda entry: (str(entry["repo_id"]), str(entry["output_root"])),
    )
    dashboard = {
        "artifact_version": ARTIFACT_VERSION,
        "generated_at": generated_at or _utc_now(),
        "advisory_only": True,
        "repo_count": len(repo_entries),
        "summary": {
            "subsystem_count": sum(int(entry["subsystem_count"]) for entry in repo_entries),
            "attention_required_count": sum(
                int(entry["attention_required_count"]) for entry in repo_entries
            ),
            "warning_count": sum(int(entry["warning_count"]) for entry in repo_entries),
            "open_findings_count": sum(int(entry["open_findings_count"]) for entry in repo_entries),
            "high_severity_open_findings": sum(
                int(entry["high_severity_open_findings"]) for entry in repo_entries
            ),
        },
        "repos": repo_entries,
    }
    validate_with_schema(dashboard, "multi-repo-dashboard.schema.json")
    return dashboard


def _snapshot_from_dashboard(dashboard: dict[str, Any]) -> dict[str, Any]:
    summary = dashboard["summary"]
    snapshot = {
        "generated_at": dashboard["generated_at"],
        "repo_count": int(dashboard["repo_count"]),
        "repo_ids": [str(entry["repo_id"]) for entry in dashboard["repos"]],
        "subsystem_count": int(summary["subsystem_count"]),
        "attention_required_count": int(summary["attention_required_count"]),
        "warning_count": int(summary["warning_count"]),
        "open_findings_count": int(summary["open_findings_count"]),
        "high_severity_open_findings": int(summary["high_severity_open_findings"]),
    }
    validate_with_schema(
        {"artifact_version": ARTIFACT_VERSION, "snapshots": [snapshot]},
        "portfolio-history.schema.json",
    )
    return snapshot


def _snapshot_signature(
    snapshot: dict[str, Any],
) -> tuple[tuple[str, ...], int, int, int, int, int, int]:
    return (
        tuple(str(value) for value in snapshot["repo_ids"]),
        int(snapshot["repo_count"]),
        int(snapshot["subsystem_count"]),
        int(snapshot["attention_required_count"]),
        int(snapshot["warning_count"]),
        int(snapshot["open_findings_count"]),
        int(snapshot["high_severity_open_findings"]),
    )


def _delta_from_previous(
    latest: dict[str, Any],
    previous: dict[str, Any] | None,
) -> dict[str, int]:
    keys = [
        "repo_count",
        "subsystem_count",
        "attention_required_count",
        "warning_count",
        "open_findings_count",
        "high_severity_open_findings",
    ]
    if previous is None:
        return {key: 0 for key in keys}
    return {key: int(latest[key]) - int(previous[key]) for key in keys}


def build_portfolio_history(
    dashboard: dict[str, Any],
    *,
    existing_history: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_with_schema(dashboard, "multi-repo-dashboard.schema.json")
    if existing_history is not None:
        validate_with_schema(existing_history, "portfolio-history.schema.json")

    snapshots = []
    if existing_history is not None:
        snapshots = list(existing_history["snapshots"])

    current_snapshot = _snapshot_from_dashboard(dashboard)
    if not snapshots or _snapshot_signature(snapshots[-1]) != _snapshot_signature(current_snapshot):
        snapshots.append(current_snapshot)

    history = {
        "artifact_version": ARTIFACT_VERSION,
        "snapshots": snapshots,
    }
    validate_with_schema(history, "portfolio-history.schema.json")
    return history


def build_portfolio_trend(
    dashboard: dict[str, Any],
    *,
    existing_history: dict[str, Any] | None = None,
    history_path_value: str = "estate/portfolio-history.json",
) -> dict[str, Any]:
    validate_with_schema(dashboard, "multi-repo-dashboard.schema.json")
    if existing_history is not None:
        validate_with_schema(existing_history, "portfolio-history.schema.json")

    latest = _snapshot_from_dashboard(dashboard)
    previous = None
    if existing_history is not None and existing_history["snapshots"]:
        previous = dict(existing_history["snapshots"][-1])

    history = build_portfolio_history(dashboard, existing_history=existing_history)
    trend = {
        "artifact_version": ARTIFACT_VERSION,
        "generated_at": dashboard["generated_at"],
        "advisory_only": True,
        "history_count": len(history["snapshots"]),
        "latest": latest,
        "previous": previous,
        "delta_from_previous": _delta_from_previous(latest, previous),
        "history_path": history_path_value,
    }
    validate_with_schema(trend, "portfolio-trend.schema.json")
    return trend


def load_multi_repo_dashboard(path: Path | None = None) -> dict[str, Any]:
    selected_path = path or multi_repo_dashboard_path()
    payload = load_json_file(selected_path)
    if not isinstance(payload, dict):
        raise TypeError("Multi-repo dashboard must be a JSON object")
    validate_with_schema(payload, "multi-repo-dashboard.schema.json")
    return payload


def load_portfolio_history(path: Path | None = None) -> dict[str, Any]:
    selected_path = path or portfolio_history_path()
    payload = load_json_file(selected_path)
    if not isinstance(payload, dict):
        raise TypeError("Portfolio history must be a JSON object")
    validate_with_schema(payload, "portfolio-history.schema.json")
    return payload


def load_portfolio_trend(path: Path | None = None) -> dict[str, Any]:
    selected_path = path or portfolio_trend_path()
    payload = load_json_file(selected_path)
    if not isinstance(payload, dict):
        raise TypeError("Portfolio trend must be a JSON object")
    validate_with_schema(payload, "portfolio-trend.schema.json")
    return payload


def write_multi_repo_outputs(
    repo_output_roots: list[Path],
    *,
    base_output_dir: Path | None = None,
    generated_at: str | None = None,
) -> tuple[Path, Path, Path]:
    dashboard = build_multi_repo_dashboard(repo_output_roots, generated_at=generated_at)
    history_file = portfolio_history_path(base_output_dir)
    existing_history = load_portfolio_history(history_file) if history_file.exists() else None
    history = build_portfolio_history(dashboard, existing_history=existing_history)
    trend = build_portfolio_trend(
        dashboard,
        existing_history=existing_history,
        history_path_value=_relative_output_path(history_file, base_output_dir),
    )

    dashboard_file = multi_repo_dashboard_path(base_output_dir)
    trend_file = portfolio_trend_path(base_output_dir)
    _write_artifacts_atomic(
        [
            (dashboard_file, dashboard, "multi-repo-dashboard.schema.json"),
            (history_file, history, "portfolio-history.schema.json"),
            (trend_file, trend, "portfolio-trend.schema.json"),
        ]
    )
    return dashboard_file, history_file, trend_file
