"""Changed-file scoped audit helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .audit import build_audit_result
from .registry import RegistrySnapshot
from .resources import project_root
from .schema_tools import validate_with_schema


def _repo_root(repo_root: Path | None = None) -> Path:
    return (repo_root or project_root()).resolve()


def list_changed_files(
    *,
    base_ref: str,
    head_ref: str,
    repo_root: Path | None = None,
) -> list[str]:
    root = _repo_root(repo_root)
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            base_ref,
            head_ref,
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    changed_paths: list[str] = []
    seen: set[str] = set()
    for line in completed.stdout.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        resolved = (root / candidate).resolve()
        if not resolved.is_relative_to(root):
            raise ValueError(f"Changed path escapes repo boundary: {candidate}")
        if not resolved.exists():
            continue
        relative = str(resolved.relative_to(root)).replace("\\", "/")
        if relative not in seen:
            seen.add(relative)
            changed_paths.append(relative)
    return sorted(changed_paths)


def build_changed_file_audit_result(
    *,
    base_ref: str,
    head_ref: str,
    domains: list[str],
    subsystem: str,
    standards_version: str,
    area_id: str | None = None,
    changed_paths: list[str] | None = None,
    registry_snapshot: RegistrySnapshot | None = None,
) -> dict[str, Any]:
    paths = changed_paths or list_changed_files(base_ref=base_ref, head_ref=head_ref)
    if not paths:
        raise ValueError("No changed files remain after repo-bounded filtering")
    request: dict[str, Any] = {
        "mode": "audit",
        "domains": domains,
        "scope": {
            "paths": paths,
            "subsystem": subsystem,
        },
        "standards_version": standards_version,
    }
    if area_id is not None:
        request["scope"]["area_id"] = area_id

    audit_result = build_audit_result(request, registry_snapshot=registry_snapshot)
    result = {
        "base_ref": base_ref,
        "head_ref": head_ref,
        "changed_paths": paths,
        "audit_result": audit_result,
    }
    validate_with_schema(result, "changed-audit-result.schema.json")
    return result
