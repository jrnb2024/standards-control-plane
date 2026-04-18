# Standards Control Plane — Status

**Last Updated:** 2026-04-18
**Current Branch:** `feature/wp-scp-019-svc-003-auth-contract` (pending PR)
**Current Work Package:** `WP-SCP-019` — Service Auth Contract (SVC-003)
**Current State:** WP-SCP-019 slices 019A–019F complete on the feature branch;
PR pending merge to `main`. SVC-003 freeze-directive unfreeze-trigger 1
(WP-SCP-019 merged) satisfied on merge; triggers 2 and 3 remain external.

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

1. **WP-SCP-019 merged** — satisfied on PR merge.
2. **CT SDK 0.4.1 / 0.8.1 vendored in at least one consuming app** —
   external; not satisfied in this repo. This repo currently vendors
   `ct_auth-0.8.0`.
3. **Per-app migration plans drafted for apps not yet conformant** —
   external; tracked under SCP-071 and individual per-app work
   packages.

Merging WP-SCP-019 lifts the freeze on SCP-side authoring work but
does not by itself unfreeze the broader estate — triggers 2 and 3
are per-app responsibilities.

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

1. merge the WP-SCP-019 PR to `main`
2. confirm the consuming-app SDK vendoring required by
   freeze-trigger 2 with the Control Tower team
3. start per-app migration planning for estate services still on
   `mode.bearer_legacy`, tracked as individual work packages
4. register SCP's own `scp-bearer-legacy-migration` waiver in
   `output/findings/waivers.json` once governance confirms owner +
   expiry (captured as SCP-071 follow-up)
5. decide whether any `later` backlog items should be pulled forward
