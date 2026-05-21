# TF-PIM-001 Wave E dispatch JSON — pragmatist lens R1

**Dispatched:** 2026-05-21 PM
**Agent type:** Plan (read-only)
**Model:** Sonnet
**Worktree isolation:** yes
**Lens domain:** execution feasibility + Codex actionability + verify_commands runnability + selftest CI correctness
**Artefact under review:** Wave E dispatch JSON v0.1

---

**Verdict:** ACCEPT-WITH-AMENDMENT
**Convergence signal:** ITERATE-EXPECTED
**Findings count:** 5 total (2 BLOCKING + 1 MAJ + 1 MIN + 1 NIT)

---

## Findings

### PRAG-BLOCKING-001

**Type:** BLOCKING
**Title:** CMD 20 `grep -cF` counts comment and string occurrences of the target pattern — post-Wave-E count is 5, not 3
**Where:** `verify_commands` CMD 20 — `test "$(grep -cF 'uses: ./.github/workflows/policy-check.yml' .github/workflows/workflow-selftest.yml)" = 3`

**Finding:** `grep -cF` performs a substring match on every line. `workflow-selftest.yml` contains two non-job lines that contain the substring:
- Line 45 (Python comment): `# uses: ./.github/workflows/policy-check.yml@<sha>` which`
- Line 60 (Python string literal): `"`uses: ./.github/workflows/policy-check.yml` (no @ref)"`

Pre-Wave-E grep count: 4 (2 comment/string + 2 actual jobs). Post-Wave-E: 5. CMD tests for `= 3` — false-BLOCKED on every correct Codex execution. Same pattern as Wave D PRAG-MAJ-001.

The existing `validate-selftest-config` Python check uses regex `r"uses:\s+\./\.github/workflows/policy-check\.yml\s*$"` with `re.M`, anchored to end-of-line — correctly distinguishes job-level `uses:` from comment/string occurrences.

**Suggested closure:** Replace CMD 20 with: `python3 -c "import re; t=open('.github/workflows/workflow-selftest.yml').read(); n=len(re.findall(r'uses:\\s+\\./\\.github/workflows/policy-check\\.yml\\s*$', t, re.M)); assert n == 3, f'expected 3 policy-check.yml uses, got {n}'"`.

---

### PRAG-BLOCKING-002

**Type:** BLOCKING
**Title:** Missing EDIT 7 — Wave E adds third `policy-check.yml` invocation but does not update `validate-selftest-config` hardcoded count guard from `!= 2` to `!= 3`
**Where:** `.github/workflows/workflow-selftest.yml` lines 56-62; dispatch JSON edits 1-6

**Finding:** Same 3-lens-consensus issue (sec SEC-BLOCKING-001 + arch-skeptic ARCH-MAJ-001). The `validate-selftest-config` Python check `if local_uses_count != 2` breaks when Wave E adds the third invocation. None of the 6 edits address this.

The Wave E PR itself triggers `workflow-selftest`, which immediately fails `validate-selftest-config`. Wave F's SCP-self dogfood verify acceptance criterion is directly compromised.

**Suggested closure:** Add EDIT 7 updating the Python check `!= 2` → `!= 3` and the error message string. Add corresponding verify_command.

---

### PRAG-MAJ-001

**Type:** MAJ
**Title:** EDIT 2 and Invariant 4 claim "14 existing env-mappings" — actual count is 15
**Where:** EDIT 2 prose ("PRESERVE all 14 existing env-mappings verbatim. The new mapping is the FIFTEENTH."); Invariant 4 ("The other 14 env-mappings are unchanged.")

**Finding:** Direct inspection of `policy-check.yml` lines 75-89 shows 15 env-mapping entries. Wave D adds no env-mappings, so count at Wave E dispatch time remains 15. The new mapping should be the SIXTEENTH, not fifteenth. gpt-5.4 encountering "14 existing" while the file has 15 may attempt to reconcile by deletion.

**Suggested closure:** Correct all occurrences: "PRESERVE all 15 existing env-mappings verbatim. The new mapping is the SIXTEENTH." (EDIT 2 prose). "The other 15 env-mappings are unchanged." (Invariant 4). Consider adding verify_command: `test "$(grep -cE '^\s+SCP_[A-Z_]+:' .github/workflows/policy-check.yml | head -1)" -ge 16`.

---

### PRAG-MIN-001

**Type:** MIN
**Title:** EDIT 3 prose says "(9 lines)" but the YAML block contains 8 lines
**Where:** EDIT 3 instruction header

**Finding:** Counting the EDIT 3 YAML block:
1. `- name: Simulate App token-exchange failure...`
2. `if: ${{ inputs.simulate-app-token-failure }}`
3. `shell: bash`
4. `env:`
5. `SCP_TEST_SIMULATE_APP_TOKEN_FAILURE: ${{ inputs.simulate-app-token-failure }}`
6. `run: |`
7. `echo "::error..."`
8. `exit 1`

= 8 lines. Header says 9. Off-by-one prose error (matches Wave D's PRAG-MIN-001 pattern — Wave D claimed 8 but had 9). The discrepancy is amplified by arch-skeptic NIT-001 (which recommends removing the step-level env declaration entirely, leaving 6 lines).

**Suggested closure:** After ARCH-NIT-001 closure (remove step-level env), the block becomes 6 lines. Correct prose to "Required YAML body (6 lines):" or "(8 lines)" depending on whether ARCH-NIT-001 is folded.

---

### PRAG-NIT-001

**Type:** NIT
**Title:** EDIT 2 "alphabetical order" parenthetical escape clause confusing — current env block is not fully alphabetical
**Where:** EDIT 2 prose — "(or wherever alphabetical ordering of the existing keys places `SCP_TEST_...`)"

**Finding:** Current env block is not strictly alphabetical (`SCP_RUNTIME_ROOT` is after `SCP_THRESHOLD`). The parenthetical escape clause creates ambiguity. The primary anchor ("Insert immediately after `SCP_SUMMARY_PATH:`") is sufficient.

**Suggested closure:** Remove the parenthetical clause.

---

## Codex execution feasibility disposition

With BLOCKING-001 and BLOCKING-002 closed plus the MAJ closure (env count), gpt-5.4 xhigh is highly likely to land verify-pass on first attempt. Six discrete edits (seven post-closure) with precise verbatim YAML, explicit anchor strings, well-reasoned design choices. EDIT 5a provides both old and new `needs:` blocks for unambiguous block-replacement. EDIT 5b anchors are globally unique. The PRECONDITION block + ARCH-MIN-002's pre-flight verify_commands provide a clear abort criterion. Once BLOCKING + MAJ closures fold, first-attempt success is high.

## Verify_commands runnability disposition

26 of 28 verify_commands are syntactically valid and semantically correct. CMDs 0-1 (YAML parse), CMDs 2-19 (`grep -F` substring matches), CMDs 21-25 (semantic ordering probes), CMD 26 (scope gate with `printf | sort`), CMD 27 (diff-size bounds) — all sound. CMD 20 (grep -cF count) is BLOCKING. After CMD 20 replacement (Python regex) and EDIT 7 addition, all verify_commands will produce a clean verify-pass on any correct Codex execution.

## Convergence signal rationale

ITERATE-EXPECTED. Two BLOCKING + one MAJ + one MIN + one NIT. BLOCKING-001 (CMD 20) — replace single command. BLOCKING-002 (missing EDIT 7) — add EDIT block + verify_command. MAJ (env count) — three string corrections + optional verify_command. MIN and NIT — one-line prose corrections. After v0.2 fold, R2 expected to reach R-FIXPOINT-MET.
