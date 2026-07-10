# ARCH-006 materialiser — plan-stage 3-lens R1 dispositions

**Date:** 2026-07-10 · **Stage:** plan (pre-build) · **Verdict:** ACCEPT with folds — no mechanism-level
defect; the eval/envelope/warn-baseline/RED-first design is sound, but the v1 draft's extraction logic
and scope had real gaps. All folded into plan v2 (`ARCH-006-materialiser-plan.md`). **Do not build until
the operator seeds the dispatch;** the two safety BLOCKERs (repo_id identity, selftest override) are
fixed in v2 and MUST be carried into the actual code.
**Reviewers:** 3× Sonnet — correctness / safety_bypass / completeness_governance, each vs. the real
WP-SCP-028 auth materialiser + SCP-R-013.rego.

## Safety / bypass lens
- **S-BLOCKER-1 (FOLDED):** `repo_id` basename-only (`split("/")[-1]`) let any org's repo *named*
  `fashion-ontology-service` win the carve-out. → v2 uses full `owner/repo`; allowlist org-qualified
  (`jrnb2024/…`). Matches the auth step's full-identity anchor.
- **S-BLOCKER-2 (FOLDED):** v1 contradicted itself on the selftest `repo_id` override and didn't draft
  it. → v2 strikes the contradiction and drafts the `SCP_ONTOLOGY_REPO_ID` seam, identity-gated to
  `selftest_mode AND GITHUB_REPOSITORY == jrnb2024/standards-control-plane` (mirrors `auth-canonical-source`).
- **S-MAJOR-3 (FOLDED → FUP):** `EMBEDDED_BASENAMES` exact-match is evadable by rename
  (`ontology_complete.yml`). → `FUP-WP-SCP-037-ARCH-006-MARKER-TIGHTENING`; warn-baseline ⇒ teeth-sharpening,
  not a blocker. Plus `.example`/fixture-tree `is_skippable()` guard added (false-positive side).
- **S-MAJOR-4 (FOLDED → explicit decision):** kg-studio allowlist widening must be a domain-authority
  call, not ad-hoc. → the ALLOWLIST DECISION section (default A: add it as a producer; operator ratifies;
  drafted constant leaves it OUT so the choice is deliberate).
- **S-MINOR-5 (FOLDED):** carry the auth step's `⚠️ D-059 GATE` fail-open→fail-closed comment verbatim-style.
- **S-MINOR-6 (FOLDED):** `.example`/fixture guard — done in `is_skippable()`.
- CONFIRMED-SAFE: allowlist is SCP-owned + injected (never adopter content); no-self-assert guard real
  (Rego reads only `repo_id ∈ allowlist`, never a `role` field); additive scope, no `--combine`; fail-open
  parity; SCP-R-013 already in both WARN_BASELINE sites.

## Correctness lens (no BLOCKERs)
- **C-MAJOR-1 (FOLDED):** services.yml env-key extraction hardcoded `(svc, local, staging)` → spurious
  missing-contract findings if an adopter uses another env key. → v2 iterates env keys generically,
  mirroring `SCP-R-001.rego:156-171`.
- **C-MAJOR-2 (FOLDED):** unanchored `re.search(class {sym})` fires on comments; bare-substring
  `FOS_MARKERS` flips `ontology_consumer` off a README; Go has no `class` (false-negative). → v2 uses
  `declares_local_class()` anchored to declaration lines, py/ts only; `FOS_CALL_RE` skips comment lines;
  Go local-class detection flagged as `FUP-WP-SCP-037-ARCH-006-GO-MARKERS`.
- **C-MINOR-3 (FOLDED):** selftest `cases`-list + job-chain wiring under-specified → covered by the full
  fixture-footprint enumeration (see CG-MAJOR-4).
- **C-MINOR-4 (FOLDED):** each `run:` heredoc is an independent process → v2 says the helpers
  (`walk_files`/`read_text`/`load_yaml_text`/`LANG_BY_EXT`/`dedupe`) are DUPLICATED, not imported.
- **C-MINOR-5 (FOLDED):** version-manifest.json gating uncertain → added to the dispatch seed proactively.
- CONFIRMED-CORRECT: envelope keys match the Rego `object.get` calls exactly; `run_eval` shape correct;
  `to_finding` filter/skip correct; RED-first mechanics sound.

## Completeness / governance lens
- **CG-BLOCKER-1 (FOLDED):** STATUS.md chain entry silently dropped → added to Files touched, dispatch
  seed, and Sequence step 5.
- **CG-BLOCKER-2 (FOLDED):** BACKLOG FUP status-close silently dropped → Sequence step 6 (close the row
  with the merge SHA).
- **CG-MAJOR-3 (FOLDED):** version-manifest.json was in the real WP-SCP-028 7-path dispatch → added to seed.
- **CG-MAJOR-4 (FOLDED):** workflow-selftest footprint understated (each fixture is a 3-job chain +
  aggregator `needs:` + keystone "all succeed" assertion + `cases` entry + count-guard) → enumerated in v2.
- **CG-MAJOR-5 (FOLDED):** kg-studio allowlist self-contradiction (open-Q said add; drafted constant
  omitted) → resolved as the explicit ALLOWLIST DECISION.
- **CG-MINOR-6 (FOLDED):** VERSIONING.md has zero SCP-R-013 text → author from scratch (Live-members line
  + new subsection), not "toggle".
- **CG-MINOR-7 (NOTED):** no standalone `docs/releases/*.md` expected (v1.5.1/v1.6.0 precedent).
- CONFIRMED-COMPLETE: both BACKLOG trust-boundary constraints honoured; cosign/live-smoke correctly N/A;
  cohort rollout present.

## Net
Two safety BLOCKERs + one correctness/completeness set, all folded into plan v2. The materialiser
mechanism is validated against the auth template; the build is now a faithful-to-v2 implementation under
an operator-seeded dispatch, RED-first. The build-stage R1 (over the actual diff) is a separate round.
