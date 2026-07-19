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


def _run_script(
    env_overrides: dict[str, str],
    *,
    args: tuple[str, ...] = (),
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update(env_overrides)
    return subprocess.run(
        [str(SCRIPT_PATH), *args],
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


def test_policy_check_python_entrypoint_strips_sensitive_overrides_without_opt_in(
    monkeypatch, capsys
) -> None:
    captured_call: dict[str, object] = {}

    def fake_run(argv, cwd, env, check):  # type: ignore[no-untyped-def]
        captured_call["argv"] = argv
        captured_call["cwd"] = cwd
        captured_call["env"] = env
        captured_call["check"] = check
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(policy_check.platform, "system", lambda: "Linux")
    monkeypatch.setattr(policy_check.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(policy_check.subprocess, "run", fake_run)
    monkeypatch.setenv("SCP_POLICY_CHECK_LOCKFILE", "/tmp/override.lock")
    monkeypatch.setenv("SCP_POLICY_CHECK_OPA_BASE_URL", "https://example.invalid/opa")
    monkeypatch.setenv("SCP_POLICY_CHECK_CONFTEST_BASE_URL", "https://example.invalid/conftest")

    assert policy_check.main([]) == 0
    captured = capsys.readouterr()

    forwarded_env = captured_call["env"]
    assert isinstance(forwarded_env, dict)
    assert "SCP_POLICY_CHECK_LOCKFILE" not in forwarded_env
    assert "SCP_POLICY_CHECK_OPA_BASE_URL" not in forwarded_env
    assert "SCP_POLICY_CHECK_CONFTEST_BASE_URL" not in forwarded_env
    assert "stripped testing-only override(s)" in captured.err


def test_scp_policy_check_rejects_sensitive_overrides_without_explicit_opt_in(tmp_path: Path) -> None:
    tool_versions = tmp_path / ".tool-versions"
    lockfile = tmp_path / "scp-policy-check.lock"

    _write_tool_versions(tool_versions)
    _write_lockfile(lockfile, opa_sha="0" * 64, conftest_sha="1" * 64)

    result = _run_script(
        {
            "SCP_POLICY_CHECK_TOOL_VERSIONS": str(tool_versions),
            "SCP_POLICY_CHECK_LOCKFILE": str(lockfile),
            "SCP_POLICY_CHECK_OPA_BASE_URL": "https://example.invalid/opa",
        }
    )

    assert result.returncode != 0
    assert "refusing testing-only override" in result.stderr


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
        },
        args=("--allow-env-overrides",),
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
    # Emit valid JSON like real `conftest --output json`: when the invoking
    # working tree has modified tracked .json files, the run reaches the
    # conftest feed and parses this stub's output.
    fake_conftest.write_text("#!/usr/bin/env bash\nprintf '[]\\n'\n", encoding="utf-8")
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
        },
        args=("--allow-env-overrides",),
    )

    assert result.returncode == 0, result.stderr
    assert "Using cached OPA" in result.stderr
    assert "Using cached Conftest" in result.stderr
    assert (output_dir / "policy-findings.json").is_file()


def test_scp_policy_check_uses_base_head_diff_when_requested(tmp_path: Path) -> None:
    platform_key = policy_check.detect_platform()
    repo_dir = tmp_path / "fixture-repo"
    tool_versions = tmp_path / ".tool-versions"
    lockfile = tmp_path / "scp-policy-check.lock"
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "output" / "findings"
    policy_dir = tmp_path / "policy-bundle"
    capture_args_path = tmp_path / "conftest-args.txt"
    opa_cache = cache_dir / "opa" / "1.15.2" / platform_key
    conftest_cache = cache_dir / "conftest" / "9.9.9" / platform_key

    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, text=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )

    repo_dir.mkdir()
    changed_file = repo_dir / "changed.yml"
    changed_file.write_text("version: 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "fixture-repo/changed.yml"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "base"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    base_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    changed_file.write_text("version: 2\n", encoding="utf-8")
    subprocess.run(["git", "commit", "-am", "head"], cwd=tmp_path, capture_output=True, text=True, check=True)
    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    opa_cache.mkdir(parents=True)
    conftest_cache.mkdir(parents=True)
    policy_dir.mkdir()
    (policy_dir / "dummy.rego").write_text("package scp\n", encoding="utf-8")
    _write_tool_versions(tool_versions)

    fake_opa = opa_cache / "opa"
    fake_opa.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_opa.chmod(0o755)

    fake_conftest = conftest_cache / "conftest"
    fake_conftest.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$@\" > \"$SCP_CAPTURE_ARGS_PATH\"\n"
        "printf '[]\\n'\n",
        encoding="utf-8",
    )
    fake_conftest.chmod(0o755)

    _write_lockfile(lockfile, opa_sha=_sha256(fake_opa), conftest_sha=_sha256(fake_conftest))

    result = _run_script(
        {
            "SCP_POLICY_CHECK_TOOL_VERSIONS": str(tool_versions),
            "SCP_POLICY_CHECK_LOCKFILE": str(lockfile),
            "SCP_POLICY_CHECK_CACHE_DIR": str(cache_dir),
            "SCP_POLICY_CHECK_OUTPUT_DIR": str(output_dir),
            "SCP_POLICY_CHECK_POLICY_ROOT": str(policy_dir),
            "SCP_CAPTURE_ARGS_PATH": str(capture_args_path),
            "SCP_BASE_SHA": base_sha,
            "SCP_HEAD_SHA": head_sha,
            "SCP_FIXTURE_PATH": "fixture-repo",
        },
        args=("--allow-env-overrides",),
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    assert "fixture-repo/changed.yml" in capture_args_path.read_text(encoding="utf-8")
