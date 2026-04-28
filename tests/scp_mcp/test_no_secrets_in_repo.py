from __future__ import annotations

import re
import subprocess

from .conftest import REPO_ROOT

SECRET_PATTERNS = [
    re.compile(r"^-----BEGIN (?:OPENSSH |ENCRYPTED |RSA |EC |DSA )?PRIVATE KEY-----$", re.MULTILINE),
    re.compile(r"^-----BEGIN PGP PRIVATE KEY BLOCK-----$", re.MULTILINE),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:ghp|ghs|gho|ghu|github_pat)_[A-Za-z0-9_]{36,}\b"),
    re.compile(r"\bxoxb-[0-9]+-[0-9A-Za-z-]+\b"),
]


def test_no_private_keys_committed() -> None:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"],
        capture_output=True,
        check=True,
        text=True,
    )

    offending_files: list[str] = []
    for relative_path in result.stdout.split("\0"):
        if not relative_path or relative_path.startswith(("vendor/", ".git/")):
            continue
        candidate = REPO_ROOT / relative_path
        contents = candidate.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(contents) for pattern in SECRET_PATTERNS):
            offending_files.append(relative_path)

    assert not offending_files, f"Secret-looking material must not be committed: {offending_files}"


def test_secret_patterns_cover_common_secret_formats() -> None:
    samples = [
        "-----BEGIN " + "PRIVATE KEY-----",
        "-----BEGIN OPENSSH " + "PRIVATE KEY-----",
        "-----BEGIN PGP PRIVATE KEY " + "BLOCK-----",
        "AKIA" + "1234567890ABCDEF",
        "ghp_" + "abcdefghijklmnopqrstuvwxyzABCDEF1234",
        "xoxb-" + "1234567890-abcDEF-ghijk",
    ]

    for sample in samples:
        assert any(pattern.search(sample) for pattern in SECRET_PATTERNS), sample
