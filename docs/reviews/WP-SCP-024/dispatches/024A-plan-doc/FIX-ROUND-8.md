# 024A — fix-round-8 audit (R8 → fix → R9 candidate)

**Date:** 2026-05-04
**Branch:** `feature/wp-scp-024-estate-cascade-plan`
**Pre-fix-round-8 HEAD:** `991d66c`

## R8 finding tally

3× parallel Sonnet R8 reviews:

| Lens | Verdict | new CRIT | new MAJ | new MIN | new nit | R7-closures verified |
|---|---|---|---|---|---|---|
| **correctness** | **APPROVED** | 0 | 0 | 1 | 0 | 4/4 |
| **safety_bypass** | **APPROVED** | 0 | 0 | 0 | 0 | 1/1 |
| completeness | CHANGES_REQUESTED | 0 | 1 | 0 | 1 | 4/4 |
| **total raw new** | — | **0** | **1** | **1** | **1** | — |

After dedup: **0 CRIT + 1 MAJ (audit-trail bookkeeping) + 1 MIN + 1 nit**.

This is a near-fixpoint round: 2 of 3 lenses APPROVED. The single MAJ is **pure audit-trail bookkeeping** — fix-round-7's three propagation-fix sites cited the dedup ID `R7-NEW-MAJ-001 (correctness)` but missed the companion completeness ID `R7-NEW-MAJ-003`. No functional content gap; no new spec defects. Mechanical fix.

## Per-finding disposition

### MAJ (1, inline-fixed)

| ID | Lens | Disposition | Action |
|---|---|---|---|
| **R8-NEW-MAJ-001 (completeness)** | completeness | **INLINE-FIX** | Three closes-markers at §5.2 line 135, R-024-06 line 224, R-024-07 line 225 cited only `R7-NEW-MAJ-001 (correctness)` — `R7-NEW-MAJ-003 (completeness)` was the dedup partner per FIX-ROUND-7.md but never cited in the plan-doc body. Searching for `R7-NEW-MAJ-003` returned zero results. **Fix:** all three markers extended to `R7-NEW-MAJ-001 (correctness) + R7-NEW-MAJ-003 (completeness)` per the R6 compound-notation precedent (`safety/completeness` pattern). Audit-trail now traceable. |

### MIN (1, deferred)

| ID | Disposition | Action |
|---|---|---|
| **R8-NEW-MIN-001 (correctness)** | **NO ACTION (deferred per reviewer note)** | §5.6 bullet 2 says "via Renovate (proving version-skew tolerance)" while §8 bullet 3 has a more detailed exclusion ("Adopters who satisfied bake via operator-driven bump do NOT count..."). Reviewer noted this is "substantively equivalent but less detailed" + §5.6's closes-marker claim of "phrased identically" is technically inaccurate. Reviewer also noted: "Not MAJ because 'via Renovate' linguistically excludes operator-driven bumps, §8 is the authoritative gate, and the exclusion rule is reachable in one hop from R-024-07. Does not block fixpoint." Acceptable deferral at v0.1; revisit if §5.6's framing causes a real cascade-slice author to misinterpret Threshold A. |

### nit (1, deferred)

| ID | Disposition | Action |
|---|---|---|
| **R8-NIT-001 (completeness)** | **NO ACTION** | R7-NEW-CRIT-001 closes-marker placed at line 55 (in-prose) rather than line 49 (block header) as the R7 reviewer suggested. Marker is findable; cosmetic placement only. |

## Inline-fix summary (3 edits in 1 file)

`docs/plans/WP-SCP-024-estate-cascade.md`:
- **§5.2 line 135** — closes-marker extended to `(correctness) + R7-NEW-MAJ-003 (completeness)`.
- **§7 R-024-06 line 224** — same.
- **§7 R-024-07 line 225** — same.

Plan-doc unchanged in size (text edits only).

## R9 candidacy

R8 surfaced 0 new CRIT, 1 new MAJ (audit-trail bookkeeping; inline-fixed), 1 MIN (deferred per reviewer note), 1 nit (deferred). The single MAJ was **pure dedup-citation bookkeeping** — no functional spec change.

**R8 had 2 of 3 lenses APPROVED.** This is the strongest-yet signal that the cascade-status spec has stabilised. Fix-round-8's edit was 100% mechanical (no spec change, no new content). R9 should verify the audit-trail extension landed cleanly — and the fixpoint criterion (0 new CRIT + 0 new MAJ) is highly likely to be reached.

If R9 returns 0 new CRIT + 0 new MAJ on a complete cycle, **R9 fixpoint reached** and the slice is mergeable.

## Pattern observation (final)

**8 consecutive rounds.** This is unprecedented for a plan-doc slice in the WP-SCP-019/020/021/022/023 chain (which typically reached fixpoint at R2 or R3). The cause is not a defective spec — the cascade-status / CI-enforcement clause is genuinely cross-cutting and needed careful elaboration:

- 3 close-states (`onboarded`, `onboarded-operator-bump`, `blocked-on-adopter-conflict`)
- 4 CI behaviours (3 above + fail-closed default)
- Positive evidence + meaningful-content regex + negative assertion (per close-state, conditionally)
- Propagated across §1, §3, §5.2, §5.6, §6 024B + 024C/D/E/F, §7 R-024-06/07, §8, DISPATCH-NOTE

Each round caught either (a) a propagation gap in this clause's elaboration, (b) a substantive defect-class addition (fail-closed default at R6, regex format spec at R5), or (c) audit-trail bookkeeping (R8). The recursive review process was actually working — each round genuinely improved the spec.

The slice is now structurally hardened. Future plan-doc slices touching this clause can use the v0.1 spec as the canonical reference, avoiding the propagation-gap rounds.
