# Standards Control Plane — Status

**Last Updated:** 2026-04-21
**Current Branch:** `feature/wp-scp-020-policy-federation-primitive-plan`
(plan-only PR pending; main otherwise clean post WP-SCP-019 closeout)
**Current Work Package:** `WP-SCP-020` — Policy Federation Primitive (plan
in adversarial-review fixpoint; v0.5 ready for plan-PR merge after James
confirms U-sec-2 and U-k per plan §14). Prior `WP-SCP-019` closed
**Current State:** WP-SCP-019 merged to `main` at commit `41bf227`
(PR #25). Post-merge calibration follow-up merged at commit `00efd62`
(PR #26). Three further 2026-04-20 SCP filings merged: trigger-2
evidence ack (PR #27, `f178e23`), CT_AGENT_KEY_OPS DRAFT review
response (PR #28, `ce03b26`), D-019 2026-05-31 checkpoint Option-B
signal (PR #29, `e801868`). SVC-003 freeze-directive all three
triggers now closed: trigger 1 satisfied by WP-SCP-019 merge;
trigger 2 closed 2026-04-20 via CT-filed evidence (FLA PR #291
vendoring + PR #305 / PR #306 dep-pin bumps) — see
`docs/reviews/WP-SCP-019/trigger-2-evidence.md`; trigger 3 closed
via hybrid evidence (CT central playbook + FLA per-app plans) —
see `docs/reviews/WP-SCP-019/trigger-3-evidence.md`. D-019
`mode.bearer_legacy` close date operationally slid from 2026-06-30
to **2026-09-30** per the Option-B signal from 2026-04-20 forward;
formal D-021 amending decision records on 2026-05-31 with observed
adoption-PR count substituted — see
`docs/reviews/WP-SCP-019/d019-option-b-signal.md` and
`docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`.
`CT_AGENT_KEY_OPS.md` review amendments all applied CT-side in CT
PR #89; DRAFT → Published flip pending (CT-owned, target
mid-to-late May 2026; blocked on CT-side test-coverage gaps per
CT's `CT-OPEN-THREADS-2026-04-20.md` T10). Threshold interpretation
for the 2026-05-31 checkpoint confirmed verbatim by CT on
2026-04-20 (`SCP-CONFIRM-D-019-THRESHOLD-2026-04-20.md`) with three
non-blocking corner cases §2.1–§2.3 flagged for SCP ack. CT also
filed `SCP-BRIEFING-GOVERNANCE-HYGIENE-2026-04-20.md` with four
hygiene items (D-NNN prefixing convention, SCP-071 waiver status,
threshold corner-case ack, path-drift fix informational) —
silence-accepted deadline 2026-05-15. SCP response filed 2026-04-21
(PR #30, `0d0b920`): prefixing convention accepted; SCP-071 waiver
registration committed to 2026-05-31 alongside D-021 filing with
`expires_at: "2026-09-30T23:59:59Z"`; threshold corner cases
§2.1–§2.3 all accepted; path-drift fix noted. Response document at
`docs/reviews/WP-SCP-019/ct-governance-hygiene-response.md`.

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
  merged to `main` across slices 019A–019F (PR #25, `41bf227`)
- post-merge calibration follow-up (trigger-3 evidence, D-019
  2026-05-31 checkpoint, ADOPT-001 §11.5) merged to `main` (PR #26,
  `00efd62`)
- trigger-2 evidence ack (CT FLA-vendoring verification, §Q4.10 all
  four conditions met, two interpretive caveats accepted) merged to
  `main` (PR #27, `f178e23`)
- CT_AGENT_KEY_OPS DRAFT review response
  (ratify-with-three-amendments + ADOPT-001 §11.7 path-drift fix)
  merged to `main` (PR #28, `ce03b26`)
- D-019 2026-05-31 checkpoint Option-B signal (operative
  `mode.bearer_legacy` close date slid to 2026-09-30 from signal
  filing forward; formal D-021 on 2026-05-31) merged to `main`
  (PR #29, `e801868`)
- CT governance-hygiene response + 2026-04-21 status/adoption
  refresh (prefixing accepted, SCP-071 waiver date committed,
  threshold corner cases §2.1–§2.3 all accepted, ADOPT-001 §11
  operative-date callout) merged to `main` (PR #30, `0d0b920`)
- WP-SCP-020 Policy Federation Primitive plan v0.5 authored
  2026-04-21 following 5-round adversarial review (18 distinct
  BLOCKING findings surfaced and closed; FIXPOINT REACHED).
  Plan + review pack on branch
  `feature/wp-scp-020-policy-federation-primitive-plan`; plan-PR
  merge requires James confirmation of U-sec-2 (GitHub plan tier)
  and U-k (org vs personal account) per plan §14. D-022 (federation
  primitive adoption) and D-023 (chat-forum rejection / proposal
  queue adoption) added to `docs/DECISIONS.md`. New Phase 9 row
  SCP-073 added to `docs/BACKLOG.md` with five follow-up tickets

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
   **satisfied** on 2026-04-20. CT filed evidence at
   `control-tower/docs/reviews/WP-SCP-019/trigger-2-evidence.md` (CT
   PR #84). SCP verified all four §Q4.10 conditions met by FLA's
   sequential merges (PR #291 vendoring prep; PR #305 `3ff0c92c4`
   TS dep-pin + lockfile; PR #306 `2621d2383` Python dep-pin). Two
   interpretive caveats accepted: SHA verification via FLA
   `ct-sdk-conformance` CI job (INFRA-034 v1) rather than raw
   `shasum` receipts; Python lockfile collapsed into
   `requirements.txt` per FLA convention. See
   `docs/reviews/WP-SCP-019/trigger-2-evidence.md`.
3. **Per-app migration plans drafted for apps not yet conformant** —
   **satisfied** via hybrid evidence: CT's central adoption playbook
   (`ESTATE_CONSUMER_ADOPTION_GUIDE.md` + `CT-SDK-ADOPTION-PROMPT.md`)
   accepted as default plan shape, plus per-app programme docs (FLA:
   INFRA-023, INFRA-024) as they emerge. See
   `docs/reviews/WP-SCP-019/trigger-3-evidence.md`.

All three triggers now closed. Estate-wide SVC-003 freeze-directive
picture complete on SCP's accounting side. Both CT-side and FLA-side
root `FREEZE_DIRECTIVE_SVC003.md` amended to LIFTED 2026-04-20.

### D-019 2026-05-31 checkpoint

CT and SCP ratified a checkpoint on 2026-04-18 to govern whether the
`mode.bearer_legacy` deprecation close date `2026-06-30` stands or is
amended. Full detail in `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`.

Summary: on 2026-05-31, if fewer than 2 of {pim, recommender,
shopify-app} have opened a `mode.api_key` adoption PR, SCP invokes the
D-019 amending-decision clause and amends the close date to
2026-09-30. Otherwise D-019 stands. SCP owns invocation.

### `mode.api_key` operational-doc gating

CT authors `CT_AGENT_KEY_OPS.md` (rotation cadence, revocation path,
default expiry, rate limits, audit-log format, mode.api_key vs
mode.service_rs256 discrimination). SCP filed a ratify-with-three-
amendments review on 2026-04-20 (PR #28); CT applied all three
amendments CT-side in CT PR #89. DRAFT flag still in place; Published
flip targets mid-to-late May 2026 (CT-owned, currently blocked on
CT-side test-coverage gaps tracked as CT-OPEN-THREADS T10). Until
the flip, ADOPT-001 §11.5 carries a Status callout telling adopters
not to plan production migration to `mode.api_key` yet; SCP removes
the callout in a follow-up PR the same week CT flips to Published.

## Current repo position

- all scheduled slices in
  `docs/plans/PROG-SCP-001-autonomous-execution-plan.md` are merged,
  plus the post-closeout Control Tower auth + service frontend
  additions
- WP-SCP-019 merged to `main` (PR #25); post-merge calibration
  follow-up merged (PR #26)
- all backlog items scheduled through `SCP-064` are complete;
  `SCP-070` (cloudflared tunnel hygiene) is open; `SCP-071`
  (CT-integration contract / service auth contract) is delivered by
  WP-SCP-019 in this PR
- later backlog items remain intentionally parked as future work

## Next sensible actions

1. CT_AGENT_KEY_OPS amendments applied CT-side in CT PR #89; await
   DRAFT → Published flip (target mid-to-late May 2026, blocked on
   CT test-coverage gaps). When CT flips, SCP removes ADOPT-001
   §11.5 Status callout in a follow-up PR
2. **2026-05-31 atomic workday.** Three-step single update per
   the hygiene response §3 commitment: (a) D-021 formal amending
   decision files in `docs/DECISIONS.md` with observed
   `mode.api_key` adoption-PR count substituted into the
   pre-written draft; (b) `services.yml` `deprecation_close_date`
   updates from `"2026-06-30"` to `"2026-09-30"`; (c)
   `output/findings/waivers.json` `scp-bearer-legacy-migration`
   registers with `approved_by` + `created_at` +
   `expires_at: "2026-09-30T23:59:59Z"`. Signal retracts only if
   ≥ 2 Go-app adoption PRs open and live on 2026-05-31 — D-021 text
   then records D-019 stands. Pre-written draft in
   `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`
3. file Phase 2 `X-CT-Timestamp` activation announcement by
   **2026-07-02** (60-day notice before proposed 2026-09-01
   activation). Contingency check 2026-07-15: if <2 consumers have
   adopted `mode.api_key` with `X-CT-Timestamp` emission, slide
   activation to 2026-11-01 and re-notice by 2026-08-01.
   Per `ct-agent-key-ops-review-response.md` §Ask 5
4. hold all per-app migration coordination until
   `CT_AGENT_KEY_OPS.md` publishes
5. decide whether any `later` backlog items should be pulled forward
