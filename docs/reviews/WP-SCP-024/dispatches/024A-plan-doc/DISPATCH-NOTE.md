# WP-SCP-024 slice 024A — plan-doc authoring (dispatch note)

**Date:** 2026-05-03 (PM-2)
**Tier:** orchestrator-applied (Tier 1) per `feedback_four_tier_dispatch.md` — plan-doc authoring is canonical Opus-tier work (estate-doctrine specification, no executor-tier code).
**Closes:** opens **WP-SCP-024** with a v0.1 plan-doc; unblocks 024B+ implementation slices on plan-doc R1+R2 fixpoint.
**Cuts:** no version bump. Internal planning artefact only.

**Slice naming.** `024A` follows the established WP-SCP-019/020/021/022/023 plan-doc convention (`<WP>A` = plan-doc slice; `<WP>B` onward = implementation slices). Branch `feature/wp-scp-024-estate-cascade-plan` mirrors the five prior plan-doc branches.

## Rationale — why this slice now

Per the operator's 2026-05-03 directive ("Just keep going autonomously, using the full process") and the just-merged WP-SCP-023 023E (PR #101 / `295e0da`):

1. **WP-SCP-023 023E just merged.** That was the closing slice of the 5-move MVCP — SCP now has cross-repo observability scaffolded (USER-GATE-D not-yet-signed, awaiting first three real adopters). The natural next move is the cascade that drives drift down across the estate.
2. **No remaining named-substantive item in the 5-move MVCP backlog.** WP-SCP-024 (estate cascade) was already named as the natural successor by WP-SCP-020 §3 ("estate rollout") + WP-SCP-022 §12 ("estate cascade") + WP-SCP-023 §10 forward-looking Q7.
3. **Plan-doc slice is the natural unblocker** for the cascade slices that follow. Following the established WP-SCP-019/020/021/022/023 pattern, every large WP starts with a plan-doc that the implementation slices reference.
4. **FLA-independent constraint per operator direction (2026-05-03).** WP-SCP-024 cascade slices MUST NOT block on FLA pilot reaching a stable state. FLA pilot continues on its own track (WP-SCP-020.1). The non-FLA cohort proceeds in parallel. This is invariant 4 in the plan-doc.
5. **D-035 already names the cohort.** `{pim, recommender, shopify-app, mapp-doc-agent, control-tower}` was enumerated when D-035 ratified `scripts/enable-required-check.sh` as canonical onboarding mechanism. WP-SCP-024 cascades that onboarding across the named 5.

## Scope decision — what's IN, what's OUT (this slice)

