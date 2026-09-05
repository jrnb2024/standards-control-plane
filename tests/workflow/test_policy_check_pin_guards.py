"""Structural guards on the cross-repo SCP checkouts in policy-check.yml.

`inputs.scp-sha` is the federation pin: the SHA the adopter's wrapper pinned
the reusable workflow to, and the ref both cross-repo `actions/checkout` steps
resolve, so SCP's runtime files (policies, tool versions, the hash-pinned
python lockfile, JSON schemas) travel with the pin.

THE FAILURE MODE. `actions/checkout` RESOLVES a bad ref rather than refusing
it. At the SHA this workflow pins (de0fac2e, v6.0.2):

  - empty `ref:`      -> `github.context.ref`/`sha` when `repository:` is the
                         workflow's own repo (src/input-helper.ts), otherwise
                         the repository DEFAULT BRANCH (src/git-source-
                         provider.ts, "Determining the default branch").
  - whitespace `ref:` -> identical: the bundled @actions/core `getInput`
                         returns `val.trim()` and input-helper passes no
                         `trimWhitespace: false`.
  - branch or tag     -> checked out AS that branch or tag (src/ref-helper.ts
                         `getCheckoutInfo`: an unqualified ref resolves via
                         `branchExists('origin/<ref>')`, then `tagExists`).

Only a ref matching no branch and no tag throws. `scp-sha` is `required: true`,
which an EMPTY STRING satisfies, so `""`, `" "`, `main` and `v1.0.0` all put a
MOVING ref on disk. The "Validate inputs.scp-sha" step rejects every one of
them, but the `_scp-workflow` checkout is `if: always()` and therefore ran
anyway: measured on run 33970219430, job `fixture-scp-sha-validation-required-
input-missing-policy-check`, where validation = failure yet that checkout =
success, fetching `+3fe10d6d...:refs/remotes/pull/269/merge` into
`_scp-workflow` with the pin empty. `_scp-workflow` is a hash-pinned-lockfile
source, so that is a pin escape inside an always() path.

WHAT THIS FILE ASSERTS. The fix is to gate both checkouts on the VALIDATION
STEP'S OUTCOME rather than on any property of the input, because `if:` has no
regex and every weaker predicate leaks (`inputs.scp-sha != ''` passes `" "`,
`main` and `v1.0.0`). So:

  1. Both cross-repo checkouts still resolve the pin, with no `||` fallback on
     `ref:` — the silent downgrade closed by v0.7 R2 Lens A HIGH-005 / Lens B
     NEW-001, where omitting `scp-sha:` fell through to `github.workflow_sha`.
  2. Every cross-repo checkout is gated on `steps.<validation>.outcome ==
     'success'`, and its `if:` contains no `||` — `always() || <guard>` is
     unconditionally true, and a status function makes the runner use the
     condition verbatim (actions/runner PipelineTemplateConverter
     .ConvertToIfCondition), so one character would otherwise reopen the hole.
  3. The validation step still exists, still carries the id the gates name,
     and still fails closed on both an empty and a malformed pin — the gate
     supplements it, it must never replace it.
  4. No `env:` aliases `inputs.scp-sha`, so a new checkout cannot route around
     rule 1 by spelling its ref indirectly.

Steps are found by `repository: jrnb2024/standards-control-plane`, not by how
`ref:` is written, so a newly added cross-repo checkout inherits the
requirement instead of the guard being a two-site allowlist.

`test_the_guard_can_fail` replays the mutations an R1 review used to kill the
first version of this file, and asserts each is still caught. Without it this
file could rot into a check that passes on anything.

RUNTIME COVERAGE. There is none for this specific path yet, and this file is
not a substitute for it: `fixture-scp-sha-validation-required-input-missing`
(workflow-selftest.yml) does run with `scp-sha: ""`, but the aggregator asserts
only that the JOB result is `failure`, which holds with or without the gate.
Observing the gate needs the checkout step's CONCLUSION, i.e. the jobs API and
`actions: read` on the aggregator — machinery PR #273 introduces. Adding that
row is tracked as a follow-up rather than duplicated here.

Exercised in CI by the `policy-check-pin-guards-unit` job in
.github/workflows/workflow-selftest.yml, which is asserted by the
workflow-selftest aggregator. NOTE that `workflow-selftest` is not a required
status check on main, so this guard is loud, not merge-blocking.

Runnable via `python tests/workflow/test_policy_check_pin_guards.py` (the
convention set by test_prepare_manifest_targets.py) and pytest-collectable for
local dev. Unlike that file this one needs PyYAML: hand-rolled line parsing was
the first version's biggest weakness, blind to flow-style `with:` blocks,
folded `if:` scalars, quoted refs and inline comments. PyYAML is hash-pinned in
requirements/policy-check.txt, which the CI job installs with --require-hashes.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "policy-check.yml"

SCP_REPOSITORY = "jrnb2024/standards-control-plane"
CHECKOUT_ACTION = "actions/checkout@"
PIN_REF = "${{ inputs.scp-sha }}"
PIN_INPUT = "inputs.scp-sha"
VALIDATION_STEP_ID = "validate-scp-sha"
OUTCOME_GATE = f"steps.{VALIDATION_STEP_ID}.outcome == 'success'"

# Both cross-repo checkouts must keep existing under these names; renaming or
# deleting one has to be a deliberate act, not an accident.
EXPECTED_CROSS_REPO_STEPS = {
    "Checkout SCP runtime repository",
    "Check out SCP repo at workflow ref for schema lookup",
}


def _load(text: str) -> dict:
    return yaml.safe_load(text)


def _steps(workflow: dict) -> list[tuple[str, dict]]:
    """Every step in the file, as (job_name, step)."""
    return [
        (job_name, step)
        for job_name, job in (workflow.get("jobs") or {}).items()
        for step in (job.get("steps") or [])
    ]


def _step_label(step: dict) -> str:
    return str(step.get("name") or step.get("uses") or step.get("id") or "<unnamed step>")


def _cross_repo_checkouts(workflow: dict) -> list[dict]:
    """Checkouts of the SCP repo, found by `repository:` not by `ref:` spelling.

    Keying on the repository is what makes this a property rather than an
    allowlist: a new checkout added with an env-indirected or flow-style ref is
    still caught.
    """
    return [
        step
        for _job, step in _steps(workflow)
        if CHECKOUT_ACTION in str(step.get("uses", ""))
        and str((step.get("with") or {}).get("repository", "")) == SCP_REPOSITORY
    ]


def _if_text(step: dict) -> str:
    """The step's `if:` as a single line (folded/literal scalars collapse)."""
    return " ".join(str(step.get("if", "")).split())


