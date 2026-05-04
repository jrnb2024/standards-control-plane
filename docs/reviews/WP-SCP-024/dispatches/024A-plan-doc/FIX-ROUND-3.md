# 024A — fix-round-3 audit (R3 → fix → R4 candidate)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-024-estate-cascade-plan`
**Pre-fix-round-3 HEAD:** `7034725`

## R3 finding tally

3× parallel Sonnet R3: all 3 CHANGES_REQUESTED (R2 closures verified; new findings introduced by fix-round-2 edits).

| Lens | Verdict | new CRIT | new MAJ | new MIN | new nit | R2-closures verified |
|---|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 1 | 0 | 0 | 2/2 |
| safety_bypass | CHANGES_REQUESTED | 0 | 1 | 0 | 0 | 3/3 (1 partial → fix-round-3 closes) |
| completeness | CHANGES_REQUESTED | 0 | 2 | 0 | 0 | 4/4 |
| **total raw new** | — | **0** | **4** | **0** | **0** | — |

After dedup (each is in a distinct lens, no overlaps): **0 CRIT + 4 unique new MAJ**.

## Per-finding disposition

### MAJ (4 unique, all inline-fixed)

| ID | Lens | Disposition | Action |
|---|---|---|---|
| **R3-NEW-MAJ-001 (correctness)** | correctness | **INLINE-FIX** | §5.2 cascade-status field enumerates only 2 values (`onboarded` / `blocked-on-adopter-conflict`), but §6 024B describes 3 distinct CI check-paths (the operator-bump fallback being the third). Added `onboarded-operator-bump` as a third value across §5.2, invariant 2, §6 024B, and R-024-07. The CI script now parses three close-states + applies three check-paths. |
| **R3-NEW-MAJ-001 (safety)** | safety | **INLINE-FIX** | The conflict-close CI check verified TF-reference presence but did NOT assert that `branch-protection-log.md` was NOT modified. A malicious slice could invoke `enable-required-check.sh`, include the log entry, declare `cascade-status: blocked-on-adopter-conflict`, file the TF, and bypass the audit trail. **Fix:** invariant 2 now says when `cascade-status: blocked-on-adopter-conflict` is declared, CI MUST assert the log file was NOT modified in the PR diff. §6 024B acceptance row explicitly enumerates this assertion. |
| **R3-NEW-MAJ-001 (completeness)** | completeness | **INLINE-FIX** | §5.5 closing sentence said "This makes the §5.6 pattern testable" — should be §5.5 (the section is talking about its own pattern, not §5.6). Single-line fix. |
| **R3-NEW-MAJ-002 (completeness)** | completeness | **INLINE-FIX** | DISPATCH-NOTE line 81 (R1 review-bullet for completeness lens) still said "Are the 10 open questions in §10 actually open" — fix-round-1 trimmed §10 to 3. Updated to "3 open questions" + parenthetical noting the trim + closure marker. |

### MIN / nit
None new at R3 (all 6 R2 MIN/nit closures were verified as CLOSED).

## Inline-fix summary (~6 edits)

1. `docs/plans/WP-SCP-024-estate-cascade.md`:
   - **Invariant 2** rewritten with three-bullet CI check-path table covering all three close-states. Adds the "log file MUST NOT be modified" assertion for `blocked-on-adopter-conflict`.
   - **§5.2 item (2)** — cascade-status field enumerates 3 values with descriptions for each.
   - **§5.5 closing sentence** — `§5.6` → `§5.5` (self-reference fix).
   - **§6 024B row** — three check-paths enumerated; explicitly notes the no-modification assertion for conflict-close.
   - **R-024-07** — references `cascade-status: onboarded-operator-bump` explicitly.
2. `docs/reviews/WP-SCP-024/dispatches/024A-plan-doc/DISPATCH-NOTE.md`:
   - **Line 81 R1 review-bullet** — "10 open questions" → "3 open questions" + closure marker.

## R4 candidacy

R3 surfaced 0 new CRIT, 4 unique new MAJ (all inline-fixed), 0 MIN, 0 nit. Ready for R4 to verify R3 closures + no new CRIT/MAJ.

If R4 returns 0 new CRIT + 0 new MAJ on a complete cycle, **R4 fixpoint reached** per `feedback_recursive_adversarial_review.md`.

## Notable lesson

Fix-round-2 closed NEW-MAJ-001 (the carve-out for blocked-on-adopter-conflict) but introduced two consequential gaps:
1. **Asymmetric carve-out spec** (R3-NEW-MAJ-001 correctness) — adding the carve-out for one branch-status (`blocked-on-adopter-conflict`) without enumerating the third path (`onboarded-operator-bump`) created a §5.2/§6 inconsistency.
2. **Negative-assertion gap** (R3-NEW-MAJ-001 safety) — the carve-out only required positive evidence (TF reference present); it didn't require negative evidence (log NOT modified). A skip-the-check carve-out on a CI assertion needs both.

These are both classic "added a carve-out without thinking through the full state-space" defects. Worth filing forward as a heuristic for future plan-doc reviews: **when adding a carve-out clause, enumerate the full set of states + assert both positive evidence AND absence of contradicting evidence.**
