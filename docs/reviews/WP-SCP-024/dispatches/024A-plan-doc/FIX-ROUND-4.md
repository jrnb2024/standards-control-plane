# 024A — fix-round-4 audit (R4 → fix → R5 candidate)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-024-estate-cascade-plan`
**Pre-fix-round-4 HEAD:** `d13157f`

## R4 finding tally

3× parallel Sonnet R4: all 3 CHANGES_REQUESTED (R3 closures verified; new findings introduced by fix-round-3 edits).

| Lens | Verdict | new CRIT | new MAJ | new MIN | new nit | R3-closures verified |
|---|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 2 | 0 | 0 | 1/1 |
| safety_bypass | CHANGES_REQUESTED | 0 | 2 | 0 | 0 | 1/1 |
| completeness | CHANGES_REQUESTED | 0 | 1 | 0 | 0 | 2/2 |
| **total raw new** | — | **0** | **5** | **0** | **0** | — |

After dedup (R-024-06 stale was flagged by ALL 3 lenses): **0 CRIT + 3 unique new MAJ**.

## Per-finding disposition

### MAJ (3 unique, all inline-fixed)

| ID | Lens(es) | Disposition | Action |
|---|---|---|---|
| **R4-NEW-MAJ-001** (correctness + safety + completeness, all 3 lenses flagged) | correctness, safety, completeness | **INLINE-FIX** | R-024-06 mitigation column still described the OLD weak behaviour: "skips log-entry assertion ... verifies the TF reference is present" — missing the new active "log file MUST NOT be modified" assertion that landed in invariant 2 + §6 024B at fix-round-3. R-024-06 is normative implementation guidance; an executor reading from the risk table alone would have produced the bypass-vulnerable check. **Fix:** rewrote R-024-06 mitigation with both positive (TF reference present) AND negative (log file NOT modified) assertions explicitly named. |
| **R4-NEW-MAJ-002** (correctness) | correctness | **INLINE-FIX** | §3 line 73 (programme-protocol section) said implementation slices ship "(b) the invocation-log entry under `branch-protection-log.md`" UNCONDITIONALLY. Post fix-round-3, the conflict-close path explicitly forbids modifying that file. **Fix:** §3 line 73 reworded to make item (b) conditional on `cascade-status` being `onboarded` or `onboarded-operator-bump`; conflict-close path explicitly noted as no-log-entry. |
| **R4-NEW-MAJ-002** (safety) | safety | **INLINE-FIX** | TF-024X-renovate / TF-024X-conflict CI checks verify only the **prefix string** is present in STATUS.md / DISPATCH-NOTE. A bare-prefix stub row (no status field, no description) passes CI — defeating the audit purpose. **This is the canonical defect class FIX-ROUND-3.md flagged**: positive evidence required without meaningful-content requirement. **Fix:** invariant 2 + §6 024B + R-024-07 all updated to require **meaningful content** in the row (status field + non-empty description); CI rejects bare-prefix stubs. |

## Inline-fix summary (~5 edits across 1 file)

`docs/plans/WP-SCP-024-estate-cascade.md`:
- **§3 line 73** — invocation-log entry made conditional on cascade-status (was unconditional).
- **Invariant 2 onboarded-operator-bump bullet** — meaningful-content requirement added.
- **Invariant 2 blocked-on-adopter-conflict bullet** — meaningful-content requirement added (TF-024X-conflict-<adopter> reference must carry status + description).
- **§6 024B row** — meaningful-content requirement enumerated for all TF-row checks.
- **R-024-06 mitigation** — rewritten with both positive (TF reference present) + negative (log file NOT modified) assertions.
- **R-024-07 mitigation** — meaningful-content requirement added.

Plan-doc grew ~3 lines.

## R5 candidacy

R4 surfaced 0 new CRIT, 3 unique new MAJ (all inline-fixed), 0 MIN, 0 nit. Ready for R5 to verify R4 closures + no new CRIT/MAJ.

If R5 returns 0 new CRIT + 0 new MAJ on a complete cycle, **R5 fixpoint reached** per `feedback_recursive_adversarial_review.md`.

## Pattern observation

This is now the **fourth** time a fix-round has surfaced gaps in the cascade-status / CI-enforcement / TF-row clauses (R2 NEW-MAJ-001 carve-out → R3 NEW-MAJ-001 missing third value + bypass surface → R4 NEW-MAJ-002 stub-row bypass + §3 propagation gap). The carve-out specification has stabilised but each round catches one more propagation gap or one more class of bypass.

The pattern aligns with the lesson surfaced in FIX-ROUND-3.md ("when adding a carve-out clause, enumerate the full set of states + assert both positive evidence AND absence of contradicting evidence") — fix-round-3's edit added the negative assertion for one path (log-NOT-modified) but didn't propagate it through R-024-06 or §3, and didn't add the meaningful-content requirement.

R5 should prioritise hunting for any remaining propagation gaps in the cascade-status / CI-enforcement spec across the entire plan-doc, especially in Section 7 risk table rows other than R-024-06/07 and in Section 4 threat model rows.
