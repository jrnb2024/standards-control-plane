"""Structured review-evidence parsing and selection."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .resources import audit_repo_root, project_root
from .schema_tools import validate_with_schema

REVIEW_BLOCK_PATTERN = re.compile(
    r"```scp-review-evidence\s*\n(.*?)\n```",
    flags=re.DOTALL,
)


def _ensure_object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{context} must be an object")
    return value


def _ensure_string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{context} must be a non-empty string")
    return value


def _ensure_string_list(value: Any, context: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise TypeError(f"{context} must be a list of non-empty strings")
    return tuple(value)


def _paths_overlap(left: str, right: str) -> bool:
    left_parts = left.replace("\\", "/")
    right_parts = right.replace("\\", "/")
    return (
        left_parts == right_parts
        or left_parts.endswith(right_parts)
        or right_parts.endswith(left_parts)
    )


def _resolve_repo_path(path_value: str) -> Path:
    root = (audit_repo_root() or project_root()).resolve()
    candidate = (root / path_value).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError(f"Review evidence path escapes project root: {path_value}")
    if not candidate.exists():
        raise FileNotFoundError(f"Review evidence path not found in repo: {path_value}")
    return candidate


def _parse_reviewed_at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class ReviewEvidenceFinding:
    finding_id: str
    status: str
    summary: str
    domain: str | None = None


@dataclass(frozen=True)
class ReviewEvidenceRecord:
    review_id: str
    area_id: str
    reviewed_at: str
    summary: str
    reviewed_paths: tuple[str, ...]
    findings: tuple[ReviewEvidenceFinding, ...]
    source_path: str


def _load_review_finding(entry: Any) -> ReviewEvidenceFinding:
    payload = _ensure_object(entry, "review evidence finding")
    return ReviewEvidenceFinding(
        finding_id=_ensure_string(payload["finding_id"], "review evidence finding_id"),
        status=_ensure_string(payload["status"], "review evidence status"),
        summary=_ensure_string(payload["summary"], "review evidence summary"),
        domain=payload.get("domain") if isinstance(payload.get("domain"), str) else None,
    )


def parse_review_evidence_file(path_value: str) -> ReviewEvidenceRecord | None:
    resolved_path = _resolve_repo_path(path_value)
    text = resolved_path.read_text(encoding="utf-8")
    match = REVIEW_BLOCK_PATTERN.search(text)
    if match is None:
        return None
    payload = json.loads(match.group(1))
    validate_with_schema(payload, "review-evidence.schema.json")
    payload = _ensure_object(payload, "review evidence")
    reviewed_paths = _ensure_string_list(payload["reviewed_paths"], "reviewed_paths")
    return ReviewEvidenceRecord(
        review_id=_ensure_string(payload["review_id"], "review_id"),
        area_id=_ensure_string(payload["area_id"], "area_id"),
        reviewed_at=_ensure_string(payload["reviewed_at"], "reviewed_at"),
        summary=_ensure_string(payload["summary"], "summary"),
        reviewed_paths=reviewed_paths,
        findings=tuple(_load_review_finding(item) for item in payload["findings"]),
        source_path=path_value,
    )


def load_review_evidence_records(paths: list[str]) -> tuple[ReviewEvidenceRecord, ...]:
    records: list[ReviewEvidenceRecord] = []
    for path_value in sorted(set(paths)):
        record = parse_review_evidence_file(path_value)
        if record is not None:
            records.append(record)
    return tuple(records)


def _candidate_review_paths() -> list[str]:
    root = project_root()
    candidates = {
        str(path.relative_to(root)).replace("\\", "/")
        for path in list(root.glob("docs/reviews/**/review_findings.md"))
        + list(root.glob("fixtures/**/docs/reviews/**/review_findings.md"))
    }
    return sorted(candidates)


def select_historical_reviews(
    *,
    area_id: str,
    request_paths: list[str],
    limit: int = 3,
) -> list[dict[str, str]]:
    records = load_review_evidence_records(_candidate_review_paths())

    def sort_key(record: ReviewEvidenceRecord) -> tuple[int, int, float, str]:
        exact_area = record.area_id == area_id
        path_overlap = any(
            _paths_overlap(reviewed_path, request_path)
            for reviewed_path in record.reviewed_paths
            for request_path in request_paths
        )
        return (
            0 if exact_area else 1,
            0 if path_overlap else 1,
            -_parse_reviewed_at(record.reviewed_at).timestamp(),
            record.source_path,
        )

    selected = [
        record
        for record in records
        if record.area_id == area_id
        or any(
            _paths_overlap(reviewed_path, request_path)
            for reviewed_path in record.reviewed_paths
            for request_path in request_paths
        )
    ]
    selected.sort(key=sort_key)
    return [
        {
            "review_id": record.review_id,
            "path": record.source_path,
            "summary": record.summary,
        }
        for record in selected[:limit]
    ]
