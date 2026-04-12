"""Waiver loading and active-waiver selection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .resources import output_dir
from .schema_tools import load_json_file, validate_with_schema

WAIVERS_FILENAME = "waivers.json"


def _ensure_object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{context} must be an object")
    return value


def _ensure_string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{context} must be a non-empty string")
    return value


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class WaiverRecord:
    waiver_id: str
    finding_id: str
    reason: str
    approved_by: str
    expires_at: str
    created_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "waiver_id": self.waiver_id,
            "finding_id": self.finding_id,
            "reason": self.reason,
            "approved_by": self.approved_by,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
        }


def _load_waiver(entry: Any) -> WaiverRecord:
    payload = _ensure_object(entry, "waiver")
    validate_with_schema(payload, "waiver.schema.json")
    return WaiverRecord(
        waiver_id=_ensure_string(payload["waiver_id"], "waiver_id"),
        finding_id=_ensure_string(payload["finding_id"], "finding_id"),
        reason=_ensure_string(payload["reason"], "reason"),
        approved_by=_ensure_string(payload["approved_by"], "approved_by"),
        expires_at=_ensure_string(payload["expires_at"], "expires_at"),
        created_at=_ensure_string(payload["created_at"], "created_at"),
    )


def _waivers_path(path: Path | None = None) -> Path:
    return path or (output_dir() / "findings" / WAIVERS_FILENAME)


def load_waivers(path: Path | None = None) -> tuple[WaiverRecord, ...]:
    waivers_path = _waivers_path(path)
    if not waivers_path.exists():
        return ()
    payload = load_json_file(waivers_path)
    validate_with_schema(payload, "waivers-file.schema.json")
    if not isinstance(payload, list):
        raise TypeError("waivers file must be a list")
    return tuple(
        sorted(
            (_load_waiver(item) for item in payload),
            key=lambda waiver: (
                waiver.finding_id,
                waiver.expires_at,
                waiver.created_at,
                waiver.waiver_id,
            ),
        )
    )


def select_active_waivers(
    waivers: tuple[WaiverRecord, ...],
    *,
    audit_timestamp: str,
) -> dict[str, WaiverRecord]:
    as_of = _parse_timestamp(audit_timestamp)
    active: dict[str, WaiverRecord] = {}
    for waiver in waivers:
        if _parse_timestamp(waiver.expires_at) < as_of:
            continue
        existing = active.get(waiver.finding_id)
        if existing is not None:
            raise ValueError(
                f"Multiple active waivers apply to finding_id {waiver.finding_id}"
            )
        active[waiver.finding_id] = waiver
    return active
