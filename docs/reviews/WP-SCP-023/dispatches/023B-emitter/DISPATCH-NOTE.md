# WP-SCP-023 slice 023B — per-repo scorecard emitter + schema (dispatch note)

**Date:** 2026-05-03
**Tier:** orchestrator-applied (Tier 1) per `feedback_four_tier_dispatch.md` — schema authoring + workflow YAML extension are mechanical translations of WP-SCP-023 plan-doc §5; no design rework required at this scope.
**Files D-041:** ratifies the cross-repo scorecard data shape + opt-in adopter participation model.
**Cuts:** **MINOR bump** v1.1.0 → v1.2.0 per `policies/VERSIONING.md` — adds a new public-surface input (`scorecard-emit: bool` on `workflow_call`) + a new opt-in artifact (`scorecard-emit.json`) + a new schema (`schemas/scorecard-emit.schema.json`). Default-false on the input means existing adopters see no behaviour change; opt-in adopters get the new emit. Per VERSIONING.md MINOR category: "additive features that adopters opt into."

## Rationale — why this slice now

WP-SCP-023 023A plan-doc landed at PR #97 / `7075234` 2026-05-03 with R4 fixpoint. 023B is the natural next slice — implements the per-repo emitter that 023C's aggregator will consume.

## Scope decision — what's IN, what's OUT

### IN

| Item | Rationale |
|---|---|
| `schemas/scorecard-emit.schema.json` (NEW v0.1) | Per plan-doc §5 emitter shape: schema_version, emitted_at, scp_version, repo, ref, commit, verdict, rule_counts (per-rule raw_findings/denies/waived/rule_config_disabled), waivers_aggregate (active_count + by_rule_id + expiring_within_30d), rule_config_aggregate (disabled_rules + expiring_within_30d), signature (placeholder; OIDC attestation is workflow-level, not in-payload). MAJOR-pinned per D-036 + plan-doc §10 Q1 closure. |
| `.github/workflows/policy-check.yml` — new `scorecard-emit: bool` `workflow_call` input (default false) | Opt-in invariant per plan-doc §2 invariant 4. |
| `.github/workflows/policy-check.yml` — new step "Build scorecard emit" gated on `inputs.scorecard-emit == true` | Reads `policy-check-summary.json` + transforms into scorecard-emit shape. Writes to `output/scorecards/scorecard-emit.json`. |
| `.github/workflows/policy-check.yml` — new step "Upload scorecard emit artifact" with `actions/upload-artifact` (gated identically) | Per plan-doc §5 step 2 — aggregator pulls via artifact-download in slice 023C. |
| `tests/scorecard-emit/fixtures/{minimal,full,deny-with-waiver}/{policy-check-summary.json, expected-scorecard-emit.json}` (3 fixtures) | Hand-crafted fixture pairs validating the transformation. |
| `tests/scorecard-emit/test_scorecard_emit_schema.py` (pytest) | Validates each fixture's `expected-scorecard-emit.json` against `schemas/scorecard-emit.schema.json`; validates the transformation produces the expected output. |
| `policies/VERSIONING.md` — add `schemas/scorecard-emit.schema.json` + `scorecard-emit` workflow-input to public-surface enumeration | Future schema changes go through proper semver per D-036. |
| `version-manifest.json` bump v1.1.0 → v1.2.0 | MINOR per VERSIONING.md additive-opt-in category. |
| `docs/releases/v1.2.0.md` (NEW) | Release notes for v1.2.0 — names the new opt-in input + emit artifact + schema; references plan-doc + D-041. |
| `docs/DECISIONS.md` D-041 ratification row | Per plan-doc §9 reservation + DECISIONS.md header note. Defines the data shape + opt-in posture in canonical form. |
| `STATUS.md` — 023B chain row | Convention. |

### OUT

| Item | Rationale |
|---|---|
| OIDC attestation generation in the emitter step | Per plan-doc §5 step 3 + D-042 (deferred to slice 023C — the aggregator is the verification side). 023B emits the artifact; 023C verifies via `gh attestation verify --signer-workflow`. The artifact is already covered by Actions Artifact Attestation when emitted by SHA-pinned reusable workflows (the platform-level attestation; not an in-emit signature). |
| `.scp/rule-config.yaml` expiry ramp warning emission | Workflow-side warning already exists in `release-gate.yml`. The scorecard's `rule_config_aggregate.expiring_within_30d` count surfaces the same data. No new emission. |
| Aggregator side (023C scope) — workflow, registry, central index | Out of scope for 023B. |
| Markdown report generator (023D scope) | Out of scope. |
| MCP method `scp.consult_scorecard` (023D scope) | Out of scope. |
| Adopter onboarding to opt-in registry (023E scope) | Out of scope. |
| ADOPT-001 §13 onboarding section | Lands in 023D when adopters can actually use the surface. |

## Tier-justification

