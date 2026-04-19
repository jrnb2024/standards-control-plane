# Standards Control Plane — Status

**Last Updated:** 2026-04-19
**Current Branch:** `main` (WP-SCP-019 merged) + `feature/wp-scp-019-post-merge-calibration` (follow-up PR pending)
**Current Work Package:** `WP-SCP-019` — Service Auth Contract (SVC-003), post-merge calibration
**Current State:** WP-SCP-019 merged to `main` at commit `41bf227`
(PR #25). Freeze-directive trigger 1 satisfied. Trigger 2 waits on
FLA PR #291 merge. Trigger 3 closed via hybrid evidence (CT central
playbook + FLA per-app plans) — see
`docs/reviews/WP-SCP-019/trigger-3-evidence.md`. D-019 2026-06-30
close date governed by the ratified 2026-05-31 checkpoint — see
`docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`. `mode.api_key`
operational-doc (`CT_AGENT_KEY_OPS.md`) is CT-led, target mid-to-late
May 2026.

## Summary

- standalone repo created and pushed to `main`
- planning set approved
- phase 1 scaffold committed as bootstrap
- first governed implementation slice now wired to live registry and findings data
- first governed implementation slice merged to `main`
- extractor and area-normaliser slice merged to `main`
- governance evaluator and live audit slice merged to `main`
- unattended execution protocol and ordered programme plan are now documented in repo
- architecture evaluator and architecture audit slice merged to `main`
- findings lifecycle foundation and persistence slice merged to `main`
- markdown reports and subsystem-keyed area summaries slice merged to `main`
- waiver-aware audit and shared scoring slice merged to `main`
- structured review-evidence and historical review retrieval slice merged to `main`
- confidence taxonomy and evidence classes slice merged to `main`
- UX / IA scaffolding and evaluator shell slice merged to `main`
- design-system scaffolding and evaluator shell slice merged to `main`
- product-coherence evaluator shell slice merged to `main`
- calibration and consult-ordering slice merged to `main`
- changed-file scoped audit slice merged to `main`
- CI outputs and advisory warning thresholds slice merged to `main`
- Control Tower surfacing and estate dashboard outputs slice merged to `main`
- service API and project overlays slice merged to `main`
- auth, multi-repo reporting, and richer evidence slice merged to `main`
- ordered autonomous delivery queue complete through `WP-SCP-018`
- post-closeout commits landed on `main` between `WP-SCP-018` and
  `WP-SCP-019` (documented per freeze directive): `ecfbce2` service
  frontend + status health UI, `66ba8a4` Control Tower auth +
  deployment contract (introduces the `mode.user_oidc` reference
  implementation that D-019 codifies), `571d086` Dockerfile hardening,
  `ba1130e` service-lifecycle governance domain with SVC-001 and
  SVC-002 rules
- new programme increment `WP-SCP-019` (Service Auth Contract, SVC-003)
  complete on feature branch across slices 019A–019F; PR pending

## WP-SCP-019 slice summary

- **019A** — SVC-003 rule text, approved-mode enum spec, WP planning
  quartet, D-019, BACKLOG Phase 7 / SCP-071 row, review-pack stub.
- **019B** — `evaluators/service_lifecycle.py` covering
  SVC-001/002/003, 31 fixtures, 36 tests. Ships `pyyaml>=6.0`
  runtime dep. Registered in `audit.py` EVALUATORS dict.
- **019B' (cross-slice sweep)** — evaluator self-poisoning,
  `additionalProperties: false` unenforced, `waiver_ref` existence
  unchecked. All three closed with tests.
- **019C** — CLI integration + tests. Example request files for
  audit and consult targeting service-lifecycle; 10 CLI-level tests
  including write-output end-to-end, overlay extension,
  `show-registry`, read-back subcommands, mixed-domain audit with
  deterministic ordering.
- **019D** — SCP dogfoods its own rules. `services.yml` at repo root,
  `examples/audit-request-scp-dogfood.json`, 10 dogfood tests. Three
  real declaration-vs-reality mismatches fixed (`/health` response
  shape, phantom `service:app` module path, `audience: scp` vs
  `scp-dev`). D-020 captures the `audit.py` `_normalise_scope`
  fallback contract with `AreaIdInferenceError` sentinel.
- **019E** — `ADOPT-001 §11` rewritten against the SVC-003 four-mode
  contract with explicit consumer and producer tracks. Adjacent
  edits across §1, §5.3, §6, §7.1, §9, §14, §15.
