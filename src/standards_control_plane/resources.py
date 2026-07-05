"""Project-local path helpers."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Iterator


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


# Worktree root the current audit reads scoped files from. Set once per audit
# by build_audit_result so evaluator file readers resolve paths against an
# external adopter worktree without every finding builder threading a
# repo_root parameter. ContextVar keeps concurrent audits (threaded HTTP
# serve mode) isolated; outside an audit it is unset and readers fall back to
# project_root().
_AUDIT_REPO_ROOT: ContextVar[Path | None] = ContextVar("scp_audit_repo_root", default=None)


def audit_repo_root() -> Path | None:
    return _AUDIT_REPO_ROOT.get()


@contextmanager
def use_audit_repo_root(repo_root: Path | None) -> Iterator[None]:
    token = _AUDIT_REPO_ROOT.set(repo_root)
    try:
        yield
    finally:
        _AUDIT_REPO_ROOT.reset(token)


def schemas_dir() -> Path:
    return project_root() / "schemas"


def standards_dir() -> Path:
    return project_root() / "standards"


def examples_dir() -> Path:
    return project_root() / "examples"


def output_dir() -> Path:
    return project_root() / "output"

