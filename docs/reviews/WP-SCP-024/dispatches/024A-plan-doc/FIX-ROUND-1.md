# 024A — fix-round-1 audit (R1 → fix → R2 candidate)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-024-estate-cascade-plan`
**Pre-fix-round-1 HEAD:** `653c958`

## R1 finding tally

3× parallel Sonnet R1: 3 CHANGES_REQUESTED.

| Lens | Verdict | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 1 | 1 | 1 |
| safety_bypass | CHANGES_REQUESTED | 0 | 4 | 2 | 0 |
| completeness | CHANGES_REQUESTED | 0 | 2 | 2 | 2 |
| **total raw** | — | **0** | **7** | **5** | **3** |

After dedup (COR-MAJ-001 + MAJ-SAFE-002 are the same issue — log path mismatch): **0 CRIT, 6 unique MAJ**.

## Per-finding disposition

### MAJ (6 unique, all inline-fixed)

| ID | Lens(es) | Disposition | Action |
|---|---|---|---|
| **COR-MAJ-001 / MAJ-SAFE-002** | correctness, safety | **INLINE-FIX** | Log path replaced 6× in plan-doc: `docs/reviews/WP-SCP-024/branch-protection-log.md` → `docs/reviews/WP-SCP-020/branch-protection-log.md` (the D-035-canonical estate-cascade audit trail; the existing file at that path already reserves itself for WP-SCP-024 cascade entries via its "Estate cascade rollout = WP-SCP-024" comment). No script change needed — `enable-required-check.sh` already hardcodes the canonical path; the plan-doc was the drift. |
| **MAJ-SAFE-001** | safety | **INLINE-FIX** | Invariant 2 expanded with **CI enforcement clause**: every cascade-slice PR MUST modify the branch-protection log AND the entry's target repo MUST match the DISPATCH-NOTE target. New script `scripts/check-invocation-log-entry.sh` lands in 024B + is a **hard predecessor** for 024C. §6 024B acceptance criteria updated. |
| **MAJ-SAFE-003** | safety | **INLINE-FIX** | Invariant 7 SLO downgraded to "**aspirational at 024A merge**" until 024B closes with a **real-repo round-trip on a throw-away test repo** (not a dry-run mock). §6 024B acceptance criterion strengthened. §10 Q9 reframed with explicit closure path: "Q3 closes only when 024B's acceptance criterion in §6 is met." |
| **MAJ-SAFE-004** | safety | **INLINE-FIX** | R-024-07 tightened: operator-driven SHA pin bumps are temporary unblocks; cascade slice MUST file `TF-024X-renovate-<adopter>` requiring Renovate enabled before adopter counts toward Threshold A. §8 Threshold A criterion 3 updated: only **Renovate-issued** propagation cycles count. §1 item 5 updated to match. |
| **CMP-MAJ-001** | completeness | **INLINE-FIX** | §10 trimmed from 10 entries (7 of which were resolved-at-plan-doc-level non-questions) to **3 genuinely open**: Q1 Renovate coverage, Q2 WP-SCP-025 successor, Q3 `--restore` test surface (with explicit closure path per MAJ-SAFE-003 fix). Header updated explaining the trim. |
| **CMP-MAJ-002** | completeness | **INLINE-FIX** | NEW §5.5 "Cross-repo coordination (notifications)" — table of 4 notification points: 024C kickoff (CT estate-cascade-start, incorporates TF-023A-002), 024C kickoff parallel (ACC), 024E kickoff (mapp-estate-regression for mapp-doc-agent + recommender), 024G closure (CT cascade-Threshold-A). Existing §5.5 Threshold A renumbered to §5.6. Each cascade slice DISPATCH-NOTE now requires a "Cross-repo coordination" subsection. |

### MIN (5 unique)

