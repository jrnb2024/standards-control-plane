"""Design-system evaluator shell."""

from __future__ import annotations

import re
from typing import Any

from ..confidence import classify_confidence
from ..registry import RuleRecord, load_registry
from ..resources import project_root
from ..schema_tools import validate_with_schema
from ..scoring import score_findings

SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}
TOKEN_MARKERS = ("tokens.", "token.", "space-", "color-", "text-", "bg-")
APPROVED_COMPONENT_MARKERS = ("<Button", "import { Button", "from \"@/components\"", "from '../components'")
RAW_PRIMITIVE_MARKERS = ("<button", "<input", "<select")
INTERACTIVE_STATE_MARKERS = ("disabled", "aria-busy", "isLoading", "loading")
HARDCODED_STYLE_PATTERN = re.compile(r"(#[0-9a-fA-F]{3,6}|\b\d{2,3}px\b|style=\{\{)")


def _deterministic_timestamp(standards_version: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", standards_version):
        raise ValueError("standards_version must use YYYY-MM-DD format in phase 1")
    return f"{standards_version}T00:00:00Z"


def _design_rules() -> dict[str, RuleRecord]:
    registry = load_registry()
    return {rule.rule_id: rule for rule in registry.active_rules_for(["design"])}


def _read_repo_file(path_value: str) -> str:
    root = project_root().resolve()
    resolved_path = (root / path_value).resolve()
    if not resolved_path.is_relative_to(root):
        return ""
    if not resolved_path.exists() or not resolved_path.is_file():
        return ""
    return resolved_path.read_text(encoding="utf-8")


def _ui_paths(project_area: dict[str, Any]) -> list[str]:
    return [str(path_value) for path_value in project_area["artefacts"]["ui_components"]]


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
        "domain": "design",
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
        "detected_by": "design-evaluator",
        "standards_version": standards_version,
        "created_at": evaluated_at,
        "updated_at": evaluated_at,
    }
    validate_with_schema(finding, "finding.schema.json")
    return finding


def _approved_component_finding(
    project_area: dict[str, Any],
    *,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any] | None:
    for path_value in _ui_paths(project_area):
        content = _read_repo_file(path_value)
        if any(marker in content for marker in RAW_PRIMITIVE_MARKERS) and not any(
            marker in content for marker in APPROVED_COMPONENT_MARKERS
        ):
            return _build_finding(
                rule=rule,
                area_id=str(project_area["area_id"]),
                standards_version=standards_version,
                evaluated_at=evaluated_at,
                title="Screen uses off-pattern raw primitives",
                summary=(
                    "The UI implementation uses raw interactive primitives in a"
                    " screen module without an approved component marker."
                ),
                evidence=[
                    {
                        "path": path_value,
                        "evidence_class": "direct_file",
                        "locator": "raw primitive marker",
                    }
                ],
                suggested_remediation=[
                    "Prefer the approved component layer for screen-level interactive elements.",
                ],
                confidence=0.83,
            )
    return None


def _token_usage_finding(
    project_area: dict[str, Any],
    *,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any] | None:
    for path_value in _ui_paths(project_area):
        content = _read_repo_file(path_value)
        if HARDCODED_STYLE_PATTERN.search(content) and not any(
            marker in content for marker in TOKEN_MARKERS
        ):
            return _build_finding(
                rule=rule,
                area_id=str(project_area["area_id"]),
                standards_version=standards_version,
                evaluated_at=evaluated_at,
                title="Screen uses hard-coded visual values",
                summary=(
                    "The UI implementation carries explicit visual literals with no"
                    " token-like marker for spacing or colour."
                ),
                evidence=[
                    {
                        "path": path_value,
                        "evidence_class": "direct_file",
                        "locator": "hard-coded visual literal",
                    }
                ],
                suggested_remediation=[
                    "Replace bespoke visual literals with token-backed spacing and colour references.",
                ],
                confidence=0.85,
            )
    return None


def _interactive_state_finding(
    project_area: dict[str, Any],
    *,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any] | None:
    for path_value in _ui_paths(project_area):
        content = _read_repo_file(path_value)
        if (
            any(marker in content for marker in RAW_PRIMITIVE_MARKERS + ("onClick",))
            and not any(marker in content for marker in INTERACTIVE_STATE_MARKERS)
        ):
            return _build_finding(
                rule=rule,
                area_id=str(project_area["area_id"]),
                standards_version=standards_version,
                evaluated_at=evaluated_at,
                title="Interactive elements omit state markers",
                summary=(
                    "The screen exposes action controls with no disabled, busy, or"
                    " loading marker in the local implementation."
                ),
                evidence=[
                    {
                        "path": path_value,
                        "evidence_class": "direct_file",
                        "locator": "missing interactive-state marker",
                    }
                ],
                suggested_remediation=[
                    "Expose disabled or busy state markers on primary interactive elements.",
                ],
                confidence=0.82,
            )
    return None


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
            value = str(action)
            if value not in seen:
                ordered.append(value)
                seen.add(value)
    return ordered


def evaluate_design(
    project_area: dict[str, Any],
    *,
    standards_version: str,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    timestamp = evaluated_at or _deterministic_timestamp(standards_version)
    rules = _design_rules()
    findings = [
        finding
        for finding in [
            _approved_component_finding(
                project_area,
                rule=rules["DS-001"],
                standards_version=standards_version,
                evaluated_at=timestamp,
            ),
            _token_usage_finding(
                project_area,
                rule=rules["DS-002"],
                standards_version=standards_version,
                evaluated_at=timestamp,
            ),
            _interactive_state_finding(
                project_area,
                rule=rules["DS-003"],
                standards_version=standards_version,
                evaluated_at=timestamp,
            ),
        ]
        if finding is not None
    ]
    sorted_findings = _sorted_findings(findings)
    return {
        "domain": "design",
        "score": score_findings(sorted_findings),
        "findings": sorted_findings,
        "recommended_actions": _recommended_actions(sorted_findings),
    }
