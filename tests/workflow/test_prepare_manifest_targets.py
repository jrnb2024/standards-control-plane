"""Unit tests for scp_policy_check_prepare_manifest_targets (lib/policy_check_invocation.sh).

The manifest target-prep logic used to live inline in the
`.github/workflows/policy-check.yml` "Prepare manifest evaluation targets"
step, which made it untestable. It now lives in the shared lib as
`scp_policy_check_prepare_manifest_targets`, so these tests drive it
directly with a synthetic changed-files manifest.

Regression target (SCP-E002 over-broad fix): in adopter mode the manifest
is built from `git diff --name-only BASE..HEAD`, which INCLUDES deletions.
A manifest (package.json / pyproject.toml / go.mod) DELETED in the PR is not
a file in the checkout — the old code emitted `::error ...SCP-E002::` and
`sys.exit(1)`, hard-failing the required gate on any adopter PR that retired
a vendored module (live repro: mapp-pim #403 deleting a vendored go.mod).
A deletion has nothing to evaluate and no vendoring-attestation surface, so
the fix SKIPS it. These tests prove the skip (no E002, exit 0, entry absent
from the surrogate set) AND keep a positive case so the fix never over-skips
a real, modified manifest.

This file is exercised in CI by the `prepare-manifest-targets-unit` job in
.github/workflows/workflow-selftest.yml. It is written to run with ONLY the
standard library (no pytest dependency) via `python <thisfile>` — so the CI
job needs no pip install — while remaining pytest-collectable for local dev
(`pytest tests/workflow/test_prepare_manifest_targets.py`). conftest-gate.yml
runs pytest only over tests/conflict_gate/, hence the dedicated runner job.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LIB_PATH = REPO_ROOT / "lib" / "policy_check_invocation.sh"
SURROGATE_DIRNAME = "scp-policy-manifest-surrogates"


def _run_prepare(
    tmp_path: Path,
    *,
    changed_lines: list[str],
    present_files: dict[str, str] | None = None,
    extra_env: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    """Run the lib function in an isolated working tree.

    Returns (completed_process, changed_files_path, github_env_path).
    `changed_lines` are written verbatim to changed-files.txt; `present_files`
    (path -> content, relative to the working tree) are materialised on disk so
    the function sees them as real files. Any manifest path in `changed_lines`
    NOT present on disk simulates a deletion in the PR diff.
    """
    work = tmp_path / "work"
    work.mkdir()
    runner_temp = tmp_path / "runner-temp"
    runner_temp.mkdir()

    changed_files_path = work / "changed-files.txt"
    changed_files_path.write_text("".join(f"{line}\n" for line in changed_lines), encoding="utf-8")

    for rel, content in (present_files or {}).items():
        target = work / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    github_env_path = tmp_path / "github-env"
    github_env_path.write_text("", encoding="utf-8")

    env = dict(os.environ)
    # Deterministic CI-detection: tests opt INTO CI mode via extra_env; an
    # inherited GITHUB_ACTIONS from the invoking environment must not leak.
    env.pop("GITHUB_ACTIONS", None)
    env.update(
        {
            "RUNNER_TEMP": str(runner_temp),
            "GITHUB_ENV": str(github_env_path),
            # exercise the default (SCP_CHANGED_FILES_PATH unset -> changed-files.txt)
        }
    )
    env.update(extra_env or {})

    script = (
        "set -euo pipefail\n"
        f"source {shlex.quote(str(LIB_PATH))}\n"
        "scp_policy_check_prepare_manifest_targets\n"
    )
    proc = subprocess.run(
        ["bash", "-c", script],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc, changed_files_path, github_env_path


def _surrogates(tmp_path: Path) -> list[Path]:
    root = tmp_path / "runner-temp" / SURROGATE_DIRNAME
    if not root.is_dir():
        return []
    return sorted(root.glob("*.yaml"))


def _assert_no_e002(proc: subprocess.CompletedProcess[str]) -> None:
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0, (
        f"expected exit 0, got {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    assert "SCP-E002" not in combined, f"unexpected SCP-E002 emitted:\n{combined}"


def test_deleted_manifest_is_skipped_not_failed(tmp_path: Path) -> None:
    """A manifest deleted in the PR diff is skipped: no SCP-E002, gate stays green."""
    deleted = "pkg/platform/vendor/github.com/mapp-fashion/ctauth/go.mod"
    proc, changed_files_path, github_env_path = _run_prepare(
        tmp_path,
        changed_lines=[deleted],  # path NOT created on disk == deleted in the diff
    )

    _assert_no_e002(proc)

    remaining = changed_files_path.read_text().splitlines()
    assert deleted not in remaining
    assert remaining == [], f"deleted manifest should leave nothing to evaluate, got {remaining!r}"
    assert _surrogates(tmp_path) == []
    assert "SCP_R003_MANIFEST_APPLICABLE=false" in github_env_path.read_text()


def test_modified_manifest_is_evaluated(tmp_path: Path) -> None:
    """A present (modified) manifest is rewritten into a YAML surrogate (no over-skip)."""
    go_mod = "module example.com/foo\n\ngo 1.22\n"
    proc, changed_files_path, github_env_path = _run_prepare(
        tmp_path,
        changed_lines=["go.mod"],
        present_files={"go.mod": go_mod},
    )

    _assert_no_e002(proc)

    surrogates = _surrogates(tmp_path)
    assert len(surrogates) == 1, f"expected one surrogate, got {surrogates!r}"
    assert surrogates[0].name.endswith("-go.mod.yaml")

    rewritten = changed_files_path.read_text().splitlines()
    assert len(rewritten) == 1
    assert SURROGATE_DIRNAME in rewritten[0]
    assert rewritten[0].endswith("-go.mod.yaml")

    surrogate_text = surrogates[0].read_text()
    assert 'source_file: "go.mod"' in surrogate_text
    assert "content: |-" in surrogate_text
    assert "module example.com/foo" in surrogate_text

    assert "SCP_R003_MANIFEST_APPLICABLE=true" in github_env_path.read_text()


def test_mixed_set_skips_only_the_deleted_manifest(tmp_path: Path) -> None:
    """Over-skip guard: a deleted manifest is dropped while a sibling present
    manifest is still evaluated and a non-manifest path passes through."""
    deleted = "pkg/old/go.mod"
    proc, changed_files_path, github_env_path = _run_prepare(
        tmp_path,
        changed_lines=["services.yml", deleted, "go.mod"],
        present_files={"go.mod": "module example.com/keep\n\ngo 1.22\n"},
    )

    _assert_no_e002(proc)

    rewritten = changed_files_path.read_text().splitlines()
    # non-manifest path passes through verbatim
    assert "services.yml" in rewritten
    # deleted manifest is dropped entirely
    assert deleted not in rewritten
    assert all(not line.endswith("/old/go.mod") for line in rewritten)
    # present manifest is rewritten to exactly one surrogate
    surrogates = _surrogates(tmp_path)
    assert len(surrogates) == 1, f"expected one surrogate, got {surrogates!r}"
    assert surrogates[0].name.endswith("-go.mod.yaml")
    assert any(line.endswith("-go.mod.yaml") for line in rewritten)

    # only the present manifest counts toward applicability
    assert "SCP_R003_MANIFEST_APPLICABLE=true" in github_env_path.read_text()


def test_deleted_package_json_is_skipped(tmp_path: Path) -> None:
    """The skip is over the whole manifest basename set, not go.mod-specific:
    a deleted package.json is also skipped (no SCP-E002)."""
    deleted = "frontend/legacy-widget/package.json"
    proc, changed_files_path, github_env_path = _run_prepare(
        tmp_path,
        changed_lines=[deleted],  # not created == deleted in the diff
    )

    _assert_no_e002(proc)
    assert changed_files_path.read_text().splitlines() == []
    assert _surrogates(tmp_path) == []
    assert "SCP_R003_MANIFEST_APPLICABLE=false" in github_env_path.read_text()


def test_env_file_is_fed_to_content_rules(tmp_path: Path) -> None:
    """WP-SCP-025 v2 P0 regression: a changed .env file MUST be surrogated so
    SCP-R-008 receives input.content (the old hardcoded feed never fed it).
    A .env-only change must NOT flip the R-003 manifest-applicability flag."""
    proc, changed_files_path, github_env_path = _run_prepare(
        tmp_path,
        changed_lines=[".env"],
        # Value deliberately too short for GitHub push-protection's Stripe
        # matcher (>=24 chars after the prefix) — this test asserts FEED
        # delivery only, not rule firing, so any sk_live_-shaped string works.
        present_files={".env": "STRIPE_KEY=sk_live_FEEDTEST\n"},
    )

    _assert_no_e002(proc)
    surrogates = _surrogates(tmp_path)
    assert len(surrogates) == 1, f"expected one surrogate, got {surrogates!r}"
    assert surrogates[0].name.endswith("-.env.yaml")
    surrogate_text = surrogates[0].read_text()
    assert 'source_file: ".env"' in surrogate_text
    assert "sk_live_" in surrogate_text  # content delivered, rule can see it
    rewritten = changed_files_path.read_text().splitlines()
    assert len(rewritten) == 1 and SURROGATE_DIRNAME in rewritten[0]
    # .env is not a vendoring manifest — R-003 applicability stays false
    assert "SCP_R003_MANIFEST_APPLICABLE=false" in github_env_path.read_text()


def test_migration_py_is_fed_and_other_py_passes_through(tmp_path: Path) -> None:
    """WP-SCP-025 v2 P0 regression: a migration .py under versions/ MUST be
    surrogated so SCP-R-012 receives input.content; a non-migration .py must
    pass through untouched (the feed is rule-declared, not a .py dragnet).

    Scope note: this validates the FEED only. The rule's own acceptance of
    the fed file is covered by policies/tests/scp_r_012_test.rego; the e2e
    pairing (feed -> surrogate -> Rego finding) is recorded in
    docs/releases/v2.0.0.md §Verification."""
    migration = "db/migrations/versions/0001_drop_users.py"
    bystander = "src/app/main.py"
    proc, changed_files_path, github_env_path = _run_prepare(
        tmp_path,
        changed_lines=[migration, bystander],
        present_files={
            migration: 'def upgrade():\n    op.drop_table("users")\n',
            bystander: "print('not a migration')\n",
        },
    )

    _assert_no_e002(proc)
    surrogates = _surrogates(tmp_path)
    assert len(surrogates) == 1, f"expected one surrogate, got {surrogates!r}"
    assert surrogates[0].name.endswith("-0001_drop_users.py.yaml")
    surrogate_text = surrogates[0].read_text()
    assert f'source_file: "{migration}"' in surrogate_text
    assert "op.drop_table" in surrogate_text
    rewritten = changed_files_path.read_text().splitlines()
    assert bystander in rewritten  # untouched passthrough
    assert any(line.endswith("-0001_drop_users.py.yaml") for line in rewritten)
    assert "SCP_R003_MANIFEST_APPLICABLE=false" in github_env_path.read_text()


def test_env_example_is_fed_feed_superset(tmp_path: Path) -> None:
    """Feed-superset invariant: .env.example IS surrogated (the feed must be a
    superset of the rule's applicability; SCP-R-008's own exempt-basename gate
    filters it, never the feed)."""
    proc, changed_files_path, _ = _run_prepare(
        tmp_path,
        changed_lines=[".env.example"],
        present_files={".env.example": "STRIPE_KEY=replace-me\n"},
    )

    _assert_no_e002(proc)
    surrogates = _surrogates(tmp_path)
    assert len(surrogates) == 1, f"feed must over-deliver, got {surrogates!r}"
    assert surrogates[0].name.endswith("-.env.example.yaml")


def test_missing_contract_falls_back_outside_ci(tmp_path: Path) -> None:
    """Outside CI a missing contract degrades to the pre-contract built-in
    R-003 manifest set (with a stderr warning): package.json is still
    surrogated, .env passes through unfed. Never less than v1 behaviour."""
    proc, changed_files_path, github_env_path = _run_prepare(
        tmp_path,
        changed_lines=["package.json", ".env"],
        present_files={"package.json": "{}\n", ".env": "X=sk_live_abc\n"},
        extra_env={"SCP_RULE_INPUTS_PATH": str(tmp_path / "does-not-exist.yaml")},
    )

    _assert_no_e002(proc)
    assert "falling back to the built-in SCP-R-003 manifest feed" in proc.stderr
    surrogates = _surrogates(tmp_path)
    assert len(surrogates) == 1 and surrogates[0].name.endswith("-package.json.yaml")
    rewritten = changed_files_path.read_text().splitlines()
    assert ".env" in rewritten  # passthrough, NOT fed (fallback = old feed)
    assert "SCP_R003_MANIFEST_APPLICABLE=true" in github_env_path.read_text()


def test_missing_contract_hard_fails_in_ci(tmp_path: Path) -> None:
    """In CI (GITHUB_ACTIONS=true) a missing contract is a hard SCP-E002 —
    the gate must never silently re-narrow the feed (the exact P0 the
    contract exists to kill)."""
    proc, _, _ = _run_prepare(
        tmp_path,
        changed_lines=[".env"],
        present_files={".env": "X=sk_live_abc\n"},
        extra_env={
            "SCP_RULE_INPUTS_PATH": str(tmp_path / "does-not-exist.yaml"),
            "GITHUB_ACTIONS": "true",
        },
    )

    assert proc.returncode != 0, "missing contract in CI must hard-fail"
    assert "SCP-E002" in proc.stdout + proc.stderr


def test_malformed_contract_hard_fails_everywhere(tmp_path: Path) -> None:
    """A PRESENT but malformed contract is a hard SCP-E002 even outside CI:
    an unparseable contract is an authoring error, not an environment gap."""
    bad = tmp_path / "rule-inputs.yaml"
    bad.write_text("schema_version: 1\nrules: [ {rule_id: ", encoding="utf-8")
    proc, _, _ = _run_prepare(
        tmp_path,
        changed_lines=[".env"],
        present_files={".env": "X=1\n"},
        extra_env={"SCP_RULE_INPUTS_PATH": str(bad)},
    )

    assert proc.returncode != 0, "malformed contract must hard-fail"
    assert "SCP-E002" in proc.stdout + proc.stderr


def test_contract_entry_with_both_patterns_is_rejected(tmp_path: Path) -> None:
    """Schema validation: a rule entry declaring BOTH basename_regex and
    path_regex (or neither) is rejected — exactly one, no ambiguity."""
    bad = tmp_path / "rule-inputs.yaml"
    bad.write_text(
        "schema_version: 1\n"
        "rules:\n"
        "  - rule_id: SCP-R-999\n"
        "    match:\n"
        "      basename_regex: '^x$'\n"
        "      path_regex: 'y'\n",
        encoding="utf-8",
    )
    proc, _, _ = _run_prepare(
        tmp_path,
        changed_lines=["x"],
        present_files={"x": "1\n"},
        extra_env={"SCP_RULE_INPUTS_PATH": str(bad)},
    )

    assert proc.returncode != 0
    out = proc.stdout + proc.stderr
    assert "SCP-E002" in out
    assert "exactly one of" in out


def test_deleted_env_file_is_skipped(tmp_path: Path) -> None:
    """The deletion-skip generalises to contract-fed files: a .env deleted in
    the PR diff is dropped (nothing to evaluate), not an error."""
    proc, changed_files_path, _ = _run_prepare(
        tmp_path,
        changed_lines=[".env"],  # not created == deleted in the diff
    )

    _assert_no_e002(proc)
    assert changed_files_path.read_text().splitlines() == []
    assert _surrogates(tmp_path) == []


def _main() -> int:
    """Stdlib-only runner so CI can execute this without installing pytest."""
    import tempfile
    import traceback

    tests = [
        test_deleted_manifest_is_skipped_not_failed,
        test_modified_manifest_is_evaluated,
        test_mixed_set_skips_only_the_deleted_manifest,
        test_deleted_package_json_is_skipped,
        test_env_file_is_fed_to_content_rules,
        test_migration_py_is_fed_and_other_py_passes_through,
        test_env_example_is_fed_feed_superset,
        test_missing_contract_falls_back_outside_ci,
        test_missing_contract_hard_fails_in_ci,
        test_malformed_contract_hard_fails_everywhere,
        test_contract_entry_with_both_patterns_is_rejected,
        test_deleted_env_file_is_skipped,
    ]
    failures = 0
    for test in tests:
        with tempfile.TemporaryDirectory() as raw:
            try:
                test(Path(raw))
            except Exception:  # noqa: BLE001 - surface every failure, keep going
                failures += 1
                print(f"FAIL {test.__name__}")
                traceback.print_exc()
            else:
                print(f"PASS {test.__name__}")
    if failures:
        print(f"{failures} of {len(tests)} manifest target-prep test(s) failed")
        return 1
    print(f"all {len(tests)} manifest target-prep tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