- **019F** — publish: STATUS.md (this file), README.md,
  `acceptance_verification.md`, `test_results.txt`, PR opened.

## Decisions added during WP-SCP-019

- **D-019** (2026-04-18): SVC-003 is declare-a-contract with a closed
  four-mode set; commit `66ba8a4` codifies `mode.user_oidc`;
  WP-SCP-018 `--auth-token` classifies as `mode.bearer_legacy` with
  deprecation close date 2026-06-30.
- **D-020** (2026-04-18): `_normalise_scope` falls back to the
  requested `area_id` when `_infer_area_id` raises
  `AreaIdInferenceError`; mismatched-inference still raises. Narrow
  ergonomic relaxation for uninferrable scopes (dogfood / root-level
  `services.yml`).

## SVC-003 freeze directive status

The SVC-003 freeze-directive (`FREEZE_DIRECTIVE_SVC003.md`, posted
2026-04-18) unfreezes when all three triggers are met (see
`docs/plans/WP-SCP-019-programme-plan.md` §7):

1. **WP-SCP-019 merged** — **satisfied** on 2026-04-18 via PR #25
   merge (commit `41bf227`).
2. **CT SDK 0.4.1 / 0.8.1 vendored in at least one consuming app** —
   waiting on FLA PR #291 merge. Evidence will be captured in
   `docs/reviews/WP-SCP-019/trigger-2-evidence.md` when CT pings.
3. **Per-app migration plans drafted for apps not yet conformant** —
   **satisfied** via hybrid evidence: CT's central adoption playbook
   (`ESTATE_CONSUMER_ADOPTION_GUIDE.md` + `CT-SDK-ADOPTION-PROMPT.md`)
   accepted as default plan shape, plus per-app programme docs (FLA:
   INFRA-023, INFRA-024) as they emerge. See
   `docs/reviews/WP-SCP-019/trigger-3-evidence.md`.

Merging WP-SCP-019 lifts the freeze on SCP-side authoring work.
Triggers 2 + 3 closure complete the estate-wide unfreeze picture —
trigger 2 fires on the next external event (FLA #291 merge); trigger 3
is closed as of 2026-04-18.

### D-019 2026-05-31 checkpoint

CT and SCP ratified a checkpoint on 2026-04-18 to govern whether the
`mode.bearer_legacy` deprecation close date `2026-06-30` stands or is
amended. Full detail in `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`.

Summary: on 2026-05-31, if fewer than 2 of {pim, recommender,
shopify-app} have opened a `mode.api_key` adoption PR, SCP invokes the
D-019 amending-decision clause and amends the close date to
2026-09-30. Otherwise D-019 stands. SCP owns invocation.

### `mode.api_key` operational-doc gating

CT is authoring `CT_AGENT_KEY_OPS.md` (rotation cadence, revocation
path, default expiry, rate limits, audit-log format, mode.api_key vs
mode.service_rs256 discrimination). Target publish mid-to-late May
2026. Until then, ADOPT-001 §11.5 carries a Status callout telling
adopters not to plan production migration to `mode.api_key` yet.

## Current repo position

- all scheduled slices in
  `docs/plans/PROG-SCP-001-autonomous-execution-plan.md` are merged,
  plus the post-closeout Control Tower auth + service frontend
  additions
- WP-SCP-019 complete on feature branch; PR pending
- all backlog items scheduled through `SCP-064` are complete;
  `SCP-070` (cloudflared tunnel hygiene) is open; `SCP-071`
  (CT-integration contract / service auth contract) is delivered by
  WP-SCP-019 in this PR
- later backlog items remain intentionally parked as future work

## Next sensible actions

1. land `feature/wp-scp-019-post-merge-calibration` PR (this branch):
   trigger-3 evidence, D-019 checkpoint record, ADOPT-001 §11.5
   calibration, SVC-003 rule-text accuracy fix
2. wait for CT ping on FLA PR #291 merge → record trigger-2 evidence
3. wait for CT ping on `CT_AGENT_KEY_OPS.md` draft URL → SCP review
   round → publish → remove §11.5 Status callout
4. 2026-05-31 checkpoint: count PR status for {pim, recommender,
   shopify-app} against the threshold and either stand D-019 or
   invoke the amending clause (pre-written draft in
   `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`)
5. register SCP's own `scp-bearer-legacy-migration` waiver in
   `output/findings/waivers.json` once governance confirms owner +
   expiry (captured as SCP-071 follow-up)
6. hold all per-app migration coordination until
   `CT_AGENT_KEY_OPS.md` publishes
7. decide whether any `later` backlog items should be pulled forward
