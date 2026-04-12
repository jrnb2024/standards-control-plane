"""UX / IA evaluator shell."""

from __future__ import annotations

import re
from typing import Any

from ..confidence import classify_confidence
from ..registry import RegistrySnapshot, RuleRecord, load_registry
from ..resources import project_root
from ..schema_tools import validate_with_schema
from ..scoring import score_findings

SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}
PRIMARY_ACTION_MARKERS = ("<button", "Button", "onClick", "primaryAction", "href=")
LOADING_MARKERS = ("loading", "spinner", "isLoading", "pending")
EMPTY_MARKERS = ("empty", "no results", "no items", "nothing to review")
ERROR_MARKERS = ("error", "failed", "try again", "retry")
NAVIGATION_MARKERS = ("<h1", "Heading", "breadcrumb", "nav", "title:")


def _deterministic_timestamp(standards_version: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", standards_version):
        raise ValueError("standards_version must use YYYY-MM-DD format in phase 1")
    return f"{standards_version}T00:00:00Z"


def _ux_rules(registry_snapshot: RegistrySnapshot | None = None) -> dict[str, RuleRecord]:
    registry = registry_snapshot or load_registry()
    return {rule.rule_id: rule for rule in registry.active_rules_for(["ux"])}


def _read_repo_file(path_value: str) -> str:
    root = project_root().resolve()
    resolved_path = (root / path_value).resolve()
    if not resolved_path.is_relative_to(root):
        return ""
    if not resolved_path.exists() or not resolved_path.is_file():
        return ""
    return resolved_path.read_text(encoding="utf-8")


def _page_paths(project_area: dict[str, Any]) -> list[str]:
    return [
        str(path_value)
        for path_value in project_area["artefacts"]["ui_components"]
        if str(path_value).replace("\\", "/").endswith(("/page.tsx", "/page.jsx"))
    ]


def _combined_ui_text(project_area: dict[str, Any]) -> str:
    return "\n".join(
        _read_repo_file(str(path_value))
        for path_value in project_area["artefacts"]["ui_components"]
    )


def _build_finding(
    *,
    rule: RuleRecord,
    area_id: str,
    standards_version: str,
    evaluated_at: str,
    title: str,
    summary: str,
    evidence: list[dict[str, str]],
    suggested_remediation: list[str],
    confidence: float,
) -> dict[str, Any]:
    finding = {
        "finding_id": f"F-{rule.rule_id}-{area_id}",
        "domain": "ux",
        "rule_id": rule.rule_id,
        "severity": rule.severity_default,
        "status": "open",
        "title": title,
        "summary": summary,
        "evidence": evidence,
        "area_id": area_id,
        "suggested_remediation": suggested_remediation,
        "confidence": confidence,
        "confidence_class": classify_confidence(confidence),
        "detected_by": "ux-evaluator",
        "standards_version": standards_version,
        "created_at": evaluated_at,
        "updated_at": evaluated_at,
    }
    validate_with_schema(finding, "finding.schema.json")
    return finding


def _primary_action_finding(
    project_area: dict[str, Any],
    *,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any] | None:
    page_paths = _page_paths(project_area)
    if not page_paths:
        return None
    for path_value in page_paths:
        content = _read_repo_file(path_value)
        if any(marker in content for marker in PRIMARY_ACTION_MARKERS):
            return None
    return _build_finding(
        rule=rule,
        area_id=str(project_area["area_id"]),
        standards_version=standards_version,
        evaluated_at=evaluated_at,
        title="Screen lacks an explicit primary action",
        summary=(
            "The route entry point does not expose an obvious action marker, so the"
            " user outcome is hard to infer from the implementation shape."
        ),
        evidence=[
            {
                "path": page_paths[0],
                "evidence_class": "direct_file",
                "locator": "missing primary action marker",
            }
        ],
        suggested_remediation=[
            "Expose one clear next-step action or review step in the route entry point.",
        ],
        confidence=0.84,
    )


def _state_coverage_finding(
    project_area: dict[str, Any],
    *,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any] | None:
    page_paths = _page_paths(project_area)
    if not page_paths:
        return None
    content = _combined_ui_text(project_area).lower()
    if (
        any(marker.lower() in content for marker in LOADING_MARKERS)
        and any(marker.lower() in content for marker in EMPTY_MARKERS)
        and any(marker.lower() in content for marker in ERROR_MARKERS)
    ):
        return None
    return _build_finding(
        rule=rule,
        area_id=str(project_area["area_id"]),
        standards_version=standards_version,
        evaluated_at=evaluated_at,
        title="Screen omits one or more basic state markers",
        summary=(
            "The UI implementation does not show a complete local signal set for"
            " loading, empty, and error handling."
        ),
        evidence=[
            {
                "path": page_paths[0],
                "evidence_class": "direct_file",
                "locator": "missing loading/empty/error markers",
            }
        ],
        suggested_remediation=[
            (
                "Represent loading, empty, and error states explicitly in the "
                "route or adjacent screen components."
            ),
        ],
        confidence=0.83,
    )


def _navigation_clarity_finding(
    project_area: dict[str, Any],
    *,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any] | None:
    page_paths = _page_paths(project_area)
    if not page_paths:
        return None
    for path_value in page_paths:
        content = _read_repo_file(path_value)
        if any(marker in content for marker in NAVIGATION_MARKERS):
            return None
    return _build_finding(
        rule=rule,
        area_id=str(project_area["area_id"]),
        standards_version=standards_version,
        evaluated_at=evaluated_at,
        title="Screen lacks a clear role or navigation cue",
        summary=(
            "The route entry point has no obvious heading, title, breadcrumb, or"
            " navigation marker to orient the user."
        ),
        evidence=[
            {
                "path": page_paths[0],
                "evidence_class": "direct_file",
                "locator": "missing heading or navigation marker",
            }
        ],
        suggested_remediation=[
            "Add a heading, title, or breadcrumb-level cue that makes the screen role obvious.",
        ],
        confidence=0.8,
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
            if action_value in seen:
                continue
            ordered.append(action_value)
            seen.add(action_value)
    return ordered


def evaluate_ux(
    project_area: dict[str, Any],
    *,
    standards_version: str,
    evaluated_at: str | None = None,
    registry_snapshot: RegistrySnapshot | None = None,
) -> dict[str, Any]:
    timestamp = evaluated_at or _deterministic_timestamp(standards_version)
    rules = _ux_rules(registry_snapshot)
    findings = [
        finding
        for finding in [
            _primary_action_finding(
                project_area,
                rule=rules["UX-001"],
                standards_version=standards_version,
                evaluated_at=timestamp,
            ),
            _state_coverage_finding(
                project_area,
                rule=rules["UX-002"],
                standards_version=standards_version,
                evaluated_at=timestamp,
            ),
            _navigation_clarity_finding(
                project_area,
                rule=rules["UX-003"],
                standards_version=standards_version,
                evaluated_at=timestamp,
            ),
        ]
        if finding is not None
    ]
    sorted_findings = _sorted_findings(findings)
    result = {
        "domain": "ux",
        "score": score_findings(sorted_findings),
        "findings": sorted_findings,
        "recommended_actions": _recommended_actions(sorted_findings),
    }
    return result
