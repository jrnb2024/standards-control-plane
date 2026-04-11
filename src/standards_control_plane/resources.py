"""Project-local path helpers."""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def schemas_dir() -> Path:
    return project_root() / "schemas"


def standards_dir() -> Path:
    return project_root() / "standards"


def examples_dir() -> Path:
    return project_root() / "examples"


def output_dir() -> Path:
    return project_root() / "output"

