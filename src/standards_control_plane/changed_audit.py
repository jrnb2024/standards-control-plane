"""Changed-file scoped audit helpers."""

from __future__ import annotations

import os
import re
import subprocess
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from .audit import build_audit_result
from .normaliser import AreaIdInferenceError
from .registry import RegistrySnapshot
from .resources import project_root
from .schema_tools import validate_with_schema


def _repo_root(repo_root: Path | None = None) -> Path:
    return (repo_root or project_root()).resolve()


def resolve_worktree_root(candidate: Path) -> Path:
    """Validate that a caller-supplied path is the root of a git worktree.

    Git prints diff paths relative to the worktree root, so an audit anchored
    at any other directory would silently drop or mis-resolve changed files.
    Returns git's own toplevel path (canonical on-disk casing).
    """
    resolved = candidate.expanduser().resolve()
    if not resolved.is_dir():
        raise ValueError(f"repo root is not a directory: {candidate}")
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=resolved,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(f"repo root is not inside a git worktree: {candidate}")
    toplevel = Path(completed.stdout.strip()).resolve()
    if not os.path.samefile(toplevel, resolved):
        raise ValueError(
            f"repo root must be the root of a git worktree (got '{resolved}', "
            f"worktree root is '{toplevel}')"
        )
    return toplevel


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


def derive_area_id(paths: list[str], subsystem: str) -> str:
    """Derive a deterministic area_id from changed paths.

    Used when the diff carries no inferable area (no ENH spec, no frontend
    route) and the caller supplied no explicit area_id: the most common
    top-level path segment (alphabetical tie-break) is appended to the
    subsystem, e.g. ``mapp-pim-services``.
    """
    counts = Counter(
        PurePosixPath(path.replace("\\", "/").strip("/")).parts[0]
        for path in paths
        if path.strip("/")
    )
    subsystem_slug = re.sub(r"[^a-z0-9]+", "-", subsystem.lower()).strip("-") or "subsystem"
    if not counts:
        return f"{subsystem_slug}-changed"
    top_segment = min(counts, key=lambda segment: (-counts[segment], segment))
    slug = re.sub(r"[^a-z0-9]+", "-", top_segment.lower()).strip("-") or "changed"
    return f"{subsystem_slug}-{slug}"


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
    repo_root: Path | None = None,
) -> dict[str, Any]:
    paths = changed_paths or list_changed_files(
        base_ref=base_ref, head_ref=head_ref, repo_root=repo_root
    )
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

    try:
        audit_result = build_audit_result(
            request, registry_snapshot=registry_snapshot, repo_root=repo_root
        )
    except AreaIdInferenceError:
        # Changed-file diffs routinely carry no ENH spec or frontend route;
        # fall back to a deterministic subsystem-derived area rather than
        # failing the audit.
        request["scope"]["area_id"] = derive_area_id(paths, subsystem)
        audit_result = build_audit_result(
            request, registry_snapshot=registry_snapshot, repo_root=repo_root
        )
    result = {
        "base_ref": base_ref,
        "head_ref": head_ref,
        "changed_paths": paths,
        "audit_result": audit_result,
    }
    validate_with_schema(result, "changed-audit-result.schema.json")
    return result
