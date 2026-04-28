"""Local entrypoint for reproducing the reusable policy-check workflow."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Sequence

_SUPPORTED_PLATFORMS = {
    ("Linux", "x86_64"): "linux-x64",
    ("Linux", "amd64"): "linux-x64",
    ("Linux", "aarch64"): "linux-arm64",
    ("Linux", "arm64"): "linux-arm64",
    ("Darwin", "x86_64"): "darwin-x64",
    ("Darwin", "amd64"): "darwin-x64",
    ("Darwin", "arm64"): "darwin-arm64",
}


def detect_platform() -> str:
    system = platform.system()
    machine = platform.machine()
    try:
        return _SUPPORTED_PLATFORMS[(system, machine)]
    except KeyError as exc:
        supported = ", ".join(sorted(set(_SUPPORTED_PLATFORMS.values())))
        raise ValueError(
            f"unsupported platform {system}/{machine}; supported platforms: {supported}"
        ) from exc


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _script_path() -> Path:
    return _repo_root() / "scripts" / "scp-policy-check"


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    script_path = _script_path()
    try:
        detect_platform()
    except ValueError as error:
        print(f"python -m standards_control_plane.policy_check: {error}", file=sys.stderr)
        return 1

    if not script_path.is_file():
        print(
            f"python -m standards_control_plane.policy_check: missing script {script_path}",
            file=sys.stderr,
        )
        return 1

    env = dict(os.environ)
    env.setdefault("SCP_POLICY_CHECK_UNAME_S", platform.system())
    env.setdefault("SCP_POLICY_CHECK_UNAME_M", platform.machine())
    completed = subprocess.run(
        [str(script_path), *args],
        cwd=_repo_root(),
        env=env,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
