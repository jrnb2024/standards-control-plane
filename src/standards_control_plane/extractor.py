"""Repo-bounded scope extraction."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .resources import project_root
from .schema_tools import validate_with_schema


def _repo_root(root: Path | None) -> Path:
    return (root or project_root()).resolve()


def _canonical_relative(path: Path, repo_root: Path) -> str:
    return str(path.resolve().relative_to(repo_root)).replace("\\", "/")


def _ensure_within_repo(path: Path, repo_root: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(repo_root):
        raise ValueError(f"{label} escapes repo boundary: {path}")
    return resolved


def _ensure_within_scope(path: Path, scope_root: Path, label: str) -> Path:
    resolved = path.resolve()
    resolved_scope_root = scope_root.resolve()
    if resolved_scope_root.is_dir():
        if not resolved.is_relative_to(resolved_scope_root):
            raise ValueError(f"{label} escapes requested scope: {path}")
        return resolved
    if resolved != resolved_scope_root:
        raise ValueError(f"{label} escapes requested scope: {path}")
    return resolved


def _ensure_no_symlink_ancestors(path: Path, repo_root: Path, label: str) -> None:
    absolute_path = path if path.is_absolute() else (repo_root / path)
    try:
        relative_parts = absolute_path.relative_to(repo_root).parts
    except ValueError:
        return

    current = repo_root
    for part in relative_parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{label} contains unsupported symlink ancestor: {current}")


def _resolve_scope_path(path_value: str, repo_root: Path) -> tuple[str, Path]:
    candidate = Path(path_value)
    scoped_candidate = candidate if candidate.is_absolute() else (repo_root / candidate)
    _ensure_no_symlink_ancestors(scoped_candidate, repo_root, "Scope path")
    if scoped_candidate.is_symlink():
        raise ValueError(f"Scope path symlinks are not supported: {path_value}")
    resolved = scoped_candidate.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Scope path not found: {path_value}")
    bounded = _ensure_within_repo(resolved, repo_root, "Scope path")
    return (_canonical_relative(bounded, repo_root), bounded)


def _iter_files(root_path: Path, repo_root: Path) -> list[Path]:
    if root_path.is_file():
        return [_ensure_within_scope(_ensure_within_repo(root_path, repo_root, "Scope file"), root_path, "Scope file")]

    collected: list[Path] = []
    for current_dir, dirnames, filenames in os.walk(root_path, followlinks=False):
        current_path = _ensure_within_repo(Path(current_dir), repo_root, "Walk path")
        _ensure_within_scope(current_path, root_path, "Walk path")
        dirnames[:] = sorted(dirnames)
        for dirname in dirnames:
            if (current_path / dirname).is_symlink():
                raise ValueError(f"Symlinked directories are not supported in extracted scope: {current_path / dirname}")
            candidate_dir = _ensure_within_repo(current_path / dirname, repo_root, "Discovered directory")
            _ensure_within_scope(candidate_dir, root_path, "Discovered directory")
        for filename in sorted(filenames):
            if (current_path / filename).is_symlink():
                raise ValueError(f"Symlinked files are not supported in extracted scope: {current_path / filename}")
            candidate = _ensure_within_repo(current_path / filename, repo_root, "Discovered file")
            _ensure_within_scope(candidate, root_path, "Discovered file")
            if candidate.is_file():
                collected.append(candidate)
    return collected


def extract_scope(scope_paths: list[str], repo_root: Path | None = None) -> dict[str, Any]:
    if not scope_paths:
        raise ValueError("At least one scope path is required")

    resolved_repo_root = _repo_root(repo_root)
    resolved_scope_paths = sorted({_resolve_scope_path(path_value, resolved_repo_root)[0] for path_value in scope_paths})

    files_by_path: dict[str, dict[str, str]] = {}
    for scope_path in resolved_scope_paths:
        _, resolved_scope = _resolve_scope_path(scope_path, resolved_repo_root)
        for resolved_file in _iter_files(resolved_scope, resolved_repo_root):
            canonical_path = _canonical_relative(resolved_file, resolved_repo_root)
            files_by_path.setdefault(
                canonical_path,
                {
                    "path": canonical_path,
                    "extension": resolved_file.suffix.lower(),
                    "source_scope_path": scope_path,
                },
            )

    payload = {
        "scope_paths": resolved_scope_paths,
        "files": [files_by_path[path_value] for path_value in sorted(files_by_path)],
    }
    validate_with_schema(payload, "extracted-scope.schema.json")
    return payload
