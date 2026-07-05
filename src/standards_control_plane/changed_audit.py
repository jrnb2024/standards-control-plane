"""Changed-file scoped audit helpers."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from .audit import build_audit_result
from .registry import RegistrySnapshot
from .resources import project_root
from .schema_tools import validate_with_schema

# GIT_DIR / GIT_WORK_TREE (and friends) in the ambient environment would
# redirect `git rev-parse --show-toplevel` and `git diff` away from the cwd we
# pass, defeating the repo-identity guard: both sides of the cwd/root comparison
# would be poisoned identically and agree while pointing at the wrong repo. Strip
# them from every git subprocess so the cwd we pass stays authoritative.
_GIT_LOCATION_ENV_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")


def git_subprocess_env() -> dict[str, str]:
    """Ambient environment with git repo-location overrides stripped."""
    return {key: value for key, value in os.environ.items() if key not in _GIT_LOCATION_ENV_VARS}


class RepoRootResolutionError(ValueError):
    """Raised when the changed-file audit repo root cannot be safely resolved.

    Replaces the historical silent fallback to ``project_root()`` (the
    standards-control-plane checkout itself). That fallback produced
    false-clean verdicts about the WRONG repository whenever ``audit-changed``
    ran from an adopter's working directory: the diff resolved against SCP's
    own tree, not the caller's. Rather than default to SCP, resolution now
    fails loudly. See WP-SCP-038.
    """


def _repo_root(repo_root: Path | None = None) -> Path:
    # Historical note: this used to default to ``project_root()`` (the SCP
    # checkout). It now defaults to the caller's working directory so a direct
    # ``list_changed_files`` caller never silently diffs SCP. The audit entry
    # point (``build_changed_file_audit_result``) resolves + validates the root
    # via ``resolve_audit_repo_root`` before this is ever reached.
    return (repo_root or Path.cwd()).resolve()


def _git_toplevel(path: Path) -> Path | None:
    """Return the git work-tree toplevel for ``path``, or None if not a repo."""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            check=True,
            capture_output=True,
            text=True,
            env=git_subprocess_env(),
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    toplevel = completed.stdout.strip()
    if not toplevel:
        return None
    return Path(toplevel).resolve()


def _ref_is_commit(repo_root: Path, ref: str) -> bool:
    """True when ``ref`` resolves to a commit inside ``repo_root``."""
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        env=git_subprocess_env(),
    )
    return completed.returncode == 0 and bool(completed.stdout.strip())


def resolve_audit_repo_root(
    repo_root: Path | None = None,
    *,
    base_ref: str,
    head_ref: str,
    cwd: Path | None = None,
) -> Path:
    """Resolve and validate the git repo root a changed-file audit will diff.

    Kills the false-clean footgun by refusing to silently default to the
    standards-control-plane checkout. Specifically:

    * defaults to the caller's working directory, not ``project_root()``;
    * requires the resolved root to be a git work tree (normalised to its
      toplevel);
    * requires both refs to resolve to commits inside that work tree;
    * refuses to diff a repository other than the one the caller is standing
      in — the cwd's git toplevel must equal the resolved root — so an operator
      cannot audit the wrong repo (or read file content from the wrong tree)
      without noticing.

    Raises :class:`RepoRootResolutionError` on any of the above.
    """
    working_dir = (cwd or Path.cwd()).resolve()
    requested = (repo_root or working_dir).resolve()

    root_toplevel = _git_toplevel(requested)
    if root_toplevel is None:
        raise RepoRootResolutionError(
            f"{requested} is not inside a git work tree; changed-file audit "
            "needs a git repository to diff. Run audit-changed from the repo "
            "you intend to audit, or pass --repo-root pointing at its checkout."
        )

    cwd_toplevel = _git_toplevel(working_dir)
    if cwd_toplevel is not None and cwd_toplevel != root_toplevel:
        raise RepoRootResolutionError(
            f"refusing to audit {root_toplevel} while the working directory "
            f"{working_dir} belongs to a different repository ({cwd_toplevel}). "
            "Run audit-changed from inside the repo you intend to audit, or set "
            "--repo-root and the working directory to the same repository."
        )

    for label, ref in (("base", base_ref), ("head", head_ref)):
        if not _ref_is_commit(root_toplevel, ref):
            raise RepoRootResolutionError(
                f"{label} ref {ref!r} does not resolve to a commit in "
                f"{root_toplevel}. Fetch the ref or correct --{label}-ref."
            )

    return root_toplevel


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
        env=git_subprocess_env(),
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
    repo_root: Path | None = None,
) -> dict[str, Any]:
    # When we resolve the diff ourselves (changed_paths is None), validate the
    # repo root loudly and use the validated toplevel for BOTH the git diff and
    # the downstream content extraction (build_audit_result -> extract_scope).
    #
    # When the caller supplies changed_paths we cannot run resolve_audit_repo_root
    # (there are no refs to validate), so the extraction root is taken from an
    # explicit repo_root, else the SCP checkout (project_root()). This branch is
    # SCP-internal — it is reached only by direct library calls auditing SCP's
    # own fixture path-sets; the CLI and MCP adopter entry points NEVER supply
    # changed_paths (they always resolve a validated repo root via git diff). A
    # library caller auditing a NON-SCP repo via changed_paths MUST pass repo_root.
    if changed_paths is None:
        resolved_root = resolve_audit_repo_root(
            repo_root,
            base_ref=base_ref,
            head_ref=head_ref,
        )
        paths = list_changed_files(
            base_ref=base_ref,
            head_ref=head_ref,
            repo_root=resolved_root,
        )
    else:
        resolved_root = (repo_root or project_root()).resolve()
        paths = changed_paths
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

    audit_result = build_audit_result(
        request,
        registry_snapshot=registry_snapshot,
        repo_root=resolved_root,
    )
    result = {
        "base_ref": base_ref,
        "head_ref": head_ref,
        "changed_paths": paths,
        "audit_result": audit_result,
    }
    validate_with_schema(result, "changed-audit-result.schema.json")
    return result
