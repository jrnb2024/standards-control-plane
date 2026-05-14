# WP-SCP-024 024A plan-doc acceptance checklist

**Slice:** WP-SCP-024 024A (plan-doc landed at PR #102 / `4dc3faa` on 2026-05-04)
**Status as of:** 2026-05-14 (post 024B-core + 024B-extras-1 + 024B-extras-2 merges; 024B-extras-3 in flight)
**Source:** `docs/plans/WP-SCP-024-estate-cascade.md` §6 (Slice plan) + §8 (Acceptance criteria + Threshold A)
**Closes governance gap:** GAP-P1-002 (orchestrator audit, 2026-05-13) — plan-doc §6 acceptance criteria did not have an enumerated checklist with per-criterion disposition.

## How to read this checklist

Each row lists one of the 14 acceptance criteria spanning plan-doc §6 (per-slice ACs) and §8 (plan-doc level + Threshold A). Status values per criterion at PR #102 merge time vs. as of today (2026-05-14):

- **CLOSED** — satisfied at the named slice merge (cited via `git log`-grade commit SHA).
- **DEFERRED** — explicitly assigned to a later named slice; not in scope at PR #102 but tracked.
- **N/A** — not applicable to this slice (e.g. a Threshold A criterion is not a plan-doc-merge criterion).

`grep_production_before_planning.md`: each closure cites file:line or commit SHA so the claim is verifiable.

## §8 plan-doc level acceptance (3 criteria)

| # | Criterion | Status at PR #102 merge (2026-05-04) | Status as of 2026-05-14 | Evidence |
|---|---|---|---|---|
| 1 | v0.1 plan-doc lands with §1–§10 populated | CLOSED | CLOSED | `docs/plans/WP-SCP-024-estate-cascade.md` §1 line 23 through §10 line 269 — all 10 sections populated; PR #102 merged at `4dc3faa` 2026-05-04 |
| 2 | 3-lens R1+R2 fixpoint reached (0 CRIT + 0 MAJ on a complete cycle) | CLOSED | CLOSED | 9 review rounds total per `project_wp_scp_024_plan.md` memory — longest in the WP-SCP-019/020/021/022/023/024 chain; 32 unique MAJ + 1 CRIT closed across 8 fix-rounds; R9 returned 0 CRIT + 0 MAJ on a complete cycle |
| 3 | D-044 / D-045 / D-046 reserved (not assigned in this slice) | CLOSED | D-044 FILED + D-045/D-046 STILL RESERVED | `docs/DECISIONS.md` D-044 row (line 100) ratifies 024B-core operational contracts — accepted 2026-05-09. D-045 (024C) and D-046 (024G) remain reserved per the DECISIONS.md header reservation note |

## §6 per-slice acceptance criteria (7 slices)

| # | Slice | Criterion | Status at PR #102 merge | Status as of 2026-05-14 | Evidence |
|---|---|---|---|---|---|
| 4 | 024A | Plan-doc R2 fixpoint reached + merged | CLOSED | CLOSED | This slice; PR #102 / `4dc3faa` |
| 5 | 024B | Scaffolder emits known-fixture wrapper; CI script implements all 4 cascade-status behaviours; D-044 filed; `--restore` + ADOPT-001 §12.8 + workflow wiring ship | DEFERRED (split per `D-SCP-024B-SCOPE-SPLIT-2026-05-09.md`) | CLOSED across 3 sibling slices: 024B-core merged `249aa9f` 2026-05-09 (D-044); 024B-extras-1 merged `d7b16d0` 2026-05-12 (D-047, PR #113); 024B-extras-2 merged `13572fe` 2026-05-13 (D-048, PR #114) + 024B-extras-3 in flight (PR #116; defensive hardening; no new D-NNN) |
| 6 | 024C | PIM `policy-check / scp/policy-check` required-check live; ≥1 Renovate-bump-propagation cycle merged clean; D-045 filed | DEFERRED | DEFERRED — gated on FUP-ACC-INSTALL-TARGET-REPO-001 (ACC-side, not SCP-side). Pre-staged at `/tmp/codex-wp/scp/024c-kickoff-prep/` per `project_wp_scp_024_plan.md` |
| 7 | 024D | control-tower `policy-check / scp/policy-check` required-check live; ≥1 Renovate-bump-propagation cycle merged clean | DEFERRED | DEFERRED — opens after 024C bake-clean (canary-first per §5.1) |
| 8 | 024E | mapp-doc-agent + recommender paired cascade — both adopters' required-checks live; ≥1 Renovate-bump-propagation cycle merged clean on each | DEFERRED | DEFERRED — opens after 024D bake-clean |
| 9 | 024F | shopify-app `policy-check / scp/policy-check` required-check live; ≥1 Renovate-bump-propagation cycle merged clean | DEFERRED | DEFERRED — opens after 024E bake-clean |
| 10 | 024G | ≥3 cohort adopters onboarded + bake-clean + USER-GATE-E signed; D-046 filed | DEFERRED | DEFERRED — closing slice; opens when ≥3 of 5 cohort adopters have all sibling §8 Threshold A criteria satisfied |

## §8 Threshold A criteria (4 mandatory)

Threshold A is the binary pass/fail closure gate for WP-SCP-024 as a whole. At PR #102 merge (plan-doc), Threshold A criteria are by definition all DEFERRED. Each criterion below names the slice or operational state where it closes.

| # | Criterion | Status at PR #102 merge | Status as of 2026-05-13 | Evidence / Closure path |
|---|---|---|---|---|
| 11 | ≥3 of {PIM, recommender, mapp-doc-agent, control-tower, shopify-app} have `policy-check / scp/policy-check` as a required status check on default branch | DEFERRED | DEFERRED (0 of 5 onboarded) | Closes incrementally via 024C–024F adopter slices; counted at 024G |
| 12 | Each onboarded adopter has a corresponding entry in `docs/reviews/WP-SCP-020/branch-protection-log.md` with operator + timestamp + before/after API JSON + script SHA256 + git SHA — OR is `cascade-status: blocked-on-adopter-conflict` with the matching TF | DEFERRED | DEFERRED | Logged per-cascade-slice; verified at 024G |
| 13 | Each onboarded adopter has survived ≥1 SCP minor version-bump cycle propagated cleanly via Renovate (Renovate-issued PR merged + observed clean on default branch); operator-driven R-024-07 bumps do NOT count toward Threshold A | DEFERRED | DEFERRED | Per-adopter bake captured in cascade slice STATUS.md row; gated on Renovate's per-adopter cadence |
| 14 | USER-GATE-E artefact (`docs/gates/USER-GATE-E.md`) signed by @jrnb2024 | DEFERRED | DEFERRED | Operator action at 024G close; `docs/gates/USER-GATE-E.md` scaffolded but unsigned until criteria 11–13 close |

## Summary

At PR #102 merge (2026-05-04):
- **CLOSED:** 4 of 14 (criteria 1, 2, 3, 4 — all plan-doc level).
- **DEFERRED:** 10 of 14 (criteria 5–14 — all implementation-slice or Threshold A level).

As of 2026-05-14 (post 024B-extras-3 defensive hardening in flight):
- **CLOSED:** 5 of 14 (criteria 1, 2, 3, 4, 5 — plan-doc + all of 024B fully delivered via 3-sibling split; 024B-extras-3 remains a separate in-flight hardening slice).
- **DEFERRED:** 9 of 14 (criteria 6–14 — cascade implementation slices + Threshold A; 024C blocked by FUP-ACC-INSTALL-TARGET-REPO-001, downstream slices gated on canary-first sequencing).

## Cross-references

- `docs/plans/WP-SCP-024-estate-cascade.md` §6 (Slice plan) + §8 (Acceptance criteria + Threshold A) — canonical AC source.
- `docs/decisions/D-SCP-024B-SCOPE-SPLIT-2026-05-09.md` — operator-decided 024B split (closes GAP-P1-001).
- `docs/DECISIONS.md` D-044 (024B-core), D-047 (024B-extras-1), D-048 (024B-extras-2) — implementation ratifications.
- `STATUS.md` "Open scheduled follow-ups" + tracked-forward section — outstanding TFs per slice.

## Maintenance

This checklist is informational. The canonical AC source is the plan-doc itself; this file mirrors the AC enumeration in checklist form with per-criterion disposition for governance-audit consumption. Update when a deferred criterion closes (cite the slice's PR + commit SHA in the Status column).
