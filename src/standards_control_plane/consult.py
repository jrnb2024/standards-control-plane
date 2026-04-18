"""Consult response assembly."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .confidence import classify_confidence
from .findings import FindingRecord, load_findings_store, select_consult_findings
from .registry import PatternRecord, RegistrySnapshot, RuleRecord, load_registry
from .review_evidence import select_historical_reviews
from .schema_tools import validate_with_schema


def _make_request_id(request: dict[str, Any]) -> str:
    canonical = json.dumps(request, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:12]
    return f"consult-{digest}"


def _dedupe_strings(values: list[str], limit: int) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
        if len(ordered) >= limit:
            break
    return ordered


def _unique_ordered(values: list[str]) -> list[str]:
    return _dedupe_strings(values, limit=len(values))


def _is_frontend_request(request: dict[str, Any], requested_domains: list[str]) -> bool:
    if any(domain in {"ux", "design", "product"} for domain in requested_domains):
        return True
    request_paths = request.get("paths", [])
    if isinstance(request_paths, list):
        for path_value in request_paths:
            if not isinstance(path_value, str):
                continue
            normalised = path_value.replace("\\", "/").lower()
            if normalised.endswith((".tsx", ".jsx")) or "/frontend/" in normalised:
                return True
    return False


def _domain_priority(domain: str, *, frontend: bool) -> int:
    if frontend:
        order = {
            "ux": 0,
            "design": 1,
            "architecture": 2,
            "product": 3,
            "governance": 4,
            "service-lifecycle": 5,
        }
    else:
        order = {
            "governance": 0,
            "architecture": 1,
            "service-lifecycle": 2,
            "ux": 3,
            "design": 4,
            "product": 5,
        }
    return order.get(domain, 99)


def _pattern_match_score(pattern: PatternRecord, request_text: str) -> int:
    lowered = request_text.lower()
    return sum(1 for tag in pattern.tags if tag.lower() in lowered)


def _order_patterns(
    patterns: list[PatternRecord],
    *,
    request: dict[str, Any],
    requested_domains: list[str],
) -> list[PatternRecord]:
    frontend = _is_frontend_request(request, requested_domains)
    request_text = " ".join(
        [
            str(request.get("question", "")),
            str(request.get("area_id", "")),
            (
                str(request.get("task_context", {}).get("feature_summary", ""))
                if isinstance(request.get("task_context"), dict)
                else ""
            ),
            " ".join(str(path) for path in request.get("paths", []) if isinstance(path, str)),
        ]
    )
    return sorted(
        patterns,
        key=lambda pattern: (
            _domain_priority(pattern.domain, frontend=frontend),
            -_pattern_match_score(pattern, request_text),
            pattern.pattern_id,
        ),
    )


def _order_rules(
    rules: list[RuleRecord],
    *,
    request: dict[str, Any],
    requested_domains: list[str],
) -> list[RuleRecord]:
    frontend = _is_frontend_request(request, requested_domains)
    return sorted(
        rules,
        key=lambda rule: (
            _domain_priority(rule.domain, frontend=frontend),
            rule.rule_id,
        ),
    )


def _order_findings(
    findings: list[FindingRecord],
    *,
    request: dict[str, Any],
    requested_domains: list[str],
) -> list[FindingRecord]:
    frontend = _is_frontend_request(request, requested_domains)
    severity_priority = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(
        findings,
        key=lambda finding: (
            severity_priority.get(finding.severity, 99),
            _domain_priority(finding.domain, frontend=frontend),
            finding.finding_id,
        ),
    )


def _build_guidance(
    rules: list[RuleRecord],
    patterns: list[PatternRecord],
    findings: list[FindingRecord],
) -> list[str]:
    candidates = [pattern.summary for pattern in patterns]
    candidates.extend(
        remediation
        for finding in findings
        for remediation in list(finding.suggested_remediation)[:1]
    )
    candidates.extend(rule.summary for rule in rules)
    return _dedupe_strings(candidates, limit=5)


def _build_risks(rules: list[RuleRecord], findings: list[FindingRecord]) -> list[str]:
    candidates = [rule.signals[0] for rule in rules if rule.signals]
    candidates.extend(finding.summary for finding in findings)
    return _dedupe_strings(candidates, limit=5)


def _calculate_confidence(
    requested_domains: list[str],
    rules: list[RuleRecord],
    patterns: list[PatternRecord],
    findings: list[FindingRecord],
) -> float:
    covered_domains = {rule.domain for rule in rules}
    coverage_bonus = 0.05 * min(len(covered_domains), len(requested_domains))
    pattern_bonus = 0.05 if patterns else 0.0
    findings_bonus = 0.05 if findings else 0.0
    return round(min(0.95, 0.75 + coverage_bonus + pattern_bonus + findings_bonus), 2)


def build_consult_response(
    request: dict[str, Any],
    *,
    registry_snapshot: RegistrySnapshot | None = None,
) -> dict[str, Any]:
    validate_with_schema(request, "consult-request.schema.json")

    registry = registry_snapshot or load_registry()
    findings_store = load_findings_store()

    requested_domains = _unique_ordered([str(domain) for domain in request["domains"]])
    rules = _order_rules(
        registry.active_rules_for(requested_domains),
        request=request,
        requested_domains=requested_domains,
    )
    patterns = _order_patterns(
        registry.active_patterns_for(requested_domains),
        request=request,
        requested_domains=requested_domains,
    )
    findings = _order_findings(
        select_consult_findings(
        findings_store,
        requested_domains=requested_domains,
        area_id=str(request["area_id"]),
        request_paths=_unique_ordered([str(path) for path in request["paths"]]),
    ),
        request=request,
        requested_domains=requested_domains,
    )
    historical_reviews = select_historical_reviews(
        area_id=str(request["area_id"]),
        request_paths=_unique_ordered([str(path) for path in request["paths"]]),
    )

    response = {
        "request_id": _make_request_id(request),
        "domains": requested_domains,
        "approved_patterns": [
            {
                "pattern_id": pattern.pattern_id,
                "reason": pattern.summary,
            }
            for pattern in patterns
        ],
        "open_findings": [
            {
                "finding_id": finding.finding_id,
                "severity": finding.severity,
                "summary": finding.summary,
                "confidence_class": finding.confidence_class,
            }
            for finding in findings
        ],
        "historical_reviews": historical_reviews,
        "applicable_rules": [
            {
                "rule_id": rule.rule_id,
                "reason": rule.summary,
            }
            for rule in rules
        ],
        "guidance": _build_guidance(rules, patterns, findings),
        "risks": _build_risks(rules, findings),
        "confidence": _calculate_confidence(requested_domains, rules, patterns, findings),
    }
    response["confidence_class"] = classify_confidence(float(response["confidence"]))
    validate_with_schema(response, "consult-response.schema.json")
    return response
