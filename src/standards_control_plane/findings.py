"""Read-only findings store loading and consult matching."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .resources import output_dir, project_root
from .schema_tools import load_json_file, validate_with_schema

SEVERITY_RANK = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


def _ensure_object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{context} must be an object")
    return value


def _ensure_string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{context} must be a non-empty string")
    return value


def _ensure_string_list(value: Any, context: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError(f"{context} must be a list of strings")
    return tuple(value)


@dataclass(frozen=True)
class EvidenceRecord:
    path: str
    locator: str | None
    snippet_ref: str | None

    def to_dict(self) -> dict[str, str]:
        result = {"path": self.path}
        if self.locator is not None:
            result["locator"] = self.locator
        if self.snippet_ref is not None:
            result["snippet_ref"] = self.snippet_ref
        return result


@dataclass(frozen=True)
class FindingRecord:
    finding_id: str
    domain: str
    severity: str
    status: str
    title: str
    summary: str
    evidence: tuple[EvidenceRecord, ...]
    area_id: str
    suggested_remediation: tuple[str, ...]
    confidence: float
    detected_by: str
    standards_version: str
    created_at: str
    updated_at: str
    rule_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "finding_id": self.finding_id,
            "domain": self.domain,
            "severity": self.severity,
            "status": self.status,
            "title": self.title,
            "summary": self.summary,
            "evidence": [item.to_dict() for item in self.evidence],
            "area_id": self.area_id,
            "suggested_remediation": list(self.suggested_remediation),
            "confidence": self.confidence,
            "detected_by": self.detected_by,
            "standards_version": self.standards_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.rule_id is not None:
            payload["rule_id"] = self.rule_id
        return payload


@dataclass(frozen=True)
class FindingsStore:
    store_version: str
    generated_at: str
    findings: tuple[FindingRecord, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "store_version": self.store_version,
            "generated_at": self.generated_at,
            "findings": [finding.to_dict() for finding in self.findings],
        }


def _paths_overlap(left: str, right: str) -> bool:
    left_parts = left.replace("\\", "/")
    right_parts = right.replace("\\", "/")
    return (
        left_parts == right_parts
        or left_parts.endswith(right_parts)
        or right_parts.endswith(left_parts)
    )


def _resolve_repo_path(path_value: str) -> Path:
    root = project_root().resolve()
    candidate = (root / path_value).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError(f"Evidence path escapes project root: {path_value}")
    if not candidate.exists():
        raise FileNotFoundError(f"Evidence path not found in repo: {path_value}")
    return candidate


def _load_evidence(entry: Any) -> EvidenceRecord:
    payload = _ensure_object(entry, "finding evidence")
    path_value = _ensure_string(payload["path"], "finding evidence path")
    _resolve_repo_path(path_value)
    return EvidenceRecord(
        path=path_value,
        locator=payload.get("locator") if isinstance(payload.get("locator"), str) else None,
        snippet_ref=payload.get("snippet_ref") if isinstance(payload.get("snippet_ref"), str) else None,
    )


def _load_finding(entry: Any) -> FindingRecord:
    payload = _ensure_object(entry, "finding")
    validate_with_schema(payload, "finding.schema.json")
    evidence_payload = payload.get("evidence", [])
    if not isinstance(evidence_payload, list):
        raise TypeError("finding evidence must be a list")
    return FindingRecord(
        finding_id=_ensure_string(payload["finding_id"], "finding_id"),
        domain=_ensure_string(payload["domain"], "domain"),
        severity=_ensure_string(payload["severity"], "severity"),
        status=_ensure_string(payload["status"], "status"),
        title=_ensure_string(payload["title"], "title"),
        summary=_ensure_string(payload["summary"], "summary"),
        evidence=tuple(_load_evidence(item) for item in evidence_payload),
        area_id=_ensure_string(payload["area_id"], "area_id"),
        suggested_remediation=_ensure_string_list(
            payload.get("suggested_remediation", []),
            "suggested_remediation",
        ),
        confidence=float(payload["confidence"]),
        detected_by=_ensure_string(payload["detected_by"], "detected_by"),
        standards_version=_ensure_string(payload["standards_version"], "standards_version"),
        created_at=_ensure_string(payload["created_at"], "created_at"),
        updated_at=_ensure_string(payload["updated_at"], "updated_at"),
        rule_id=payload.get("rule_id") if isinstance(payload.get("rule_id"), str) else None,
    )


def load_findings_store(path: Path | None = None) -> FindingsStore:
    findings_path = path or (output_dir() / "findings" / "open-findings.json")
    payload = _ensure_object(load_json_file(findings_path), "findings store")
    validate_with_schema(payload, "findings-store.schema.json")
    findings_payload = payload.get("findings", [])
    if not isinstance(findings_payload, list):
        raise TypeError("findings store findings must be a list")
    return FindingsStore(
        store_version=_ensure_string(payload["store_version"], "store_version"),
        generated_at=_ensure_string(payload["generated_at"], "generated_at"),
        findings=tuple(_load_finding(item) for item in findings_payload),
    )


def select_consult_findings(
    store: FindingsStore,
    requested_domains: list[str],
    area_id: str,
    request_paths: list[str],
    limit: int = 5,
) -> list[FindingRecord]:
    def specificity_score(finding: FindingRecord) -> int:
        score = 0
        if finding.area_id == area_id:
            score += 2
        if any(
            _paths_overlap(evidence.path, request_path)
            for evidence in finding.evidence
            for request_path in request_paths
        ):
            score += 1
        return score

    candidates = [
        finding
        for finding in store.findings
        if finding.status == "open"
        and (finding.domain in requested_domains or specificity_score(finding) > 0)
    ]

    return sorted(
        candidates,
        key=lambda finding: (
            -specificity_score(finding),
            0 if finding.domain in requested_domains else 1,
            -SEVERITY_RANK[finding.severity],
            finding.finding_id,
        ),
    )[:limit]
