"""Product-coherence evaluator shell."""

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
USER_OUTCOME_MARKERS = ("review", "resolve", "approve", "manage", "track", "help")
INTERNAL_MARKERS = ("shard", "pipeline", "recompute", "replay", "raw event", "console", "internals")


def _deterministic_timestamp(standards_version: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", standards_version):
        raise ValueError("standards_version must use YYYY-MM-DD format in phase 1")
    return f"{standards_version}T00:00:00Z"


def _product_rules(
    registry_snapshot: RegistrySnapshot | None = None,
) -> dict[str, RuleRecord]:
    registry = registry_snapshot or load_registry()
    return {rule.rule_id: rule for rule in registry.active_rules_for(["product"])}


def _read_repo_file(path_value: str) -> str:
    root = project_root().resolve()
    resolved_path = (root / path_value).resolve()
    if not resolved_path.is_relative_to(root):
        return ""
    if not resolved_path.exists() or not resolved_path.is_file():
        return ""
    return resolved_path.read_text(encoding="utf-8")


def _spec_text(project_area: dict[str, Any]) -> str:
    specs = list(project_area["artefacts"]["enhancement_specs"])
    if not specs:
        return ""
    return "\n".join(_read_repo_file(str(path_value)) for path_value in specs)


def _ui_text(project_area: dict[str, Any]) -> str:
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
        "domain": "product",
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
        "detected_by": "product-evaluator",
        "standards_version": standards_version,
        "created_at": evaluated_at,
        "updated_at": evaluated_at,
    }
    validate_with_schema(finding, "finding.schema.json")
    return finding


def _job_to_be_done_finding(
    project_area: dict[str, Any],
    *,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any] | None:
    spec_text = _spec_text(project_area).lower()
    if not spec_text:
        return None
    if any(marker in spec_text for marker in INTERNAL_MARKERS) and not any(
        marker in spec_text for marker in USER_OUTCOME_MARKERS
    ):
        spec_path = str(project_area["artefacts"]["enhancement_specs"][0])
        return _build_finding(
            rule=rule,
            area_id=str(project_area["area_id"]),
            standards_version=standards_version,
            evaluated_at=evaluated_at,
            title="Feature intent reads as internal mechanics",
            summary=(
                "The enhancement spec foregrounds internal system activity without"
                " clearly stating the user task or outcome."
            ),
            evidence=[
                {
                    "path": spec_path,
                    "evidence_class": "direct_file",
                    "locator": "internal-language dominant spec",
                }
            ],
            suggested_remediation=[
                "Rewrite the enhancement summary around the user task and intended outcome.",
            ],
            confidence=0.78,
        )
    return None


def _action_alignment_finding(
    project_area: dict[str, Any],
    *,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any] | None:
    ui_text = _ui_text(project_area).lower()
    for path_value in project_area["artefacts"]["ui_components"]:
        content = _read_repo_file(str(path_value)).lower()
        if any(marker in content for marker in INTERNAL_MARKERS):
            return _build_finding(
                rule=rule,
                area_id=str(project_area["area_id"]),
                standards_version=standards_version,
                evaluated_at=evaluated_at,
                title="Screen actions expose internal mechanics",
                summary=(
                    "The visible screen language reads like internal maintenance or"
                    " pipeline control rather than a user outcome."
                ),
                evidence=[
                    {
                        "path": str(path_value),
                        "evidence_class": "direct_file",
                        "locator": "internal-language action marker",
                    }
                ],
                suggested_remediation=[
                    (
                        "Rename visible actions so they read like user outcomes "
                        "rather than internal operations."
                    ),
                ],
                confidence=0.8,
            )
    if ui_text:
        return None
    return None


def _language_consistency_finding(
    project_area: dict[str, Any],
    *,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any] | None:
    area_id = str(project_area["area_id"]).lower()
    combined_text = f"{_spec_text(project_area).lower()}\n{_ui_text(project_area).lower()}"
    if any(marker in area_id for marker in ("internals", "console", "pipeline")) or any(
        marker in combined_text for marker in ("shard", "raw event", "recompute", "replay")
    ):
        evidence_path = str(project_area["paths"][0])
        return _build_finding(
            rule=rule,
            area_id=str(project_area["area_id"]),
            standards_version=standards_version,
            evaluated_at=evaluated_at,
            title="Visible terminology is not user-facing",
            summary=(
                "The route or visible labels foreground internal architecture terms"
                " instead of stable product language."
            ),
            evidence=[
                {
                    "path": evidence_path,
                    "evidence_class": "direct_file",
                    "locator": "internal terminology marker",
                }
            ],
            suggested_remediation=[
                (
                    "Replace internal architecture terms in visible language with "
                    "stable product terminology."
                ),
            ],
            confidence=0.76,
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


def evaluate_product(
    project_area: dict[str, Any],
    *,
    standards_version: str,
    evaluated_at: str | None = None,
    registry_snapshot: RegistrySnapshot | None = None,
) -> dict[str, Any]:
    timestamp = evaluated_at or _deterministic_timestamp(standards_version)
    rules = _product_rules(registry_snapshot)
    findings = [
        finding
        for finding in [
            _job_to_be_done_finding(
                project_area,
                rule=rules["PROD-001"],
                standards_version=standards_version,
                evaluated_at=timestamp,
            ),
            _action_alignment_finding(
                project_area,
                rule=rules["PROD-002"],
                standards_version=standards_version,
                evaluated_at=timestamp,
            ),
            _language_consistency_finding(
                project_area,
                rule=rules["PROD-003"],
                standards_version=standards_version,
                evaluated_at=timestamp,
            ),
        ]
        if finding is not None
    ]
    sorted_findings = _sorted_findings(findings)
    return {
        "domain": "product",
        "score": score_findings(sorted_findings),
        "findings": sorted_findings,
        "recommended_actions": _recommended_actions(sorted_findings),
    }
