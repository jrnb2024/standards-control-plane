"""Shared deterministic score calculation."""

from __future__ import annotations

from typing import Any, Iterable

SEVERITY_DEDUCTIONS = {
    "critical": 40,
    "high": 30,
    "medium": 15,
    "low": 5,
}

NON_PENALTY_STATUSES = {
    "accepted",
    "false_positive",
    "resolved",
    "superseded",
    "waived",
}


def finding_penalty(finding: dict[str, Any]) -> int:
    status = str(finding.get("status", "open"))
    if status in NON_PENALTY_STATUSES:
        return 0
    severity = str(finding.get("severity"))
    return SEVERITY_DEDUCTIONS[severity]


def score_findings(findings: Iterable[dict[str, Any]]) -> int:
    score = 100
    for finding in findings:
        score -= finding_penalty(finding)
    return max(score, 0)