| Item | Disposition | Rationale |
|---|---|---|
| `docs/plans/WP-SCP-024-estate-cascade.md` (NEW) | **IN** | Primary deliverable. Plan-doc authored at v0.1 status: Draft — ready for plan-PR review. |
| Slice ordering: 024A (plan, this), 024B (scaffolder + `enable-required-check.sh --restore`), 024C (PIM canary), 024D (control-tower), 024E (mapp-doc-agent + recommender paired), 024F (shopify-app), 024G (Threshold A + USER-GATE-E) | **IN** | Mirror of WP-SCP-020 §3 / WP-SCP-021 §3 / WP-SCP-023 §6 pattern. |
| Reservation block for D-044 / D-045 / D-046 in `docs/DECISIONS.md` header | **IN** | Mirror of D-021 + D-041/042/043 reservation blocks per the established Codex-executor reservation guard pattern. |
| **D-044 / D-045 / D-046** decision rows in `docs/DECISIONS.md` body | **OUT (this slice)** | Decision rows land at the slice that ratifies them — D-044 lands in 024B, D-045 lands in 024C, D-046 lands in 024G. The plan-doc references each as "to be filed at slice 024X" per the WP-SCP-022 §1 / WP-SCP-023 §9 pattern. |
| Implementation code (scaffolder script, `enable-required-check.sh --restore`, adopter wrappers) | **OUT (this slice)** | Implementation slices follow plan-doc fixpoint. Each is its own future PR with its own DISPATCH-NOTE + R1+R2. |
| Adopter-facing wrapper template (`templates/adopter-wrapper.yml.tmpl`) | **OUT (this slice)** | Template lands at 024B alongside the scaffolder it feeds. |
| Adopter-side PRs to PIM / control-tower / etc. | **OUT (this slice)** | Adopter PRs are slice-024C/D/E/F deliverables, not plan-doc deliverables. |
| Cross-repo notification to ACC / CT / mapp-estate-regression | **OUT (this slice)** | Cross-repo coordination starts when cascade rollout begins (024C onwards). The plan-doc is SCP-internal. |
| `version-manifest.json` bump | **OUT (this slice)** | Plan artefact only; no public-surface change. |
| `RELEASE_NOTES.md` entry | **OUT (this slice)** | Plan artefact only. |
| New CODEOWNERS entry | **OUT (this slice)** | Existing `docs/plans/** @jrnb2024` covers the new plan-doc. |
| USER-GATE-E artefact (`docs/gates/USER-GATE-E.md`) | **OUT (this slice)** | The plan-doc names the gate; the actual artefact + sign-off process lands at 024G per the WP-SCP-020 USER-GATE-A / WP-SCP-023 USER-GATE-D pattern. |
| `.github/workflows/scorecard-aggregator.yml` extensions for cascade-status | **OUT (this slice)** | Aggregator extensions land at 024G if at all (open question per §10 Q7 / §5.5 — may be rolled into existing `consult_scorecard` instead). |

## Tier-justification (why orchestrator-applied)

Plan-doc authoring is canonical Opus-tier work per `feedback_four_tier_dispatch.md`:
- **Estate-doctrine specification:** the plan-doc binds operator + adopter behaviour estate-wide. Codex-tier executors are inappropriate for spec authoring.
- **No code surface:** the slice produces a single markdown file (~240 lines) + STATUS.md row + DECISIONS.md reservation block. 3-lens R1 review is the right adversarial layer (correctness against the established WP-SCP-019/020/021/022/023 patterns; safety against bypass surface from estate-wide branch-protection mutations; completeness against the WP-SCP-024 acceptance criteria).
- All five prior plan-docs (WP-SCP-019/020/021/022/023) used orchestrator-applied + 3-lens R1 to fixpoint.

If R1 surfaces a CRIT/MAJ requiring spec-level rework (e.g. the cascade ordering is unsafe or the FLA-independent constraint creates a hidden dependency), a fix-round-2 may itself dispatch additional Sonnet review — the plan-doc IS the spec, not the implementation.

## Slice acceptance