def violations(text: str) -> list[str]:
    """Every guard violation in a policy-check.yml, worst first.

    Factored out so the real file and the mutation self-tests below run through
    exactly the same checker.
    """
    workflow = _load(text)
    found = []

    checkouts = _cross_repo_checkouts(workflow)
    names = {_step_label(step) for step in checkouts}
    for missing in sorted(EXPECTED_CROSS_REPO_STEPS - names):
        found.append(
            f"cross-repo checkout step {missing!r} is gone or no longer targets "
            f"{SCP_REPOSITORY}; present cross-repo checkouts: {sorted(names)}. If it was "
            "renamed, update EXPECTED_CROSS_REPO_STEPS deliberately."
        )

    for step in checkouts:
        label = _step_label(step)
        ref = str((step.get("with") or {}).get("ref", ""))
        condition = _if_text(step)

        if ref != PIN_REF:
            found.append(
                f"{label!r}: `ref:` is {ref!r}, must be exactly {PIN_REF!r}. A fallback "
                "(e.g. `|| github.workflow_sha`) lets a caller that omits `scp-sha:` "
                "silently check out a DIFFERENT ref — the silent downgrade closed by "
                "v0.7 R2 Lens A HIGH-005 / Lens B NEW-001."
            )

        if OUTCOME_GATE not in condition:
            found.append(
                f"{label!r}: `if:` is {condition or '<absent>'!r}, must contain "
                f"{OUTCOME_GATE!r}. actions/checkout RESOLVES an empty, whitespace, "
                "branch or tag ref instead of failing, so a checkout that can run on an "
                "unvalidated pin puts a MOVING ref on disk (measured: run 33970219430). "
                "Gate on the validation step's outcome — a predicate over the input "
                "value cannot express this: `inputs.scp-sha != ''` passes `\" \"`, "
                "`main` and `v1.0.0`."
            )

        if "||" in condition:
            found.append(
                f"{label!r}: `if:` contains `||` ({condition!r}). These conditions are "
                "conjunctions by design; a disjunction can neutralise the gate "
                "silently — `always() || <gate>` is unconditionally true, and a "
                "condition containing a status function is used verbatim by the runner "
                "(PipelineTemplateConverter.ConvertToIfCondition)."
            )

    validation = [
        step for _job, step in _steps(workflow) if step.get("id") == VALIDATION_STEP_ID
    ]
    if len(validation) != 1:
        found.append(
            f"expected exactly one step with `id: {VALIDATION_STEP_ID}` (the step both "
            f"checkout gates name), found {len(validation)}."
        )
    else:
        run = str(validation[0].get("run", ""))
        if 'if [ -z "${SCP_SHA}" ]; then' not in run:
            found.append(
                f"step `id: {VALIDATION_STEP_ID}` no longer fails closed on an EMPTY "
                "pin. Gating the checkouts on its outcome is defence in depth for the "
                "always() path, NOT a substitute for the SCP-E001 that makes the run "
                "red."
            )
        if "^[a-f0-9]{40}$" not in run:
            found.append(
                f"step `id: {VALIDATION_STEP_ID}` no longer enforces the 40-char "
                "lowercase-hex shape. The checkout gates inherit their strength from "
                "this step: weaken it and `main` or `v1.0.0` becomes an accepted pin."
            )

    # Only env a CHECKOUT could dereference: workflow- and job-level env is
    # visible to every step, and a checkout's own step-level env to itself.
    # Step-level env elsewhere is scoped to that step and is fine — the
    # validation step legitimately does `env: SCP_SHA: ${{ inputs.scp-sha }}`
    # to read the value in bash.
    scopes = [("workflow", workflow.get("env") or {})]
    for job_name, job in (workflow.get("jobs") or {}).items():
        scopes.append((f"job {job_name}", job.get("env") or {}))
    for step in checkouts:
        scopes.append((f"checkout step {_step_label(step)}", step.get("env") or {}))
    for scope, env in scopes:
        for key, value in env.items():
            if PIN_INPUT in str(value):
                found.append(
                    f"{scope}: `env.{key}` aliases `{PIN_INPUT}` ({value!r}). An env "
                    "alias a checkout can dereference lets a new checkout spell its ref "
                    "indirectly and slip past the `ref:` check above; pass the input "
                    "directly."
                )

    return found


