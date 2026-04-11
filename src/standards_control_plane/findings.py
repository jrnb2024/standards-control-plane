"""Findings store loading, consult matching, and persistence helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterable

from .resources import output_dir, project_root
from .schema_tools import load_json_file, validate_with_schema

DEFAULT_STORE_VERSION = "0.1.0"
OPEN_FINDINGS_FILENAME = "open-findings.json"
HISTORY_FINDINGS_FILENAME = "findings-history.json"

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


def _finding_sort_key(finding: FindingRecord) -> tuple[str, str, str]:
    return (
        finding.domain,
        finding.area_id,
        finding.finding_id,
    )


def _sorted_findings(findings: Iterable[FindingRecord]) -> tuple[FindingRecord, ...]:
    return tuple(sorted(findings, key=_finding_sort_key))


def _clone_finding(
    finding: FindingRecord,
    *,
    status: str | None = None,
    created_at: str | None = None,
    updated_at: str | None = None,
) -> FindingRecord:
    return FindingRecord(
        finding_id=finding.finding_id,
        domain=finding.domain,
        severity=finding.severity,
        status=status or finding.status,
        title=finding.title,
        summary=finding.summary,
        evidence=finding.evidence,
        area_id=finding.area_id,
        suggested_remediation=finding.suggested_remediation,
        confidence=finding.confidence,
        detected_by=finding.detected_by,
        standards_version=finding.standards_version,
        created_at=created_at or finding.created_at,
        updated_at=updated_at or finding.updated_at,
        rule_id=finding.rule_id,
    )


def _findings_dir(base_dir: Path | None = None) -> Path:
    return base_dir or (output_dir() / "findings")


def _findings_paths(base_dir: Path | None = None) -> tuple[Path, Path]:
    root = _findings_dir(base_dir)
    return root / OPEN_FINDINGS_FILENAME, root / HISTORY_FINDINGS_FILENAME


def empty_findings_store(
    *,
    generated_at: str,
    store_version: str = DEFAULT_STORE_VERSION,
) -> FindingsStore:
    return FindingsStore(
        store_version=store_version,
        generated_at=generated_at,
        findings=(),
    )


def _store_version(*stores: FindingsStore) -> str:
    versions = {store.store_version for store in stores}
    if not versions:
        return DEFAULT_STORE_VERSION
    if len(versions) != 1:
        raise ValueError("Persisted findings stores must use the same store_version")
    return next(iter(versions))


def load_findings_store(path: Path | None = None) -> FindingsStore:
    findings_path = path or (output_dir() / "findings" / OPEN_FINDINGS_FILENAME)
    payload = _ensure_object(load_json_file(findings_path), "findings store")
    validate_with_schema(payload, "findings-store.schema.json")
    findings_payload = payload.get("findings", [])
    if not isinstance(findings_payload, list):
        raise TypeError("findings store findings must be a list")
    return FindingsStore(
        store_version=_ensure_string(payload["store_version"], "store_version"),
        generated_at=_ensure_string(payload["generated_at"], "generated_at"),
        findings=_sorted_findings(_load_finding(item) for item in findings_payload),
    )


def load_findings_store_or_empty(
    path: Path,
    *,
    generated_at: str,
    store_version: str = DEFAULT_STORE_VERSION,
) -> FindingsStore:
    if path.exists():
        return load_findings_store(path)
    return empty_findings_store(generated_at=generated_at, store_version=store_version)


def _ensure_scope_match(left: FindingRecord, right: FindingRecord, *, context: str) -> None:
    if left.domain != right.domain or left.area_id != right.area_id:
        raise ValueError(
            f"{context} reused finding_id {left.finding_id} across different scope pairs"
        )


def _merge_existing_record(
    existing: FindingRecord | None,
    candidate: FindingRecord,
) -> FindingRecord:
    if existing is None:
        return candidate
    _ensure_scope_match(existing, candidate, context="Persisted findings stores")
    if existing.to_dict() == candidate.to_dict():
        return existing
    if existing.updated_at != candidate.updated_at:
        return existing if existing.updated_at > candidate.updated_at else candidate
    if existing.status == "open" and candidate.status != "open":
        return existing
    if candidate.status == "open" and existing.status != "open":
        return candidate
    raise ValueError(
        f"Persisted findings stores disagree for finding_id {candidate.finding_id}"
    )


def _merge_existing_stores(
    history_store: FindingsStore,
    open_store: FindingsStore,
) -> dict[str, FindingRecord]:
    merged: dict[str, FindingRecord] = {}
    for finding in history_store.findings:
        merged[finding.finding_id] = _merge_existing_record(
            merged.get(finding.finding_id),
            finding,
        )
    for finding in open_store.findings:
        merged[finding.finding_id] = _merge_existing_record(
            merged.get(finding.finding_id),
            finding,
        )
    return merged


def _deduplicate_audit_findings(audit_result: dict[str, Any]) -> dict[str, FindingRecord]:
    deduplicated: dict[str, FindingRecord] = {}
    findings_payload = audit_result.get("findings", [])
    if not isinstance(findings_payload, list):
        raise TypeError("audit result findings must be a list")
    for finding_payload in findings_payload:
        record = _load_finding(finding_payload)
        existing = deduplicated.get(record.finding_id)
        if existing is None:
            deduplicated[record.finding_id] = record
            continue
        _ensure_scope_match(existing, record, context="Audit result")
        if existing.to_dict() != record.to_dict():
            raise ValueError(
                f"Audit result contains conflicting duplicate payloads for {record.finding_id}"
            )
    return deduplicated


def reconcile_findings(
    audit_result: dict[str, Any],
    *,
    open_store: FindingsStore | None = None,
    history_store: FindingsStore | None = None,
) -> tuple[FindingsStore, FindingsStore]:
    validate_with_schema(audit_result, "audit-result.schema.json")

    generated_at = _ensure_string(audit_result["generated_at"], "audit result generated_at")
    scope = _ensure_object(audit_result["scope"], "audit result scope")
    scope_area_id = _ensure_string(scope["area_id"], "audit result scope.area_id")
    current_findings = _deduplicate_audit_findings(audit_result)

    default_version = DEFAULT_STORE_VERSION
    current_open_store = open_store or empty_findings_store(
        generated_at=generated_at,
        store_version=default_version,
    )
    current_history_store = history_store or empty_findings_store(
        generated_at=generated_at,
        store_version=current_open_store.store_version,
    )
    store_version = _store_version(current_open_store, current_history_store)

    domain_status = audit_result.get("domain_status", {})
    if not isinstance(domain_status, dict):
        raise TypeError("audit result domain_status must be an object")
    evaluated_domains = {
        domain
        for domain, status in domain_status.items()
        if isinstance(status, dict) and status.get("status") == "evaluated"
    }

    existing_records = _merge_existing_stores(current_history_store, current_open_store)
    reconciled_history: dict[str, FindingRecord] = dict(existing_records)

    for finding_id, finding in current_findings.items():
        if finding.domain not in evaluated_domains:
            raise ValueError(
                f"Audit result finding {finding_id} is not in an evaluated domain"
            )
        existing = reconciled_history.get(finding_id)
        if existing is not None:
            _ensure_scope_match(existing, finding, context="Reconciliation")
        reconciled_history[finding_id] = _clone_finding(
            finding,
            status="open",
            created_at=existing.created_at if existing is not None else finding.created_at,
            updated_at=generated_at,
        )

    for finding_id, finding in list(reconciled_history.items()):
        if finding_id in current_findings:
            continue
        if finding.status != "open":
            continue
        if finding.area_id != scope_area_id:
            continue
        if finding.domain not in evaluated_domains:
            continue
        reconciled_history[finding_id] = _clone_finding(
            finding,
            status="resolved",
            updated_at=generated_at,
        )

    history_result = FindingsStore(
        store_version=store_version,
        generated_at=generated_at,
        findings=_sorted_findings(reconciled_history.values()),
    )
    open_result = FindingsStore(
        store_version=store_version,
        generated_at=generated_at,
        findings=tuple(
            finding for finding in history_result.findings if finding.status == "open"
        ),
    )

    validate_with_schema(open_result.to_dict(), "findings-store.schema.json")
    validate_with_schema(history_result.to_dict(), "findings-store.schema.json")
    return open_result, history_result


def _stage_json_payload(target_path: Path, payload: dict[str, Any]) -> Path:
    validate_with_schema(payload, "findings-store.schema.json")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=target_path.parent,
        delete=False,
        prefix=f".{target_path.name}.",
        suffix=".tmp",
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        return Path(handle.name)


def _stage_backup(target_path: Path) -> Path | None:
    if not target_path.exists():
        return None
    with NamedTemporaryFile(
        mode="wb",
        dir=target_path.parent,
        delete=False,
        prefix=f".{target_path.name}.",
        suffix=".bak",
    ) as handle:
        handle.write(target_path.read_bytes())
        return Path(handle.name)


def _cleanup_path(path: Path | None) -> None:
    if path is not None and path.exists():
        path.unlink()


def write_findings_stores(
    open_store: FindingsStore,
    history_store: FindingsStore,
    *,
    findings_dir: Path | None = None,
) -> tuple[Path, Path]:
    open_path, history_path = _findings_paths(findings_dir)
    staged_open = _stage_json_payload(open_path, open_store.to_dict())
    staged_history = _stage_json_payload(history_path, history_store.to_dict())
    backup_open = _stage_backup(open_path)
    backup_history = _stage_backup(history_path)

    try:
        os.replace(staged_open, open_path)
        staged_open = None
        os.replace(staged_history, history_path)
        staged_history = None
    except Exception:
        if backup_open is not None:
            os.replace(backup_open, open_path)
            backup_open = None
        elif open_path.exists():
            open_path.unlink()
        if backup_history is not None:
            os.replace(backup_history, history_path)
            backup_history = None
        elif history_path.exists():
            history_path.unlink()
        raise
    finally:
        _cleanup_path(staged_open)
        _cleanup_path(staged_history)
        _cleanup_path(backup_open)
        _cleanup_path(backup_history)

    return open_path, history_path


def persist_audit_findings(
    audit_result: dict[str, Any],
    *,
    findings_dir: Path | None = None,
) -> tuple[FindingsStore, FindingsStore]:
    validate_with_schema(audit_result, "audit-result.schema.json")
    generated_at = _ensure_string(audit_result["generated_at"], "audit result generated_at")
    open_path, history_path = _findings_paths(findings_dir)
    history_store = load_findings_store_or_empty(
        history_path,
        generated_at=generated_at,
    )
    open_store = load_findings_store_or_empty(
        open_path,
        generated_at=generated_at,
        store_version=history_store.store_version,
    )
    reconciled_open, reconciled_history = reconcile_findings(
        audit_result,
        open_store=open_store,
        history_store=history_store,
    )
    write_findings_stores(
        reconciled_open,
        reconciled_history,
        findings_dir=findings_dir,
    )
    return reconciled_open, reconciled_history


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
