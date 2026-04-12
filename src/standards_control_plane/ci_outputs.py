"""CI-oriented output projection and advisory warning thresholds."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .confidence import CONFIDENCE_CLASSES
from .resources import output_dir
from .schema_tools import load_json_file, validate_with_schema

CI_ARTIFACT_VERSION = "0.1.0"
CI_DIRNAME = "ci"
LATEST_CI_JSON_FILENAME = "latest-ci.json"
LATEST_CI_MARKDOWN_FILENAME = "latest-ci.md"

DEFAULT_WARNING_SEVERITIES = ("critical", "high")
DEFAULT_MINIMUM_CONFIDENCE_CLASS = "high"
DEFAULT_WARN_ON_REGRESSIONS = True

SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

CONFIDENCE_ORDER = {
    confidence_class: index for index, confidence_class in enumerate(reversed(CONFIDENCE_CLASSES))
}


def _ci_dir(base_output_dir: Path | None = None) -> Path:
    root = base_output_dir or output_dir()
    return root / CI_DIRNAME


def latest_ci_json_path(base_output_dir: Path | None = None) -> Path:
    return _ci_dir(base_output_dir) / LATEST_CI_JSON_FILENAME


def latest_ci_markdown_path(base_output_dir: Path | None = None) -> Path:
    return _ci_dir(base_output_dir) / LATEST_CI_MARKDOWN_FILENAME


def _stage_text(target_path: Path, content: str) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=target_path.parent,
        delete=False,
        prefix=f".{target_path.name}.",
        suffix=".tmp",
    ) as handle:
        handle.write(content)
        return Path(handle.name)


def _stage_json(target_path: Path, payload: dict[str, Any]) -> Path:
    validate_with_schema(payload, "ci-output.schema.json")
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


def _write_artifacts_atomic(targets: list[tuple[Path, str | dict[str, Any]]]) -> None:
    staged: list[tuple[Path, Path]] = []
    backups: list[tuple[Path, Path | None]] = []
    for target_path, payload in targets:
        if isinstance(payload, str):
            staged_path = _stage_text(target_path, payload)
        else:
            staged_path = _stage_json(target_path, payload)
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


def _confidence_meets_threshold(confidence_class: str, minimum_confidence_class: str) -> bool:
    return CONFIDENCE_ORDER[confidence_class] >= CONFIDENCE_ORDER[minimum_confidence_class]


def _build_source(
    *,
    source_mode: str,
    base_ref: str | None,
    head_ref: str | None,
    changed_paths: list[str] | None,
) -> dict[str, Any]:
    if source_mode not in {"audit", "audit_changed"}:
        raise ValueError("source_mode must be 'audit' or 'audit_changed'")

    source: dict[str, Any] = {"mode": source_mode}
    if source_mode == "audit_changed":
        if not base_ref or not head_ref:
            raise ValueError("audit_changed CI output requires base_ref and head_ref")
        source["base_ref"] = base_ref
        source["head_ref"] = head_ref
        source["changed_paths"] = list(changed_paths or [])
    return source


def _finding_warning(finding: dict[str, Any]) -> dict[str, Any]:
    evidence_paths = sorted(
        {
            str(evidence["path"])
            for evidence in finding.get("evidence", [])
            if isinstance(evidence, dict) and isinstance(evidence.get("path"), str)
        }
    )
    warning = {
        "warning_id": f"WARN-FINDING-{finding['finding_id']}",
        "category": "finding_threshold",
        "severity": finding["severity"],
        "summary": (
            f"Open finding {finding['finding_id']} meets the CI warning threshold: "
            f"{finding['title']}"
        ),
        "finding_id": finding["finding_id"],
        "confidence_class": finding["confidence_class"],
        "area_id": finding["area_id"],
        "evidence_paths": evidence_paths,
    }
    validate_with_schema(warning, "ci-warning.schema.json")
    return warning


def _regression_warning(regression: str, index: int) -> dict[str, Any]:
    warning = {
        "warning_id": f"WARN-REGRESSION-{index:03d}",
        "category": "regression",
        "severity": "high",
        "summary": regression,
    }
    validate_with_schema(warning, "ci-warning.schema.json")
    return warning


def _warning_sort_key(warning: dict[str, Any]) -> tuple[int, int, str, str]:
    category_rank = 0 if warning["category"] == "finding_threshold" else 1
    return (
        category_rank,
        SEVERITY_ORDER.get(str(warning["severity"]), 99),
        str(warning.get("finding_id", "")),
        str(warning["warning_id"]),
    )


def build_ci_output(
    audit_result: dict[str, Any],
    *,
    source_mode: str = "audit",
    base_ref: str | None = None,
    head_ref: str | None = None,
    changed_paths: list[str] | None = None,
    warning_severities: tuple[str, ...] = DEFAULT_WARNING_SEVERITIES,
    minimum_confidence_class: str = DEFAULT_MINIMUM_CONFIDENCE_CLASS,
    warn_on_regressions: bool = DEFAULT_WARN_ON_REGRESSIONS,
) -> dict[str, Any]:
    validate_with_schema(audit_result, "audit-result.schema.json")
    if minimum_confidence_class not in CONFIDENCE_ORDER:
        raise ValueError("minimum_confidence_class is not recognised")

    source = _build_source(
        source_mode=source_mode,
        base_ref=base_ref,
        head_ref=head_ref,
        changed_paths=changed_paths,
    )

    warnings: list[dict[str, Any]] = []
    for finding in audit_result["findings"]:
        if finding["status"] != "open":
            continue
        if finding["severity"] not in warning_severities:
            continue
        confidence_class = str(finding["confidence_class"])
        if not _confidence_meets_threshold(confidence_class, minimum_confidence_class):
            continue
        warnings.append(_finding_warning(finding))

    if warn_on_regressions:
        regressions = sorted(str(item) for item in audit_result["regressions"])
        for index, regression in enumerate(regressions, start=1):
            warnings.append(_regression_warning(regression, index))

    sorted_warnings = sorted(warnings, key=_warning_sort_key)
    ci_output = {
        "artifact_version": CI_ARTIFACT_VERSION,
        "audit_id": audit_result["audit_id"],
        "generated_at": audit_result["generated_at"],
        "source": source,
        "scope": audit_result["scope"],
        "domain_status": audit_result["domain_status"],
        "scores": audit_result["scores"],
        "summary": audit_result["summary"],
        "warning_thresholds": {
            "advisory_only": True,
            "finding_severities": list(warning_severities),
            "minimum_confidence_class": minimum_confidence_class,
            "warn_on_regressions": warn_on_regressions,
        },
        "warnings": sorted_warnings,
        "warning_count": len(sorted_warnings),
        "outcome": "pass_with_warnings" if sorted_warnings else "pass",
        "recommended_actions": list(audit_result.get("recommended_actions", [])),
    }
    validate_with_schema(ci_output, "ci-output.schema.json")
    return ci_output


def render_ci_markdown(ci_output: dict[str, Any]) -> str:
    validate_with_schema(ci_output, "ci-output.schema.json")
    source = ci_output["source"]
    source_line = f"**Source:** {source['mode']}"
    if source["mode"] == "audit_changed":
        source_line = (
            f"{source_line} (`{source['base_ref']}`..`{source['head_ref']}`, "
            f"{len(source['changed_paths'])} changed path(s))"
        )

    lines = [
        "# Standards Control Plane — CI Summary",
        "",
        "**Status:** advisory only",
        f"**Generated at:** {ci_output['generated_at']}",
        f"**Audit ID:** {ci_output['audit_id']}",
        source_line,
        f"**Outcome:** {ci_output['outcome']}",
        f"**Warnings:** {ci_output['warning_count']}",
        "",
        "## Domain Scores",
    ]

    scores = ci_output.get("scores", {})
    if scores:
        for domain, score in scores.items():
            lines.append(f"- {domain}: {score}")
    else:
        lines.append("- none")

    lines.extend(["", "## Warning Thresholds"])
    thresholds = ci_output["warning_thresholds"]
    lines.extend(
        [
            f"- advisory_only: {str(thresholds['advisory_only']).lower()}",
            f"- finding_severities: {', '.join(thresholds['finding_severities']) or 'none'}",
            f"- minimum_confidence_class: {thresholds['minimum_confidence_class']}",
            f"- warn_on_regressions: {str(thresholds['warn_on_regressions']).lower()}",
            "",
            "## Warnings",
        ]
    )

    if ci_output["warnings"]:
        for warning in ci_output["warnings"]:
            lines.append(
                f"- `{warning['warning_id']}` [{warning['category']}] {warning['summary']}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Recommended Actions"])
    if ci_output["recommended_actions"]:
        for action in ci_output["recommended_actions"]:
            lines.append(f"- {action}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_ci_outputs(
    audit_result: dict[str, Any],
    *,
    source_mode: str = "audit",
    base_ref: str | None = None,
    head_ref: str | None = None,
    changed_paths: list[str] | None = None,
    base_output_dir: Path | None = None,
) -> tuple[Path, Path]:
    ci_output = build_ci_output(
        audit_result,
        source_mode=source_mode,
        base_ref=base_ref,
        head_ref=head_ref,
        changed_paths=changed_paths,
    )
    ci_markdown = render_ci_markdown(ci_output)
    json_path = latest_ci_json_path(base_output_dir)
    markdown_path = latest_ci_markdown_path(base_output_dir)
    _write_artifacts_atomic(
        [
            (json_path, ci_output),
            (markdown_path, ci_markdown),
        ]
    )
    return json_path, markdown_path


def load_ci_output(path: Path | None = None) -> dict[str, Any]:
    ci_path = path or latest_ci_json_path()
    payload = load_json_file(ci_path)
    if not isinstance(payload, dict):
        raise TypeError("CI output must be a JSON object")
    validate_with_schema(payload, "ci-output.schema.json")
    return payload
