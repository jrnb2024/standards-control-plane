# Conflict-gate (SCP-E005) — engine-agreement contract

The conflict-gate (slice 020C.1, WP-SCP-020 §4 020C.1 (iii) + (iv)) asserts that the Rego rules and their Python-evaluator equivalents produce the **same verdict** on a shared set of fixtures. Disagreement is `SCP-E005` and merge-blocked.

## Why

The federation primitive runs two engines:
- **Rego (OPA/Conftest)** — fast pre-merge gate at PR time on changed files.
- **Python evaluators** in `src/standards_control_plane/evaluators/` — deeper audits at nightly / manual / release time.

Both engines must say the same thing about the same input, or the gate becomes unreliable for adopters. The conflict-gate enforces this empirically per-fixture.

## Mechanics

- Adapter at `tests/conflict_gate/adapter.py` normalises both engines' outputs to `{rule_id, file, verdict: allow|deny, reason}`.
- Fixtures at `tests/conflict_gate/fixtures/<rule_id>/<scenario>/` — each contains an `input.yml`/`input.json` and a canonical `expected-verdict.json`.
- Pytest module `tests/conflict_gate/test_conflict_gate.py` parameterises over every fixture; runs both engines; asserts `rego.verdict == python.verdict == expected.verdict`.
- CI job `rego-vs-python-conflict` runs the same module on every PR. Disagreement → SCP-E005 → merge-block.

## Unblock procedure (when disagreement is genuine)

1. **Don't** modify either engine to "win" the disagreement in the same PR — the conflict-gate is failing, the PR is blocked, and trying to fix it from inside the blocked PR creates a chicken-and-egg.
2. Open a **separate** PR (the "amending decision PR") that:
   - Adds a `D-NNN` row to `docs/DECISIONS.md` ratifying which engine's verdict is correct + why.
   - Updates the fixture's `expected-verdict.json` to match the now-ratified verdict.
3. Once that PR lands, the originally-blocked PR rebases on `main` and the CI job re-runs against the updated fixture. Both engines now agree with the ratified expectation, gate passes, original PR can merge.

This pattern keeps the gate's authority intact (the gate is never overridden in-flight) while giving adopters a clear escalation path.

## Coverage of the v1.0.0 rule library

| Rule | Python equivalent | Conflict-gate fixtures |
|------|-------------------|-------------------------|
| SCP-R-001 (services.yml SVC-003 mode set) | `src/standards_control_plane/evaluators/service_lifecycle.py` | `fixtures/SCP-R-001/{allow,deny}/` |
| SCP-R-002 (waivers.json schema) | Approximated in-test via the same shape (no dedicated evaluator module — the Python audit handles waiver schema validation as part of `audit.py` / `waivers.py`). | `fixtures/SCP-R-002/{allow,deny}/` |
| **SCP-R-003 (vendoring-manifest marker presence)** | **No Python equivalent today.** The Rego rule operates on the changed-file set + manifest contents directly. There's no per-rule Python evaluator that mirrors this check; the closest is the broader audit framework, which doesn't operate on PR-changed-files in the same way. | **Documented gap.** No fixtures committed for SCP-R-003. The conflict-gate skips it gracefully (returns empty Python findings, matches Rego when Rego also returns no deny). Tracked as a follow-up: when SCP-R-003 gets a Python-evaluator equivalent (likely as part of WP-SCP-022.1 or the broader audit refactor), add fixtures `fixtures/SCP-R-003/{allow,deny}/` and remove the gap note. |

## Fixture authoring checklist

When adding a new rule + fixtures:

1. Create `tests/conflict_gate/fixtures/<RULE-ID>/allow/` with `input.<ext>` + `expected-verdict.json` (verdict: `allow`).
2. Create `tests/conflict_gate/fixtures/<RULE-ID>/deny/` with `input.<ext>` + `expected-verdict.json` (verdict: `deny`).
3. Verify locally: `opa eval --format=json --data policies/<RULE-ID>.rego --data policies/scp_common.rego --input <fixture-input> 'data.main.deny'`. Result should be `[]` for allow, non-empty for deny. (`scp_common.rego` provides the waiver-aware / rule-config-aware helpers used by every rule; without it, helper calls evaluate as `not undefined = true` and the conflict-gate fails to detect bypass-path bugs. Closes WP-SCP-022 R1 completeness MAJ-001.)
4. Verify the Python evaluator returns matching findings (or gracefully skips per the SCP-R-003 gap note above).
5. Run `pytest tests/conflict_gate/ -xvs` locally.
6. CI's `rego-vs-python-conflict` job will re-run on every PR.

## Scope of conflict-gate coverage (waivers + rule-config)

The conflict-gate covers **raw rule verdicts AND suppressed verdicts** as of slice 020Q (closes TF-006). Both halves of the suppression contract are exercised by the fixture corpus:

- **Raw rule code path** — fixtures under `tests/conflict_gate/fixtures/<RULE-ID>/{allow,deny}/` run both engines without any sibling waivers/rule-config files. Both engines must agree on the raw verdict.
- **Waiver-suppression code path** — fixtures under `tests/conflict_gate/fixtures/<RULE-ID>/waiver-suppressed/` carry a sibling `waivers.json` containing an active rule-id-matching waiver. Both engines must short-circuit to allow. Fixtures under `tests/conflict_gate/fixtures/<RULE-ID>/waiver-expired/` carry a sibling `waivers.json` with an EXPIRED waiver; both engines must apply the documented fail-closed semantics (per `policies/scp_common.rego` `scp_waiver_expired`) and emit deny.
- **Rule-config-disable code path** — fixtures under `tests/conflict_gate/fixtures/<RULE-ID>/rule-config-disabled/` carry a sibling `.scp/rule-config.yaml` with `rules.<RULE-ID>.disable: true`. Both engines must short-circuit to allow.

The Python-side suppression mirror lives in `tests/conflict_gate/test_conflict_gate.py` as `_scp_active_waiver_for`, `_scp_waiver_expired`, `_scp_rule_config_disabled`, and `_parse_dateish_ns` — each function is a translation of the matching `policies/scp_common.rego` predicate (see in-file docstrings for line citations). The OPA invocation in `_run_opa` detects sibling files and combines them into a tempfile passed via `--data`, so the Rego suppression helpers receive the same data the Python helpers see.

Finding-id-level matching (where a waiver targets a specific finding within a rule) remains deferred to WP-SCP-023's aggregator path — `_scp_active_waiver_for` mirrors Rego's rule-id-only fail-closed semantic.

## Operator notes

- The conflict-gate is for **EXISTING rules vs existing Python evaluators**. New rules without a Python equivalent should land first; the conflict-gate fixture for that rule lands in a follow-up PR alongside the Python equivalent.
- "Python authoritative on conflict" is the **eventual-resolution direction** — at runtime, the gate fails closed and adjudication happens in the amending PR. Python is not silently auto-winning.
