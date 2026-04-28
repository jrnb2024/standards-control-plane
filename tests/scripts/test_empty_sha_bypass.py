"""Regression test for the empty-string SHA256 bypass in
lib/policy_check_invocation.sh.

This file is the explicit closure evidence for slice 020B.2 R3 finding
R3-SAF-MAJ-01: prior to fr3, scp_policy_check_verify_runtime_binary
silently returned 0 (PASS) when either path or expected_sha256 was the
empty string, and the wrapper scp_policy_check_verify_runtime_binaries
passed `${VAR:-}`-expanded values that collapsed to empty when env vars
were unset, silently bypassing all SHA256 verification.

These tests assert the post-fix behaviour: empty inputs are explicitly
rejected with a non-zero exit code.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LIB = REPO_ROOT / "lib" / "policy_check_invocation.sh"


def _source_and_invoke(env_overrides: dict[str, str], func_call: str) -> subprocess.CompletedProcess[str]:
    """Source lib/policy_check_invocation.sh and invoke a function.

    env_overrides is added to the subshell env (use '' to set empty,
    None semantics not supported — caller must explicitly include or
    omit a var).
    """
    bash_path = shutil.which("bash") or "/bin/bash"
    cmd = f"source {LIB!s}; {func_call}"
    return subprocess.run(
        [bash_path, "-c", cmd],
        capture_output=True,
        text=True,
        env={**env_overrides, "PATH": "/usr/bin:/bin:/usr/local/bin"},
    )


def test_inner_function_rejects_both_empty():
    res = _source_and_invoke({}, 'scp_policy_check_verify_runtime_binary "OPA" "" ""')
    assert res.returncode != 0, "verify_runtime_binary must refuse empty path + empty expected"
    assert "empty path" in res.stderr.lower() or "refused" in res.stderr.lower()


def test_inner_function_rejects_path_set_expected_empty():
    res = _source_and_invoke({}, 'scp_policy_check_verify_runtime_binary "OPA" "/nonexistent" ""')
    assert res.returncode != 0


def test_inner_function_rejects_path_empty_expected_set():
    res = _source_and_invoke({}, 'scp_policy_check_verify_runtime_binary "OPA" "" "abc123"')
    assert res.returncode != 0


def test_wrapper_rejects_all_env_vars_unset():
    res = _source_and_invoke({}, "scp_policy_check_verify_runtime_binaries")
    assert res.returncode != 0
    assert "unset" in res.stderr.lower() or "required" in res.stderr.lower()


def test_wrapper_rejects_partial_env_unset_opa_bin():
    env = {
        "SCP_POLICY_CHECK_OPA_SHA256": "deadbeef",
        "SCP_POLICY_CHECK_CONFTEST_BIN": "/nonexistent/conftest",
        "SCP_POLICY_CHECK_CONFTEST_SHA256": "deadbeef",
    }
    res = _source_and_invoke(env, "scp_policy_check_verify_runtime_binaries")
    assert res.returncode != 0


def test_wrapper_rejects_partial_env_unset_opa_sha():
    env = {
        "SCP_POLICY_CHECK_OPA_BIN": "/nonexistent/opa",
        "SCP_POLICY_CHECK_CONFTEST_BIN": "/nonexistent/conftest",
        "SCP_POLICY_CHECK_CONFTEST_SHA256": "deadbeef",
    }
    res = _source_and_invoke(env, "scp_policy_check_verify_runtime_binaries")
    assert res.returncode != 0


def test_wrapper_rejects_partial_env_unset_conftest_bin():
    env = {
        "SCP_POLICY_CHECK_OPA_BIN": "/nonexistent/opa",
        "SCP_POLICY_CHECK_OPA_SHA256": "deadbeef",
        "SCP_POLICY_CHECK_CONFTEST_SHA256": "deadbeef",
    }
    res = _source_and_invoke(env, "scp_policy_check_verify_runtime_binaries")
    assert res.returncode != 0


def test_wrapper_rejects_partial_env_unset_conftest_sha():
    env = {
        "SCP_POLICY_CHECK_OPA_BIN": "/nonexistent/opa",
        "SCP_POLICY_CHECK_OPA_SHA256": "deadbeef",
        "SCP_POLICY_CHECK_CONFTEST_BIN": "/nonexistent/conftest",
    }
    res = _source_and_invoke(env, "scp_policy_check_verify_runtime_binaries")
    assert res.returncode != 0
