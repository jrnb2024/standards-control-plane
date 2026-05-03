# 023A — fix-round-2 audit (R2 → fix → R3 candidate)

**Date:** 2026-05-03 (PM-1)
**Branch:** `feature/wp-scp-023-cross-repo-scorecards-plan`
**Pre-fix-round-2 HEAD:** `94d096e` (fix-round-1)

## R2 finding tally

3× parallel Sonnet R2: all 3 lenses CHANGES_REQUESTED.

| Lens | Verdict | new CRIT | new MAJ | new MIN | new nit |
|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 3 | 1 | 0 |
| safety_bypass | CHANGES_REQUESTED | 0 | 1 | 2 | 1 |
| completeness_governance | CHANGES_REQUESTED | 0 | 1 | 0 | 2 |
| **total raw** | — | **0** | **5** | **3** | **3** |

After deduplicating: 0 CRIT, **4 unique MAJ** (vendor/scp-public.key §8 stale; MVCP move-numbering still inaccurate; id-token: write misapplied; OIDC `job_workflow_ref` gap).

## Per-finding disposition

### MAJ (4 unique)

| ID | Lens(es) | Disposition | Action |
|---|---|---|---|
| **COR-R2-MAJ-001 / COMP-R2-MAJ-001** | correctness, completeness | **INLINE-FIX** | Stale `vendor/scp-public.key` in §8 Threshold A criterion. Updated §8 to `docs/security/mcp-signing-keys.pub` (covered via `docs/security/**`). |
| **COR-R2-MAJ-002** | correctness | **INLINE-FIX** | fix-round-1 wording said "move #2 = WP-SCP-021", but WP-SCP-021 §1 explicitly self-numbers as **move #3**. Rewrote §1 honouring per-plan-doc explicit self-numbering: move #1 = WP-SCP-020; move #3 = WP-SCP-021; move #4 = WP-SCP-022-proposal-queue; move #5 = WP-SCP-023; **move #2 unassigned** in current corpus (WP-SCP-020 §1 vs §3 internal inconsistency, out of scope to resolve here). |
| **COR-R2-MAJ-003** | correctness | **INLINE-FIX** | §5 Job 1 specified `id-token: write` for OIDC verification — wrong permission. Replaced with `attestations: read` + explanatory note. |
| **MAJ-SAFE-R2-001** | safety | **INLINE-FIX (architectural commit)** | OIDC JWKS-only verification proves GitHub issued the token but does NOT prove the SCP reusable workflow produced the artifact. Added "Non-negotiable verification constraint" block to §5 step 3 + bound to D-042: aggregator MUST verify `job_workflow_ref` OIDC claim against expected SCP reusable workflow path AND SHA pin. Untrusted-workflow-source attestations rejected with `verification_failure: untrusted_workflow_source`. |

### MIN (3)

| ID | Lens | Disposition |
|---|---|---|
| COR-R2-MIN-001 | correctness | NO ACTION (audit-trail wording in FIX-ROUND-1.md; per-finding table is authoritative) |
| MIN-SAFE-R2-001 | safety | NO ACTION (invariant 6 claim accurate as long as consumer-side verification path honored, which §5 step 3 mandates) |
| MIN-SAFE-R2-002 | safety | NO ACTION (subsumed by MAJ-SAFE-R2-001 fix — `job_workflow_ref` constraint gives the faithfulness commitment teeth) |

### nit (3)

| ID | Disposition |
|---|---|
| COMP-R2-nit-001 | INLINE-FIX (§10 Q1 reframed as "Resolved at plan-doc level: MAJOR-pinned per VERSIONING.md (D-036)") |
| COMP-R2-nit-002 | INLINE-FIX (DISPATCH-NOTE.md AC(ii) "move #4" → "move #5") |
| nit-SAFE-R2-001 | NO ACTION (TF-023A-001 framing is appropriate) |

## Inline-fix summary (6 edits across 3 files)

1. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §1: MVCP move-numbering refined per per-plan-doc explicit self-numbering (COR-R2-MAJ-002).
2. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §5 Job 1: `id-token: write` → `attestations: read` + explanatory note (COR-R2-MAJ-003).
3. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §5 step 3: "Non-negotiable verification constraint" block added (MAJ-SAFE-R2-001).
4. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §8: `vendor/scp-public.key` → `docs/security/mcp-signing-keys.pub` (COR-R2-MAJ-001 + COMP-R2-MAJ-001).
5. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §10 Q1: reframed as Resolved (COMP-R2-nit-001).
6. `docs/reviews/WP-SCP-023/dispatches/023A-plan-doc/DISPATCH-NOTE.md` AC(ii): "move #4" → "move #5" (COMP-R2-nit-002).

## Forward-filed TFs

R2 surfaced no new TF candidates. TF-023A-001 + TF-023A-002 remain filed forward from R1.

## Smoke-test post-fix

- `pytest tests/conflict_gate/`: 12/12 pass.
- `scripts/scp-pre-push-verify.sh`: ✓ all 3 SCP-R gates pass.

## R3 candidacy

R2 surfaced 0 new CRIT, 4 unique MAJ (all inline-fixed). The slice is ready for **R3 dispatch** to verify no NEW CRIT/MAJ findings emerge against the fix-round-2 surface. Per `feedback_recursive_adversarial_review.md` fixpoint criterion: R3 must surface 0 CRIT + 0 MAJ on a complete cycle.
