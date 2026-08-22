# WP-SCP-037 §1b/c/d — build-stage 3-lens adversarial review dispositions

**Date:** 2026-07-03 · **Stage:** build (over the SVC-ADOPT-001 / SVC-005 / ADOPT-001 §12.7.0 diff) ·
**Verdict:** ACCEPT with folds (no REJECT; no correctness/safety BLOCKER or MAJOR) ·
**Reviewers:** 3× parallel Sonnet — correctness / safety_bypass / completeness_governance.

**Batching (GOV-004 note-and-justify):** §1b (SVC-ADOPT-001), §1c (SVC-005), §1d (ADOPT-001 §12.7.0) are
all **advisory-consult prose, no Rego, no `policies/`/`src/`/`tests/` change, same family** (the estate
bring-up trio). Authored in one PR with one 3-lens R1 covering all three — the substantive adversarial
protection, without ceremonial per-prose-rule review (GOV-005 no-governance-theatre). All three reviewers
independently judged the batching legitimate.

**Post-fold gate state:** service-lifecycle index 6/6 rules schema-valid, v1.1.0→1.2.0, no `applies_to`;
JSON parses; no bare `§12.7` refs left in SVC-ADOPT-001; ADOPT-001 §12.7.0 present; all cross-refs resolve.

## Correctness lens — no BLOCKER/MAJOR; 3 MINOR folds

- **CONFIRMED:** both index entries schema-valid, no applies_to, version bump correct; 9 touchpoints match
  `reference_estate_canonical_sources.md` exactly; SVC-005 tunnel recipe accurate (UUID `6d21b62e-…`,
  ingress-before-404, CNAME to cfargotunnel.com); §12.7.0 ceremony order + merge-before-flip correct;
  §12.7.1/12.7.3/12.7.16a references all resolve; no Rego; all cross-refs exist.
- **C-D1 (FOLDED):** SVC-ADOPT-001 index signal omitted SVC-002 (health path) → now `(see SVC-001/SVC-002/SVC-003)`.
- **C-D2 (FOLDED in my new text; pre-existing left):** §12.7.0 step 3 said `policy-check.yml`; the onboard
  scaffolders + SCP-self use `policy-check-wrapper.yml` → my step-3 now says `policy-check-wrapper.yml`.
  The stale name in the PRE-EXISTING §12.7.1 (7 other occurrences repo-wide) is NOT changed here — a
  separate pre-existing inconsistency, noted below.
- **C-D3 (FOLDED):** three `§12.7` refs in SVC-ADOPT-001 → `§12.7.0` (the specific ceremony subsection).

## Safety / bypass lens — no BLOCKER/MAJOR; 4 MINOR folds

- **CONFIRMED (the two primary risks clean):** enforcement-posture banners honest (ADVISORY-CONSULT, no
  Rego); the §12.7.0 merge-before-flip guard is correctly ordered (flip AFTER merge, names the Recommender
  half-apply, directs to the guarded `enable-required-check.sh` not a bare flip). App ID 3795720 correctly
  non-secret; no key value leaked; SVC-ADOPT-001 does not over-reach cross-repo registries (LINKAGE-not-
  VALUES stated); SVC-005 no-prod correct.
- **S-D1 (FOLDED):** §12.7.0 step 4 now flags `--preserve-existing-contexts` as brownfield-only (greenfield
  omits) + the silent-remove hazard, cross-referencing §12.7.3.
- **S-D2 (FOLDED):** §12.7.0 step 5 now qualifies the invocation-log lands in the SCP repo (a PR on
  `standards-control-plane`), NOT the adopter's own repo.
- **S-D4 (FOLDED):** SVC-ADOPT-001 touchpoint 4 now names the **check-run** `policy-check / scp/policy-check`
  (NOT the commit-status `scp/policy-check-readback`), per §12.7.3.
- **S-D3 (NOT folded — pre-existing, out of scope):** §12.7.10's `secrets: inherit` section opens "MUST NOT"
  then amends to "required for the caller-job" without a consolidated summary box. This PRE-DATES WP-SCP-037;
  my §12.7.0 does not route readers to §12.7.10 (it references §12.7.1/.3/.16a). Left as a pre-existing
  doc-clarity item rather than expanding this PR into a section with its own amendment history.

## Completeness / governance lens — 1 expected BLOCKER + 1 MAJOR (folded)

- **CONFIRMED-COMPLETE:** all artefacts present — both rule prose, both index entries, ADOPT-001 §12.7.0,
  D-063/064/065 (ACCEPTED, referencing PROP-005/006), PROP-005/006 retired, STATUS chain entry, BACKLOG row
  updated. Every §1b/1c/1d brief bullet covered; §1d ENHANCES ADOPT-001 (not a new standard). No silent
  descope. Batching justified + recorded.
- **G-BLOCKER-1 (FOLDED — this file):** the build-stage R1 evidence file was missing; this document is it.
- **G-MAJOR-2 (FOLDED):** the two rule prose files lacked explicit `## Signals` / `## Rationale` sections
  (the runbook cites GOV-001's format; the estate itself varies — ARCH-005 uses `## Why this rule exists` /
  `## Conformance`). Added explicit `## Signals` (pointing to the index; advisory rules carry no enforced
  prose signals) + `## Rationale` sections to BOTH SVC-ADOPT-001 and SVC-005.

## Pre-existing items surfaced (not fixed here — flagged for a future docs pass)

- §12.7.1 names the adopter wrapper `policy-check.yml` while the onboard scaffolders + SCP-self use
  `policy-check-wrapper.yml` (7 stale occurrences repo-wide).
- §12.7.10 `secrets: inherit` needs a consolidated "current position (v2)" summary box.
Both are pre-existing, low-risk, and outside the WP-SCP-037 §1b/c/d scope.

## Net

Zero correctness/safety BLOCKER or MAJOR. One expected completeness BLOCKER (this evidence file) + one MAJOR
(prose section format) folded. Seven MINOR folds applied; two pre-existing doc items flagged. The three
advisory standards ship accurate, schema-valid, honestly advisory, with the critical merge-before-flip
ceremony correct.
