# TF-PIM-001 Wave E dispatch JSON — sec lens R1

**Dispatched:** 2026-05-21 PM (post Wave D R-FIXPOINT MET)
**Agent type:** Plan (read-only; DO-NOT-EDIT mandate per `feedback_subagent_review_only_scope_must_be_enforced`)
**Model:** Sonnet
**Worktree isolation:** yes
**Lens domain:** threat-model + auth-surface + backdoor-attack-surface + bypass-prevention
**Artefact under review:** Wave E dispatch JSON v0.1

---

**Verdict:** ACCEPT-WITH-AMENDMENT
**Convergence signal:** ITERATE-EXPECTED
**Findings count:** 5 total (1 BLOCKING + 1 MAJ + 2 MIN + 1 NIT)

---

## Findings

### SEC-BLOCKING-001

**Type:** BLOCKING
**Title:** `validate-selftest-config` hardcoded `!= 2` guard breaks CI — missing EDIT 7
**Where:** `instruction` (EDIT 4 description) + `verify_commands` (28 commands; none covering this). Root artefact: `.github/workflows/workflow-selftest.yml` line 57: `if local_uses_count != 2:` / `"workflow-selftest must invoke policy-check.yml exactly twice"`.

**Finding:** The `validate-selftest-config` job in `workflow-selftest.yml` contains a Python inline script (lines 51-61) that reads the file's own text, counts matches of `uses: ./.github/workflows/policy-check.yml` and asserts `local_uses_count != 2` — raising SystemExit. Wave E's EDIT 4 adds a third `uses: ./.github/workflows/policy-check.yml` job. After Wave E's edits land, the count will be 3, the assertion fires, and `validate-selftest-config` exits non-zero — failing the entire `workflow-selftest` workflow on every subsequent PR that touches the workflow-selftest trigger paths. The dispatch JSON contains no instruction to amend the `!= 2` guard.

**Why it matters:** The immediate consequence is that the `workflow-selftest` workflow fails on every PR after Wave E. This is the primary harness gate for the federation primitive. A broken `workflow-selftest` gate puts the entire selftest harness offline — the precise opposite of Wave E's purpose.

**Suggested closure:** Add a new EDIT (EDIT 7) updating the `validate-selftest-config` Python check from `!= 2` to `!= 3` and the error message string from 'exactly twice' to 'exactly three times'. Add a verify_command: `grep -F 'local_uses_count != 3' .github/workflows/workflow-selftest.yml`.

---

### SEC-MAJ-001

**Type:** MAJ
**Title:** SCP-E001 semantic conflict — Wave E reuses infra-failure code for test-only simulation; emits without `file=` parameter (format inconsistency with 16 existing SCP-E001 sites)
**Where:** EDIT 3 step body — `echo "::error title=SCP-E001::Simulated App installation token-exchange failure..."`; ADOPT-001 §12.7.7 closed set

**Finding:** ADOPT-001 §12.7.7 defines SCP-E001 as "Infrastructure fetch failure (OPA/Conftest binary unreachable, SHA256 mismatch, lockfile pin missing)." The existing 16 SCP-E001 emission sites all use the format `::error file=.github/workflows/policy-check.yml,title=SCP-E001::...`. Wave E's EDIT 3 emits SCP-E001 with NO `file=` parameter. This is both a semantic-bleed concern (real infra failure vs test stub) and a format inconsistency. An adopter monitoring SCP-E001 may receive false-positive signals.

**Why it matters:** Not a security bypass; an annotation-surface semantic corruption that erodes the closed-set invariant's value. The closed annotation set exists so adopters can write deterministic monitors on SCP-EXXX codes.

**Suggested closure:** Add `file=.github/workflows/policy-check.yml` to the EDIT 3 error annotation matching existing SCP-E001 format. Add `(selftest)` suffix to the title so monitoring adopters can distinguish the test-only annotation. Document in `notes`: SCP-E001 reuse rationale (App token-exchange failure IS an infrastructure failure semantically; selftest exercises the same failure path).

---

### SEC-MIN-001

