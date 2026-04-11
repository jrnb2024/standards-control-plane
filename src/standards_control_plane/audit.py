"""Audit request assembly and evaluator dispatch."""

from __future__ import annotations

import re
from typing import Any

from .evaluators import evaluate_architecture, evaluate_governance
from .extractor import extract_scope
from .normaliser import normalise_project_area
from .schema_tools import validate_with_schema

EVALUATORS = {
    "architecture": evaluate_architecture,
    "governance": evaluate_governance,
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


def _summary_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "high_severity_count": sum(1 for finding in findings if finding["severity"] == "high"),
        "medium_severity_count": sum(1 for finding in findings if finding["severity"] == "medium"),
        "low_severity_count": sum(1 for finding in findings if finding["severity"] == "low"),
    }


def _ordered_unique(values: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def _sorted_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        findings,
        key=lambda finding: (
            SEVERITY_ORDER.get(str(finding.get("severity")), 99),
            str(finding.get("finding_id", "")),
        ),
    )


def _ensure_scope(request: dict[str, Any]) -> tuple[list[str], str, str | None]:
    scope = request.get("scope")
    if not isinstance(scope, dict):
        raise ValueError("audit request scope must be an object")

    scope_paths = scope.get("paths")
    if not isinstance(scope_paths, list) or not scope_paths or not all(
        isinstance(path_value, str) and path_value for path_value in scope_paths
    ):
        raise ValueError("audit request scope.paths must be a non-empty list of strings")

    subsystem = scope.get("subsystem")
    if not isinstance(subsystem, str) or not subsystem:
        raise ValueError("audit request scope.subsystem must be a non-empty string")

    area_hint = scope.get("area_id")
    if area_hint is not None and (not isinstance(area_hint, str) or not area_hint):
        raise ValueError("audit request scope.area_id must be a non-empty string when provided")

    return scope_paths, subsystem, area_hint


def _normalise_scope(
    *,
    scope_paths: list[str],
    subsystem: str,
    requested_area_id: str | None,
) -> dict[str, Any]:
    extracted_scope = extract_scope(scope_paths)
    project_area = normalise_project_area(
        extracted_scope,
        subsystem=subsystem,
    )
    if requested_area_id is not None and requested_area_id != project_area["area_id"]:
        raise ValueError(
            "audit request scope.area_id does not match the area inferred from extracted files"
        )
    return project_area


def build_audit_result(request: dict[str, Any]) -> dict[str, Any]:
    validate_with_schema(request, "audit-request.schema.json")
    standards_version = str(request["standards_version"])
    evaluated_at = _deterministic_timestamp(standards_version)
    scope_paths, subsystem, area_hint = _ensure_scope(request)
    project_area = _normalise_scope(
        scope_paths=scope_paths,
        subsystem=subsystem,
        requested_area_id=area_hint,
    )

    requested_domains = [str(domain) for domain in request["domains"]]
    findings: list[dict[str, Any]] = []
    recommended_actions: list[str] = []
    scores: dict[str, int] = {}
    domain_status: dict[str, dict[str, str]] = {}

    for domain in requested_domains:
        evaluator = EVALUATORS.get(domain)
        if evaluator is not None:
            evaluation = evaluator(
                project_area,
                standards_version=standards_version,
                evaluated_at=evaluated_at,
            )
            scores[domain] = int(evaluation["score"])
            findings.extend(evaluation["findings"])
            recommended_actions.extend(evaluation["recommended_actions"])
            domain_status[domain] = {"status": "evaluated"}
            continue

        domain_status[domain] = {
            "status": "not_evaluated",
            "reason": f"{domain.title()} evaluator is not implemented in this phase.",
        }
        recommended_actions.append(
            f"{domain.title()} domain was requested but not evaluated in this phase."
        )

    sorted_findings = _sorted_findings(findings)
    result = {
        "audit_id": f"audit-{subsystem}-{standards_version}",
        "scope": {
            **request["scope"],
            "area_id": project_area["area_id"],
        },
        "domain_status": domain_status,
        "scores": scores,
        "summary": _summary_counts(sorted_findings),
        "findings": sorted_findings,
        "drift": [],
        "regressions": [],
        "recommended_actions": _ordered_unique(recommended_actions),
        "generated_at": evaluated_at,
    }
    validate_with_schema(result, "audit-result.schema.json")
    return result