def test_policy_check_pin_guards_hold() -> None:
    found = violations(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert not found, f"{WORKFLOW_PATH.name}:\n" + "\n".join(f"  - {v}" for v in found)


def test_the_guard_can_fail() -> None:
    """Replay the mutations R1 used to kill v1 of this file; each must be caught.

    Every case below is a real escape that the first, substring-matching version
    of this test passed. Without this test the checker could silently rot into
    one that accepts anything.
    """
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    gated = f"        if: always() && {OUTCOME_GATE}\n"
    assert text.count(gated) == 1, "the _scp-workflow gate moved; update these mutations"

    new_checkout = """      - name: Sneaky extra checkout
        if: always()
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          repository: jrnb2024/standards-control-plane
          ref: ${{ env.SCP_PIN }}
          path: _scp-sneaky
"""
    mutations = {
        # R1 COR-001 / SAFE-002: one character reopens the escape.
        "and_to_or": lambda t: t.replace(gated, f"        if: always() || {OUTCOME_GATE}\n", 1),
        # R1 SAFE-002 M2': parenthesised disjunction, no precedence assumption.
        "or_true": lambda t: t.replace(
            gated, f"        if: always() && ({OUTCOME_GATE} || true)\n", 1
        ),
        # R1 SAFE-002 M1: the guard demoted to an inline comment.
        "guard_to_comment": lambda t: t.replace(
            gated, f"        if: always()  # {OUTCOME_GATE}\n", 1
        ),
        # The weak predicate this file exists to reject.
        "weak_predicate": lambda t: t.replace(
            gated, "        if: always() && inputs.scp-sha != ''\n", 1
        ),
        "gate_removed": lambda t: t.replace(gated, "        if: always()\n", 1),
        # R1 v0.7 HIGH-005: the ref fallback, restored.
        "ref_fallback": lambda t: t.replace(
            f"          ref: {PIN_REF}\n",
            "          ref: ${{ inputs.scp-sha || github.workflow_sha }}\n",
            1,
        ),
        # R1 COR-003 / SAFE-002 M4: a new cross-repo checkout, ref spelled via env.
        "env_indirected_checkout": lambda t: t.replace(gated, gated + new_checkout, 1),
        # ...and the job-level alias that would make such a ref resolve.
        "job_env_alias": lambda t: t.replace(
            "      SCP_RUNTIME_ROOT: .scp-runtime\n",
            "      SCP_RUNTIME_ROOT: .scp-runtime\n      SCP_PIN: ${{ inputs.scp-sha }}\n",
            1,
        ),
        # The gate must not outlive the step it names.
        "validation_id_removed": lambda t: t.replace(
            f"        id: {VALIDATION_STEP_ID}\n", "", 1
        ),
        # The gate is defence in depth, not a replacement.
        "fail_closed_defanged": lambda t: t.replace(
            'if [ -z "${SCP_SHA}" ]; then', "if false; then", 1
        ),
        "shape_check_defanged": lambda t: t.replace(
            '"${SCP_SHA}" =~ ^[a-f0-9]{40}$', '"${SCP_SHA}" =~ ^.*$', 1
        ),
    }

    survivors = []
    for name, mutate in mutations.items():
        mutated = mutate(text)
        assert mutated != text, f"mutation {name!r} did not apply — it needs updating"
        if not violations(mutated):
            survivors.append(name)
    assert not survivors, (
        "these mutations reopen a pin escape (or remove the fail-closed validation) "
        f"and the checker did NOT catch them: {survivors}"
    )


def _main() -> int:
    tests = [test_policy_check_pin_guards_hold, test_the_guard_can_fail]
    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {test.__name__}: {exc}")
        else:
            print(f"PASS {test.__name__}")
    if failures:
        print(f"{failures} of {len(tests)} policy-check pin-guard tests failed")
        return 1
    print(f"all {len(tests)} policy-check pin-guard tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
