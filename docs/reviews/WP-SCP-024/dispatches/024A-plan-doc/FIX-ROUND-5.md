# 024A — fix-round-5 audit (R5 → fix → R6 candidate)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-024-estate-cascade-plan`
**Pre-fix-round-5 HEAD:** `f182b35`

## R5 finding tally

3× parallel Sonnet R5: all 3 CHANGES_REQUESTED.

| Lens | Verdict | new CRIT | new MAJ | new MIN | new nit |
|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 2 | 0 | 0 |
| safety_bypass | CHANGES_REQUESTED | 0 | 2 | 0 | 0 |
| completeness | CHANGES_REQUESTED | 0 | 2 | 1 | 1 |
| **total raw new** | — | **0** | **6** | **1** | **1** |

After dedup:
- §1 item 2 unconditional invocation-log: correctness + safety BOTH flagged (R5-NEW-MAJ-001 each lens) = 1 unique MAJ
- DISPATCH-NOTE risk surface item 4 stale "log-entry mandatory": correctness only (R5-NEW-MAJ-002) = 1 unique MAJ
- meaningful-content format spec needed: safety only (R5-NEW-MAJ-002) = 1 unique MAJ
- §5.2 + R-024-06 missing meaningful-content qualifier: completeness (R5-NEW-MAJ-001 + R5-NEW-MAJ-002) = 2 unique MAJ
- DISPATCH-NOTE criterion (iii) stale invariant 2 summary: completeness MIN
- Closes-marker missing "(safety)" lens qualifier: completeness nit

After dedup: **0 CRIT + 5 unique new MAJ + 1 MIN + 1 nit**.

## Per-finding disposition

### MAJ (5 unique, all inline-fixed)

| ID | Lens(es) | Disposition | Action |
|---|---|---|---|
| **R5-NEW-MAJ-001 (correctness + safety)** | correctness, safety | **INLINE-FIX** | §1 Purpose item 2 said "(b) `enable-required-check.sh` invocation per D-035 with invocation-log entry" UNCONDITIONALLY. Same defect class as fix-round-4's R4-NEW-MAJ-002 §3 fix; §1 was the highest-level reader entry-point that was missed. Fix: §1 item 2 (b) now references "conditional on the slice's `cascade-status:` declaration per §5.2 + invariant 2". |
| **R5-NEW-MAJ-002 (correctness)** | correctness | **INLINE-FIX** | DISPATCH-NOTE risk surface item 4 said "invariant 2 makes log-entry mandatory" — pre-fix-round-3 framing. Fix: rewrote with three-path cascade-status spec; explicit reference to log-NOT-modified for conflict-close. |
| **R5-NEW-MAJ-002 (safety)** | safety | **INLINE-FIX** | "Meaningful content" was specified only as "status field + non-empty description" — not machine-enforceable; two executors could produce different specs. **Fix: invariant 2 now ships a precise regex spec** + 3 worked examples (one ✅, two ❌). The regex is `^- \*\*TF-024X-(renovate\|conflict)-[a-z0-9]+(?:-[a-z0-9]+)+\*\* \((open\|pending\|in-progress\|closed)\): .{20,}$`. Codex executors implementing `check-invocation-log-entry.sh` use this regex literally. |
| **R5-NEW-MAJ-001 (completeness)** | completeness | **INLINE-FIX** | §5.2 item (2) blocked-on-adopter-conflict description didn't carry "with meaningful content" qualifier. Fix: §5.2 now references "meaningful content per invariant 2's regex spec" with cross-reference. |
| **R5-NEW-MAJ-002 (completeness)** | completeness | **INLINE-FIX** | R-024-06 mitigation column described CI check as just "verifies the TF reference IS present" — missing meaningful-content + format-match. Fix: R-024-06 now lists three CI checks (positive evidence + meaningful-content format match + negative assertion). |

### MIN / nit (closed)

