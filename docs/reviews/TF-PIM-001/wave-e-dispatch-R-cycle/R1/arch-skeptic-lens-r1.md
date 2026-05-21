# TF-PIM-001 Wave E dispatch JSON — arch-skeptic lens R1

**Dispatched:** 2026-05-21 PM
**Agent type:** Plan (read-only)
**Model:** Sonnet
**Worktree isolation:** yes
**Lens domain:** architectural fit + reversibility + failure-surface + plan-doc fidelity + cross-wave coupling
**Artefact under review:** Wave E dispatch JSON v0.1

---

**Verdict:** ACCEPT-WITH-AMENDMENT
**Convergence signal:** ITERATE-EXPECTED
**Findings count:** 7 total (0 BLOCKING + 1 MAJ + 3 MIN + 3 NIT)

---

## Findings

### ARCH-MAJ-001

**Type:** MAJ (escalated to BLOCKING-class by sec + pragmatist 3-lens consensus)
**Title:** `validate-selftest-config` job hardcodes `local_uses_count != 2` — Wave E's third invocation will break the harness's own preflight check
**Where:** `.github/workflows/workflow-selftest.yml` lines 52-61; dispatch JSON has no EDIT to amend this guard

**Finding:** The `validate-selftest-config` job contains a Python inline check asserting `local_uses_count != 2`. Wave E's EDIT 4 adds a third `uses: ./.github/workflows/policy-check.yml` line. After Wave E, count=3, assertion fires, `validate-selftest-config` exits non-zero, ALL downstream selftest jobs blocked.

**Why it matters:** Permanent runtime failure that blocks every subsequent PR until amended. Same finding raised as sec SEC-BLOCKING-001 + pragmatist PRAG-BLOCKING-002.

**Suggested closure:** Add EDIT 7: change `if local_uses_count != 2:` to `if local_uses_count != 3:` and update error string from "exactly twice" to "exactly three times". Add verify_command.

---

### ARCH-MIN-001

**Type:** MIN
**Title:** EDIT 5b assertion does not guard against `cancelled`
**Where:** EDIT 5b step body; EDIT 4 `needs: fixture-fail-policy-check`

**Finding:** Upstream cancellation propagates `cancelled` not `failure`. EDIT 5b's strict equality on `failure` false-fails. Matches sec SEC-MIN-002.

**Suggested closure:** Add `|| [ "${SIMULATE_FAILURE_RESULT}" = "cancelled" ]` to the assertion.

---

### ARCH-MIN-002

**Type:** MIN
**Title:** PRECONDITION enforcement not verifiable via verify_commands — abort condition stated in prose only
**Where:** Dispatch JSON `instruction` PRECONDITION block; `verify_commands` 7-13 (run POST-edit, not pre-flight)

**Finding:** PRECONDITION says ABORT if Wave D anchors absent. Verify_commands check anchors POST-edit. If anchors missing, Codex applies EDIT 3 with no insertion target — YAML may still parse but step is misplaced. No machine-enforced pre-flight gate.

**Suggested closure:** Add two pre-flight verify_commands AT THE START of the list:
- `grep -qF 'Obtain SCP federation App installation token' .github/workflows/policy-check.yml || { echo 'PRECONDITION FAIL: Wave D token-exchange step missing'; exit 1; }`
- `grep -qF 'id: scp-app-token' .github/workflows/policy-check.yml || { echo 'PRECONDITION FAIL: Wave D scp-app-token step id missing'; exit 1; }`

---

### ARCH-MIN-003

**Type:** MIN
**Title:** Diff-bound lower 35 calibration off after MAJ-001 closure
**Where:** verify_commands CMD 28 — `test "$ADDED" -ge 35 -le 90`

**Finding:** Post-MAJ-001-closure adds 1-2 more lines (the count-guard amendment). Estimated minimum becomes ~65-70 lines. Lower bound 35 gives no meaningful containment.

**Suggested closure:** Re-calibrate to `-ge 55 -le 95` after MAJ-001 closure.

---

### ARCH-NIT-001

**Type:** NIT
**Title:** EDIT 3 step-level env-mapping is redundant given EDIT 2's job-level env-mapping
**Where:** EDIT 3 YAML body — `env: SCP_TEST_SIMULATE_APP_TOKEN_FAILURE: ${{ inputs.simulate-app-token-failure }}`

**Finding:** Step-level env declaration is dead code in the implemented approach (simulate step uses `if:` gate, not env-var runtime check; `run:` script doesn't reference the env-var). Job-level mapping already provides the var.

**Suggested closure:** Remove the step-level `env:` block from EDIT 3 entirely.

---

### ARCH-NIT-002

**Type:** NIT
**Title:** `needs: fixture-fail-policy-check` rationale comment inaccurate
**Where:** EDIT 4 comment block — "depends on `fixture-fail-policy-check` for sequencing (avoids parallel artifact-name conflict)"

**Finding:** The simulate job exits at step 2 before any artifact-write step. Artifact-name conflict concern doesn't apply. Real reason: harness sequencing convention.

**Suggested closure:** Amend comment to: "needs `fixture-fail-policy-check` for linear harness sequencing (not for artifact-name conflict, which does not apply since this job exits before the artifact-write step; sequencing convention preserved for harness consistency)."

---

### ARCH-NIT-003

**Type:** NIT
**Title:** conftest.md describes superseded SHA-pinning convention as current
**Where:** `tests/workflow/conftest.md` lines 11-13 (existing paragraph about `uses:` pins)

**Finding:** The existing conftest.md says "The selftest pins `policy-check.yml` to the latest commit... Any PR that changes that workflow must update both pinned `uses:` lines." But `workflow-selftest.yml`'s `validate-selftest-config` inline comment says this approach was ABANDONED — local-ref `@<ref>` is invalid; local workflows always run at calling workflow's HEAD SHA. Wave E modifying conftest.md is the right time to fix this stale text.

**Suggested closure:** Extend EDIT 6 to replace the stale paragraph with: "The selftest invokes `policy-check.yml` as a local reusable workflow (`uses: ./.github/workflows/policy-check.yml` without `@<ref>`). GitHub Actions does not support `@<ref>` for local reusable-workflow `uses:` lines; local workflows always run at the calling workflow's HEAD SHA. The `validate-selftest-config` preflight job verifies the invocation count instead."

---

## Plan-doc fidelity disposition

The dispatch JSON's ENV-VAR-vs-input divergence from plan-doc §4 Wave E Action step 2 is well-rationalised in the `notes` field. The functional semantics are identical to the plan-doc's intent. The post-R-fixpoint hygiene amendment flag for the plan-doc is appropriate. One additional fidelity gap: the plan-doc §4 Wave E Action step 5 names `tests/workflow-selftest/README.md` (non-existent path) while the dispatch JSON correctly uses `tests/workflow/conftest.md`. This path-discrepancy should also be flagged as a plan-doc hygiene amendment candidate post-R-fixpoint.

## Cross-wave coupling disposition

Wave E reverts cleanly without touching Wave D. Wave D revert while Wave E is present would orphan Wave E's simulate step. The dispatch JSON documents this correctly. The PRECONDITION block is the weak point — sequencing is prose-stated. ARCH-MIN-002's pre-flight verify_commands provide the nearest-feasible machine enforcement.

## Convergence signal rationale

ITERATE-EXPECTED. One MAJ (ARCH-MAJ-001 = sec BLOCKING + pragmatist BLOCKING — 3-lens consensus). Three MIN + three NIT all addressable inline in a single v0.2 fold. After v0.2, R2 expected to reach R-FIXPOINT-MET.