**Type:** MIN
**Title:** Wave D `persist-credentials: false` preservation under EDIT 3 — count is structurally preserved but not explicitly asserted
**Where:** Invariant 1 description; EDIT 3 step body

**Finding:** EDIT 3 simulate step is `run:`-only (no `actions/checkout`), so `persist-credentials: false` count of 3 is structurally preserved by construction. The dispatch instruction does not explicitly state this — a careful reader sees the EDIT 3 step body has no checkout, but the invariant description doesn't call it out. If Codex misreads the insertion target, a regression could be introduced.

**Suggested closure:** Fold into invariant 1: "EDIT 3 is a `run:`-only step and adds no `actions/checkout` call — the `persist-credentials: false` count of 3 is structurally preserved." Optionally add: `! grep -A20 'Simulate App token-exchange failure' .github/workflows/policy-check.yml | grep -F 'actions/checkout'`.

---

### SEC-MIN-002

**Type:** MIN
**Title:** EDIT 5b assertion does not guard against `cancelled` upstream outcome
**Where:** EDIT 5b step body — `[ "${SIMULATE_FAILURE_RESULT}" = "failure" ] || { ... exit 1; }`

**Finding:** EDIT 4 has `needs: fixture-fail-policy-check`. If upstream is cancelled (user cancellation, runner loss), the simulate job propagates `cancelled` not `failure`. EDIT 5b's strict equality test false-fails on this realistic edge case. The existing harness's `Assert upstream job outcomes are inspectable` step already distinguishes `cancelled` for `fixture-fail-policy-check`.

**Suggested closure:** Amend EDIT 5b: `[ "${SIMULATE_FAILURE_RESULT}" = "failure" ] || [ "${SIMULATE_FAILURE_RESULT}" = "cancelled" ] || { ... exit 1; }`. Error message should distinguish: failure = by-design (good); cancelled = workflow-run cancellation (acceptable); anything else = wiring broken (bad).

---

### SEC-NIT-001

**Type:** NIT
**Title:** Notes blast-radius description omits accidental mis-set scenario
**Where:** `notes` blast-radius assessment paragraph

**Finding:** Description covers malicious case but omits accidental case (typo, Renovate misconfiguration, copy-paste error). The accidental case has the same bounded blast radius — should be on-record.

**Suggested closure:** Amend `notes`: "Blast radius if mis-set (accidentally or maliciously): the policy-check job fails on the mis-setting caller's own PR; no cross-adopter contamination; no escape from the caller's own context. Accidental mis-set is the more likely scenario."

---

## Federation-primitive invariants 1-5 disposition

All five invariants preserved under Wave E v0.1 with the SEC-MAJ-001 SCP-E001 semantic-bleed noted as a closure-required precision issue. The simulate step is `run:`-only with no `actions/checkout`, no token, no `secrets:` block — preserves invariants 1+2+4. The new input is a boolean flag, not a secret carrier. The trust-root SHA pins are unchanged. Annotation surface is preserved in the sense that no NEW SCP-EXXX code is introduced (D-050 §Justification invariant 5 still satisfied), but SCP-E001 semantic reuse needs the SEC-MAJ-001 closure to keep the monitoring surface clean.

## Backdoor surface assessment

The `simulate-app-token-failure` input does not introduce a meaningful backdoor. The only effect of setting it true is the simulate step emits SCP-E001 and exits 1 — failing the caller's own PR. No bypass path: there is no conditional branch inside the step that could pass. Combining with `inputs.threshold` manipulation does not change this (the simulate step exits before threshold logic runs). Default `false` → production callers see no behavior change. Blast radius bounded to caller's own PR.

## Convergence signal rationale

ITERATE-EXPECTED. One BLOCKING (SEC-BLOCKING-001 = missing EDIT 7 for validate-selftest-config count guard — 3-lens consensus with arch-skeptic ARCH-MAJ-001 + pragmatist PRAG-BLOCKING-002). One MAJ (SCP-E001 format + semantic precision). Two MIN. One NIT. All remediable inline in a v0.2 fold. After fold, R2 expected to reach R-FIXPOINT-MET.
