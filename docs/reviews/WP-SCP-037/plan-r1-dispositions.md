# WP-SCP-037 — plan-stage 3-lens adversarial review dispositions

**Date:** 2026-07-02 · **Stage:** plan (pre-build) · **Verdict:** ACCEPT with folds (no REJECT) ·
**Reviewers:** 3× parallel Sonnet — correctness / safety_bypass / completeness_governance.
Plan reviewed: the canonical-source standards family + 5-app registration + finish-the-cascade plan
(approved; saved to the session plan file). Each finding below was verified against the real repo before
disposition. **This is the plan-stage R1;** a second build-stage R1 (over the authored Rego/rule diff)
lands as `docs/reviews/WP-SCP-037/r1-dispositions.md`.

> ⚠️ WP number correction at author time: the plan said "WP-SCP-031" but `docs/BACKLOG.md` already holds
> WP-SCP-031 (Vendored-SDK pinning, named-but-not-built). Next clean umbrella = **WP-SCP-037**. All
> evidence/BACKLOG/DECISIONS references use WP-SCP-037.

## Correctness lens — folds

- **C-BLOCKER-1 (FOLD):** enforcement Rego must be `policies/SCP-R-013.rego`, not `ARCH-006.rego` — the CI
  workflow loads only `SCP-R-*.rego` (`policy-check.yml:801`) and the scorecard filters `SCP-R-[0-9]+`. So
  **ARCH-006 = standards-domain ID** (doc + index; served by `consult_rules`); **SCP-R-013 = enforcement
  policy ID** (Rego + test; internal `rule_id` string = `"ARCH-006"`). SCP-R-012 taken → 013 is next free.
  Test = `policies/tests/scp_r_013_test.rego`.
- **C-BLOCKER-2 (FOLD):** add `"SCP-R-013"` to BOTH `WARN_BASELINE_RULES` sets in `policy-check.yml`
  (~1995, ~2351) in the SAME PR as the Rego (the WP-SCP-028 coupling guard). `policy-check.yml` added to
  the Pattern-3 dispatch scope.
- **C-BLOCKER-3 (FOLD):** architecture domain fallback globs (`resources.py:67-79`) exclude services.yml →
  add a `_FALLBACK_APPLIES_TO_BY_RULE_ID["ARCH-006"]` entry (SVC-001..004 precedent, `resources.py:45`) so
  the MCP surface fires on services.yml + source. CI enforcement uses the SCP-R-009-style opa-eval
  materialiser (companion FUP), not per-file conftest. `resources.py` added to dispatch scope.
- **C-MAJOR-4 (FOLD):** the FLA carve-out is Rego-only; `exceptions[]` in the index schema is prose-doc
  (Rego never reads it). Dispatch instructions must say so explicitly.
- **C-MAJOR-5 (FOLD):** removed all "enforced NOW" language — none of checks (i)-(v) can fire without the
  materialiser. Correct framing: **ships dormant/vacuous-pass**, exactly like SCP-R-009 pre-materialiser.
- **C-MINOR-6/7 (FOLD):** test filename convention corrected to `scp_r_013_test.rego`; runbook stale line
  is `adjudicate-proposal.md:37` (fixed this PR).

## Safety / bypass lens — folds

- **S-BLOCKER-1 (FOLD — the important one):** the FLA-author carve-out must be **SCP-controlled, not
  self-asserted.** The exemption reads an SCP-injected `input.ontology_authoring_allowlist` (FOS + FLA),
  NEVER a `role: authoring-source` field the adopter writes into its own services.yml — otherwise any
  adopter self-exempts from the no-embedded-ontology check. The RED test includes a
  non-allowlisted-repo-self-asserting-the-role → still-DENY fixture to prove no bypass.
- **S-MAJOR-2 (FOLD):** duplicate of C-BLOCKER-2 — WARN_BASELINE both sites; materialiser PR scope must
  include `policy-check.yml`.
- **S-MAJOR-3 (FOLD):** WS3 invocation-log commit is now gated on parsing `verification passed ✓` from the
  onboard-script output; on `verification failed`/absent → halt and alert operator, do NOT commit.
- **S-MINOR-4 (FOLD):** dormant rule with `status: active` gets a visible `> Enforcement status: DORMANT`
  banner in the prose served by `consult_rules`.
- **S-MINOR-5 (FOLD):** dropped the redundant `docs/**` entries from the re-seed scope (always-allowed;
  listing them creates a misleading audit trail).
- Confirmed-safe: re-seed scope is minimal + passes the dispatch script's refusals; PR-workflow upheld; no
  `-A`/`-am`; no hook-disable; signing preserved; onboard scripts (merge-before-flip) relied on, not bare
  flips.

## Completeness / governance lens — folds

- **G-BLOCKER-1 (FOLD):** assign WP designator (**WP-SCP-037**) + create `docs/reviews/WP-SCP-037/`;
  R1 evidence dir named and cited in every rule PR `## R1 evidence` block.
- **G-BLOCKER-2 (FOLD):** fixed the stale `adjudicate-proposal.md:37` `applies_to` line pre-dispatch
  (this PR) so the Codex author isn't misled into a schema-invalid entry.
- **G-BLOCKER-3 (FOLD):** `STATUS.md` added to dispatch scope + a STATUS.md update step after each rule
  merge.
- **G-MAJOR-1 (FOLD):** each WS1 author sequence now explicitly retires the PROP-0NN file
  (`adjudication_status: accepted` + RULE-ID + D-ref).
- **G-MAJOR-3 (FOLD):** D-062..D-065 reservation block added to `docs/DECISIONS.md` (this PR).
- **G-MAJOR-4 (FOLD):** advisory rules 1b/1c/1d still get full four-tier (3× Sonnet review +
  operator-verify), not a lightweight doc-write path.
- **G-MAJOR-2 (RESOLVED BY OPERATOR):** WS2 scope — operator chose **all 5 apps this WP** (not the
  FOS+status-only default). Order: FOS → status → kg-studio → consumer-language → amplience-kg-mvp, with
  SVC-ADOPT-001 authored first as the checklist apps 3/4/5 follow.
- **G-MINOR-1/2/3 (FOLD):** BACKLOG rows added (materialiser FUP + WS5 hardening + private-keys
  false-positive); post-merge MCP-reconnect + `consult_rules` verify added to each rule's sequence.

## Deferrals (explicit, not silent descope)

- WS4 REACH-2 consult hook → ACC authors (D-058); BACKLOG.
- WS5 cleanup → BACKLOG rows this session (gated-merge harden; private-keys false-positive; the two
  WP-SCP-024 smoke-test FUPs remain recorded inline in the WP-SCP-024 SMOKE row).
- ARCH-006 materialiser → `FUP-WP-SCP-037-ARCH-006-MATERIALISER-001` (rule ships dormant first).