Orchestrator-applied + 3-lens R1 (per `feedback_four_tier_dispatch.md`). The implementation is mechanical translation: plan-doc §5 emitter shape → schema; plan-doc §5 step 2 → workflow YAML; plan-doc §5 invariants → fixture validations. No design rework needed at this scope. If R1 surfaces a CRIT/MAJ requiring design rework (e.g. schema shape doesn't survive contact with real `policy-check-summary.json` data), escalate to Codex executor for fix-round-2.

## Slice acceptance

- [ ] **(i) `schemas/scorecard-emit.schema.json`** — new schema with `schema_version` `const: "0.1"`, all per-plan-doc §5 fields covered, `additionalProperties: false`.
- [ ] **(ii) `.github/workflows/policy-check.yml`** — `scorecard-emit` `workflow_call` input added (default false); gated step "Build scorecard emit" + "Upload scorecard emit artifact" added; default-false ensures no behaviour change for existing adopters.
- [ ] **(iii) Per-rule rule_counts derivation** — for each `SCP-R-NNN` in the rule library, count raw_findings (from policy-check-summary findings), denies (effective_denies after waiver suppression), waived (waivers_applied with matching rule_id), rule_config_disabled (boolean from disabled_rules).
- [ ] **(iv) waivers_aggregate derivation** — read sibling `output/findings/waivers.json` if present; count active waivers (not expired); group by rule_id; count expiring_within_30d (expires_at within next 30 days).
- [ ] **(v) rule_config_aggregate derivation** — read sibling `.scp/rule-config.yaml` if present; list disabled_rules with `disable: true`; count expiring_within_30d.
- [ ] **(vi) NO waiver content emitted** — invariant 2 of plan-doc. Verify the schema explicitly does NOT include `reason`, `approved_by`, `waiver_id` strings.
- [ ] **(vii) 3 fixture pairs validated** — minimal (no waivers, no rule-config, allow verdict), full (multiple waivers + rule-config disable, allow verdict), deny-with-waiver (raw deny suppressed by waiver, allow verdict). Each fixture's expected emit validates against the schema.
- [ ] **(viii) Pytest passes** — `pytest tests/scorecard-emit/`.
- [ ] **(ix) Pre-push wrapper passes** — `scripts/scp-pre-push-verify.sh` green.
- [ ] **(x) `policies/VERSIONING.md`** — schemas/scorecard-emit.schema.json + scorecard-emit input added to public-surface scope enumeration.
- [ ] **(xi) `version-manifest.json`** — v1.1.0 → v1.2.0 (MINOR).
- [ ] **(xii) `docs/releases/v1.2.0.md`** — release notes.
- [ ] **(xiii) `docs/DECISIONS.md` D-041 ratification row** — defines data shape + opt-in posture.
- [ ] **(xiv) `STATUS.md` 023B row** in "Today's chain (2026-05-03)".
- [ ] **(xv) Adversarial review reaches fixpoint** — 3-lens R1 → recurse to fixpoint.
- [ ] **(xvi) PR + CI + operator-merge per D-040.**
- [ ] **(xvii) Tag cut v1.2.0** post-merge per VERSIONING.md tag-cut procedure.

## Risk surface

1. **Schema drift between v0.1 and v1.0.** Plan-doc §10 Q1 commits to MAJOR-pinned. v0.1 schema can be amended freely until first adopter opts in (FLA pilot at slice 023E). Documented in §10 Q1.
2. **`output/scorecards/scorecard-emit.json` path collision** with adopter's existing files. Path is unlikely to collide (no adopter currently has `output/scorecards/`); if collision detected at adopter onboarding, opt-out per invariant 4.
3. **Default-false workflow input** must NOT break existing adopters' wrappers (which omit the input entirely). Verified by GitHub Actions workflow_call semantics: omitted inputs use the default. Tested in workflow-selftest harness.
4. **Per-rule rule_counts derivation depends on policy-check-summary.json shape.** If a future SCP-R-NNN rule emits findings differently (e.g. without a clean `rule_id` field), the aggregation could miscount. Mitigation: schema validation at emit time; future rule additions pass through SCP-R-NNN schema-conformance tests.
5. **Waiver content leakage via `expiring_within_30d` count.** Per plan-doc R-023-01 — acknowledged; mitigation deferred to slice 024 if material.

## R1 review

3× parallel Sonnet R1 (correctness / safety_bypass / completeness_governance). Recurse to fixpoint.

## Files

### Modified
- `.github/workflows/policy-check.yml` — `scorecard-emit` input + 2 new steps.
- `policies/VERSIONING.md` — public-surface enumeration extension.
- `version-manifest.json` — v1.1.0 → v1.2.0.
- `docs/DECISIONS.md` — D-041 row + Last Updated.
- `STATUS.md` — 023B chain row.

### Added
- `schemas/scorecard-emit.schema.json` (NEW v0.1).
- `tests/scorecard-emit/test_scorecard_emit_schema.py` (NEW).
- `tests/scorecard-emit/fixtures/{minimal,full,deny-with-waiver}/{policy-check-summary.json, expected-scorecard-emit.json}` (NEW × 6 files).
- `docs/releases/v1.2.0.md` (NEW).
- `docs/reviews/WP-SCP-023/dispatches/023B-emitter/{DISPATCH-NOTE.md, review-*-package.json, review-*.json, FIX-ROUND-N.md}`.

## Forward-looking

- **Slice 023C** picks up here — the aggregator workflow consumes the artifacts emitted by this slice.
- **D-042** (023C) ratifies the aggregator + `gh attestation verify --signer-workflow` constraint.
- **Tag cut v1.2.0** post-merge.
