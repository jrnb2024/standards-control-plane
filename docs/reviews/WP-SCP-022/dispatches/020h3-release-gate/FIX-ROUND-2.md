# 020h3-release-gate fix-round-2 (post-r2 — fixpoint reached)

**Date:** 2026-05-01

## Triggers — fixpoint reached at R2

R2 lens cycle returned **0 CRIT + 0 MAJ across all three lenses**:

| Lens | Verdict | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|---|
| R2 correctness | APPROVED_WITH_FINDINGS | 0 | 0 | 1 | 4 |
| R2 safety | APPROVED_WITH_FINDINGS | 0 | 0 | 1 | 2 |
| R2 completeness | APPROVED_WITH_FINDINGS | 0 | 0 | 1 | 1 |
| **TOTAL** | — | **0** | **0** | **3** | **7** |

Per `feedback_recursive_adversarial_review.md`: **fixpoint criterion is "no new BLOCKING (CRIT/MAJ)"** — R2 confirms.

Per `feedback_protocol_over_shortcuts.md` (no descoping): all 3 MIN + 7 nit closed inline this round.

## Closures applied

| Finding | Severity | Closure |
|---|---|---|
| R2-COR-MIN-001 | MIN | release-gate.yml workflow header line 17 reworded: "and (per TF-020H3rg-003, not yet implemented at v1.0.0) will open a `release-gate-violation` issue for triage" — matches VERSIONING.md + DISPATCH-NOTE qualified language. |
| R2-MIN-SAFE-001 | MIN | VERSIONING.md "Bad-tag recovery procedure" detection-latency clause rewritten — Renovate-using adopters see automated bump PR within hours; manually SHA-pinning adopters see SCP-FRESH-001 only after 3+ subsequent MINOR releases (per the freshness threshold default of 2). Manual quarterly review of the SCP releases page (per §12.7.11 fallback) named as the supplementary signal. |
| COMP-R2-MIN-001 | MIN | schemas/deprecations.schema.json target_release pattern tightened from `^v[0-9]+\.[0-9]+\.[0-9]+$` to `^v[0-9]+\.0\.0$` — schema-level enforcement of the MAJOR-only constraint that fix-round-1 added at the workflow level (defense in depth). Description extended with the MAJOR-vehicle rationale. Smoke-tested: target=v2.0.0 passes; target=v1.1.0 rejected. |
| R2-COR-nit-001 | nit | schemas/deprecations.schema.json surface_id description extended with `tag_protection_pattern` guidance ("the ruleset pattern string, e.g. v* or renovate/v*"). |
| R2-COR-nit-002 | nit | VERSIONING.md "Bad-tag recovery procedure" emergency path expanded with: (1) ruleset-id discovery `gh api .../rulesets --jq '.[] | {id, name}'`; (2) tag deletion `git push --delete origin <bad-tag>`; (3) ruleset restore `bash scripts/configure-020j-protections.sh`. |
| R2-COR-nit-003 | nit | release-gate.yml tampering-warning guard tightened to `if ann_major < cand_major - 1 and target != candidate` — eliminates double-fire alongside the structural-inconsistency error for target-matched entries. |
| R2-COR-nit-004 | nit | DISPATCH-NOTE acceptance checklist (iii) concurrency-group text updated from `release-gate-${ref}` to `release-gate-${{ github.event_name == 'workflow_dispatch' && inputs.dry_run_tag || github.ref }}` with cross-reference to fix-round-1 COR-MIN-003 + nit-SAFE-007. |
| R2-nit-SAFE-001 | nit | VERSIONING.md "Tag-cut procedure" step 2 dry-run command corrected from `gh run list --workflow=release-gate.yml --limit 1` (always exit 0) to a `RUN_ID="$(gh run list ... --json databaseId --jq '.[0].databaseId')"; gh run watch "${RUN_ID}" --exit-status` idiom that surfaces the workflow's verdict via non-zero exit on failure. |
| R2-nit-SAFE-002 | nit | ADOPT-001 §12.7.7 SCP-EREL-001 row extended with parenthetical describing the `SCP-EREL-001-warn` ::warning:: variant (non-blocking, fires on ann_major < cand_major - 1; SCP-source only). |
| COMP-R2-nit-001 | nit | ADOPT-001 §12.7.7 SCP-EREL-001 Adopter-side relevance cell phrasing fixed: "the per-surface deprecation `::warning::` annotations (SCP-DEP-001) emitted during the one-MINOR ramp window" (was: misleading "the deprecation `::warning::` annotations on rule denies"). |

## Closures NOT applied

None. All R2 findings closed.

## Cumulative across 2 rounds

| Round | Verdict by lens | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|---|
| R1 corr | APPROVED_WITH_FINDINGS | 0 | 2 | 3 | 1 |
| R1 safety | CHANGES_REQUESTED | 1 | 3 | 2 | 2 |
| R1 comp | NEEDS_FIX | 0 | 2 | 2 | 0 |
| R2 corr | APPROVED_WITH_FINDINGS | 0 | 0 | 1 | 4 |
| R2 safety | APPROVED_WITH_FINDINGS | 0 | 0 | 1 | 2 |
| R2 comp | APPROVED_WITH_FINDINGS | 0 | 0 | 1 | 1 |
| **TOTAL** | — | **1** | **7** | **10** | **10** |

1 CRIT + 7 MAJ closed (most inline; 3 via TF-020H3rg-NNN tracking). 10 MIN closed. 10 nit closed.

**Slice 020H.3 ready for merge.**
