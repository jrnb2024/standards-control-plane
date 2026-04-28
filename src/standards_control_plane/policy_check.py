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

_SENSITIVE_OVERRIDE_NAMES = (
    "SCP_POLICY_CHECK_LOCKFILE",
    "SCP_POLICY_CHECK_OPA_BASE_URL",
    "SCP_POLICY_CHECK_CONFTEST_BASE_URL",
)


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


def _prepare_env_for_script(*, allow_env_overrides: bool) -> dict[str, str]:
    env = dict(os.environ)
    stripped: list[str] = []
    default_lockfile = str(_repo_root() / "scripts" / "scp-policy-check.lock")

    lockfile_override = env.get("SCP_POLICY_CHECK_LOCKFILE")
    if lockfile_override and lockfile_override != default_lockfile and not allow_env_overrides:
        env.pop("SCP_POLICY_CHECK_LOCKFILE", None)
        stripped.append("SCP_POLICY_CHECK_LOCKFILE")

    for name in ("SCP_POLICY_CHECK_OPA_BASE_URL", "SCP_POLICY_CHECK_CONFTEST_BASE_URL"):
        if env.get(name) and not allow_env_overrides:
            env.pop(name, None)
            stripped.append(name)

    if stripped:
        stripped_names = ", ".join(stripped)
        print(
            "python -m standards_control_plane.policy_check: stripped testing-only "
            f"override(s) {stripped_names}; rerun with --allow-env-overrides to pass "
            "them through intentionally",
            file=sys.stderr,
        )
    elif allow_env_overrides and any(name in os.environ for name in _SENSITIVE_OVERRIDE_NAMES):
        forwarded_names = ", ".join(
            name for name in _SENSITIVE_OVERRIDE_NAMES if name in os.environ
        )
        print(
            "python -m standards_control_plane.policy_check: forwarding testing-only "
            f"override(s) {forwarded_names}",
            file=sys.stderr,
        )

    env.setdefault("SCP_POLICY_CHECK_UNAME_S", platform.system())
    env.setdefault("SCP_POLICY_CHECK_UNAME_M", platform.machine())
    return env


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    script_path = _script_path()
    allow_env_overrides = "--allow-env-overrides" in args

    if "--help" not in args and "-h" not in args:
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

    env = _prepare_env_for_script(allow_env_overrides=allow_env_overrides)
    completed = subprocess.run(
        [str(script_path), *args],
        cwd=_repo_root(),
        env=env,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
