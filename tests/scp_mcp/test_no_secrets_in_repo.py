from __future__ import annotations

import re
import subprocess

from .conftest import REPO_ROOT

PRIVATE_KEY_HEADER = re.compile(
    r"^-----BEGIN (?:OPENSSH |ENCRYPTED |RSA |EC |DSA )?PRIVATE KEY-----$",
    re.MULTILINE,
)


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
        if PRIVATE_KEY_HEADER.search(contents):
            offending_files.append(relative_path)

    assert not offending_files, f"Private key material must not be committed: {offending_files}"
