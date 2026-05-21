# 023A — fix-round-1 audit (R1 → fix → R2 candidate)

**Date:** 2026-05-03 (PM-1)
**Branch:** `feature/wp-scp-023-cross-repo-scorecards-plan`
**Pre-fix-round-1 HEAD:** `51bc926` (initial plan-doc + DISPATCH-NOTE)

## R1 finding tally

3× parallel Sonnet R1: 2× CHANGES_REQUESTED + 1× APPROVED_WITH_FINDINGS.

| Lens | Verdict | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 1 | 3 | 2 | 1 |
| safety_bypass | CHANGES_REQUESTED | 0 | 3 | 4 | 3 |
| completeness_governance | APPROVED_WITH_FINDINGS | 0 | 2 | 5 | 4 |
| **total raw** | — | **1** | **8** | **11** | **8** |

After deduplicating cross-lens findings (the same underlying issue surfaced under multiple lenses):
- **Unique CRIT:** 1 — MVCP move-numbering inconsistency.
- **Unique MAJ:** 7 — scp_common.rego line citation; signing-key path; aggregator workflow permissions; signing mechanism contradiction; key rotation gap; src/** CODEOWNERS gap; cron cadence inconsistency; D-NNN reservation guard absence (the last two share a "consistency-with-canonical-pattern" theme).

## Per-finding disposition

### CRIT (1)

| ID | Lens | Disposition | Action |
|---|---|---|---|
| **COR-CRIT-001** | correctness | **INLINE-FIX** | Plan-doc said "move #4 of 5-move MVCP". Verified against WP-SCP-020 §3 + WP-SCP-022 §12 — canonical numbering is move #1=WP-SCP-020, #2=WP-SCP-021, #3/4=WP-SCP-022 (programme + proposal-queue), **#5=WP-SCP-023 scorecards**. WP-SCP-024 (estate cascade) is OUTSIDE the 5-move MVCP. Rewrote §1 framing accordingly. |

### MAJ (7 unique)

| ID | Lens | Disposition | Action |
|---|---|---|---|
| **COR-MAJ-001** | correctness | **INLINE-FIX** | Invariant 3 cited `scp_common.rego` lines 36-43; actual comment block is lines 31-44. Corrected citation. |
| **COR-MAJ-002** | correctness | **INLINE-FIX** | §5 referenced `vendor/scp-public.key` (path doesn't exist). Corrected to `docs/security/mcp-signing-keys.pub` (the WP-SCP-021-established path; verified exists; CODEOWNERS-covered via `docs/security/**`). |
| **COR-MAJ-003** | correctness | **INLINE-FIX** | §5 didn't specify aggregator workflow permissions. Added two-job permission scoping per WP-SCP-022 D-037 pattern: read-only `aggregate` job (`contents: read, actions: read, id-token: write`) + write-scoped `commit` job (`contents: write, pull-requests: write`) gated on aggregate success. |
| **MAJ-SAFE-001** | safety | **INLINE-FIX (architectural commit)** | Real architectural gap: SCP cannot distribute private signing keys to adopter runners without enabling estate-wide forgery. Resolved by committing in §5 + D-042 to **GitHub Actions Artifact Attestation** (OIDC-based) for adopter emits — GitHub signs each artifact with the run's OIDC token at upload time; the aggregator verifies against GitHub's OIDC JWKS. No SCP private key ever in adopter runners. SCP-side aggregator-emitted index uses the existing `docs/security/mcp-signing-keys.pub` Ed25519 registry. |
| **MAJ-SAFE-002** | safety | **INLINE-FIX (key registry model)** | Key rotation cliff: a single-key aggregator marks all pre-rotation emits as `verification_failure` after a rotation. Resolved by committing in §5 + D-042 to a **key registry model**: `(key_id, public_key, valid_from, valid_until)` entries; each emit carries its `key_id`; aggregator verifies against the key current at `emitted_at`. Bounded extension of WP-SCP-021's existing infrastructure. |
| **MAJ-SAFE-003** | safety | **INLINE-FIX** | `src/**` was absent from CODEOWNERS. Added `src/** @jrnb2024` with explanatory comment block (pre-emptive coverage so any future MCP method mutation primitive routes through review, protecting invariant 5). Pattern mirrors `vendor/**`. |
| **COMP-MAJ-001** | completeness | **INLINE-FIX** | §5 cron 'nightly' contradicted §10 Q3 ('daily/weekly') and §8 Threshold A ('weekly'). Resolved by picking **weekly** consistently across all three sections. §10 Q3 reframed as "Resolved at plan-doc level: weekly default; revisitable in D-042". |
| **COMP-MAJ-002** | completeness | **INLINE-FIX** | D-NNN reservations lacked the WP-SCP-022 D-021-style "Codex executors must NOT assign" guard in `docs/DECISIONS.md`. Added a header reservation note for D-041/D-042/D-043 mirroring D-021's pattern. Updated §9 of plan-doc with explicit cross-reference. |

### MIN (~11 raw, ~7 unique after dedup)

| ID(s) | Lens | Disposition | Action |
|---|---|---|---|
| **COR-MIN-001** | correctness | **INLINE-FIX** (closed by COMP-MAJ-001 fix) | Same root issue: §5 vs §10 Q3 cadence inconsistency. Resolved. |
| **MIN-SAFE-005** | safety | **INLINE-FIX** | CODEOWNERS coverage on `docs/scorecards/**` and `output/scorecards/**` deferred to 023E. Added pre-emptive coverage now (paths don't yet exist; rule is no-op until 023B/C creates them). Pattern mirrors `vendor/**` + `.scp/**`. |
| **COMP-MIN-001 + COMP-MIN-002** | completeness | **INLINE-FIX** | §10 Q1 + Q2 partially-closed by §5 content. Reframed both as "Resolved at plan-doc level" with explicit references to the resolving sections + D-NNN scope. |
| **COMP-MIN-004** | completeness | **INLINE-FIX** | Invariant 1 needed positive aggregator-faithfulness commitment. Added "**Positively: the aggregator MUST faithfully report verified emit content** — it does not transform, smooth, or 'best-interpret' verdicts" sentence + explicit failure-mode framing. |
| **COR-MIN-002** | correctness | **NO ACTION** | Output path `output/scorecards/scorecard-emit.json` not yet established convention. Path establishes at 023B with D-041; no plan-doc change required (plan-doc names the path; the convention establishes when 023B lands). |
| **MIN-SAFE-004** | safety | **NO ACTION** (closed by MAJ-SAFE-002 fix) | Consumer-side verification path is now specified by the key registry model in §5 step 3. |
| **MIN-SAFE-006** | safety | **TF-FORWARD** | k-anonymity mismatch with R-023-01 framing. Filed as **TF-023A-001**: clarify R-023-01 mitigation when slice 024 begins (currently the mitigation is forward-looking; the framing tightens once the cascade slice exists). |
| **MIN-SAFE-007** | safety | **INLINE-FIX** (closed by D-042 update) | D-042 now pre-commits to OIDC + key-registry model in the §9 + reserved-decisions block. |
| **COMP-MIN-003** | completeness | **TF-FORWARD** | Cross-repo notification to ACC / CT / mapp-estate-regression not named. Filed as **TF-023A-002**: send notification at 023B kickoff (per the established cross-repo coordination pattern in `reference_ct_notifications.md`). The plan-doc-itself is SCP-internal; cross-repo coordination starts at 023B emitter rollout. |
| **COMP-MIN-005** | completeness | **NO ACTION** | "Deployed MCP server" reference assumes WP-SCP-021's deployment posture. WP-SCP-021 is closed + landed; the MCP server already runs; this reference is accurate. |

### nit (~8 raw, mostly minor)

All nit-level findings batched as **NO ACTION** for fixpoint reachability. Specifically: COR-nit-001 (jsonc comment in code block), nit-SAFE-008/009/010 (CODEOWNERS specificity / write-surface clarification / WP-SCP-024 naming), COMP-nit-001/002/003/004 (Programme Ref placeholder / FLA-stability framing / external-dependencies section / memory-update naming) are all stylistic or process-pending. No security or correctness impact.

## Inline-fix summary (12 edits across 3 files)

1. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §1: MVCP move numbering #4 → #5 + WP-SCP-024 reframed (COR-CRIT-001).
2. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` invariant 3: scp_common.rego line citation 36-43 → 31-44 (COR-MAJ-001).
3. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §5 step 3: vendor/scp-public.key → docs/security/mcp-signing-keys.pub + key registry model + OIDC attestation commitment (COR-MAJ-002 + MAJ-SAFE-001 + MAJ-SAFE-002 + MIN-SAFE-007).
4. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §5: two-job aggregator permission scoping (COR-MAJ-003).
5. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §5 + §10 Q3 + §8: cron cadence reconciled to weekly (COMP-MAJ-001 + COR-MIN-001).
6. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` header + §9: D-NNN reservation guard wording aligned with D-021 pattern (COMP-MAJ-002).
7. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §10 Q1 + Q2: reframed as "Resolved at plan-doc level" with cross-references (COMP-MIN-001 + COMP-MIN-002).
8. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §10 Q4: weekly retention framing (consistent with §5 cadence change).
9. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` invariant 1: aggregator-faithfulness positive commitment (COMP-MIN-004).
10. `docs/DECISIONS.md` header: D-041/042/043 reservation note mirroring D-021 pattern (COMP-MAJ-002).
11. `CODEOWNERS`: added `src/** @jrnb2024` (MAJ-SAFE-003) + `docs/scorecards/** @jrnb2024` + `output/scorecards/** @jrnb2024` (MIN-SAFE-005).
12. `docs/DECISIONS.md` header: Last Updated 2026-05-02 → 2026-05-03.

## Forward-filed TFs

- **TF-023A-001** (low priority): clarify R-023-01 k-anonymity mitigation framing when WP-SCP-024 cascade slice begins.
- **TF-023A-002** (medium priority): cross-repo notification to ACC / CT / mapp-estate-regression at 023B kickoff per `reference_ct_notifications.md`.

## Smoke-test post-fix

- `scripts/scp-pre-push-verify.sh`: ✓ all 3 SCP-R gates pass; coverage 98.58% (above 90% threshold).
- Plan-doc renders cleanly (no broken markdown).
- CODEOWNERS file integrity preserved (ORDERING INVARIANT: new entries inserted before /CODEOWNERS self-protection).

## R2 candidacy

R1 surfaced 1 CRIT (closed inline), 7 unique MAJ (all closed inline including a real architectural gap on signing-key distribution), 7 unique MIN (5 inline-fixed + 2 TF-forwarded), 8 nit (all NO ACTION). The slice is ready for **R2 dispatch** to verify no NEW CRIT/MAJ findings emerge against the fix-round-1 surface. Per `feedback_recursive_adversarial_review.md` fixpoint criterion: R2 must surface 0 CRIT + 0 MAJ on a complete cycle.
