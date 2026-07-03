# WP-SCP-037 §1a — build-stage 3-lens adversarial review dispositions

**Date:** 2026-07-02 · **Stage:** build (over the authored ARCH-006 / SCP-R-013 diff) ·
**Verdict:** ACCEPT with folds (no REJECT / no BLOCKER to the build) ·
**Reviewers:** 3× parallel Sonnet — correctness / safety_bypass / completeness_governance.
Complements the plan-stage review (`plan-r1-dispositions.md`). Every finding verified against the
code (reviewers ran `opa test`, read the templates); each disposition below was applied and re-verified.

**Post-fold gate state:** `opa test` 14/14 PASS · SCP-R-013.rego coverage **100%** · aggregate 94.27%
(≥90 gate) · `opa fmt` clean · `regal` clean (repo disable-flags) · index entry schema-valid · both
`WARN_BASELINE_RULES` sites carry SCP-R-013 · resources.py 25/25 tests · workflow YAML valid.

## Correctness lens

- **CONFIRMED:** 12→14 tests pass; SCP-R-013.rego 100% coverage; vacuous-pass dormancy sound; WARN_BASELINE
  both sites; resources.py rule-specific entry keyed by `ARCH-006` replaces the domain fallback and lists
  services.yml explicitly; index schema-valid; split identity (finding `SCP-R-013` / prose `ARCH-006`)
  consistent incl. remediation_url + scorecard `SCP-R-[0-9]+` filter; all 5 signals structurally sound;
  carve-out reads only the SCP-injected allowlist.
- **C-MINOR-1 (FOLDED):** signal 2 with the `cs != ""` guard let a non-empty contract that OMITS
  `canonical_service` escape both signal 1 (contract non-empty) and signal 2 (cs empty). Dropped the
  `cs != ""` guard → an empty/absent authority in a declared contract now fires signal 2. Added
  `test_scp_r_013_deny_missing_canonical_service`.
- **C-MINOR-2 (FOLDED):** observability `kind` strings `opt_out`/`rule_disabled` deviated from the
  estate template. Harmonised both to `rule-config-disable` (SCP-R-009 convention).

## Safety / bypass lens

- **CONFIRMED (the primary concern):** the carve-out `scp_r_013_is_authoring_source` reads ONLY
  `input.repo_id` + `input.ontology_authoring_allowlist` — never adopter file content; the
  `role: authoring-source` self-assertion in the bypass fixture is invisible to the predicate;
  `test_scp_r_013_no_self_assert_bypass` proves a non-allowlisted self-asserter still DENYs. WARN_BASELINE
  both sites confirmed (cannot block a merge). Dormancy honestly represented. Suppression always emits an
  observability warn. No existing rule weakened.
- **S-MAJOR-1 (FOLDED into the FUP):** the carve-out's safety depends on `input.repo_id` coming from a
  workflow-controlled source. The auth materialiser doesn't inject `repo_id` (no precedent). Added an
  explicit constraint to `FUP-WP-SCP-037-ARCH-006-MATERIALISER-001`: `input.repo_id` MUST be sourced from
  `$GITHUB_REPOSITORY`, never from services.yml — else an adopter spoofs `repo_id: fashion-labelling-agent`
  and escapes signals (3)/(4). (Forward constraint; the Rego is correct today.)
- **S-MINOR-3 (FOLDED):** added `test_scp_r_013_deny_authoring_repo_if_allowlist_absent` proving the
  carve-out fail-CLOSES (FLA markers still DENY when the allowlist is absent) — so an incomplete
  materialiser can't fail-open.
- **S-MINOR-4 (FOLDED into the FUP):** added an atomicity constraint — the materialiser MUST inject the
  allowlist in the SAME envelope as the markers, or FLA gets a false-positive (warn-only) finding.
- **S-MINOR-2 (FOLDED):** same as C-MINOR-2 (kind harmonisation).

## Completeness / governance lens

- **CONFIRMED:** every adjudicate-runbook artefact present — rule prose (DORMANT banner), index entry
  (schema-valid, no applies_to, version 1.1.0→1.2.0), Rego + test, WARN_BASELINE both sites, resources.py
  entry, D-062 row (ACCEPTED, consumes the reservation), PROP-004 retired, STATUS chain entry, materialiser
  FUP in BACKLOG. No silent descope: every WS1a brief bullet (contract fields, 5 signals, carve-out,
  advisory-until-manifest, materialiser deferral) realised. DECISIONS/STATUS/prose consistently represent
  the rule as dormant, not live.
- **G-BLOCKER-1 (FOLDED — this file):** the build-stage R1 evidence file was missing; this document is it.
  Cited in the D-062 row, STATUS entry, and the PR `## R1 evidence` block.
- **G-MAJOR-2 (in progress):** PR + gated-merge are the next steps (post this file).
- **G-MAJOR-3 (verified NON-ISSUE):** `exceptions[]` IS a declared schema field — the ARCH-006 entry
  passes `jsonschema.validate` against `schemas/standards-rule.schema.json` (confirmed).
- **G-MINOR-4/5 (verified NON-ISSUE):** the 1.1.0→1.2.0 bump is this PR's (scaffold PR #232 did not touch
  index.json); the stale-runbook `applies_to` fix landed in #232.

## Net

Two Rego correctness folds (signal-2 empty-authority, kind harmonisation), two new tests (empty-authority,
fail-closed allowlist), two forward trust-boundary constraints pinned to the materialiser FUP, and this
evidence file. No BLOCKER to the build; the rule ships correct, dormant, warn-baseline, bypass-guarded.
