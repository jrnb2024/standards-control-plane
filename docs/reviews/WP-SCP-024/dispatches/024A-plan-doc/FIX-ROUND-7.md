# 024A — fix-round-7 audit (R7 → fix → R8 candidate)

**Date:** 2026-05-04
**Branch:** `feature/wp-scp-024-estate-cascade-plan`
**Pre-fix-round-7 HEAD:** `dfae0b8`

## R7 finding tally

3× parallel Sonnet R7: all 3 CHANGES_REQUESTED.

| Lens | Verdict | new CRIT | new MAJ | new MIN | new nit | R6-closures verified |
|---|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 1 | 2 | 0 | 6/6 |
| safety_bypass | CHANGES_REQUESTED | 0 | 1 | 1 | 0 | 4/4 |
| completeness | CHANGES_REQUESTED | 1 | 3 | 0 | 0 | 3/3 |
| **total raw new** | — | **1** | **5** | **3** | **0** | — |

After dedup:
- **R7-NEW-CRIT-001 (completeness) = R7-NEW-MAJ-001 (safety)**: regex closing-`**` bug — fix-round-6 dropped trailing `**` when restructuring; Example 1 silently failed its own regex. **CRIT** because the script implementing the regex literally would reject ALL legitimate STATUS.md rows for the operator-bump path.
- **R7-NEW-MAJ-001 (correctness) = R7-NEW-MAJ-003 (completeness)**: §5.2 + R-024-06 + R-024-07 paraphrases missing `\S` anchor + ≥20-char language. Same propagation-class as R6 noted; sites not swept at fix-round-6.
- **R7-NEW-MAJ-001 (completeness)**: missing closes-marker for R6-NEW-MAJ-001 correctness §6 024C/D/E/F fix.
- **R7-NEW-MAJ-002 (completeness) = R7-NEW-MIN-001 (correctness)**: "three-path" labels stale at DISPATCH-NOTE criterion (iii) + risk item 4. R6 added fail-closed default → 4 behaviours.
- **R7-RESIDUAL-MIN-001 (safety)**: `\S.{19,}` allows 1 non-whitespace + 19 trailing whitespace. Reviewer noted "no fix strictly required for fixpoint."

After dedup: **1 CRIT + 3 unique MAJ + 1 MIN (optional)**.

## Per-finding disposition

### CRIT (1, inline-fixed)

| ID | Lens(es) | Disposition | Action |
|---|---|---|---|
| **R7-NEW-CRIT-001 (completeness) + R7-NEW-MAJ-001 (safety)** | completeness, safety | **INLINE-FIX** | Regex changed from `TF-024X-(renovate\|conflict)-[a-z0-9]+(?:-[a-z0-9]+)+ \(...` to `TF-024X-(renovate\|conflict)-[a-z0-9]+(?:-[a-z0-9]+)+(?:\*\*)? \(...`. The `(?:\*\*)?` optional group accepts the trailing `**` closing-bold marker that STATUS.md bullet format produces between the slug and the status parenthetical. Example 1 (`- **TF-024X-renovate-jrnb2024-pim** (open): ...`) now passes. Example 2 (DISPATCH-NOTE prose with no `**`) still passes via the optional group. |

### MAJ (3 unique, all inline-fixed)

| ID | Lens(es) | Disposition | Action |
|---|---|---|---|
| **R7-NEW-MAJ-001 (correctness) + R7-NEW-MAJ-003 (completeness)** | correctness, completeness | **INLINE-FIX** | §5.2 blocked-on-adopter-conflict description, R-024-06 mitigation, and R-024-07 mitigation all carried pre-R6 paraphrases ("status field + ≥20 char description" or "status field + non-empty description") that omitted the `\S` non-whitespace anchor + the literal "≥20 chars total" framing. **Fix:** all three sites rewritten to use the canonical phrasing — "status field ∈ {open, pending, in-progress, closed} + description starting with a non-whitespace character (`\S` anchor) + ≥20 chars total; bare-prefix stubs and all-whitespace descriptions fail CI". |
| **R7-NEW-MAJ-001 (completeness)** | completeness | **INLINE-FIX** | R6-NEW-MAJ-001 (correctness) §6 024C/D/E/F conditional-on-cascade-status fix landed at fix-round-6 but had no closes-marker. **Fix:** §6 024C row now carries closes-marker `(closes 024A R6 R6-NEW-MAJ-001 (correctness) — §6 024C/D/E/F rows now conditional on cascade-status — closes-marker per 024A R7 R7-NEW-MAJ-001 completeness)`. |
| **R7-NEW-MAJ-002 (completeness) + R7-NEW-MIN-001 (correctness)** | completeness, correctness | **INLINE-FIX** | DISPATCH-NOTE criterion (iii) + risk surface item 4 still said "three-path cascade-status" / "three-path CI enforcement" — pre-R6 framing. R6 added the fail-closed default as a fourth CI behaviour. **Fix:** both DISPATCH-NOTE sites rewritten to "four CI behaviours per invariant 2: fail-closed default for absent/unrecognised cascade-status + three named paths". |

### MIN (1, deferred)

| ID | Disposition | Action |
|---|---|---|
| **R7-RESIDUAL-MIN-001** (safety) | **NO ACTION (deferred per reviewer note)** | `\S.{19,}` allows `x` + 19 trailing spaces (1 non-whitespace + 19 whitespace = 20 total). Reviewer noted "no fix strictly required for fixpoint given prose alignment". A future tightening to `\S\S.{18,}` or similar would close this narrow edge case but loses some legitimate descriptions ("I'm onboarding..." starts with `I` then space). Acceptable tradeoff at v0.1; revisit if narrow-content TF rows become a real audit gap. |

## Inline-fix summary (~6 edits across 2 files)

`docs/plans/WP-SCP-024-estate-cascade.md`:
- **Invariant 2 regex** — added `(?:\*\*)?` optional closing-bold marker (CRIT fix).
- **§5.2 blocked-on-adopter-conflict description** — `\S` + ≥20-char canonical phrasing.
- **§6 024C row** — closes-marker for R6-NEW-MAJ-001 correctness fix.
- **§7 R-024-06** — `\S` + ≥20-char canonical phrasing.
- **§7 R-024-07** — `\S` + ≥20-char canonical phrasing.

`docs/reviews/WP-SCP-024/dispatches/024A-plan-doc/DISPATCH-NOTE.md`:
- **Criterion (iii)** — "three-path" → "four CI behaviours" (fail-closed default).
- **Risk surface item 4** — "three-path CI enforcement" → "four CI behaviours" (fail-closed default).

Plan-doc + DISPATCH-NOTE grew negligibly (text changes, no new lines).

## R8 candidacy

R7 surfaced 1 CRIT (regex bug) + 3 unique MAJ (paraphrase propagation, missing closes-marker, "three-path" stale) + 1 MIN (deferred). All CRIT + MAJ inline-fixed.

This is the **7th consecutive round** with new findings. The pattern aligns with FIX-ROUND-6's observation: the cascade-status / CI-enforcement clause is structurally cross-cutting + each round catches one more propagation gap. fix-round-7's most consequential finding (the CRIT regex bug) is a *meta-failure* of fix-round-6's restructuring — I changed the regex anchor without testing the worked examples against the new regex. **Lesson:** when restructuring a regex spec, always test the worked examples against the new regex before declaring the fix done.

If R8 returns 0 new CRIT + 0 new MAJ on a complete cycle, **R8 fixpoint reached**.