| ID | Disposition | Action |
|---|---|---|
| **COR-MIN-001** | **INLINE-FIX** | DISPATCH-NOTE criterion (iii) updated to enumerate all 10 invariants (was 9 — invariant 3 "Cascade does NOT touch existing adopter content" was omitted). |
| **MIN-SAFE-005** | **INLINE-FIX** | §5.2 gains item (5): "FLA pilot safety findings reviewed: [...]" checkpoint — surfaces FLA learnings without creating an FLA precondition (invariant 4 still holds). |
| **MIN-SAFE-006** | **INLINE-FIX** | T-024-10 + invariant 10 reconciled: cascade slice CLOSES with status `blocked-on-adopter-conflict` (not deferred indefinitely); forward TF owned by slice author; new sub-slice opens on conflict resolution. |
| **CMP-MIN-001** | **CLOSED via CMP-MAJ-001 fix** | Q10 (self-declared non-question) removed when §10 was trimmed. |
| **CMP-MIN-002** | **INLINE-FIX** | §8 Threshold A "(Optional, D-046 to confirm)" row reframed: Threshold A binary pass/fail is the 4 mandatory criteria; the MCP-method decision is informational and recorded in §9 D-046, not §8. |

### nit (3 unique)

| ID | Disposition | Action |
|---|---|---|
| **COR-nit-001** | **INLINE-FIX** | Invariant 7 `--restore` notation normalised to `<pre-state.json>` (matches §5.4). |
| **CMP-nit-001** | **INLINE-FIX** | §5.2 item (3) ordering clarified: invocation runs AFTER adopter PR merges + green-CI observed AND BEFORE post-bake window begins. Step (3) and (4) explicitly not concurrent. |
| **CMP-nit-002** | **INLINE-FIX** | §6 rows 024D / 024E / 024F gain inline note: "No new D-NNN filed — D-045 at 024C ratifies the per-adopter onboarding contract pattern that this slice inherits unchanged." |

## Inline-fix summary (~10 edits across 2 files)

1. `docs/plans/WP-SCP-024-estate-cascade.md`:
   - 6× path replacement (WP-SCP-024 → WP-SCP-020 branch-protection-log)
   - Invariant 2 — CI enforcement clause added
   - Invariant 7 — SLO downgraded to aspirational + §6 024B round-trip predecessor
   - Invariant 10 + T-024-10 — conflict-handling resolution path
   - §1 item 5 — Renovate-only Threshold A claim
   - §5.2 — step (3) ordering clarified + new step (5) FLA safety checkpoint
   - §5.5 NEW — Cross-repo coordination table; §5.6 = old §5.5 renumbered
   - §6 — 024B acceptance strengthened (real-repo round-trip + check-invocation-log-entry.sh as 024C predecessors); 024D/E/F D-NNN footnotes
   - §7 — R-024-07 tightened (operator-bump TF requirement)
   - §8 — Threshold A row 3 (Renovate-only) + optional MCP criterion reframed
   - §10 — trimmed from 10 to 3 questions; explanatory header
2. `docs/reviews/WP-SCP-024/dispatches/024A-plan-doc/DISPATCH-NOTE.md`:
   - Criterion (iii) — all 10 invariants enumerated

## Forward-filed TFs

R1 surfaced no new estate-level TFs beyond what's already filed at WP-SCP-023 023E (TF-023E-001, TF-023E-002). The R1 findings were all plan-doc spec-level gaps fixable inline — no architectural pivot, no descope.

The MAJ-SAFE-001 fix names a new script (`scripts/check-invocation-log-entry.sh`) that lands in 024B; this is a deliverable-add, not a TF.

The MAJ-SAFE-004 fix names a TF naming convention (`TF-024X-renovate-<adopter>`); these TFs only get filed if/when an adopter actually has Renovate disabled at cascade time.

## R2 candidacy

R1 surfaced 0 CRIT, 6 unique MAJ (all inline-fixed), 5 MIN (4 inline-fixed + 1 closed by MAJ-fix), 3 nit (all inline-fixed). Ready for R2 to verify no new CRIT/MAJ.
