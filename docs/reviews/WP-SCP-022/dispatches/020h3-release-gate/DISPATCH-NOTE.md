# WP-SCP-022 slice 020H.3 — release-gate (dispatch note)

**Date:** 2026-05-01
**Tier:** orchestrator-applied (Tier 1 only)
**Closes:**
- WP-SCP-022 020H.1 TF-020H1-001 (`enforce_release_gate` workflow).
- WP-SCP-022 020C.1 TF-005 (release-tag-time refusal of expired rule-config).

**Slice naming.** "020H.3" follows the post-Threshold-A dot-N
convention (mirroring 020H.1, 020H.2 — see ADOPT-001 §12.7.13's
naming clarification). NOT the same as the already-merged "020H
**part** 3" (federation-primitive adopter integration appendix,
PR #75). The dispatches directory uses the suffix `020h3-release-gate`
to avoid collision with the existing `dispatches/020h3/` (which
holds the 020H part 3 review artefacts).

## Justification for not invoking Codex executor

Per `feedback_four_tier_dispatch.md` in-line escalation guidance.
The slice's surface is **3 new files + 1 doc update + 1 STATUS row**:

- `policies/deprecations.yaml` — empty initial state (`deprecations: []`).
- `schemas/deprecations.schema.json` — JSON Schema Draft 2020-12.
- `.github/workflows/release-gate.yml` — new workflow with two checks
  (deprecation ramp + expired rule-config).
- `policies/VERSIONING.md` — extends "Deprecation ramp" section with
  the machine-enforcement subsection.
- `docs/adoption/ADOPT-001-project-onboarding.md` §12.7.7 — adds
  `SCP-EREL-001` row.

All surfaces are policy-text or YAML/JSON authorship + a workflow
that uses well-established patterns (pyyaml + jsonschema, the same
deps the existing policy-check.yml workflow uses). Codex Tier 3
dispatch overhead would exceed the marginal benefit; orchestrator-
applied + R1 × 3 is the right posture.

## Slice acceptance

- [x] **(i) `policies/deprecations.yaml` empty initial state.**
  v1.0.0 ships with no deprecations announced; the file documents
  the schema-conformant empty shape.
- [x] **(ii) `schemas/deprecations.schema.json` — Draft 2020-12.**
  Required fields: `surface_kind`, `surface_id`, `announced_at`,
  `announced_release`, `target_release`, `migration_pointer`.
  Optional `rationale`. Pattern-validates `v<MAJOR>.<MINOR>.<PATCH>`
  on the two release fields. `additionalProperties: false`.
