# 024A — fix-round-2 audit (R2 → fix → R3 candidate)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-024-estate-cascade-plan`
**Pre-fix-round-2 HEAD:** `79b2c1b`

## R2 finding tally

3× parallel Sonnet R2: all 3 CHANGES_REQUESTED.

| Lens | Verdict | new CRIT | new MAJ | new MIN | new nit | R1-closures verified |
|---|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 2 | 0 | 0 | 3/3 |
| safety_bypass | CHANGES_REQUESTED | 0 | 1 | 2 | 0 | 6/6 (1 partial) |
| completeness | CHANGES_REQUESTED | 0 | 3 | 0 | 1 | 6/6 |
| **total raw new** | — | **0** | **6** | **2** | **1** | — |

After dedup:
- **R2-NEW-MAJ-001** (correctness) = **CMP-MAJ-004** (completeness): DISPATCH-NOTE criterion (xi) "(10 questions)" stale.
- **R2-NEW-MAJ-002** (correctness) = **CMP-MAJ-003** (completeness): DISPATCH-NOTE line 36 stale references (`§10 Q7` + `§5.5`).
- **CMP-MAJ-005** (completeness) NEW: DISPATCH-NOTE Forward-looking section "WP-SCP-025 is open question §10 Q7" — Q7 removed by trim, now Q2.
- **NEW-MAJ-001** (safety) NEW: invariant 10 `blocked-on-adopter-conflict` close-state vs invariant 2 CI invocation-log enforcement — a conflict-close slice has no log entry; the CI check needs explicit carve-out spec.

After dedup: **0 CRIT + 4 unique new MAJ + 2 MIN + 1 nit**.

3 of 4 unique MAJ are DISPATCH-NOTE propagation gaps from fix-round-1's §10 trim + §5.5 renumbering — all single-line text edits. The 4th MAJ (NEW-MAJ-001) is a real plan-doc body gap that fix-round-1's MIN-SAFE-006 closure surfaced indirectly.

## Per-finding disposition

### MAJ (4 unique, all inline-fixed)

| ID | Lens(es) | Disposition | Action |
|---|---|---|---|
| **R2-NEW-MAJ-001 / CMP-MAJ-004** | correctness, completeness | **INLINE-FIX** | DISPATCH-NOTE criterion (xi) reframed: drops "(10 questions)"; explicitly explains the trim from 10 → 3 + acceptance check is now "§10 contains only genuinely-open questions; resolved questions are in their proper sections." References R2-NEW-MAJ-001 / CMP-MAJ-004 closure. |
| **R2-NEW-MAJ-002 / CMP-MAJ-003** | correctness, completeness | **INLINE-FIX** | DISPATCH-NOTE scope-table line 36 reworded: drops `§10 Q7 / §5.5` references; cleanly references "D-046 to confirm" + "informational per §8" + "See §5.6 Threshold A telemetry". |
| **CMP-MAJ-005** | completeness | **INLINE-FIX** | DISPATCH-NOTE Forward-looking line 103: `§10 Q7` → `§10 Q2` (the post-trim numbering for WP-SCP-025 successor). |
| **NEW-MAJ-001** | safety | **INLINE-FIX** | Invariant 2 CI enforcement clause now explicitly carves out `cascade-status: blocked-on-adopter-conflict` slices: those skip the log-entry assertion (no invocation occurred) but MUST reference the filed `TF-024X-conflict-<adopter>` TF. The CI script parses the DISPATCH-NOTE `cascade-status:` field and applies the appropriate check. §5.2 item (2) updated to require `cascade-status:` field in DISPATCH-NOTE header. §6 024B acceptance row updated to enumerate both close-states. R-024-06 mitigation rewritten to match (closes NEW-MIN-001 simultaneously). |

### MIN (2 unique)

| ID | Disposition | Action |
|---|---|---|
| **NEW-MIN-001** (safety) | **CLOSED via NEW-MAJ-001 fix** | R-024-06 stale "cascade defers" language replaced with "CLOSES with status `blocked-on-adopter-conflict`" as part of the same edit that landed the carve-out. |
| **NEW-MIN-002** (safety) | **INLINE-FIX** | R-024-07 expanded: `TF-024X-renovate-<adopter>` MUST be filed as a STATUS.md "Tracked-forward items" row using exactly the standardised prefix; `check-invocation-log-entry.sh` verifies STATUS.md contains the matching row when DISPATCH-NOTE declares operator-bump fallback. §5.2 item (2) names the row as a deliverable. §6 024B acceptance row enumerates this third check-path. |

### nit (1)

| ID | Disposition | Action |
|---|---|---|
| **CMP-nit-003** | **INLINE-FIX** | DISPATCH-NOTE criterion (vi) updated to enumerate all 6 architecture subsections including the new §5.5 cross-repo coordination. Added subsection numbers for clarity. |

## Inline-fix summary (~7 edits)

1. `docs/reviews/WP-SCP-024/dispatches/024A-plan-doc/DISPATCH-NOTE.md`:
   - Scope-table line 36 — fix stale §10 Q7 / §5.5 references.
   - Criterion (vi) — enumerate §5.1–§5.6 explicitly.
   - Criterion (xi) — drop "(10 questions)" + explain the trim.
   - Forward-looking line 103 — fix §10 Q7 → §10 Q2.
2. `docs/plans/WP-SCP-024-estate-cascade.md`:
   - Invariant 2 — add `cascade-status:` carve-out for `blocked-on-adopter-conflict` slices.
   - §5.2 item (2) — require `cascade-status:` field in DISPATCH-NOTE; require `TF-024X-renovate-<adopter>` STATUS.md row when operator-bump used.
   - §6 024B row — enumerate three check-paths the CI script enforces.
   - §7 R-024-06 — rewrite mitigation to match invariant 10 / T-024-10 (CLOSES not defers).
   - §7 R-024-07 — name STATUS.md row standard + CI verification.

Plan-doc grew 247 → ~250 lines.

## Forward-filed TFs

R2 surfaced no new estate-level TFs. The naming conventions `TF-024X-conflict-<adopter>` and `TF-024X-renovate-<adopter>` are now standardised in the plan-doc body, not floating.

## R3 candidacy

R2 surfaced 0 new CRIT, 4 unique new MAJ (all inline-fixed), 2 MIN (1 inline-fixed + 1 closed via MAJ-fix), 1 nit (inline-fixed). Ready for R3 to verify R1+R2 closures + no new CRIT/MAJ.
