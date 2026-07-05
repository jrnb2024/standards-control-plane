"""Audit request assembly and evaluator dispatch."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .evaluators import (
    evaluate_architecture,
    evaluate_design,
    evaluate_governance,
    evaluate_product,
    evaluate_service_lifecycle,
    evaluate_ux,
)
from .extractor import extract_scope
from .normaliser import AreaIdInferenceError, normalise_project_area
from .registry import RegistrySnapshot
from .schema_tools import validate_with_schema
from .scoring import score_findings
from .waivers import load_waivers, select_active_waivers

EVALUATORS = {
    "architecture": evaluate_architecture,
    "design": evaluate_design,
    "governance": evaluate_governance,
    "product": evaluate_product,
    "service-lifecycle": evaluate_service_lifecycle,
    "ux": evaluate_ux,
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
        "high_severity_count": sum(
            1
            for finding in findings
            if finding["status"] == "open" and finding["severity"] == "high"
        ),
        "medium_severity_count": sum(
            1
            for finding in findings
            if finding["status"] == "open" and finding["severity"] == "medium"
        ),
        "low_severity_count": sum(
            1
            for finding in findings
            if finding["status"] == "open" and finding["severity"] == "low"
        ),
        "waived_count": sum(1 for finding in findings if finding["status"] == "waived"),
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


def _recommended_actions(findings: list[dict[str, Any]]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for finding in findings:
        if finding.get("status") != "open":
            continue
        for action in finding.get("suggested_remediation", []):
            action_value = str(action)
            if action_value in seen:
                continue
            ordered.append(action_value)
            seen.add(action_value)
    return ordered


def _apply_waivers(
    findings: list[dict[str, Any]],
    active_waivers: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    adjusted: list[dict[str, Any]] = []
    applied: list[dict[str, str]] = []
    for finding in findings:
        finding_id = str(finding["finding_id"])
        waiver = active_waivers.get(finding_id)
        if waiver is None:
            adjusted.append(dict(finding))
            continue
        adjusted.append({**finding, "status": "waived"})
        applied.append(waiver.to_dict())
    applied.sort(key=lambda waiver: (waiver["finding_id"], waiver["waiver_id"]))
    return adjusted, applied


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
    repo_root: Path | None = None,
) -> dict[str, Any]:
    extracted_scope = extract_scope(scope_paths, repo_root=repo_root)
    # Prefer inference from the extracted scope (ENH specs, frontend routes)
    # so a mismatched requested area_id still raises. Fall back to the
    # requested area_id as the hint only when inference has no signal —
    # this lets adopters audit scopes without an ENH-style placeholder
    # (e.g. a root-level services.yml dogfood) by supplying area_id
    # explicitly in the request.
    try:
        project_area = normalise_project_area(
            extracted_scope,
            subsystem=subsystem,
        )
    except AreaIdInferenceError:
        if requested_area_id is None:
            raise
        return normalise_project_area(
            extracted_scope,
            subsystem=subsystem,
            area_hint=requested_area_id,
        )
    if requested_area_id is not None and requested_area_id != project_area["area_id"]:
        raise ValueError(
            "audit request scope.area_id does not match the area inferred from extracted files"
        )
    return project_area


def build_audit_result(
    request: dict[str, Any],
    *,
    waivers_path: Path | None = None,
    registry_snapshot: RegistrySnapshot | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    validate_with_schema(request, "audit-request.schema.json")
    standards_version = str(request["standards_version"])
    evaluated_at = _deterministic_timestamp(standards_version)
    scope_paths, subsystem, area_hint = _ensure_scope(request)
    # repo_root threads the audit target down to extract_scope so a changed-file
    # audit of an adopter repo reads that repo's files, not the SCP checkout.
    # Defaults to None => extract_scope keeps its project_root() default, so the
    # plain `audit` command and SCP self-dogfood are unchanged.
    project_area = _normalise_scope(
        scope_paths=scope_paths,
        subsystem=subsystem,
        requested_area_id=area_hint,
        repo_root=repo_root,
    )

    requested_domains = [str(domain) for domain in request["domains"]]
    active_waivers = select_active_waivers(
        load_waivers(waivers_path),
        audit_timestamp=evaluated_at,
    )
    findings: list[dict[str, Any]] = []
    recommended_actions: list[str] = []
    waivers_applied: list[dict[str, str]] = []
    scores: dict[str, int] = {}
    domain_status: dict[str, dict[str, str]] = {}

    for domain in requested_domains:
        evaluator = EVALUATORS.get(domain)
        if evaluator is not None:
            evaluation = evaluator(
                project_area,
                standards_version=standards_version,
                evaluated_at=evaluated_at,
                registry_snapshot=registry_snapshot,
            )
            domain_findings, domain_waivers = _apply_waivers(
                list(evaluation["findings"]),
                active_waivers,
            )
            sorted_domain_findings = _sorted_findings(domain_findings)
            scores[domain] = score_findings(sorted_domain_findings)
            findings.extend(sorted_domain_findings)
            recommended_actions.extend(_recommended_actions(sorted_domain_findings))
            waivers_applied.extend(domain_waivers)
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
    sorted_waivers = sorted(
        waivers_applied,
        key=lambda waiver: (waiver["finding_id"], waiver["waiver_id"]),
    )
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
        "waivers_applied": sorted_waivers,
        "drift": [],
        "regressions": [],
        "recommended_actions": _ordered_unique(recommended_actions),
        "generated_at": evaluated_at,
    }
    validate_with_schema(result, "audit-result.schema.json")
    return result
