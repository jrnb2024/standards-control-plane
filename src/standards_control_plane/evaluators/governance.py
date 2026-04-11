"""Governance evaluator."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

from ..registry import RuleRecord, load_registry
from ..resources import project_root
from ..schema_tools import validate_with_schema

AREA_SPEC_PATTERN = re.compile(r"ENH-\d+-([a-z0-9-]+)\.md$", re.IGNORECASE)
SEVERITY_DEDUCTIONS = {
    "critical": 40,
    "high": 30,
    "medium": 15,
    "low": 5,
}
SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


def _deterministic_timestamp(standards_version: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", standards_version):
        raise ValueError("standards_version must use YYYY-MM-DD format in phase 1")
    return f"{standards_version}T00:00:00Z"


def _governance_rules() -> dict[str, RuleRecord]:
    registry = load_registry()
    return {
        rule.rule_id: rule
        for rule in registry.active_rules_for(["governance"])
    }


def _evidence_path(project_area: dict[str, Any], preferred: str | None = None) -> str:
    if preferred:
        return preferred
    docs = project_area["artefacts"]["docs"]
    if docs:
        return str(docs[0])
    paths = project_area["paths"]
    if paths:
        return str(paths[0])
    return f"area:{project_area['area_id']}"


def _enhancement_slug(path_value: str) -> str | None:
    match = AREA_SPEC_PATTERN.search(PurePosixPath(path_value).name)
    if match is None:
        return None
    return match.group(1).lower()


def _resolved_area_markers(project_area: dict[str, Any]) -> tuple[str, ...]:
    enhancement_specs = list(project_area["artefacts"]["enhancement_specs"])
    enhancement_slug = _enhancement_slug(enhancement_specs[0]) if enhancement_specs else None
    markers = {str(project_area["area_id"]).lower()}
    if enhancement_slug:
        markers.add(enhancement_slug)
    return tuple(sorted(markers))


def _read_review_evidence(path_value: str) -> str:
    root = project_root().resolve()
    resolved_path = (root / path_value).resolve()
    if not resolved_path.is_relative_to(root):
        return ""
    if not resolved_path.exists() or not resolved_path.is_file():
        return ""
    return resolved_path.read_text(encoding="utf-8").lower()


def _has_traceable_review_evidence(project_area: dict[str, Any]) -> bool:
    markers = _resolved_area_markers(project_area)
    for path_value in project_area["artefacts"]["review_evidence"]:
        content = _read_review_evidence(str(path_value))
        if not content:
            continue
        if not any(marker in content for marker in markers):
            continue
        if "f-" not in content:
            continue
        if not any(
            status in content
            for status in (
                "open",
                "accepted",
                "waived",
                "resolved",
                "false_positive",
                "superseded",
                "deferred",
            )
        ):
            continue
        return True
    return False


def _build_finding(
    *,
    rule: RuleRecord,
    project_area: dict[str, Any],
    title: str,
    summary: str,
    evidence: list[dict[str, str]],
    suggested_remediation: list[str],
    confidence: float,
    evaluated_at: str,
) -> dict[str, Any]:
    finding = {
        "finding_id": f"F-{rule.rule_id}-{project_area['area_id']}",
        "domain": "governance",
        "rule_id": rule.rule_id,
        "severity": rule.severity_default,
        "status": "open",
        "title": title,
        "summary": summary,
        "evidence": evidence,
        "area_id": project_area["area_id"],
        "suggested_remediation": suggested_remediation,
        "confidence": confidence,
        "detected_by": "governance-evaluator",
        "standards_version": project_area["metadata"].get("standards_version", "unknown"),
        "created_at": evaluated_at,
        "updated_at": evaluated_at,
    }
    validate_with_schema(finding, "finding.schema.json")
    return finding


def _boundary_finding(
    project_area: dict[str, Any],
    rule: RuleRecord,
    evaluated_at: str,
) -> dict[str, Any] | None:
    subsystem = str(project_area["subsystem"])
    area_id = str(project_area["area_id"])
    enhancement_specs = list(project_area["artefacts"]["enhancement_specs"])
    enhancement_path = enhancement_specs[0] if enhancement_specs else None
    enhancement_slug = _enhancement_slug(enhancement_path) if enhancement_path else None
    resolved_area = enhancement_slug or area_id

    issues: list[str] = []
    if enhancement_slug and enhancement_slug != area_id:
        issues.append(
            f"enhancement spec slug '{enhancement_slug}' does not match area_id '{area_id}'"
        )
    if not resolved_area.startswith(f"{subsystem}-"):
        issues.append(
            f"resolved area '{resolved_area}' falls outside subsystem '{subsystem}'"
        )
    if not issues:
        return None

    evidence = []
    if enhancement_path:
        evidence.append(
            {
                "path": enhancement_path,
                "locator": "artefacts.enhancement_specs[0]",
            }
        )
    evidence.append(
        {
            "path": _evidence_path(project_area),
            "locator": "area_id",
        }
    )
    return _build_finding(
        rule=rule,
        project_area=project_area,
        title="Declared area boundary does not align",
        summary="; ".join(issues),
        evidence=evidence,
        suggested_remediation=[
            "Align the enhancement-spec slug, area_id, and subsystem naming before implementation continues.",
            "Keep the requested subsystem boundary explicit when preparing audit scope.",
        ],
        confidence=0.94,
        evaluated_at=evaluated_at,
    )


def _missing_enhancement_spec_finding(
    project_area: dict[str, Any],
    rule: RuleRecord,
    evaluated_at: str,
) -> dict[str, Any] | None:
    if project_area["artefacts"]["enhancement_specs"]:
        return None
    return _build_finding(
        rule=rule,
        project_area=project_area,
        title="Required enhancement spec is missing",
        summary=(
            f"Area '{project_area['area_id']}' has no enhancement spec artefact under "
            "docs/enhancements, so the work lacks the expected planning record."
        ),
        evidence=[
            {
                "path": _evidence_path(project_area),
                "locator": "artefacts.enhancement_specs",
            }
        ],
        suggested_remediation=[
            "Add an enhancement spec under docs/enhancements for this area before continuing implementation.",
        ],
        confidence=0.97,
        evaluated_at=evaluated_at,
    )


def _missing_review_evidence_finding(
    project_area: dict[str, Any],
    rule: RuleRecord,
    evaluated_at: str,
) -> dict[str, Any] | None:
    if _has_traceable_review_evidence(project_area):
        return None
    return _build_finding(
        rule=rule,
        project_area=project_area,
        title="Review evidence is missing",
        summary=(
            f"Area '{project_area['area_id']}' has no traceable review evidence tied "
            "to the area, with finding identifiers and statuses, under docs/reviews."
        ),
        evidence=[
            {
                "path": _evidence_path(project_area),
                "locator": "artefacts.review_evidence",
            }
        ],
        suggested_remediation=[
            "Add review findings under docs/reviews that reference the area and include finding IDs plus explicit statuses.",
        ],
        confidence=0.92,
        evaluated_at=evaluated_at,
    )


def _sorted_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        findings,
        key=lambda finding: (
            SEVERITY_ORDER[str(finding["severity"])],
            str(finding["finding_id"]),
        ),
    )


def _recommended_actions(findings: list[dict[str, Any]]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for finding in findings:
        for action in finding.get("suggested_remediation", []):
            action_value = str(action)
            if action_value not in seen:
                ordered.append(action_value)
                seen.add(action_value)
    return ordered


def _score_for_findings(findings: list[dict[str, Any]]) -> int:
    score = 100
    for finding in findings:
        score -= SEVERITY_DEDUCTIONS[str(finding["severity"])]
    return max(score, 0)


def evaluate_governance(
    project_area: dict[str, Any],
    *,
    standards_version: str,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    validate_with_schema(project_area, "project-area.schema.json")
    timestamp = evaluated_at or _deterministic_timestamp(standards_version)
    project_area_with_metadata = {
        **project_area,
        "metadata": {
            **project_area["metadata"],
            "standards_version": standards_version,
        },
    }
    rules = _governance_rules()
    findings = [
        finding
        for finding in [
            _boundary_finding(project_area_with_metadata, rules["GOV-001"], timestamp),
            _missing_enhancement_spec_finding(
                project_area_with_metadata,
                rules["GOV-002"],
                timestamp,
            ),
            _missing_review_evidence_finding(
                project_area_with_metadata,
                rules["GOV-003"],
                timestamp,
            ),
        ]
        if finding is not None
    ]
    sorted_findings = _sorted_findings(findings)
    return {
        "score": _score_for_findings(sorted_findings),
        "findings": sorted_findings,
        "recommended_actions": _recommended_actions(sorted_findings),
    }
