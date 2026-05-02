# WP-SCP-022 slice 020P — RULE-001 Phase 2: implement SCP-R-004 + cut v1.1.0 (dispatch note)

**Date:** 2026-05-02
**Tier:** orchestrator-applied (Tier 1) per `feedback_four_tier_dispatch.md` in-line escalation guidance — see "Tier-justification" below.
**Closes:** Phase 2 of slice 020L (RULE-001 / SCP-R-004 implementation per merged proposal at PR #89, commit `25db685`); also closes **TF-020L-002** (RULE-TEMPLATE.md §5 residual-bypass guidance) + **TF-020L-003** (README.md §3 "new domain" definition) — both natural-adjacent process-doc fixes since this slice IS the next RFC-process-touching slice and we just learned both lessons.
**Cuts:** **v1.1.0** (MINOR bump from v1.0.1) per `policies/VERSIONING.md` "new rule at warn → MINOR".

**Slice naming.** Letter `P` is the next free post-Threshold-A letter after 020N (skipping `O` per repo convention to avoid O/0 ambiguity). `020P` is a substantive standalone slice introducing a new SCP-R rule + cutting a new MINOR version, distinct from the H-series hardening pattern (which has been about post-v1.0.0 hardening, not new rules). Calling it `020P` rather than `020L Phase 2` keeps the per-letter slice convention intact and lets `020L` remain dedicated to the merged proposal as its canonical-spec PR.

## Rationale — why this slice now

The user requested Phase 2 immediately after slice 020L closed. Strategic considerations:

1. **020L is fresh in the repo and reviewer mind.** Implementing the rule while the proposal text is the most-recently-merged document maximises spec-implementation parity. A delay would risk drift between RULE-001 and `policies/scp_r_004.rego`.
2. **TF-020L-002 + TF-020L-003 are best closed in the same slice as their teaching example.** Both TFs were filed because the RULE-001 dogfood surfaced general lessons the framework now needs to encode. Closing them in 020P (the slice that implements the very rule that taught the lessons) is the cleanest causal chain.
3. **v1.1.0 cut is the first MINOR bump on the federation primitive.** Exercising the tag-cut + release-gate dry-run + Renovate cascade BEFORE estate cascade (WP-SCP-024) begins is the smaller-blast-radius validation moment.

## Scope decision — what's IN, what's OUT

| Item | Disposition | Rationale |
|---|---|---|
| `policies/scp_r_004.rego` (rule implementation) | **IN** | Phase 2 primary deliverable. |
| `policies/tests/scp_r_004_test.rego` (Conftest tests) | **IN** | ~14 cases per RULE-001 §8.1. |
| `tests/conflict_gate/fixtures/SCP-R-004/{allow,deny}/` (fixtures) | **IN** | 1 allow + 1 deny, matching SCP-R-001/002 pattern. |
| `tests/conflict_gate/test_conflict_gate.py` (Python evaluator wiring) | **IN** | Add `_evaluate_scp_r_004_python` + dispatch in `_run_python_audit`. |
| `.github/workflows/policy-check.yml` (warn-baseline rendering) | **IN** | Render SCP-R-004 deny output as `::warning::` instead of `::error::`. Hardcoded `WARN_BASELINE_RULES = {"SCP-R-004"}` set inline; data-driven manifest filed forward as TF-020P-NNN if more warn-baseline rules land. |
| `version-manifest.json` (v1.0.1 → v1.1.0 bump) | **IN** | MINOR bump per VERSIONING.md. |
| `RELEASE_NOTES.md` (or equivalent) for v1.1.0 | **IN** | Per VERSIONING.md "Tag-cut procedure" + per RULE-001 §11. |
| `docs/adoption/ADOPT-001-project-onboarding.md` §12.7.X (adopter response) | **IN** | Per RULE-001 §9 "ADOPT-001 maintenance"; new §12.7.14 subsection. |
| `docs/reviews/rule-proposals/RULE-TEMPLATE.md` §5 residual-bypass note | **IN** | Closes TF-020L-002. |
| `docs/reviews/rule-proposals/README.md` §3 "new domain" definition | **IN** | Closes TF-020L-003. |
| Tag-cut + GitHub release | **IN** (operator-driven) | Per VERSIONING.md Tag-cut procedure. |
| TF-020L-001 disposition (Unicode-whitespace observation) | **IN** (mostly observe + decide) | Per TF-020L-001 closure path. |
| `policies/deprecations.yaml` entry | **OUT** | Rule-add at warn baseline does not trigger a deprecation per VERSIONING.md. |
| TF-020N-001 (`conflict-gate.yml` `id-token: write` narrowing) | **OUT** | Different workflow + supply-chain concern; bundling would scope-creep. |
| TF-020H4-001 (`replay-canary.sh` registry tuple extension) | **OUT** | Different concern (canary observability); not adjacent to this slice. |
| TF-020H3rg-004 (release-gate auto-close on corrective tag) | **OUT** | Different workflow (release-gate); not adjacent. |
| TF-020H4-003 (`replay-canary.sh` error-handling) | **OUT** | Different concern; pre-exists. |
| New `policies/rule-baselines.yaml` data-driven manifest | **OUT** | Architectural addition; deferred until 2nd warn-baseline rule lands. Hardcoded set is sufficient at v1.1.0. |
| `scp_r_004_remediation_url` permalink-pinning (per COMP-NIT-001) | **OUT** | Cosmetic; matches SCP-R-001/002/003 `/blob/main/` pattern; consistent. |

## Tier-justification (why orchestrator-applied + 3-lens R1, NOT Codex executor)

Per `feedback_four_tier_dispatch.md` in-line escalation guidance, this slice is borderline between orchestrator-applied and Codex-executor.

**Arguments for Codex executor:** Rego rule + tests + workflow YAML edit + Python adapter wiring + multiple file additions. Substantial new code surface.

**Arguments for orchestrator-applied:**
- The Rego implementation is **substantially specified by RULE-001** §3.4 sketch (post-fix-round-1). Phase 2's Rego is a near-1:1 expansion of the sketch with full record shapes.
- The Conftest tests follow `policies/tests/scp_r_002_test.rego` shape exactly (verified by reading that file as ground).
- The conflict-gate fixtures follow `tests/conflict_gate/fixtures/SCP-R-002/{allow,deny}/` shape exactly.
- The workflow integration is small: a dozen lines added to the existing "Render deny annotations" step.
- The version-manifest bump + release notes are straightforward.
- The TF-020L-002 + TF-020L-003 closures are one-paragraph each.

**Decision: orchestrator-applied + 3-lens R1.** The implementation surface is large but mostly mechanical translation from spec → code. Codex executor adds dispatch overhead without commensurate value-add when the design is fully pre-specified. Per-file inline-author + 3-lens recursive-adversarial review is the right posture (symmetric with 020M / 020N / 020L dispatch notes).

If R1 surfaces a CRIT/MAJ that requires non-trivial design rework, escalate to Codex executor for fix-round-2.

## Slice acceptance

- [ ] **(i) Rule implementation.** `policies/scp_r_004.rego` with own `scp_r_004_is_waiver_payload` + `scp_r_004_has_nonempty_string` + `scp_r_004_has_url` predicates; `scp_r_004_raw_findings` set; `deny` rule; two `warn` rules (waiver-suppression + rule-config-disable observability). Annotation message includes `rule_id` + `finding_id` from the entry + 80-char-truncated `reason` per RULE-001 §3.3.
- [ ] **(ii) Conftest tests.** `policies/tests/scp_r_004_test.rego` covering ~14 cases per RULE-001 §8.1: empty array; single-with-github-issue-url; single-with-non-github-url; multi-all-with-urls; single-no-url; multi-mixed; no-op object/string/null inputs; no-op missing/empty `reason` (SCP-R-002 covers); URL-bearing meta-waiver suppression; rule-config disable suppression; expired-waiver fail-closed; expired rule-config still-suppresses-for-one-release.
- [ ] **(iii) Conflict-gate fixtures.** `tests/conflict_gate/fixtures/SCP-R-004/allow/{input.json, expected-verdict.json}` (single waiver with URL — should not fire) + `.../deny/{input.json, expected-verdict.json}` (single waiver without URL — should fire).
- [ ] **(iv) Conflict-gate adapter wiring.** `tests/conflict_gate/test_conflict_gate.py` `_run_python_audit` adds `if rule_id == "SCP-R-004": return _evaluate_scp_r_004_python(...)`; new `_evaluate_scp_r_004_python` function with `URL_PATTERN = re.compile(r"https?://\S+")`.
- [ ] **(v) Workflow warn-baseline rendering.** `.github/workflows/policy-check.yml` "Render deny annotations and enforce threshold" step amended: `WARN_BASELINE_RULES = {"SCP-R-004"}` set; warn-baseline denies emit `::warning::` instead of `::error::` AND are excluded from `effective_denies` so the threshold check does not trip.
- [ ] **(vi) version-manifest.json bump.** `version` 1.0.1 → 1.1.0; `minor` 1.0 → 1.1; `released_at` 2026-05-02; `_comment` updated if necessary.
- [ ] **(vii) Release notes for v1.1.0.** `RELEASE_NOTES.md` (or `docs/releases/v1.1.0.md`) — name SCP-R-004 at warn baseline + adopter-side response options (link to ADOPT-001 §12.7.14) + 90-day transition window per RULE-001 §9 + reference to `docs/reviews/rule-proposals/RULE-001-waiver-reason-must-cite-issue-or-pr.md` as canonical spec.
- [ ] **(viii) ADOPT-001 §12.7.14.** New subsection "Adopter response to SCP-R-004 warn annotations" — three response options (gradual amendment / rule-config disable / bulk cleanup PR).
- [ ] **(ix) RULE-TEMPLATE.md §5 residual-bypass note (TF-020L-002 closure).** One-paragraph addition pointing at RULE-001 §5 case 5 as worked example.
- [ ] **(x) README.md §3 "new domain" definition (TF-020L-003 closure).** Definition: new top-level input schema OR no-existing-SCP-R counterpart. Same-input-schema additions are same-domain.
- [ ] **(xi) Adversarial review reaches fixpoint.** 3-lens R1 → recurse R2 / R3 until no new CRIT/MAJ on a complete cycle. Lens packages + result JSONs + FIX-ROUND-N.md alongside this DISPATCH-NOTE.
- [ ] **(xii) PR opens + operator-merge per D-040.** PR description names the deliverables + the v1.1.0 cut intent. CI green prerequisite. No `scp-rule-proposal` label (this is a CODE PR, not a rule-RFC PR).
- [ ] **(xiii) Tag-cut v1.1.0.** Per VERSIONING.md Tag-cut procedure: dry-run release-gate → push tag → publish GitHub release → Renovate cascade follows.
- [ ] **(xiv) STATUS.md backfill + memory + continuation prompt.** Close-out commit / PR.

## Risk surface

1. **Workflow warn-baseline rendering may misfire on existing SCP-R-001/002/003 deny outputs.** Mitigation: the `WARN_BASELINE_RULES` set is a strict allow-list; only SCP-R-004 enters the warn-baseline branch. SCP-R-001/002/003 continue to render as `::error::`. Verified by reading the existing deny-annotation step before editing.
2. **Conflict-gate flap on Unicode whitespace (TF-020L-001).** Mitigation: the conflict-gate fixtures (per (iii)) are ASCII-only — no Unicode whitespace path is exercised in v1.1.0. Phase-2 monitor closes TF-020L-001 as no-op if no SCP-E005 fires during the warn-baseline observation window.
3. **v1.1.0 release-gate dry-run may surface deprecation-ramp false positives.** SCP-R-004 is a rule-add at warn — no deprecation. `policies/deprecations.yaml` remains empty (per (vi)). Release-gate should pass dry-run cleanly.
4. **Renovate preset cascade may bump adopter pins without their explicit consent.** This is the existing Renovate behaviour and is intentional — adopters opted into the preset at federation onboarding. v1.1.0's warn-baseline SCP-R-004 cannot break adopter merges (warn ≠ deny). Release notes name the rule + transition options upfront.
5. **Hardcoded `WARN_BASELINE_RULES` set is a code-coupling risk** if a 2nd warn-baseline rule lands without updating the set. Mitigation: Phase-2 documents the data-driven manifest as TF-020P-001 (file in this slice's risk surface for future-PR context). The single-rule case at v1.1.0 is acceptable.

## R1 review

3× parallel Sonnet R1 review (correctness / safety_bypass / completeness_governance). Recurse to fixpoint per `feedback_recursive_adversarial_review.md`. Lens packages + result JSONs + FIX-ROUND-N.md alongside this file.

Review surface focuses:
- **Correctness.** Does `scp_r_004.rego` match RULE-001 §3.4 sketch + §3.3 annotation contract? Are Conftest tests exhaustive against §8.1? Does the conflict-gate Python evaluator match the Rego semantics on the fixture corpus? Does the workflow warn-baseline rendering actually emit `::warning::` and exclude SCP-R-004 from threshold trip?
- **Safety/bypass.** Does the warn-baseline rendering create any new bypass surface (e.g. could an adopter hide a real deny by aliasing their rule to SCP-R-004)? Is the `WARN_BASELINE_RULES` set a complete + intentional allow-list? Does the meta-waiver test correctly exercise the SAFE-MIN-001 closure (URL-bearing meta-waiver)?
- **Completeness.** Does v1.1.0 release notes cover everything an adopter needs? Does ADOPT-001 §12.7.14 give adopters concrete migration options? Does the slice acceptance checklist actually cover all RULE-001 §9 deliverables? Does TF-020L-002 + TF-020L-003 closure actually solve the framework gaps as documented in the R2 fix-round-2 commits?

## Files

- `policies/scp_r_004.rego` (NEW).
- `policies/tests/scp_r_004_test.rego` (NEW).
- `tests/conflict_gate/fixtures/SCP-R-004/allow/{input.json, expected-verdict.json}` (NEW).
- `tests/conflict_gate/fixtures/SCP-R-004/deny/{input.json, expected-verdict.json}` (NEW).
- `tests/conflict_gate/test_conflict_gate.py` — `_evaluate_scp_r_004_python` + dispatch.
- `.github/workflows/policy-check.yml` — "Render deny annotations" step warn-baseline branch.
- `version-manifest.json` — v1.0.1 → v1.1.0.
- `RELEASE_NOTES.md` (or `docs/releases/v1.1.0.md`) — NEW or appended.
- `docs/adoption/ADOPT-001-project-onboarding.md` — new §12.7.14.
- `docs/reviews/rule-proposals/RULE-TEMPLATE.md` — §5 residual-bypass note.
- `docs/reviews/rule-proposals/README.md` — §3 "new domain" definition.
- `docs/reviews/WP-SCP-022/dispatches/020p/DISPATCH-NOTE.md` (this file).
- `docs/reviews/WP-SCP-022/dispatches/020p/review-{correctness,safety,completeness}-package.json` — R1 lens packages.
- `docs/reviews/WP-SCP-022/dispatches/020p/review-{correctness,safety,completeness}.json` — R1 results.
- `docs/reviews/WP-SCP-022/dispatches/020p/FIX-ROUND-N.md` — per fix-round audit.
- `STATUS.md` — chain row + recent-decisions row + Tracked-forward update + Post-Threshold-A backlog amendment.

## Forward-looking

- **TF-020P-001 candidate** (filed at slice close if warranted): data-driven `policies/rule-baselines.yaml` manifest + `schemas/rule-baselines.schema.json` to replace the hardcoded `WARN_BASELINE_RULES` set in policy-check.yml. Closure path: file when a 2nd warn-baseline rule lands.
- **v1.2.0+** earliest plausible promotion of SCP-R-004 from warn to deny default — would require a separate RFC-002 proposal per `README.md` §When to file.