- [ ] **(i) Plan-doc exists.** `docs/plans/WP-SCP-024-estate-cascade.md` with the established header (WP-SCP-024, version 0.1, status Draft, branch, programme ref, decisions reserved).
- [ ] **(ii) Purpose section.** §1 names what WP-SCP-024 is (estate cascade across the D-035 5-cohort) + position relative to the 5-move MVCP (natural successor; turns observation into action).
- [ ] **(iii) Invariants section.** §2 names the 10 non-negotiable invariants — opt-in per-adopter, operator-run + invocation-logged, **cascade does NOT touch existing adopter content (purely additive)**, FLA-independent, required-check primary + scorecard-emit secondary, no cross-repo write, per-adopter rollback, version-skew tolerance via post-bake observation, bus-factor-1 acknowledged, no backwards-incompatible adopter-side work. Plus "What this is NOT" exclusions. (Closes 024A R1 COR-MIN-001 — earlier draft listed only 9.)
- [ ] **(iv) Programme protocol position.** §3 names plan-PR semantics + four-tier dispatch + adversarial review applies twice (SCP-side + adopter-side).
- [ ] **(v) Threat model.** §4 names T-024-NN threat rows covering operator misfire, credential compromise, adopter rejection, version-skew, stale SHA pin, default-branch heterogeneity, post-bake premature-clean, estate-wide concentration, cost spike, name conflict.
- [ ] **(vi) Architecture / components.** §5 names cohort + sequencing, per-adopter onboarding contract, scaffolder helper, `enable-required-check.sh --restore`, Threshold A telemetry. Names data flows + decision points.
- [ ] **(vii) Slice plan.** §6 enumerates 024A (this), 024B (scaffolder), 024C (PIM canary), 024D (control-tower), 024E (mapp-doc-agent + recommender), 024F (shopify-app), 024G (Threshold A). Each carries deliverable + acceptance criteria. Sequence is non-parallelisable.
- [ ] **(viii) Risk surface.** §7 names R-024-NN risk rows (15 rows) covering each invariant + threat-model crossover.
- [ ] **(ix) Acceptance + Threshold criteria.** §8 names plan-doc acceptance + Threshold A definition (≥3 of 5 onboarded + ≥1 Renovate cycle clean per adopter + USER-GATE-E signed).
- [ ] **(x) Decisions reserved.** §9 reserves D-044 for slice 024B; D-045 for slice 024C; D-046 for slice 024G. Codex-executor reservation guard explicit.
- [ ] **(xi) Forward-looking + open questions.** §10 captures questions that should be revisited at each implementation slice (10 questions).
- [ ] **(xii) Adversarial review reaches fixpoint.** 3-lens R1 → recurse R2/R3 until 0 new CRIT + 0 new MAJ on a complete cycle.
- [ ] **(xiii) PR opens + CI green + operator-merge per D-040.** No `scp-rule-proposal` label (this is a plan-doc PR, not a rule-RFC).
- [ ] **(xiv) STATUS.md backfill + memory + close-out.** STATUS.md gets a 023E close-out row pointer (#101) + 024A row; `project_post_threshold_a_state.md` updated to reference WP-SCP-024 opening.

## Risk surface

1. **Cohort completeness drift.** The D-035 enumeration was 2026-04-30; new in-flight estate repos may have emerged. Mitigation: §10 Q1 explicitly resolves to "stick to the D-035 enumeration" + names non-cohort opportunistic onboarding as post-Threshold-A maintenance.
2. **FLA pilot interaction risk.** If the plan-doc ends up with implicit FLA dependency, the cascade is no longer FLA-independent. Mitigation: invariant 4 + §10 Q2 explicit; R1 review checks for FLA references that aren't framed as "explicitly independent".
3. **Scorecard-emit coupling risk.** TF-023E-002 must close before any cascade slice can include scorecard-emit. Mitigation: invariant 5 makes required-check primary + scorecard-emit secondary. Cascade slices that complete without scorecard-emit are fully Threshold-A-counting.
4. **Estate-wide branch-protection mass-mutation risk.** Cascade slices invoke `enable-required-check.sh` — a mishap here mass-mutates the estate. Mitigation: D-035's CI-refusal + invocation log + invariant 2 makes log-entry mandatory. Plan-doc surfaces this as T-024-01 + T-024-02.
5. **Plan-doc drift from implementation reality.** The plan-doc commits to a scaffolder shape that may not survive contact with reality. Mitigation: every implementation slice ratifies (or amends) the plan-doc via D-NNN amendment per the D-033 / D-040 amendment pattern. Plan-doc is v0.1; v1.0 would only be cut after Threshold A.
6. **Cascade slice ordering is sequential — perceived slowness.** Per §5.1 + §6 slice-ordering note, cascade slices CANNOT parallelise. Mitigation: post-bake observation per invariant 8 is the safety primitive; parallelising defeats canary purpose. Plan-doc surfaces this in §6 explicit "NOT parallelisable" note.
7. **Adopter-side review-shape heterogeneity risk.** Some adopters require multi-reviewer; the plan-doc must not assume single-reviewer. Mitigation: R-024-03 + invariant per `enable-required-check.sh` D-035 ("preserves any pre-existing `required_pull_request_reviews` shape").

## R1 review

3× parallel Sonnet R1 (correctness / safety_bypass / completeness_governance). Recurse to fixpoint per `feedback_recursive_adversarial_review.md`.

Review surface focuses:
- **Correctness.** Does the plan-doc accurately describe the cascade architecture? Are the 10 invariants internally consistent + load-bearing? Does §5 (architecture) match §6 (slice plan)? Does the sequencing in §5.1 actually achieve the canary-first goal stated in §1? Are the references to D-035 / D-036 / D-031 / WP-SCP-020 020G / WP-SCP-023 023E carve-outs accurate? Does the FLA-independent invariant 4 actually hold across all 10 invariants (no hidden FLA dependency)? Does the acceptance criteria in §8 match the slice deliverables in §6? Are §6's "NOT parallelisable" note + invariant 8 consistent (sequential bake + Renovate-cycle observation)?
- **Safety/bypass.** Does the proposed cascade create any new bypass surface? Could a cascade slice accidentally enable required-check on a wrong adopter? Could an adopter PR be merged that bypasses the post-bake observation? Are the invocation-log / no-CI-write / operator-only constraints actually enforceable (not just policy)? Does the rollback procedure in invariant 7 + §5.4 actually work, or is it aspirational? Does the FLA-independent constraint create any safety gap (e.g. FLA learnings that should be inherited)? Does invariant 10 (no backwards-incompatible adopter-side work) leave any cascade slice in an undefined state when adopter-side conflicts surface?
- **Completeness.** Are all 14 acceptance criteria addressable by the plan-doc? Are slice boundaries clean (each cascade slice has a defined deliverable)? Are cross-repo coordination points named (notifications to CT, ACC, mapp-estate-regression at 024C cascade kickoff)? Are the WP-SCP-023 carry-forward TFs (TF-023E-001, TF-023E-002) properly tracked as cascade preconditions? Is the Threshold A criterion in §8 measurable? Are the 10 open questions in §10 actually open or have they been silently closed in the plan-doc body? Is the bus-factor-1 acknowledgement (invariant 9) consistent with the 2026-07-21 quarterly review timeline? Does the cascade ordering in §5.1 / §6 actually satisfy the canary-first goal stated in §1?

## Files

### Modified
- `STATUS.md` — close out 023E pointer (#101 / `295e0da`) + add 024A row to "Today's chain (2026-05-03)".
- `docs/DECISIONS.md` — add D-044 / D-045 / D-046 reservation block + bump "Last Updated" date.

### Added
- `docs/plans/WP-SCP-024-estate-cascade.md` (NEW; plan-doc).
- `docs/reviews/WP-SCP-024/dispatches/024A-plan-doc/DISPATCH-NOTE.md` (this file).
- `docs/reviews/WP-SCP-024/dispatches/024A-plan-doc/review-{correctness,safety,completeness}-package.json` — R1 lens packages (added before R1 dispatch).
- `docs/reviews/WP-SCP-024/dispatches/024A-plan-doc/review-{correctness,safety,completeness}.json` — R1 results (added after R1 dispatch).
- `docs/reviews/WP-SCP-024/dispatches/024A-plan-doc/FIX-ROUND-N.md` — per fix-round audit (if any rounds needed).

## Forward-looking

- **Implementation slices** (024B / 024C / 024D / 024E / 024F / 024G) follow plan-doc R2 fixpoint + merge + STATUS.md backfill. Each is a separate branch + DISPATCH-NOTE + R1+R2 + merge cycle. 024C-024F also include adopter-side PRs (separate repos).
- **D-044** to be filed in 024B (scaffolder + restore mode): operational contract.
- **D-045** to be filed in 024C (PIM canary cascade): cascade ordering + per-adopter onboarding contract.
- **D-046** to be filed in 024G (Threshold A + USER-GATE-E): Threshold A criteria + post-Threshold-A maintenance.
- **TF-023E-001 / TF-023E-002** carry forward as cascade preconditions for the scorecard-emit secondary surface (per invariant 5). Cascade primary surface (required-check) is unblocked.
- **WP-SCP-025** is open question §10 Q7 — not pre-committed in this plan-doc.
