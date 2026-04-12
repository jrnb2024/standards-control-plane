"""Consult response assembly."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .confidence import classify_confidence
from .findings import FindingRecord, load_findings_store, select_consult_findings
from .registry import PatternRecord, RuleRecord, load_registry
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


def _build_guidance(rules: list[RuleRecord], patterns: list[PatternRecord]) -> list[str]:
    candidates = [pattern.summary for pattern in patterns]
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


def build_consult_response(request: dict[str, Any]) -> dict[str, Any]:
    validate_with_schema(request, "consult-request.schema.json")

    registry = load_registry()
    findings_store = load_findings_store()

    requested_domains = _unique_ordered([str(domain) for domain in request["domains"]])
    rules = registry.active_rules_for(requested_domains)
    patterns = registry.active_patterns_for(requested_domains)
    findings = select_consult_findings(
        findings_store,
        requested_domains=requested_domains,
        area_id=str(request["area_id"]),
        request_paths=_unique_ordered([str(path) for path in request["paths"]]),
    )
    historical_reviews = select_historical_reviews(
        area_id=str(request["area_id"]),
        request_paths=_unique_ordered([str(path) for path in request["paths"]]),
    )

    response = {
        "request_id": _make_request_id(request),
        "domains": requested_domains,
        "applicable_rules": [
            {
                "rule_id": rule.rule_id,
                "reason": rule.summary,
            }
            for rule in rules
        ],
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
        "guidance": _build_guidance(rules, patterns),
        "risks": _build_risks(rules, findings),
        "confidence": _calculate_confidence(requested_domains, rules, patterns, findings),
    }
    response["confidence_class"] = classify_confidence(float(response["confidence"]))
    validate_with_schema(response, "consult-response.schema.json")
    return response
