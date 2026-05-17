"""Regression coverage for `scripts/enable-required-check.sh` brownfield-
adopter flags added in WP-SCP-024 024C fix-round-4.

R4 closed an estate-cascade blocker: the script previously REPLACED the
adopter's `required_status_checks.contexts` with a single-element list
(`[$REQUIRED_CONTEXT]`), silently removing any pre-existing required
checks the adopter had configured. Two new flags address this without
changing the default greenfield semantic:

- `--preserve-existing-contexts` — reads the target branch's current
  contexts via `gh api` and merges `$REQUIRED_CONTEXT` into that list
  with idempotent dedup. Re-running with the flag a second time is a
  no-op (the canonical context is already present, `unique` collapses
  the duplicate).

- `--skip-required-signatures` — skips the dedicated POST to
  `.../required_signatures` so adopters that aren't yet
  commit-signing-capable don't have future merges blocked.

Both flags are forward-mode-only and refused in restore mode.

These tests avoid mocking `gh` end-to-end (the script is a thin shell
over `gh api` and `jq`). Instead they exercise the pure code paths that
can be tested without network: the `build_payload` function with the
caller-resolved contexts argument, and the script-level mode-validation
guards that gate the new flags.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "enable-required-check.sh"


def _invoke(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run the script with given args. Returns the CompletedProcess.

    The script writes a loud stderr warning before option parsing and
    refuses to run when CI=true, so tests must NOT inherit CI=true.
    """
    bash_path = shutil.which("bash") or "/bin/bash"
    return subprocess.run(
        [bash_path, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
            "HOME": str(REPO_ROOT),
        },
        check=False,
    )


def _eval_build_payload(
    existing_reviews_json: str,
    contexts_json: str,
    *,
    enforce_admins: str = "true",
    required_context: str = "policy-check / scp/policy-check",
) -> dict:
    """Source the script up to `build_payload` and invoke the function.

    SYNC: this inlines a verbatim copy of `build_payload` from
    `scripts/enable-required-check.sh` (around line ~933) because the
    script has no `[[ "${BASH_SOURCE[0]}" == "$0" ]]` guard and cannot
    be sourced safely without executing its main body (which would
    require live `gh` credentials + a real target repo). Any future
    refactor of `build_payload` MUST update this inline copy in
    lockstep, OR the script should be restructured to extract
    `build_payload` into a sourceable lib file. R5 closes R1 C-MIN-01
    by documenting the drift risk explicitly; no present defect.

    Returns the parsed JSON payload as a Python dict.
    """
    bash_path = shutil.which("bash") or "/bin/bash"
    snippet = (
        f"ENFORCE_ADMINS={enforce_admins}; "
        f'REQUIRED_CONTEXT={json.dumps(required_context)}; '
        "build_payload() { local existing_reviews=\"$1\"; local contexts_json=\"$2\"; "
        "jq -n --argjson contexts \"$contexts_json\" --argjson admins \"$ENFORCE_ADMINS\" "
        "--argjson reviews \"$existing_reviews\" "
        "'{required_status_checks: {strict: true, contexts: $contexts}, "
        "enforce_admins: $admins, required_pull_request_reviews: $reviews, "
        "restrictions: null, required_linear_history: false, "
        "allow_force_pushes: false, allow_deletions: false, "
        "block_creations: false, required_conversation_resolution: false, "
        "lock_branch: false, allow_fork_syncing: false}'; }; "
        f"build_payload {json.dumps(existing_reviews_json)} {json.dumps(contexts_json)}"
    )
    proc = subprocess.run(
        [bash_path, "-c", snippet],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"},
        check=True,
    )
    return json.loads(proc.stdout)


# ----------------------------------------------------------------------
# Scenario 1: greenfield (no prior contexts; flag has no effect on the
# payload constructor — the caller passes contexts=[$REQUIRED_CONTEXT]
# regardless of greenfield/brownfield path).
# ----------------------------------------------------------------------


def test_greenfield_payload_single_context():
    """Default (greenfield) call: caller passes contexts=[<canonical>]."""
    payload = _eval_build_payload(
        existing_reviews_json="null",
        contexts_json='["policy-check / scp/policy-check"]',
    )
    assert payload["required_status_checks"]["contexts"] == [
        "policy-check / scp/policy-check"
    ]
    assert payload["required_status_checks"]["strict"] is True
    assert payload["enforce_admins"] is True


