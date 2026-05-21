# TF-PIM-001 Wave E dispatch JSON — R1 synthesis

**Date:** 2026-05-21 PM
**Artefact under review:** `docs/governance/work-packages/tf-pim-001-wave-e-selftest-harness-coverage.json` (v0.1)
**Lenses dispatched:** sec / arch-skeptic / pragmatist (3-lens auth-surface default)
**Scope-breach observations:** R1 ZERO scope-breach across all three lenses (preserves 11-cycle estate-wide ZERO-violation streak → 12-cycle).

## Verdict matrix

| Lens | Verdict | Convergence | BLOCK | MAJ | MIN | NIT |
|------|---------|-------------|-------|-----|-----|-----|
| sec | ACCEPT-WITH-AMENDMENT | ITERATE-EXPECTED | 1 | 1 | 2 | 1 |
| arch-skeptic | ACCEPT-WITH-AMENDMENT | ITERATE-EXPECTED | 0 | 1 | 3 | 3 |
| pragmatist | ACCEPT-WITH-AMENDMENT | ITERATE-EXPECTED | 2 | 1 | 1 | 1 |
| **TOTAL** | | | **3 (2 unique)** | **3 (2 unique)** | **6 (4 unique after dedup)** | **5** |

3-lens consensus: ITERATE-EXPECTED. 3 BLOCKING findings collapse to 2 unique issues; 3 MAJ to 2 unique; 6 MIN to ~4 unique.

## v0.2 closure plan

### BLOCKING closures (mandatory)

1. **3-lens consensus: missing EDIT 7 for `validate-selftest-config` count guard.** sec BLOCKING-001 + arch-skeptic MAJ-001 + pragmatist BLOCKING-002 all converge. Add EDIT 7 changing `if local_uses_count != 2:` to `if local_uses_count != 3:` + error message string from "exactly twice" to "exactly three times". Add verify_command. Without this, the `validate-selftest-config` job hard-fails on the Wave E PR itself, blocking ALL downstream selftest jobs.
2. **pragmatist BLOCKING-001: CMD 20 grep-cF counts comment + string lines.** Pre-Wave-E count is 4 (2 comment/string + 2 actual jobs); post-Wave-E is 5; CMD tests for `= 3`. False-BLOCKED every correct run. Replace with Python regex using `re.M` + `\s*$` end-of-line anchor (same mechanism `validate-selftest-config` uses).

### MAJ closures (must close pre-dispatch)

3. **sec MAJ-001: SCP-E001 annotation format + semantic.** Add `file=.github/workflows/policy-check.yml` parameter to EDIT 3 error annotation (matches existing 16 SCP-E001 emission sites). Add `(selftest)` suffix to title for monitoring-adopter distinguishability. Document SCP-E001 reuse rationale in notes (App token-exchange failure IS infrastructure-failure semantically per ADOPT-001 §12.7.7).
4. **pragmatist MAJ-001: env-mapping count off-by-one.** EDIT 2 + Invariant 4 say "14 existing"; actual is 15. Fix to "15 existing" + "SIXTEENTH". Optionally add count verify_command.

### MIN closures (fold cheap)

5. **sec MIN-002 + arch-skeptic MIN-001: EDIT 5b cancelled clause.** Add `|| [ "${SIMULATE_FAILURE_RESULT}" = "cancelled" ]` to the assertion. Distinguish three outcomes in error message: failure (good), cancelled (acceptable workflow-run cancellation), other (wiring broken).
6. **arch-skeptic MIN-002: PRECONDITION pre-flight verify_commands.** Add two pre-flight checks AT THE START of the verify_commands array: assert Wave D token-exchange step name + step id present BEFORE any other check fires.
7. **arch-skeptic MIN-003: diff-bound recalibration.** Bump CMD 28 (now CMD 30 after additions) from `-ge 35 -le 90` to `-ge 55 -le 95` reflecting the post-EDIT-7 minimum.
8. **sec MIN-001: persist-credentials structural preservation note.** Fold into Invariant 1 description that EDIT 3 is `run:`-only (no checkout, so count preserved by construction).

### NIT closures (one-line fixes)

9. **arch-skeptic NIT-001: remove EDIT 3 step-level env.** Dead code in the implemented `if:`-gated approach. Reduces EDIT 3 from 8 to 6 lines.
10. **arch-skeptic NIT-002: amend EDIT 4 `needs:` rationale comment.** Replace "avoids parallel artifact-name conflict" (incorrect — simulate job exits before artifact write) with "harness sequencing convention".
11. **arch-skeptic NIT-003: extend EDIT 6 to fix conftest.md stale paragraph** about SHA-pinning convention (superseded by local-ref approach per `validate-selftest-config` comment).
12. **pragmatist MIN-001: EDIT 3 line-count correction.** After ARCH-NIT-001 closure removes step-level env, EDIT 3 YAML is 6 lines, not 8 or 9. Update prose accordingly.
13. **pragmatist NIT-001: remove EDIT 2 alphabetical parenthetical.** Current env block not strictly alphabetical; parenthetical creates ambiguity.
14. **sec NIT-001: notes blast-radius accidental case.** Add "accidental mis-set is the more likely scenario" to the blast-radius description.

## ARCH-NIT-002 + ARCH-NIT-003: Special considerations

ARCH-NIT-003 (conftest.md stale paragraph) extends EDIT 6 scope but stays within `scope_boundary` (conftest.md already listed). Fold without scope expansion.

ARCH-NIT-002 (EDIT 4 comment rationale) is a YAML-comment correctness issue; one-line replacement in the dispatch instruction. Fold.

## Total v0.2 fold size

7 EDITS (up from 6 in v0.1) across 3 files. ~32 verify_commands (up from 28). v0.2 instruction prose substantively rewritten to absorb closures. Plan-doc fidelity hygiene notes preserved.

## R2 expectations

After v0.2 fold: zero new BLOCKING/MAJ findings expected. Possibly 1-2 NIT findings on the closure prose itself. R-FIXPOINT-MET projected at R2 per the Wave D R-cycle precedent (R1 surfaced 14 findings; R2 with R-FIXPOINT-MET + 1 residual NIT).

## DO-NOT-EDIT mandate streak

ZERO scope-breach observations across Wave E R1 — 12-cycle estate-wide streak preserved. Sample-size-3 incident citation continues to be load-bearing in lens prompts.
