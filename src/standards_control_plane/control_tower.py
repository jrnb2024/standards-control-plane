"""Control Tower-facing dashboard exports over persisted SCP artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .findings import FindingRecord, FindingsStore
from .resources import output_dir
from .schema_tools import load_json_file, validate_with_schema

ARTIFACT_VERSION = "0.1.0"
CONTROL_TOWER_DIRNAME = "control-tower"
SUBSYSTEMS_DIRNAME = "subsystems"
SURFACE_FILENAME = "surface.json"
ESTATE_DASHBOARD_FILENAME = "estate-dashboard.json"

SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


def _control_tower_dir(base_output_dir: Path | None = None) -> Path:
    root = base_output_dir or output_dir()
    return root / CONTROL_TOWER_DIRNAME


def _subsystems_dir(base_output_dir: Path | None = None) -> Path:
    return _control_tower_dir(base_output_dir) / SUBSYSTEMS_DIRNAME


def surface_path(base_output_dir: Path | None = None) -> Path:
    return _control_tower_dir(base_output_dir) / SURFACE_FILENAME


def estate_dashboard_path(base_output_dir: Path | None = None) -> Path:
    return _control_tower_dir(base_output_dir) / ESTATE_DASHBOARD_FILENAME


def subsystem_dashboard_path(subsystem: str, base_output_dir: Path | None = None) -> Path:
    return _subsystems_dir(base_output_dir) / f"{subsystem}.json"


def _relative_output_path(path: Path, base_output_dir: Path | None = None) -> str:
    root = base_output_dir or output_dir()
    return path.relative_to(root).as_posix()


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


def _cleanup(path: Path | None) -> None:
    if path is not None and path.exists():
        path.unlink()


def _write_artifacts_atomic(
    targets: list[tuple[Path, dict[str, Any], str]],
) -> None:
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


def _finding_sort_key(finding: FindingRecord) -> tuple[int, str]:
    return (
        SEVERITY_ORDER.get(finding.severity, 99),
        finding.finding_id,
    )


def _area_findings(open_store: FindingsStore, area_id: str) -> list[FindingRecord]:
    findings = [
        finding
        for finding in open_store.findings
        if finding.status == "open" and finding.area_id == area_id
    ]
    return sorted(findings, key=_finding_sort_key)


def _subsystem_status(
    *,
    worst_score: int,
    open_findings_count: int,
    high_severity_open_findings: int,
    warning_count: int,
) -> str:
    if warning_count > 0 or high_severity_open_findings > 0 or worst_score < 60:
        return "attention_required"
    if open_findings_count > 0 or worst_score < 75:
        return "monitor"
    return "healthy"


def build_subsystem_dashboard(
    audit_result: dict[str, Any],
    *,
    open_store: FindingsStore,
    ci_output: dict[str, Any],
    base_output_dir: Path | None = None,
) -> dict[str, Any]:
    validate_with_schema(audit_result, "audit-result.schema.json")
    validate_with_schema(ci_output, "ci-output.schema.json")

    scope = audit_result["scope"]
    subsystem = str(scope["subsystem"])
    area_id = str(scope["area_id"])
    subsystem_findings = _area_findings(open_store, area_id)
    high_severity_count = sum(
        1 for finding in subsystem_findings if finding.severity in {"critical", "high"}
    )
    warning_count = 0
    if ci_output.get("scope", {}).get("subsystem") == subsystem:
        warning_count = int(ci_output["warning_count"])
    scores = dict(audit_result["scores"])
    worst_score = min(scores.values()) if scores else 100
    domains_evaluated = sorted(
        domain
        for domain, status in audit_result["domain_status"].items()
        if isinstance(status, dict) and status.get("status") == "evaluated"
    )

    entry = {
        "artifact_version": ARTIFACT_VERSION,
        "latest_audit_id": audit_result["audit_id"],
        "subsystem": subsystem,
        "area_id": area_id,
        "generated_at": audit_result["generated_at"],
        "status": _subsystem_status(
            worst_score=worst_score,
            open_findings_count=len(subsystem_findings),
            high_severity_open_findings=high_severity_count,
            warning_count=warning_count,
        ),
        "domains_evaluated": domains_evaluated,
        "scores": scores,
        "worst_score": worst_score,
        "open_findings_count": len(subsystem_findings),
        "high_severity_open_findings": high_severity_count,
        "warning_count": warning_count,
        "report_path": _relative_output_path(
            (base_output_dir or output_dir()) / "reports" / "subsystems" / f"{subsystem}-review.md",
            base_output_dir,
        ),
        "ci_artifact_path": _relative_output_path(
            (base_output_dir or output_dir()) / "ci" / "latest-ci.json",
            base_output_dir,
        ),
        "ci_summary_path": _relative_output_path(
            (base_output_dir or output_dir()) / "ci" / "latest-ci.md",
            base_output_dir,
        ),
        "area_summary_path": _relative_output_path(
            (base_output_dir or output_dir()) / "findings" / "area-summaries" / f"{subsystem}.json",
            base_output_dir,
        ),
        "top_open_findings": [
            {
                "finding_id": finding.finding_id,
                "severity": finding.severity,
                "title": finding.title,
                "summary": finding.summary,
            }
            for finding in subsystem_findings[:3]
        ],
    }
    validate_with_schema(entry, "control-tower-subsystem.schema.json")
    return entry


def _load_subsystem_dashboard(path: Path) -> dict[str, Any]:
    payload = load_json_file(path)
    if not isinstance(payload, dict):
        raise TypeError("Control Tower subsystem artifact must be a JSON object")
    validate_with_schema(payload, "control-tower-subsystem.schema.json")
    return payload


def build_estate_dashboard(
    subsystem_entries: list[dict[str, Any]],
    *,
    generated_at: str,
) -> dict[str, Any]:
    ordered_entries = sorted(subsystem_entries, key=lambda entry: str(entry["subsystem"]))
    dashboard = {
        "artifact_version": ARTIFACT_VERSION,
        "generated_at": generated_at,
        "advisory_only": True,
        "summary": {
            "subsystem_count": len(ordered_entries),
            "healthy_count": sum(1 for entry in ordered_entries if entry["status"] == "healthy"),
            "monitor_count": sum(1 for entry in ordered_entries if entry["status"] == "monitor"),
            "attention_required_count": sum(
                1 for entry in ordered_entries if entry["status"] == "attention_required"
            ),
            "open_findings_count": sum(
                int(entry["open_findings_count"]) for entry in ordered_entries
            ),
            "high_severity_open_findings": sum(
                int(entry["high_severity_open_findings"]) for entry in ordered_entries
            ),
            "warning_count": sum(int(entry["warning_count"]) for entry in ordered_entries),
        },
        "subsystems": ordered_entries,
    }
    validate_with_schema(dashboard, "estate-dashboard.schema.json")
    return dashboard


def build_control_tower_surface(*, generated_at: str) -> dict[str, Any]:
    surface = {
        "artifact_version": ARTIFACT_VERSION,
        "generated_at": generated_at,
        "advisory_only": True,
        "runtime_owner": "standards-control-plane",
        "schemas": {
            "control_tower_subsystem": "schemas/control-tower-subsystem.schema.json",
            "estate_dashboard": "schemas/estate-dashboard.schema.json",
            "audit_result": "schemas/audit-result.schema.json",
            "ci_output": "schemas/ci-output.schema.json",
            "area_summary": "schemas/area-summary.schema.json",
        },
        "artifacts": {
            "subsystems_dir": "control-tower/subsystems",
            "estate_dashboard_path": "control-tower/estate-dashboard.json",
            "reports_dir": "reports/subsystems",
            "ci_artifact_path": "ci/latest-ci.json",
            "ci_summary_path": "ci/latest-ci.md",
            "area_summaries_dir": "findings/area-summaries",
        },
        "integration_notes": [
            (
                "Control Tower should consume these emitted artifacts rather than "
                "invoking evaluator runtime directly."
            ),
            (
                "The exported dashboard remains advisory in this phase and does "
                "not replace repo-local audit artifacts."
            ),
        ],
    }
    validate_with_schema(surface, "control-tower-surface.schema.json")
    return surface


def write_control_tower_outputs(
    audit_result: dict[str, Any],
    *,
    open_store: FindingsStore,
    ci_output: dict[str, Any],
    base_output_dir: Path | None = None,
) -> tuple[Path, Path, Path]:
    subsystem_entry = build_subsystem_dashboard(
        audit_result,
        open_store=open_store,
        ci_output=ci_output,
        base_output_dir=base_output_dir,
    )
    subsystem = str(subsystem_entry["subsystem"])
    subsystem_dir = _subsystems_dir(base_output_dir)
    existing_entries: list[dict[str, Any]] = []
    if subsystem_dir.exists():
        for path in sorted(subsystem_dir.glob("*.json")):
            if path.stem == subsystem:
                continue
            existing_entries.append(_load_subsystem_dashboard(path))

    estate_dashboard = build_estate_dashboard(
        [*existing_entries, subsystem_entry],
        generated_at=audit_result["generated_at"],
    )
    surface = build_control_tower_surface(generated_at=audit_result["generated_at"])

    subsystem_path = subsystem_dashboard_path(subsystem, base_output_dir)
    dashboard_path = estate_dashboard_path(base_output_dir)
    surface_json_path = surface_path(base_output_dir)
    _write_artifacts_atomic(
        [
            (surface_json_path, surface, "control-tower-surface.schema.json"),
            (subsystem_path, subsystem_entry, "control-tower-subsystem.schema.json"),
            (dashboard_path, estate_dashboard, "estate-dashboard.schema.json"),
        ]
    )
    return surface_json_path, subsystem_path, dashboard_path


def load_estate_dashboard(path: Path | None = None) -> dict[str, Any]:
    dashboard_path = path or estate_dashboard_path()
    payload = load_json_file(dashboard_path)
    if not isinstance(payload, dict):
        raise TypeError("Estate dashboard must be a JSON object")
    validate_with_schema(payload, "estate-dashboard.schema.json")
    return payload


def load_control_tower_surface(path: Path | None = None) -> dict[str, Any]:
    selected_path = path or surface_path()
    payload = load_json_file(selected_path)
    if not isinstance(payload, dict):
        raise TypeError("Control Tower surface artifact must be a JSON object")
    validate_with_schema(payload, "control-tower-surface.schema.json")
    return payload