| ID | Disposition | Action |
|---|---|---|
| **R5-NEW-MIN-001 (completeness)** | **INLINE-FIX** | DISPATCH-NOTE criterion (iii) invariant 2 summary updated from "operator-run + invocation-logged" to "operator-run + invocation-logged + CI-enforced (three-path cascade-status...)". |
| **R5-NEW-nit-001 (completeness)** | **INLINE-FIX** | Closes-marker for R4-NEW-MAJ-002 in invariant 2 line 46 now reads "(safety)" lens qualifier. |

### Companion sweep findings (proactive, not from R5)

While doing the comprehensive grep sweep for R5 propagation gaps, I also caught + fixed:

- §6 line 176 (Threshold A telemetry): "branch-protection-log.md is current (one entry per onboarded adopter)" → clarified that "onboarded adopter" means `cascade-status: onboarded` or `onboarded-operator-bump`; conflict-close slices have NO entry per invariant 2.
- §8 line 228 (Threshold A acceptance): "Each onboarded adopter has a corresponding entry..." → same clarification + explicit note that `blocked-on-adopter-conflict` adopters do NOT count toward Threshold A's "≥3 of 5" until a successor sub-slice onboards them.

These weren't separately flagged but they have the same propagation-class defect; closing now means R6 won't surface them.

## Inline-fix summary (~9 edits across 2 files)

1. `docs/plans/WP-SCP-024-estate-cascade.md`:
   - **§1 item 2** (b) — conditional carve-out + cross-reference to §5.2 + invariant 2.
   - **Invariant 2 onboarded-operator-bump bullet** — references format spec below.
   - **Invariant 2 blocked-on-adopter-conflict bullet** — references format spec below.
   - **Invariant 2 NEW format-spec block** — regex + 3 worked examples (✅ / ❌ × 2).
   - **§5.2 blocked-on-adopter-conflict description** — references invariant 2's regex spec.
   - **§5.6 Threshold A telemetry** — clarifies log-entry counting.
   - **§6 R-024-06** — three CI checks named explicitly.
   - **§8 Threshold A row 2** — clarifies which cascade-status counts.
   - **Closes-marker line 46** — "(safety)" lens qualifier added.
2. `docs/reviews/WP-SCP-024/dispatches/024A-plan-doc/DISPATCH-NOTE.md`:
   - **Risk surface item 4** — three-path cascade-status framing replaces "log-entry mandatory".
   - **Criterion (iii)** — invariant 2 summary updated to reflect three-path CI spec.

Plan-doc grew ~10 lines (mostly the regex format-spec block + worked examples).

## R6 candidacy

R5 surfaced 0 new CRIT, 5 unique new MAJ (all inline-fixed), 1 MIN (closed), 1 nit (closed). Companion sweep proactively closed 2 additional propagation gaps that R5 didn't flag but that were the same class.

The cascade-status / CI-enforcement spec has now been hardened across **5 rounds** of adversarial review. The regex format spec at fix-round-5 closes the last "implementation-dependent" surface (R5 safety MAJ-002). The propagation gaps in §1, §3 (closed at R4), §5.2, §6, §8, R-024-06, R-024-07, and DISPATCH-NOTE risk-surface + criterion (iii) are all closed.

If R6 returns 0 new CRIT + 0 new MAJ on a complete cycle, **R6 fixpoint reached** per `feedback_recursive_adversarial_review.md`.

## Pattern observation (continued)

**5 consecutive rounds caught propagation gaps in this clause.** That's enough rounds to claim the clause was structurally over-complex for the document layout — every site that referenced "invocation log entry" needed its own conditional carve-out, and the gaps surfaced at one site per round.

The fix-round-5 comprehensive grep sweep ("find every mention of invocation log / TF-024X / meaningful content / log-entry mandatory") is the right defensive technique for this kind of cross-cutting clause. Documented for future plan-doc fix rounds: when a propagation gap surfaces, do a comprehensive grep sweep BEFORE the next R round, not just the surfaced sites.