# ----------------------------------------------------------------------
# Scenario 2: brownfield with 0-overlap. Adopter has 4 prior required
# checks; flag should result in a 5-element list after canonical merge.
# This test exercises the call-site jq merge (`($existing + [$new]) |
# unique`) directly.
# ----------------------------------------------------------------------


def test_brownfield_merge_no_overlap():
    bash_path = shutil.which("bash") or "/bin/bash"
    existing = ["lint", "test-platform", "contract-tests", "playwright-uat"]
    new_ctx = "policy-check / scp/policy-check"
    snippet = (
        f"jq -n --argjson existing '{json.dumps(existing)}' "
        f"--arg new {json.dumps(new_ctx)} "
        "'($existing + [$new]) | unique'"
    )
    proc = subprocess.run(
        [bash_path, "-c", snippet],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"},
        check=True,
    )
    merged = json.loads(proc.stdout)
    assert set(merged) == {
        "lint",
        "test-platform",
        "contract-tests",
        "playwright-uat",
        "policy-check / scp/policy-check",
    }
    assert len(merged) == 5


# ----------------------------------------------------------------------
# Scenario 3: brownfield with overlap (idempotency). Adopter ALREADY has
# policy-check / scp/policy-check in their list; re-running with
# --preserve-existing-contexts must result in the same list (no
# duplicate). This is the second-run no-op guarantee.
# ----------------------------------------------------------------------


def test_brownfield_merge_idempotent_with_overlap():
    bash_path = shutil.which("bash") or "/bin/bash"
    existing = [
        "lint",
        "test-platform",
        "policy-check / scp/policy-check",
        "playwright-uat",
    ]
    new_ctx = "policy-check / scp/policy-check"
    snippet = (
        f"jq -n --argjson existing '{json.dumps(existing)}' "
        f"--arg new {json.dumps(new_ctx)} "
        "'($existing + [$new]) | unique'"
    )
    proc = subprocess.run(
        [bash_path, "-c", snippet],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"},
        check=True,
    )
    merged = json.loads(proc.stdout)
    assert set(merged) == {
        "lint",
        "test-platform",
        "policy-check / scp/policy-check",
        "playwright-uat",
    }
    assert len(merged) == 4  # idempotent — no duplicate added


# ----------------------------------------------------------------------
# Scenario 4: regression — flag-absent default preserves the original
# destructive semantic (caller passes contexts=[$REQUIRED_CONTEXT]
# unconditionally; payload constructor honours it). This guards against
# accidental behaviour-flip of greenfield adopters during a future
# refactor.
# ----------------------------------------------------------------------


def test_flag_absent_default_replaces_contexts():
    """Without --preserve-existing-contexts, the resolved contexts arg
    is a single-element list. Test asserts the constructor honours this
    (does not silently merge with anything else).

    NOTE: this test is structurally identical to
    `test_greenfield_payload_single_context` by design (R5 G-nit-02
    closure). Greenfield documents the *default shape*; this test
    guards against an accidental behaviour-flip during refactor that
    would change the flag-absent path. Both must be retained.
    """
    payload = _eval_build_payload(
        existing_reviews_json="null",
        contexts_json='["policy-check / scp/policy-check"]',
    )
    assert payload["required_status_checks"]["contexts"] == [
        "policy-check / scp/policy-check"
    ]
    # Negative assertion: the constructor MUST NOT inject anything else.
    assert len(payload["required_status_checks"]["contexts"]) == 1


# ----------------------------------------------------------------------
# Scenario 5 (R5 C-MIN-02): brownfield with empty existing list. Covers
# the `// []` fallback path for the "Branch not protected" sentinel.
# When BEFORE_JSON has no required_status_checks key, the jq merge must
# reduce to greenfield-equivalent ([$canonical]).
# ----------------------------------------------------------------------


def test_brownfield_merge_empty_existing():
    """Preserve-mode against an unprotected branch (empty existing
    list) MUST reduce to a single-element list — equivalent to the
    greenfield path. Closes R1 C-MIN-02.
    """
    bash_path = shutil.which("bash") or "/bin/bash"
    new_ctx = "policy-check / scp/policy-check"
    # Empty existing list (the // [] fallback for the "Branch not
    # protected" sentinel emits this shape).
    snippet = (
        "jq -n --argjson existing '[]' "
        f"--arg new {json.dumps(new_ctx)} "
        "'($existing + [$new]) | unique'"
    )
    proc = subprocess.run(
        [bash_path, "-c", snippet],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"},
        check=True,
    )
    merged = json.loads(proc.stdout)
    assert merged == ["policy-check / scp/policy-check"]
    assert len(merged) == 1


