# WP-SCP-022 slice 020L — first rule-RFC dogfood (dispatch note)

**Date:** 2026-05-02
**Tier:** orchestrator-applied (Tier 1 only)
**Closes:** post-Threshold-A backlog item "WP-SCP-022 proposal-queue" (per `STATUS.md` and `CONTINUATION-PROMPT-2026-05-02-pm.md`).
**Opens:** RFC-001 (`docs/reviews/rule-proposals/RULE-001-waiver-reason-must-cite-issue-or-pr.md`) → target rule **SCP-R-004** at `threshold: warn` baseline → target release **v1.1.0** (Phase 2 implementation slice).

**Slice naming.** Letter `L` was reserved in `CONTINUATION-PROMPT-2026-05-01-pm.md` and `CONTINUATION-PROMPT-2026-05-02-pm.md` for the first rule-RFC dogfood. 020L sits between 020K (CODEOWNERS / single-operator branch posture, 2026-04-30) and 020M (supply-chain hash-pinning, 2026-05-02) alphabetically; the letter ordering is decoupled from chronological landing because the rule-RFC dogfood was scheduled later in the post-Threshold-A backlog.

## Rationale — why this slice now

The rule-RFC process landed at slice 020H.1 (PR #78, 2026-05-01) as `docs/reviews/rule-proposals/README.md` + `RULE-TEMPLATE.md`. **It has never been exercised.** WP-SCP-024 (estate cascade FLA → PIM → recommender → ...) presumes the RFC works. Discovering process gaps with a single operator is materially cheaper than discovering them when an estate adopter is also blocked.

The dogfood is split into two phases:

- **Phase 1 (this slice 020L):** author RFC-001 + open the proposal PR + walk the 48h quorum=1 window + merge the proposal. Deliverable is the merged proposal as the canonical specification for SCP-R-004.
- **Phase 2 (next slice — likely 020P, or 020H.5 if folded into the H series):** implement the rule (`policies/scp_r_004.rego` + tests + conflict-gate fixtures + canary update if the rule's deny path materially changes adopter PR behaviour) + bump v1.0.1 → v1.1.0 + cut tag.

Phase 1 keeps the docs-only blast radius small. Phase 2 follows once the proposal is merged.

## Topic selection — SCP-R-004 = waiver `reason` must cite an issue/PR URL

Three candidate first-rule topics were enumerated in `CONTINUATION-PROMPT-2026-05-02-pm.md`:

| Option | Topic | Risk | Selected? |
|---|---|---|---|
| A | Waivers must reference an issue/PR URL in `reason` | LOW (additive, warn baseline) | ✅ this slice |
| B | Waiver-expiry stale-detection at PR time | MEDIUM (new behaviour; date handling) | deferred |
| C | Deprecate SCP-R-002 to waivers.json paths only (closes TF-008) | HIGH (breaking change to live rule) | deferred |

Selection rationale:

- **First-dogfood goal is to find process gaps in the common case**, not stress-test the most exotic branch of the RFC infrastructure. Option A exercises the happy path end-to-end (PR open → 48h window → quorum-1 approval → merge → Phase-2 v1.1.0 cut) and surfaces gaps that would block Option B / Option C / any subsequent RFC.
- **Real motivation we can cite (per `README.md` §"Authorship guidance"):** SCP-R-002 enforces waiver shape but `reason` is a free-text string. Today nothing prevents `reason: "approved by Jim"` — there is no machine-checkable link from the waiver to a reviewable decision artifact. Audit trail is paper-thin.
- **Smallest implementation surface for Phase 2:** one Rego rule reading `data.waivers[_].reason` against a URL pattern, plus tests, plus conflict-gate fixtures. No new schema, no new bypass surface.
- **§5 Bypass surface = "None — uses existing mechanisms"** → the proposal does NOT trigger the non-waivable 48h front-matter path (`Bypass-surface non-empty: false`). Acceptable: that path is well-specified by 020H.1 R2 SAFE-MIN-001 closure and a future RFC (e.g. Option B or C) will exercise it.

## Justification for not invoking Codex executor

Per `feedback_four_tier_dispatch.md` in-line escalation guidance.

The slice surface is:

- One new Markdown file: `docs/reviews/rule-proposals/RULE-001-waiver-reason-must-cite-issue-or-pr.md` (~250 lines following `RULE-TEMPLATE.md`).
- Optional: `docs/reviews/WP-SCP-022/dispatches/020l/DISPATCH-NOTE.md` (this file).
- Optional: `STATUS.md` row for "Today's chain (2026-05-02)" extension.

No Rego rule paths are exercised in this slice (Phase 2 deliverable). No schema changes. No workflow changes. No public-surface changes. **No semver bump** for the proposal merge — `policies/VERSIONING.md` Scope clause excludes documentation-only changes.

Pure-governance + pure-docs work. Orchestrator-applied + R1 × 3 is the right posture (symmetric with the 020M / 020N dispatch notes' justification shape).

## Slice acceptance

- [ ] **(i) RFC-001 proposal authored.** `docs/reviews/rule-proposals/RULE-001-waiver-reason-must-cite-issue-or-pr.md` filled following `RULE-TEMPLATE.md` §1–§11. Every section completed (no `<placeholder>` left).
- [ ] **(ii) Front-matter machine-readable fields correct.** `Status: UNDER REVIEW`, `Author: @jrnb2024`, `Filed: 2026-05-02`, `Target release: v1.1.0`, `Type: rule-add`, `Quorum required: 1 (single-operator mode per D-031)`, `Review window: 48h wall-clock from PR open`, `Bypass-surface non-empty: false`.
- [ ] **(iii) §1 Summary self-contained.** Adopter reading only §1 can decide whether to engage with the rest. Includes target rule ID (SCP-R-004), match-condition one-liner, severity (warn baseline), target release.
- [ ] **(iv) §2 Motivation cites a real motivation.** Concrete: SCP-R-002 enforces waiver shape but `reason` is unconstrained; current waivers.json file in repo (`output/findings/waivers.json` if present, else inline example) demonstrates the audit-trail gap.
- [ ] **(v) §3 Rule specification complete.** Match conditions named, severity = warn at baseline, annotation contract uses existing SCP-EXXX infrastructure code (no new code required), Rego implementation sketch included.
- [ ] **(vi) §4 False-positive surface enumerated.** At least 2 named FP cases with estimated rate + recommended adopter response.
- [ ] **(vii) §5 Bypass surface = "None — uses existing mechanisms".** Implicit-exclusion set explicitly enumerated (when does the rule return allow?). Per 020H.1 R1 SAFE-MAJ-002 closure, the absence-of-field exemption is named explicitly.
- [ ] **(viii) §6 Conflict-gate strategy.** Match conditions are expressible in Python (regex match on `reason` field); fixture corpus enumerated; conflict-gate disagreement risk = LOW (deterministic regex).
- [ ] **(ix) §7 Estate-cascade considerations.** All 6 named estate adopters (FLA, PIM, recommender, shopify-app, mapp-doc-agent, control-tower) classified by likely warn opt-in vs needing transition period.
- [ ] **(x) §8 Test plan.** Conftest + conflict-gate + workflow-selftest coverage enumerated. Canary update flagged as optional (rule fires at warn, not deny — no canary needed for Phase-1 merge).
- [ ] **(xi) §9 Migration / rollout.** Maps to MINOR bump v1.0.1 → v1.1.0; promotion to deny default deferred to a separate proposal post-warn-period observation.
- [ ] **(xii) §10 Open questions.** Each marked `[BLOCKING]` or `[deferrable]` per RULE-TEMPLATE.md. No `[BLOCKING]` left at proposal-merge time.
- [ ] **(xiii) §11 References.** Cites: README.md (RFC process), RULE-TEMPLATE.md, policies/VERSIONING.md (semver contract for v1.1.0 target), schemas/rule-config.schema.json, ADOPT-001 §12.7.7 (SCP-EXXX codespace), D-022 (federation primitive adoption).
- [ ] **(xiv) PR opens 48h wall-clock window.** PR description includes one-paragraph "Bypass surface enumeration" stating "None — §5 confirms `Bypass-surface non-empty: false`. Existing `scp_bypass: true` three-gate model and `.scp/rule-config.yaml disable: true` per-adopter override remain the only bypass paths."
- [ ] **(xv) Adversarial review reaches fixpoint.** 3-lens R1 (correctness / safety_bypass / completeness_governance) → recurse R2 / R3 until no new CRIT/MAJ on a complete cycle. Lens-package files committed alongside; result files alongside; fix-round-N.md alongside.
- [ ] **(xvi) Operator-as-CODEOWNER approval after fixpoint.** Approval ratifies the proposal as canonical specification.
- [ ] **(xvii) STATUS.md update.** "Today's chain (2026-05-02)" row added; Post-Threshold-A backlog "WP-SCP-022 proposal-queue" line resolved or amended to point at RFC-001 + Phase-2 follow-up.

## Risk surface

1. **RFC infrastructure may have undiscovered gaps.** This is the slice's purpose; gaps surface as TF-020L-NNN entries with closure paths into a follow-up slice.
2. **Phase-2 implementation may surface §5 Bypass-surface gaps.** The proposal asserts §5 = None; if Phase-2 implementation discovers a new bypass surface (e.g. a `.scp/rule-config.yaml` `allow_unbounded_waivers: <bool>` key gets added to override the rule for legacy waivers), the proposal must be amended (a new PR; the original merged proposal stays on record as the v1 spec).
3. **False-positive rate may exceed estimates.** Phase-2 deploys at warn — adopters can opt out via rule-config. Phase-2 review will tune the URL-pattern regex against any FPs surfaced by SCP-self runs.
4. **No canary update at Phase-1 merge.** The proposal does not gate the canary suite (rule does not exist yet). Phase-2 implementation slice will add `canary/<topic>` if appropriate.
5. **Estate-cascade adopters may push back at proposal time.** This is a feature, not a bug — the 48h window IS the adversarial-review surface for the estate. If an adopter requests changes, the proposal can be revised in-window or extended (per `README.md` step 2 "non-bypass proposals" allow extension by author).

## R1 review

3× parallel Sonnet R1 review (correctness / safety_bypass / completeness_governance). Recurse to fixpoint per `feedback_recursive_adversarial_review.md` (no-new-CRIT/MAJ on a complete cycle).

Lens packages:
- `review-correctness-package.json` — does the proposal correctly specify the rule? Are §3.1 match conditions precise? Is the §3.4 implementation sketch consistent with §3.1? Does §6 conflict-gate strategy match §3.1? Does §9 migration target the right semver category?
- `review-safety-package.json` — is §5 Bypass surface honestly enumerated? Is the implicit-exclusion set in §5 exhaustive? Could the rule introduce a bypass-by-omission (e.g. waivers without a `reason` field at all — does SCP-R-002 require it?)? Does §4 false-positive surface understate any class?
- `review-completeness-package.json` — does the proposal follow `RULE-TEMPLATE.md` §1–§11 in full? Does it cite the right references? Does §10 mark every open question as `[BLOCKING]` or `[deferrable]`? Does the proposal close the named backlog item ("WP-SCP-022 proposal-queue")?

Lens-package files committed alongside; result + fix-round files alongside.

## Files

- `docs/reviews/rule-proposals/RULE-001-waiver-reason-must-cite-issue-or-pr.md` (NEW) — the proposal.
- `docs/reviews/WP-SCP-022/dispatches/020l/DISPATCH-NOTE.md` (this file).
- `docs/reviews/WP-SCP-022/dispatches/020l/review-{correctness,safety,completeness}-package.json` — R1 lens packages.
- `docs/reviews/WP-SCP-022/dispatches/020l/review-{correctness,safety,completeness}.json` — R1 results.
- `docs/reviews/WP-SCP-022/dispatches/020l/FIX-ROUND-N.md` — per fix-round audit (one per round).
- `STATUS.md` — chain row + backlog amendment.

## Forward-looking — Phase 2 (separate slice)

Phase 2 deliverables (out of scope for 020L):

- `policies/scp_r_004.rego` — rule implementation.
- `policies/tests/scp_r_004_test.rego` — Conftest tests.
- `tests/conflict_gate/scp-r-004/{allow,deny}/` — conflict-gate fixture corpus.
- `tests/workflow/<harness>/` — workflow-selftest harness coverage if needed.
- `version-manifest.json` bump v1.0.1 → v1.1.0.
- `policies/deprecations.yaml` — no entry needed (rule-add at warn baseline; see `policies/VERSIONING.md`).
- Release notes for v1.1.0.
- Tag-cut + GitHub release.

The Phase-2 slice will reference this merged proposal as its canonical specification per `README.md` §3.