- [x] **(iii) `.github/workflows/release-gate.yml`.** Triggers on
  `push: tags: ['v*']` (live enforcement) + `workflow_dispatch:`
  with a `dry_run_tag` input (operator pre-flight). Steps:
  - Checkout repo (pinned actions/checkout SHA matching policy-check.yml).
  - Install pyyaml + jsonschema (lockfile-pinned versions matching policy-check.yml's existing pip install).
  - Resolve candidate tag (workflow_dispatch input vs push ref); validate semver shape.
  - Validate `policies/deprecations.yaml` against schema (per-error annotations on schema failure).
  - Check deprecation-ramp invariant: for each entry where `target_release == candidate`, refuse if `announced_release` major matches but minor delta < 1; allow if announced is exactly one major behind (major bump IS the removal vehicle); refuse if announced is more than one major behind (structural inconsistency).
  - Check expired rule-config (SCP-self): if `.scp/rule-config.yaml` exists, refuse the tag-cut for any `disable: true` entry with `expires_at < today`.
  - Verdict step: print ALLOW + tag + mode.
  All refusals emit `::error::title=SCP-EREL-001`; backdating
  warnings emit `::warning::title=SCP-EREL-001-warn`. Concurrency
  group `release-gate-${{ github.event_name == 'workflow_dispatch' && inputs.dry_run_tag || github.ref }}`
  with `cancel-in-progress: false` serialises overlapping
  invocations on the same candidate tag (updated per fix-round-1
  COR-MIN-003 + nit-SAFE-007).
- [x] **(iv) `SCP-EREL-001` annotation registered** in ADOPT-001
  §12.7.7 error-code table — adopter-side relevance is "none directly"
  (this fires on SCP source's own tag pushes only; adopters interact
  with the same invariants via SCP-E007 + deprecation `::warning::`s).
- [x] **(v) VERSIONING.md cross-references** the new file + workflow
  in both the "Deprecation ramp" section (with the
  `policies/deprecations.yaml` write step now part of the doctrinal
  ramp) and the "References" section (3 new entries).
- [x] **(vi) STATUS.md updates.** TF-005 + TF-020H1-001 marked
  ✅ closed in 020H.3; 020H.3 IN FLIGHT row added to Post-Threshold-A
  backlog; "Last updated" bumped.

## Out of scope / forward-looking — TF-020H3rg-NNN tracked-forward items

Per fix-round-1 closure of R1 CRIT-SAFE-001 (post-tag observer
limitation) + COMP-MIN-002 (auto-defer disposition), every "future
work" item is now a named TF-020H3rg-NNN entry in `STATUS.md`
"Tracked-forward items from 020H.3 (release-gate)":

- **TF-020H3rg-001** — PR-time deprecation-announcement linter
  (cross-checks `deprecated` warnings vs `policies/deprecations.yaml`
  entries in PR diff).
- **TF-020H3rg-002** — `pip install --require-hashes` for
  `policy-check.yml` + `release-gate.yml` pyyaml/jsonschema installs.
- **TF-020H3rg-003** — Auto-open `release-gate-violation` issue on
  push:tags failure (the post-tag observer's missing follow-up step;
  per the canary-replay.yml gh-issue-create pattern).

Out-of-scope without TF (resolved-as-not-needed):

- **Adopter-side rule-config expiry at release-tag time** — adopters
  don't cut SCP release tags; their PR-time enforcement is SCP-E007
  via `policy-check.yml` (already shipped at 020C.1). The release-gate
  workflow's expired-config check is SCP-self only.
- **Release-notes auto-generation** from `policies/deprecations.yaml`
  entries scheduled for the candidate tag — release notes are
  operator-authored at 020H part 1 / 020H part 2 cadence; no
  meaningful gain from automation at v1.0.0 cadence.

## Architectural framing — IMPORTANT (added in fix-round-1)

Per R1 CRIT-SAFE-001 closure, the workflow's two operating modes
are explicit:

1. **Dry-run pre-flight (workflow_dispatch).** The pre-emptive
   enforcement path. Operators MUST run `gh workflow run release-gate.yml -f dry_run_tag=<tag>`
   BEFORE pushing the tag. Per VERSIONING.md "Tag-cut procedure".
2. **Post-tag observer (push:tags).** GitHub Actions fires on
   `push:tags` AFTER the tag exists on the remote. The workflow
   annotates the bad tag with `SCP-EREL-001` and (per TF-020H3rg-003)
   will open a `release-gate-violation` issue. The bad tag is
   immutable per D-030; recovery is via a corrected v<X>.<Y+1>.0
   per the new VERSIONING.md "Bad-tag recovery procedure" section.

## R1 review

3× parallel Sonnet R1 review (correctness / safety_bypass /
completeness_governance). Recurse to fixpoint per
`feedback_recursive_adversarial_review.md`.

## Files

- `policies/deprecations.yaml` — empty initial register.
- `schemas/deprecations.schema.json` — Draft 2020-12 validator.
- `.github/workflows/release-gate.yml` — tag-cut gate workflow.
- `policies/VERSIONING.md` — "Deprecation ramp" + "References" extended.
- `docs/adoption/ADOPT-001-project-onboarding.md` — §12.7.7 SCP-EREL-001 row.
- `STATUS.md` — TF-005 + TF-020H1-001 closed; 020H.3 IN FLIGHT row.
- `docs/reviews/WP-SCP-022/dispatches/020h3-release-gate/DISPATCH-NOTE.md` — this file.
