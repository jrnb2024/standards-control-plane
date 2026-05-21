# TF-PIM-001 Wave E dispatch JSON — pragmatist lens R2

**Dispatched:** 2026-05-21 PM (post v0.2 fold)
**Agent type:** Plan (read-only)
**Model:** Sonnet
**Worktree isolation:** yes
**Lens domain:** execution feasibility + Codex actionability + verify_commands runnability
**Artefact under review:** Wave E dispatch JSON v0.2

---

**Verdict:** ACCEPT
**Convergence signal:** R-FIXPOINT-MET
**Findings count:** 3 total (0 BLOCKING + 0 MAJ + 1 MIN + 2 NIT)
**R1 closures verified:** PRAG-BLOCKING-001, PRAG-BLOCKING-002, PRAG-MAJ-001, PRAG-MIN-001, PRAG-NIT-001 — all CONFIRMED CLOSED
**New findings:** 3 (PRAG-R2-MIN-001 CMD 28 redundant; PRAG-R2-NIT-001 EDIT 5b line count; PRAG-R2-NIT-002 "machine-enforced" label)

---

## R1 closure verification

### PRAG-BLOCKING-001 — CLOSED
CMD 25 is the Python regex one-liner. Escaping chain traced: JSON `\\\\s` → bash `\\s` → Python `\s` (regex whitespace). The pattern Python receives is `uses:\s+\./\.github/workflows/policy-check\.yml\s*$` with `re.M`. Pre-Wave-E count=2 (job-level only); post-Wave-E count=3. Comment and string occurrences correctly excluded.

### PRAG-BLOCKING-002 — CLOSED
EDIT 7 present; `local_uses_count != 2:` → `local_uses_count != 3:` plus message update. CMDs 23+24 verify. Anchor `local_uses_count != 2:` is unique in `workflow-selftest.yml`.

### PRAG-MAJ-001 — CLOSED
EDIT 2 + Invariant 4 prose corrected to "15 existing env-mappings" and "SIXTEENTH".

### PRAG-MIN-001 — CLOSED
EDIT 3 prose says "(6 lines)" matching the 6-line YAML block after step-level env removal.

### PRAG-NIT-001 — CLOSED
EDIT 2 alphabetical parenthetical removed.

---

## New findings

### PRAG-R2-MIN-001

**Type:** MIN
**Title:** CMD 28 (SCP env-mapping count check) is vacuously true pre-Wave-E
**Where:** `verify_commands[28]` — `test "$(grep -cE '^\s+SCP_[A-Z_]+:' .github/workflows/policy-check.yml)" -ge 16`

**Finding:** The regex matches every YAML line with leading whitespace + `SCP_` name + colon — including 3 step-level env entries in the `attest-scorecard` job (lines ~1241-1243). Pre-Wave-E count is already 18. Post-Wave-E without EDIT 2 the count remains 18, still passing `-ge 16`. The CMD does not detect a missing EDIT 2. The actual reliable EDIT 2 verification is CMD 5 (`grep -F 'SCP_TEST_SIMULATE_APP_TOKEN_FAILURE: ${{ inputs.simulate-app-token-failure }}'`). CMD 28 is redundant but not false-FAIL.

**Impact:** Verification-suite documentation accuracy issue; no Codex first-attempt risk.

**Suggested closure (optional):** Remove CMD 28 (covered by CMD 5) OR tighten to `-eq 19` with comment explaining the +3 from step-level env entries. Operator-paced post-R-fixpoint.

---

### PRAG-R2-NIT-001

**Type:** NIT
**Title:** EDIT 5b prose says "(11 lines)" but the YAML block is 10 lines
**Where:** EDIT 5b instruction header

**Finding:** Counting EDIT 5b block: `- name:`, `shell: bash`, `env:`, `SIMULATE_FAILURE_RESULT: ...`, `run: |`, `set -euo pipefail`, `[ ... ] || [ ... ] || {`, `echo "::error::..."`, `exit 1`, `}` = 10 lines. Prose says 11. Same off-by-one pattern as R1 PRAG-MIN-001. gpt-5.4 xhigh uses verbatim YAML; no correctness risk.

**Suggested closure (optional):** Change "(11 lines)" to "(10 lines)".

---

### PRAG-R2-NIT-002

**Type:** NIT
**Title:** Pre-flight CMDs 0-1 labelled "machine-enforced" but `codex_dispatch.py` runs verify_commands post-Codex
**Where:** PRECONDITION block — "machine-enforced via verify_commands 0-1; aborts hard before any edit if violated"

**Finding:** `codex_dispatch.py` lines 574-590 run all verify_commands AFTER Codex completes its session. Pre-edit abort relies on Codex self-aborting from reading the verify_commands in its prompt. The safety outcome is equivalent (failed pre-flight CMDs still trigger `gate_failure = "verify_failed"`), but the "machine-enforced" label overstates the guarantee.

**Suggested closure (optional):** Rephrase "machine-enforced via verify_commands 0-1" to "enforced via verify_commands 0-1; these run post-edit and will hard-fail the dispatcher if Wave D artefacts are absent; Codex is instructed to self-abort before editing if either check would fail". Alternatively leave unchanged — practical safety identical.

---

## Codex execution feasibility (post-v0.2)

Seven edits across three files; all anchors globally unique in their target files. gpt-5.4 xhigh at reasoning_effort: xhigh has high first-attempt success probability. EDIT 6a (paragraph replacement) is the only edit with elevated risk (prose document); anchor specificity mitigates.

## Verify_commands runnability (post-v0.2)

All 37 verify_commands syntactically valid + semantically correct on a correct Codex execution. CMD 28 produces false-PASS on unmodified tree but is covered by CMD 5. No false-FAIL risk.

## Convergence signal rationale

R-FIXPOINT-MET. All five R1 PRAG findings closed. Three new findings (1 MIN + 2 NIT) all are documentation precision issues with zero operational impact on Codex first-attempt success or CI correctness. None require structural changes. The dispatch is ready for Tier 2 operator-attended fire.
