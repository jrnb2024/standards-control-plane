from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from standards_control_plane import policy_check

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "scp-policy-check"

OPA_ASSETS = {
    "linux-x64": "opa_linux_amd64",
    "linux-arm64": "opa_linux_arm64",
    "darwin-arm64": "opa_darwin_arm64",
    "darwin-x64": "opa_darwin_amd64",
}


CONFTST_ARCHIVES = {
    "linux-x64": "conftest_9.9.9_Linux_x86_64.tar.gz",
    "linux-arm64": "conftest_9.9.9_Linux_arm64.tar.gz",
    "darwin-arm64": "conftest_9.9.9_Darwin_arm64.tar.gz",
    "darwin-x64": "conftest_9.9.9_Darwin_x86_64.tar.gz",
}


def _run_script(env_overrides: dict[str, str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update(env_overrides)
    return subprocess.run(
        [str(SCRIPT_PATH)],
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _write_tool_versions(path: Path, *, opa_version: str = "1.15.2", conftest_version: str = "9.9.9") -> None:
    path.write_text(f"opa {opa_version}\nconftest {conftest_version}\n", encoding="utf-8")


def _write_lockfile(path: Path, *, opa_sha: str, conftest_sha: str) -> None:
    payload = {"opa": {}, "conftest": {}}
    for platform_key, asset in OPA_ASSETS.items():
        payload["opa"][platform_key] = {"asset": asset, "sha256": opa_sha}
    for platform_key, asset in CONFTST_ARCHIVES.items():
        payload["conftest"][platform_key] = {"asset": asset, "sha256": conftest_sha}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_policy_check_python_entrypoint_rejects_unlisted_platform(monkeypatch, capsys) -> None:
    monkeypatch.setattr(policy_check.platform, "system", lambda: "Linux")
    monkeypatch.setattr(policy_check.platform, "machine", lambda: "ppc64")

    assert policy_check.main([]) == 1
    captured = capsys.readouterr()
    assert "unsupported platform Linux/ppc64" in captured.err


def test_scp_policy_check_refuses_sha256_mismatch(tmp_path: Path) -> None:
    platform_key = policy_check.detect_platform()
    tool_versions = tmp_path / ".tool-versions"
    lockfile = tmp_path / "scp-policy-check.lock"
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output" / "findings"
    opa_downloads = tmp_path / "opa-downloads"
    conftest_downloads = tmp_path / "conftest-downloads"

    opa_downloads.mkdir()
    conftest_downloads.mkdir()

    _write_tool_versions(tool_versions)
    fake_opa = opa_downloads / OPA_ASSETS[platform_key]
    fake_opa.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    _write_lockfile(lockfile, opa_sha="0" * 64, conftest_sha="1" * 64)

    result = _run_script(
        {
            "SCP_POLICY_CHECK_TOOL_VERSIONS": str(tool_versions),
            "SCP_POLICY_CHECK_LOCKFILE": str(lockfile),
            "SCP_POLICY_CHECK_CACHE_DIR": str(cache_dir),
            "SCP_POLICY_CHECK_OUTPUT_DIR": str(output_dir),
            "SCP_POLICY_CHECK_OPA_BASE_URL": opa_downloads.as_uri(),
            "SCP_POLICY_CHECK_CONFTEST_BASE_URL": conftest_downloads.as_uri(),
        }
    )

    assert result.returncode != 0
    assert "failed SHA256 verification" in result.stderr


def test_scp_policy_check_uses_cached_binaries_in_offline_mode(tmp_path: Path) -> None:
    platform_key = policy_check.detect_platform()
    tool_versions = tmp_path / ".tool-versions"
    lockfile = tmp_path / "scp-policy-check.lock"
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output" / "findings"
    opa_cache = cache_dir / "opa" / "1.15.2" / platform_key
    conftest_cache = cache_dir / "conftest" / "9.9.9" / platform_key

    opa_cache.mkdir(parents=True)
    conftest_cache.mkdir(parents=True)
    _write_tool_versions(tool_versions)

    fake_opa = opa_cache / "opa"
    fake_opa.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_opa.chmod(0o755)

    fake_conftest = conftest_cache / "conftest"
    fake_conftest.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_conftest.chmod(0o755)

    _write_lockfile(lockfile, opa_sha=_sha256(fake_opa), conftest_sha=_sha256(fake_conftest))

    result = _run_script(
        {
            "SCP_POLICY_CHECK_TOOL_VERSIONS": str(tool_versions),
            "SCP_POLICY_CHECK_LOCKFILE": str(lockfile),
            "SCP_POLICY_CHECK_CACHE_DIR": str(cache_dir),
            "SCP_POLICY_CHECK_OUTPUT_DIR": str(output_dir),
            "SCP_POLICY_CHECK_OPA_BASE_URL": "file:///path/that/does/not/exist",
            "SCP_POLICY_CHECK_CONFTEST_BASE_URL": "file:///path/that/does/not/exist",
        }
    )

    assert result.returncode == 0, result.stderr
    assert "Using cached OPA" in result.stderr
    assert "Using cached Conftest" in result.stderr
    assert (output_dir / "policy-findings.json").is_file()
