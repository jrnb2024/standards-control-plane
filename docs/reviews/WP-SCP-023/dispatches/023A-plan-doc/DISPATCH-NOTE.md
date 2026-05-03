# WP-SCP-023 slice 023A — plan-doc authoring (dispatch note)

**Date:** 2026-05-03 (PM-1)
**Tier:** orchestrator-applied (Tier 1) per `feedback_four_tier_dispatch.md` — plan-doc authoring is canonical Opus-tier work (estate-doctrine specification, no executor-tier code).
**Closes:** opens **WP-SCP-023** with a v0.1 plan-doc; unblocks 023B+ implementation slices on plan-doc R1+R2 fixpoint.
**Cuts:** no version bump. Internal planning artefact only.

**Slice naming.** `023A` follows the established WP-SCP-019/020/021/022 plan-doc convention (`<WP>A` = plan-doc slice; `<WP>B` onward = implementation slices). Branch `feature/wp-scp-023-cross-repo-scorecards-plan` mirrors the four prior plan-doc branches (`feature/wp-scp-020-policy-federation-primitive-plan`, `feature/wp-scp-021-mcp-server-plan`, `feature/wp-scp-022-implementation-programme-plan`).

## Rationale — why this slice now

Per `docs/reviews/WP-SCP-022/CONTINUATION-PROMPT-2026-05-02-pm-3.md` "What's next" + the just-merged TF-006 closure (PR #96 / `974a173`):

1. **TF-006 (conflict-gate suppression-path corpus + Python waiver-awareness) just merged.** That was WP-SCP-023's listed sequencing prerequisite — without Python waiver-awareness, the cross-repo aggregator couldn't apply waivers consistently across adopters' PR-time evaluations and the centralised summary view. With TF-006 closed, the path to scorecard implementation is unblocked.
2. **No named-substantive backlog item remains** post-TF-020P-005 + 020Q. WP-SCP-023 is the next-substantive WP candidate per the continuation prompt.
3. **Plan-doc slice is the natural unblocker** for the implementation slices that follow. Following the established WP-SCP-019/020/021/022 pattern, every large WP starts with a plan-doc that the implementation slices reference.
4. **v1.1.0 ships sufficient federation-primitive surface to underpin scorecards.** SCP-R-001/002/003/004 + warn-baseline rendering + tag-protection + release-gate + canary corpus + waiver-aware conflict-gate fixtures all live. The data feeding scorecards already exists per-PR (`policy-check-summary.json`); WP-SCP-023 only adds aggregation + exposure.

## Scope decision — what's IN, what's OUT (this slice)

| Item | Disposition | Rationale |
|---|---|---|
| `docs/plans/WP-SCP-023-cross-repo-scorecards.md` (NEW) | **IN** | Primary deliverable. Plan-doc authored at v0.1 status: Draft — ready for plan-PR review. |
| Slice ordering: 023A (plan, this), 023B (per-repo scorecard emitter), 023C (aggregator + central index), 023D (exposure surface — markdown report + MCP method), 023E (Threshold criteria + sign-off) | **IN** | Mirror of WP-SCP-020 §3 / WP-SCP-021 §3 pattern. |
| **D-041** decision row in `docs/DECISIONS.md` (cross-repo scorecard data model + opt-in adopter participation) | **OUT (this slice)** | Decision rows land at the slice that ratifies them — D-041 lands in 023B (per-repo emitter) when the schema is finalised. The plan-doc references D-041 as "to be filed in 023B" per the WP-SCP-022 §1 "Decisions reserved" pattern. |
| Implementation code (per-repo collector, aggregator, exposure surface) | **OUT (this slice)** | Implementation slices follow plan-doc fixpoint. Each is its own future PR with its own DISPATCH-NOTE + R1+R2. |
| Schema files (`schemas/scorecard-emit.schema.json`, `schemas/scorecard-index.schema.json`) | **OUT (this slice)** | Schemas land at slice 023B/023C alongside the implementations they specify. |
| MCP method definitions (`scp.consult_scorecard`, `scp.audit_scorecard_changed`) | **OUT (this slice)** | MCP method scaffolding lands at slice 023D when the exposure surface is implemented. The plan-doc names them as forward-looking. |
| Adopter-facing onboarding doc updates (`ADOPT-001` §13 cross-repo scorecards) | **OUT (this slice)** | Onboarding doc updates land at 023D/023E when adopters can actually participate. The plan-doc references the future section. |
| Threshold A criteria sign-off helper (`USER-GATE-D` artefact) | **OUT (this slice)** | The plan-doc names the gate; the actual artefact + sign-off process lands at 023E per the WP-SCP-020 USER-GATE-A pattern. |
| Cross-repo notification to ACC / CT / mapp-estate-regression | **OUT (this slice)** | Cross-repo coordination starts when scorecard-emitter rollout begins (023B onwards). The plan-doc is SCP-internal. |
| `version-manifest.json` bump | **OUT (this slice)** | Plan artefact only; no public-surface change. |
| `RELEASE_NOTES.md` entry | **OUT (this slice)** | Plan artefact only. |
| New CODEOWNERS entry | **OUT (this slice)** | Existing `docs/plans/** @jrnb2024` covers the new plan-doc. |

## Tier-justification (why orchestrator-applied)

Plan-doc authoring is canonical Opus-tier work per `feedback_four_tier_dispatch.md`:
- **Estate-doctrine specification:** the plan-doc binds adopter behaviour estate-wide. Codex-tier executors are inappropriate for spec authoring.
- **No code surface:** the slice produces a single markdown file (~250-350 lines). 3-lens R1 review is the right adversarial layer (correctness against the established WP-SCP-019/020/021/022 patterns; safety against bypass surface introduced by aggregating cross-repo waiver content; completeness against the WP-SCP-023 acceptance criteria). 
- All four prior plan-docs (WP-SCP-019/020/021/022) used orchestrator-applied + 3-lens R1 to fixpoint.

If R1 surfaces a CRIT/MAJ requiring spec-level rework (e.g. the data model is unsound), a fix-round-2 may itself dispatch additional Sonnet review — the plan-doc IS the spec, not the implementation.

## Slice acceptance

- [ ] **(i) Plan-doc exists.** `docs/plans/WP-SCP-023-cross-repo-scorecards.md` with the established header (WP-SCP-023, version 0.1, status Draft, branch, programme ref, decisions reserved).
- [ ] **(ii) Purpose section.** §1 names what WP-SCP-023 is (cross-repo scorecard aggregation surface) + what move number in the MVCP it represents (move #4 — "estate-wide observability for the federation primitive").
- [ ] **(iii) Invariants section.** §2 names the non-negotiable invariants — (a) rule-id-only matching (per scp_common.rego); (b) waiver content is NEVER exposed to non-CODEOWNERS of the source repo; (c) opt-in adopter participation; (d) aggregator never suppresses denies (informational only); (e) MCP exposure is read-only. Plus "What this is NOT" exclusions.
- [ ] **(iv) Programme protocol position.** §3 names slice ordering + plan-PR semantics + dispatch protocol per WP-SCP-022.
- [ ] **(v) Threat model + invariants.** §4 names the cross-repo data flow threat model — what data crosses which boundary, who can read what, what signing/integrity is required.
- [ ] **(vi) Architecture / components.** §5 names the per-repo emitter, the aggregator, the central index, the exposure surface (markdown + MCP method). Names the data flow pipeline.
- [ ] **(vii) Slice plan.** §6 enumerates 023A (this slice), 023B (per-repo emitter), 023C (aggregator + central index), 023D (exposure surface), 023E (Threshold + sign-off). Each slice carries a deliverable + acceptance criteria.
- [ ] **(viii) Risk surface.** §7 names R-023-NN risk rows (privacy, supply-chain on aggregator pipeline, waiver-content disclosure, opt-in unfairness, MCP method abuse, etc.).
- [ ] **(ix) Acceptance + Threshold criteria.** §8 names the Threshold A definition for WP-SCP-023 (analogous to WP-SCP-020 Threshold A).
- [ ] **(x) Decisions reserved.** §9 reserves D-041 for slice 023B; reserves D-042 / D-043 for likely future slices.
- [ ] **(xi) Forward-looking + open questions.** §10 captures questions that should be revisited at each implementation slice.
- [ ] **(xii) Adversarial review reaches fixpoint.** 3-lens R1 → recurse R2/R3 until no new CRIT + 0 MAJ on a complete cycle.
- [ ] **(xiii) PR opens + CI green + operator-merge per D-040.** No `scp-rule-proposal` label (this is a plan-doc PR, not a rule-RFC).
- [ ] **(xiv) STATUS.md backfill + memory + close-out.** STATUS.md gets a 020Q close-out row + 023A row; `project_post_threshold_a_state.md` updated.

## Risk surface

1. **Data-model decisions made too early.** The plan-doc commits to a scorecard data shape before any adopter has implemented an emitter. Mitigation: explicitly mark the scorecard schema as v0.x (pre-1.0) until 023B's R1 fixpoint validates the shape works against at least one real adopter (FLA pilot per `reference_fla_gold_standard.md`).
2. **Cross-repo waiver content disclosure.** Centralising scorecards risks aggregating waiver content (waiver_id, reason, expires_at) into a single index visible to anyone with read access to that index. Mitigation: make the aggregator emit aggregated counts + verdicts only; raw waiver content stays in the source repo's `output/findings/waivers.json` (CODEOWNERS-protected). This is an invariant in §2.
3. **Bypass surface from aggregator pipeline compromise.** A compromised aggregator could mis-report a deny as allow, fooling estate observers. Mitigation: aggregator output is informational-only (per invariant); the federation primitive remains the per-PR authority; the aggregator output carries a per-emit Ed25519-signed receipt (extends MCP signing pattern from WP-SCP-021).
4. **Adopter opt-in unfairness.** A scorecard surface that lists adopter compliance ranks could create social pressure on opt-out adopters. Mitigation: scorecard exposure is opt-in by adopter; non-participating repos appear as "no data" (not "non-compliant"). Documented in invariants.
5. **MCP method abuse via cross-repo query.** A new `scp.consult_scorecard` MCP method could be used to enumerate adopter waivers across the estate. Mitigation: MCP method returns aggregated metrics only (counts, verdicts, version); raw waiver content stays out of MCP responses.
6. **Plan-doc drift from implementation reality.** The plan-doc commits to a slice ordering that may not survive contact with reality. Mitigation: every implementation slice ratifies (or amends) the plan-doc via D-NNN amendment per the D-033 / D-040 amendment pattern.

## R1 review

3× parallel Sonnet R1 (correctness / safety_bypass / completeness_governance). Recurse to fixpoint per `feedback_recursive_adversarial_review.md`.

Review surface focuses:
- **Correctness.** Does the plan-doc accurately describe the proposed architecture? Are the slice deliverables internally consistent? Does §6 (architecture) match the slice plan in §7? Does the data flow described in §5 actually achieve what §1 (purpose) claims? Are the references to WP-SCP-019/020/021/022 + scp_common.rego + ADOPT-001 accurate?
- **Safety/bypass.** Does the proposed cross-repo data flow create any new bypass surface? Could an adopter spoof a scorecard emit to fake compliance? Could the central index be tampered with to hide a real deny? Are the invariants in §2 actually load-bearing or aspirational? Does the Ed25519 signing model named in §5 match WP-SCP-021's prior art? Is the opt-in invariant enforceable in code (not just policy)?
- **Completeness.** Are all 14 acceptance criteria addressable by the plan-doc? Are the slice boundaries clean (each implementation slice has a defined deliverable)? Are the cross-repo coordination points named (notifications to CT, ACC, mapp-estate-regression)? Are the FLA-pilot-as-canary expectations clear? Is the Threshold A criterion in §8 measurable? Are the open questions in §10 actually open or have they been silently closed?

## Files

### Modified
- `STATUS.md` — close out 020Q row + add 023A row to "Today's chain (2026-05-03)".

### Added
- `docs/plans/WP-SCP-023-cross-repo-scorecards.md` (NEW; plan-doc).
- `docs/reviews/WP-SCP-023/dispatches/023A-plan-doc/DISPATCH-NOTE.md` (this file).
- `docs/reviews/WP-SCP-023/dispatches/023A-plan-doc/review-{correctness,safety,completeness}-package.json` — R1 lens packages.
- `docs/reviews/WP-SCP-023/dispatches/023A-plan-doc/review-{correctness,safety,completeness}.json` — R1 results.
- `docs/reviews/WP-SCP-023/dispatches/023A-plan-doc/FIX-ROUND-N.md` — per fix-round audit (if any rounds needed).

## Forward-looking

- **Implementation slices** (023B / 023C / 023D / 023E) follow plan-doc R2 fixpoint + merge + STATUS.md backfill. Each is a separate branch + DISPATCH-NOTE + R1+R2 + merge cycle.
- **D-041** to be filed in 023B (per-repo emitter): cross-repo scorecard data shape + opt-in adopter participation model.
- **D-042** likely to be filed in 023C (aggregator + central index): aggregator pipeline trust model + Ed25519 signing.
- **D-043** likely to be filed in 023D (exposure surface): MCP method shape + read-only contract.
- **WP-SCP-024 plan-doc** follows next per the user's directive.