# ----------------------------------------------------------------------
# Mode-validation guards (--preserve-existing-contexts and
# --skip-required-signatures both refused in restore mode).
# ----------------------------------------------------------------------


def test_preserve_contexts_refused_in_restore_mode():
    proc = _invoke(
        [
            "--repo",
            "jrnb2024/test",
            "--branch",
            "main",
            "--restore",
            "/tmp/nonexistent-restore-state.json",
            "--preserve-existing-contexts",
        ]
    )
    assert proc.returncode == 2
    assert "--preserve-existing-contexts" in proc.stderr
    assert "restore" in proc.stderr.lower()


def test_skip_required_signatures_refused_in_restore_mode():
    proc = _invoke(
        [
            "--repo",
            "jrnb2024/test",
            "--branch",
            "main",
            "--restore",
            "/tmp/nonexistent-restore-state.json",
            "--skip-required-signatures",
        ]
    )
    assert proc.returncode == 2
    assert "--skip-required-signatures" in proc.stderr
    assert "restore" in proc.stderr.lower()


# ----------------------------------------------------------------------
# Help-text surface (catches accidental removal of flag documentation
# during future refactors).
# ----------------------------------------------------------------------


def test_help_documents_both_flags():
    proc = _invoke(["--help"])
    # --help exits 0 and writes usage to stderr.
    assert proc.returncode == 0
    assert "--preserve-existing-contexts" in proc.stderr
    assert "--skip-required-signatures" in proc.stderr
    # Both flags must self-identify as forward-mode-only so an operator
    # reading --help knows they can't be combined with --restore.
    assert proc.stderr.count("Forward-mode only") >= 2
    # R5 S-MAJ-01: the ACK companion flag must appear in --help so an
    # operator reading the help for --skip-required-signatures sees the
    # required companion immediately.
    assert "--i-understand-this-defers-commit-signing-enforcement" in proc.stderr


# ----------------------------------------------------------------------
# R5 S-MAJ-01: --skip-required-signatures requires the ACK companion
# flag. Mirrors the --no-enforce-admins + --i-understand-this-bypasses-
# the-gate symmetry so both posture-degrading forward-mode flags need
# identical per-invocation acknowledgement.
# ----------------------------------------------------------------------


def test_skip_required_signatures_requires_ack_flag():
    """Without --i-understand-this-defers-commit-signing-enforcement,
    the script MUST refuse --skip-required-signatures. Closes R1
    S-MAJ-01.
    """
    proc = _invoke(
        [
            "--repo",
            "jrnb2024/test",
            "--branch",
            "main",
            "--skip-required-signatures",
        ]
    )
    assert proc.returncode == 2
    assert "--skip-required-signatures requires" in proc.stderr
    assert "--i-understand-this-defers-commit-signing-enforcement" in proc.stderr
    # The error message MUST also surface the FUP obligation.
    assert "FUP" in proc.stderr.upper()


def test_ack_defer_flag_meaningless_without_skip():
    """The ACK flag passed alone (without --skip-required-signatures)
    is meaningless and MUST be refused. Symmetric with
    --i-understand-this-bypasses-the-gate + --no-enforce-admins
    handling. Prevents an operator pre-filling the long flag from
    shell history but forgetting the trigger from silently no-op'ing.
    """
    proc = _invoke(
        [
            "--repo",
            "jrnb2024/test",
            "--branch",
            "main",
            "--i-understand-this-defers-commit-signing-enforcement",
        ]
    )
    assert proc.returncode == 2
    assert "meaningless without --skip-required-signatures" in proc.stderr


# ----------------------------------------------------------------------
# R5 C-nit-01: --preserve-existing-contexts +
# --i-understand-this-repo-has-no-prior-green-ci is semantically
# contradictory (preserve assumes prior state; cold-start asserts no
# prior state). The combination MUST be refused.
# ----------------------------------------------------------------------


def test_preserve_contexts_refused_with_no_prior_green_ci():
    """The contradictory combination must error out, not silently
    reduce one to no-op. Closes R1 C-nit-01."""
    proc = _invoke(
        [
            "--repo",
            "jrnb2024/test",
            "--branch",
            "main",
            "--preserve-existing-contexts",
            "--i-understand-this-repo-has-no-prior-green-ci",
        ]
    )
    assert proc.returncode == 2
    assert "--preserve-existing-contexts" in proc.stderr
    assert "--i-understand-this-repo-has-no-prior-green-ci" in proc.stderr
