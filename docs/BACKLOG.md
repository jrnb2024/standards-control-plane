# Standards Control Plane — Backlog

**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-11

This backlog is the initial execution list for the standalone standards
consult-and-audit app.

## Phase 0 — Framing

| ID | Title | Priority | Status | Notes |
|----|-------|----------|--------|-------|
| SCP-001 | Create standalone repo and docs structure | P0 | done | Initial planning scaffold and reference capture |
| SCP-002 | Capture original specification verbatim | P0 | done | Keep source intent intact for future review |
| SCP-003 | Record placement recommendation and rollout strategy | P0 | done | New app, docs-agent integration later, CT surfacing later |
| SCP-004 | Define project naming, scope, and initial doc map | P1 | done | `standards-control-plane` chosen as working repo name |
| SCP-005 | Select pilot subsystem and seed review corpus | P1 | ready | Recommend Returns Intelligence |
| SCP-006 | Define unattended autonomous delivery protocol and programme queue | P0 | done | Default decisions, blocker rules, and work-package sequencing now live in repo docs |

## Phase 1 — Advisory MVP

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-010 | Define consult, audit, finding, waiver, and summary schemas | P0 | done | SCP-005 | Contracts first |
| SCP-011 | Build standards registry loader and validator | P0 | done | SCP-010 | Live loader now backs `consult` and `show-registry` |
| SCP-012 | Create governance and architecture rule scaffolding | P0 | done | SCP-011 | Structured rule metadata now lives in domain indexes |
| SCP-013 | Build repo extractor for docs, code paths, tests, and configs | P0 | done | SCP-010 | Repo-bounded extractor landed with explicit extracted-scope contract and symlink-safe scope handling |
| SCP-014 | Build area normaliser / intermediate representation | P0 | done | SCP-013 | Explicit project-area contract landed with fixture-backed docs/code-path normalisation |
| SCP-015 | Implement consult retrieval and response assembly | P0 | done | SCP-011, SCP-014 | Live consult now assembles rules, patterns, findings, guidance, and risks |
| SCP-015A | Add minimal findings-store read path for consult | P0 | done | SCP-010 | Read-only findings selection with domain scope plus exact area/path escalation and deterministic ordering |
| SCP-016 | Implement governance evaluator | P0 | done | SCP-012, SCP-014 | Live governance audit path merged via WP-SCP-003 |
| SCP-017 | Implement architecture evaluator | P0 | done | SCP-012, SCP-014 | Architecture evaluator and live audit path merged in WP-SCP-004 |
| SCP-018 | Implement full findings store lifecycle and markdown report generator | P0 | done | SCP-016, SCP-017 | Findings lifecycle and report generation landed across WP-SCP-005 to WP-SCP-007 |
| SCP-019 | Build CLI commands for consult, audit, findings, report | P0 | done | SCP-015, SCP-018 | `consult`, `show-registry`, and `findings` now exercise live data paths |
| SCP-020 | Create fixtures, example requests, example outputs | P1 | done | SCP-019 | Example consult response now mirrors real consult output and seeded pilot fixtures are inspectable in repo |
| SCP-021 | Add tests for contracts, retrieval shape, evaluators, report output | P0 | done | SCP-019 | Retrieval, findings, and CLI tests added; current local run is green |
| SCP-022 | Promote review evidence from path bucket to structured metadata contract | P1 | done | SCP-016 | Structured review-evidence contract landed in WP-SCP-008 |

## Phase 2 — Findings Lifecycle and Retrieval Hardening

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-030 | Add finding lifecycle transitions and validation | P0 | done | SCP-018 | Lifecycle foundation landed in WP-SCP-005 |
| SCP-031 | Add waiver model with expiry handling | P0 | done | SCP-030 | Waiver expiry handling landed in WP-SCP-007 |
| SCP-032 | Implement finding identity, dedup, and history tracking | P0 | done | SCP-018 | Finding identity, dedup, and history tracking landed in WP-SCP-005 |
| SCP-033 | Implement deterministic score calculation and documentation | P1 | done | SCP-032 | Shared score model landed in WP-SCP-007 |
| SCP-034 | Generate area summaries and subsystem rollups | P1 | done | SCP-033 | Deterministic area summaries landed in WP-SCP-006 |
| SCP-035 | Build retrieval adapter for historical review docs | P1 | done | SCP-015 | Historical review retrieval landed in WP-SCP-008 |
| SCP-036 | Add optional docs-agent connector for consult enrichment | P2 | later | SCP-035 | Do not make phase 1 depend on it |
| SCP-037 | Run pilot on Returns Intelligence and tune false positives | P0 | done | SCP-021, SCP-032 | First pilot tuning pass landed in WP-SCP-008 |
| SCP-038 | Add crash-safe pair commit for persisted findings stores | P1 | later | SCP-032 | Current slice uses per-file atomic replacement plus rollback on caught failures; true crash-safe pair commit needs a stronger storage model |
| SCP-039 | Add crash-safe bundled commit for findings plus report artifacts | P1 | later | SCP-038 | Reporting will initially reuse the existing write-flow guarantees rather than invent a cross-artifact transaction |
| SCP-046 | Add score-model version tag to audit output | P2 | later | SCP-033 | Current phase documents score semantics in repo only; future score-model changes will need output-level traceability |
| SCP-047 | Cache parsed structured review evidence for repeated consult and audit calls | P2 | later | SCP-035 | Current phase reparses repo review markdown on demand; acceptable now, but not ideal for larger estates |

## Phase 3 — UX / Design / Product Expansion

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-040 | Add UX / IA standards scaffolding and evaluator shell | P1 | done | SCP-037 | UX evaluator shell landed in WP-SCP-010 |
| SCP-041 | Add design system standards scaffolding and evaluator shell | P1 | done | SCP-037 | Design evaluator shell landed in WP-SCP-011 |
| SCP-042 | Add product coherence standards scaffolding and evaluator shell | P2 | done | SCP-037 | Product evaluator shell landed in WP-SCP-012 |
| SCP-043 | Define confidence taxonomy and evidence classes | P0 | done | SCP-040 | Confidence taxonomy and evidence classes landed in WP-SCP-009 |
| SCP-044 | Add false-positive review loop and calibration pack | P0 | done | SCP-043 | Calibration and false-positive summary landed in WP-SCP-013 |
| SCP-045 | Tune consult output ordering for front-end implementation use | P1 | done | SCP-040, SCP-041 | Front-end consult ordering landed in WP-SCP-013 |

## Phase 4 — CI and Control Tower Surfacing

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-050 | Add changed-file scoped audit mode | P0 | done | SCP-032 | Changed-file audit landed in WP-SCP-014 |
| SCP-051 | Emit CI-friendly JSON and markdown outputs | P0 | done | SCP-050 | CI-facing JSON and markdown outputs landed in WP-SCP-015 |
| SCP-052 | Add warning thresholds for unresolved high-confidence regressions | P1 | done | SCP-051 | Advisory warning thresholds landed in WP-SCP-015 |
| SCP-053 | Design Control Tower integration surface | P1 | done | SCP-034 | Control Tower surface landed in WP-SCP-016 |
| SCP-054 | Publish subsystem summaries suitable for estate dashboards | P1 | done | SCP-053 | Estate dashboard outputs landed in WP-SCP-016 |

## Phase 5 — Shared Service Promotion

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-060 | Expose service API for consult and audit operations | P1 | done | SCP-051 | Service API landed in WP-SCP-017 |
| SCP-061 | Add project overlay mechanism | P0 | done | SCP-011 | Overlay-aware registry loading landed in WP-SCP-017 |
| SCP-062 | Add auth/access model for shared service use | P2 | done | SCP-060 | Optional bearer auth landed in WP-SCP-018 |
| SCP-063 | Build multi-repo reporting and trend views | P2 | done | SCP-054, SCP-060 | Multi-repo dashboard, history, and trend outputs landed in WP-SCP-018 |
| SCP-064 | Add richer evidence adapters (Storybook, screenshots, graphs) | P3 | done | SCP-044 | Richer evidence buckets landed in WP-SCP-018 |

## Phase 6 — Cross-Estate Dev Infrastructure Debt

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-070 | Resolve dev cloudflared tunnel management hygiene | P2 | open | — | Shared `brokapps-dev` tunnel on developer Macs is managed by a legacy-named launchd plist (`com.brokapps.sizecurves.cloudflared`) that fronts every `*-dev.brokapps.ai` app. The `three-body-problem/scripts/{add-to-dev-tunnel,tunnel-bringup}.sh` helpers have drift — one kickstarts a hardcoded-wrong label (silently fails), the other pkill-restarts without recognising launchd (produces duplicate connectors). Not urgent while routing is up, but a silent restart miss would cascade through the shared `.brokapps.ai` session-cookie scope and take auth down across every dev app. Primary tracking ticket lives in Control Tower backlog as `FUP-CT-004-19`; this row exists so the SCP estate view reflects it. Fix sequence: dynamic label discovery → validate → rename plist → re-validate. See `control-tower/docs/strategy/environment-strategy.md` §2.1. |

## Phase 7 — Estate Service Auth Contract (SVC-003)

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-071 | Publish SVC-003 service auth contract and reconcile in-repo auth stories | P0 | done (in-repo) | SCP-062 | Delivered by `WP-SCP-019` — SVC-003 rule, service-lifecycle evaluator (covers SVC-001/002/003), closed mode set (`mode.user_oidc`, `mode.service_rs256`, `mode.api_key`, `mode.bearer_legacy`), codification of commit `66ba8a4` as the `mode.user_oidc` reference, deprecation of `--auth-token` (classified as `mode.bearer_legacy`, close date 2026-06-30), SCP's own `services.yml` dogfood, and the ADOPT-001 §11 rewrite all merged via the WP-SCP-019 PR. The broader freeze-directive unfreeze still depends on two external triggers owned by the estate: consuming-app SDK vendoring (`ct_auth 0.4.1` TS / `0.8.1` Python — this repo currently vendors `0.8.0`) and per-app migration plans for apps still on `mode.bearer_legacy`. Those are captured as SCP-071 follow-up tickets per consuming app and do not gate `WP-SCP-019` itself (see `docs/plans/WP-SCP-019-programme-plan.md` §7). |

## Phase 8 — Cross-Estate Regression Testing

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| PLAN-ESTATE-REGRESSION-001 | Register cross-estate regression test suite | P1 | open | SCP-071, PLAN-CT-GOV-001 | Primary tracking lives in `mapp-estate-regression` backlog as `ER-001`..`ER-023`. This row exists so the SCP estate view reflects the cross-cutting programme. Purpose: incident-derived regression fixtures for flows spanning ≥2 estate repos (e.g. CT auth flow that broke in INC-GOV-001 on 2026-04-13). First scenario (ER-010) targets INC-GOV-001. Blocked on SVC-003 publication (SCP-071) for finding schema compatibility, and PLAN-CT-GOV-001 for branch-protection baseline. Standalone repo per D-001 in `mapp-estate-regression/docs/governance/DECISIONS.md`. See `~/Projects/mapp-estate-regression/docs/governance/STRATEGY.md`. GitHub: `jrnb2024/mapp-estate-regression` (private). |

## Phase 9 — Policy Federation Primitive

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-073 | Publish policy federation primitive (reusable workflow + OPA + Renovate preset + required-status-check) | P0 | in planning | SCP-071 | Move #1 of the 5-move MVCP captured in the 2026-04-21 multi-agent strategy session. Converts SCP from post-merge advisory auditor to pre-merge deterministic gate. Delivered by `WP-SCP-020`; see `docs/plans/WP-SCP-020-policy-federation-primitive.md`. Plan v0.5 ships post 5-round adversarial review (18 distinct BLOCKINGs surfaced and closed). Follow-ups opened: `SCP-073-compose` (FLA `.claude/review_gate` ↔ federation composition, delivered in WP-SCP-021), `SCP-073-scaffolder` (ready before WP-SCP-024 estate rollout), `SCP-073.audit` (append-only audit mirror, WP-SCP-023 or sooner), `SCP-073.sec` (`SECURITY.md` embargo path), `SCP-074` (deny-by-default JSON-schema conformance against file-restructure evasion). Plan-PR merge requires James's confirmation of U-sec-2 (GitHub plan tier) and U-k (org vs personal account) per plan §14. |
| SCP-073-compose | FLA `.claude/review_gate` ↔ federation-primitive composition | P2 | open | SCP-073, WP-SCP-021 | Local gate must mention SCP check-name when triggered by a conftest fail. Delivered in WP-SCP-021 (MCP server). |
| SCP-073-scaffolder | `scripts/scaffold-downstream.sh` | P1 | open | SCP-073 | Emits all adopter artefacts (wrapper workflow, renovate.json, branch-protection invocation, waivers.json skeleton, SECURITY.md pointer) from a template. Ready before WP-SCP-024 estate rollout. |
| SCP-073.audit | Append-only audit mirror of policy-check JSON summary artefacts | P2 | open | SCP-073 | Extended audit-trail retention beyond GH Actions 90-day default. Delivered with WP-SCP-023 (scorecards) or sooner if incident-driven. |
| SCP-073.sec | `SECURITY.md` embargo / security-contact path | P2 | open | SCP-073 | Pointer landed in ADOPT-001 §12; separate PR populates `SECURITY.md`. |
| SCP-074 | Deny-by-default JSON-schema conformance on known filenames | P3 | open | SCP-073 | Hardens against agents routing around Rego shape checks by restructuring file keys. Scheduled post-estate-rollout. |

## Phase 10 — SCP as MCP Server (agent-facing consult surface)

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-075 | Publish SCP as MCP server with scoped pre-code consult + Ed25519-signed receipts | P0 | in planning | SCP-073 | Move #3 of the 5-move MVCP. Delivered by `WP-SCP-021`. Plan v0.3 ships post 3-round adversarial review (5 distinct BLOCKINGs surfaced and closed). Exposes tools (`consult_rules`, `check_waiver`, `list_open_decisions`, `check_finding`, `audit_changed`, `resolve_domain`, `propose`) and resources (`scp://rules/registry`, `scp://rules/domain-map`, `scp://decisions`, `scp://findings/open`, `scp://waivers`, `scp://status`, `scp://security/signing-keys`, per-ID URIs). Pairs with WP-SCP-020 as belt + braces: client-side hook + server-side gate. Follow-ups opened: `SCP-075-oauth`, `SCP-075-crossrepo`, `SCP-075-ratelimit`, `SCP-075-errors`, `SCP-075-scaffolder-compose`. Plan details in `docs/plans/WP-SCP-021-scp-as-mcp-server.md`. |
| SCP-075-oauth | OAuth 2.0 for HTTP MCP transport | P2 | open | SCP-075 | Replaces bearer-token auth with per-caller OAuth identity. Enables fine-grained rate limits + audit attribution. |
| SCP-075-crossrepo | Cross-repo decision-record indexing | P2 | open | SCP-075 | Exposes CT's DECISIONS + notifications under `scp://external/ct/*` URIs. |
| SCP-075-ratelimit | Per-caller rate-limit on read tools | P3 | open | SCP-075 | Today only `propose` is rate-limited. |
| SCP-075-errors | Expanded SCP-MCP-E0NN error UX + remediation links | P2 | open | SCP-075 | Mirror federation-gate SCP-E00N scheme; every code has a remediation URL. |
| SCP-075-scaffolder-compose | SCP-073-scaffolder emits MCP adopter bits | P1 | open | SCP-073, SCP-075 | `scripts/scaffold-downstream.sh` emits `.mcp.json`, `CLAUDE.md` snippet, PreCommit hook alongside federation wrapper. Ready before WP-SCP-024 estate rollout. |

## Phase 11 — Implementation Programme (autonomous-dispatch execution of WP-SCP-020 + WP-SCP-021)

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-077 | Run WP-SCP-020 + WP-SCP-021 implementation slices through autonomous four-tier dispatch to self-dogfood landing | P0 | in planning | SCP-073, SCP-075 | Delivered by `WP-SCP-022`. Two parallel tracks: Track 1 (federation primitive 020B → 020D2) + Track 2 (MCP server 021B → 021E). Each slice flows through Opus-orchestrated four-tier dispatch (D-026) with 3× Sonnet R1 review and fix rounds to fixpoint. Pauses at user-gate A (post-020D2 self-dogfood) + user-gate C (post-021E MCP scaffold). Evidence persists at `docs/reviews/WP-SCP-022/dispatches/<slice-id>/`. |
| SCP-077-d048-followup | File operational SCP-side D-048 / DPBM follow-up once CT PR #202 + ACC PR #106 merge | P1 | open | SCP-077 | D-028 declares adoption; this follow-up lands the per-slice DPBM-applies predicate in WP-SCP-020 rule library so Rego gate can require design-artefact references on PRs touching designated frontend paths. Sequenced after both upstream merges. |
| SCP-077-cost-cap | Define review-cost cap for the autonomous chain | P1 | closed-in-v0.2 | SCP-077 | Closed in WP-SCP-022 v0.2 (R1 fix-round): per-slice $30, aggregate $300 default per `docs/plans/WP-SCP-022-implementation-programme-plan.md` §8 R-022-07 + §13 U-022-01. User may override at USER-GATE-A. |
| SCP-077-d021-reserved | D-021 decision-ID slot reserved for 2026-05-31 atomic workday | P0 | scheduled | SCP-077 | Reservation per WP-SCP-019 hygiene response (PR #30, 2026-04-21). Filing date 2026-05-31. Records (a) D-021 amending decision; (b) services.yml deprecation_close_date update 2026-06-30 → 2026-09-30; (c) waivers.json scp-bearer-legacy-migration registration. Pre-written draft at `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`. WP-SCP-022 §4.7 gate helper detects collisions. |
| FUP-022-01 | ACC dispatcher: surface session_id in DispatcherResult | P2 | open | SCP-077 | Modify `~/Projects/acc/scripts/codex_dispatch.py` to surface the Codex CLI's session_id in the DispatcherResult so future fix rounds can use `resume_session_id` per WP-SCP-022 §4.3. Closes WP-SCP-022 R1 C-MAJ-04. Owner: ACC repo. |
| FUP-022-02 | ACC dispatcher: scope-boundary symlink resolution | P1 | open | SCP-077 | Modify `~/Projects/acc/scripts/codex_dispatch.py` to resolve symlinks before applying scope_boundary fnmatch checks. Closes residual WP-SCP-022 R1 CRIT-BYPASS-001. Owner: ACC repo. |
| FUP-022-03 | ACC dispatcher: pre-hoc scope-boundary enforcement | P3 | open | SCP-077, FUP-022-02 | Refactor `~/Projects/acc/scripts/codex_dispatch.py` to refuse out-of-scope edits before they land on disk (closes residual WP-SCP-022 R1 CRIT-BYPASS-001 fully). Owner: ACC repo. |

## Phase 12 — Cross-Repo Adopter Fixes (surfaced by WP-SCP-024 PIM cascade rollout)

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| TF-PIM-001 | Cross-repo checkout authentication for SCP federation adopters | P0 | open | SCP-073, SCP-073-scaffolder | **Fundamental blocker for external adopters.** PIM PR #236 (WP-300 Workbench Assembly) 2026-05-19 unblock surfaced: the SCP `policy-check.yml` reusable workflow's `actions/checkout` steps (paths `.scp-runtime` + `_scp-workflow`) fail when invoked cross-repo from an adopter against private SCP. Default `GITHUB_TOKEN` is scoped to the calling repo only and cannot clone the private SCP repo. SCP's own dogfood works because it's same-repo (GITHUB_TOKEN auto-has same-repo access). Affects ALL external adopters of WP-SCP-024 cascade. Two canonical fix paths: (a) accept a PAT or GitHub-App token via `secrets: inherit` in the reusable workflow and use it for cross-repo `actions/checkout` steps; (b) make the SCP repo public/org-owned so default GITHUB_TOKEN suffices. Decision needed before next adopter onboards. **PIM unblock today: operator-attended branch protection relaxation — `policy-check / scp/policy-check` removed from PIM main required-checks until this lands.** Evidence: failed run https://github.com/jrnb2024/mapp-pim/actions/runs/26131634673 — "Populate .scp-runtime (self-call fallback)" + "Check out SCP repo at workflow ref for schema lookup" both FAILED; all 12 policy-check steps SKIPPED; schema validation failed because `_scp-workflow/schemas/policy-check-summary.schema.json` unreachable. Filed via PIM diagnostic 2026-05-19 evening. Distinct from TF-023E-002 (attest-scorecard ceiling) which gates v1.2.0 SHA bump; TF-PIM-001 affects v1.0.0 SHA too. |
| FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001 | Scaffolder template generates wrapper with `with:` block incompatible with pinned SHA | P1 | open | SCP-073-scaffolder | `scripts/scaffold-downstream.sh` (= SCP-073-scaffolder) generates adopter wrappers with `with: scorecard-emit: false` clause. The `scorecard-emit` input was added in WP-SCP-023 023B (post-v1.0.0; in v1.2.0). Scaffolder pins SHA to `04523fac` (v1.0.0 tag SHA per `V1_0_0_SCP_SHA` in scaffolder line 16; PIM PR #234 instance used the older variant `41a5299`) — both are PRE-WP-SCP-023 and don't have the `scorecard-emit` input. Result: generated wrapper has phantom input → GitHub Actions parse-rejects at workflow startup → empty jobs array → no required status emitted → blocks ALL adopter PRs. Two fix paths: (a) remove `with: scorecard-emit: false` from scaffolder template until TF-023E-002 lands (matches SCP's own production dogfood wrapper which has NO `with:` block); (b) wait for TF-023E-002 to land then bump scaffolder default SHA to post-v1.2.0 (canonical adopters then get `scorecard-emit` opt-in). Path (a) is cleaner immediate fix — preserves current SHA pin discipline AND matches SCP's own working pattern byte-for-byte. Evidence: PIM `.github/workflows/policy-check-wrapper.yml` as generated by scaffolder in PR #234 (2026-05-18). Filed via PIM diagnostic 2026-05-19 evening. Blocks until TF-PIM-001 resolution (without cross-repo auth, scaffolder output can't run anyway). |
| FUP-WP-CT-GOV-002-PHANTOM-CITATION-PREFLIGHT-001 | Plan-doc + dispatch-artefact phantom-citation preflight (expanded scope) | P1 | open | SCP-073, SCP-073-scaffolder, WP-CT-GOV-002 | Extend WP-CT-GOV-002 dispatch preflight script to grep plan-docs + dispatch-artefacts + R-cycle review JSONs for ALL governance citation patterns: `INT-*`, `FUP-*`, `TF-*`, `ASC-NNNN`, `D-NNN`, `feedback_*`. Cross-check each against `BACKLOG.md` (INT/FUP/TF) OR `docs/decisions/` (ASC/D-NNN) OR estate-level memory dir (`~/.claude/projects/-Users-amplience-Projects/memory/feedback_*.md`). HARD-FAIL on phantom citation. Same shape as dispatch-scope-omission preflight. Driver: **7th recurrence** of `feedback_int_pre_grep_at_plan_ready` violation surfaced 2026-05-20 in Recommender V14 INT #1 dispatch artefact (PR #157) + **4 phantom feedback-memo citations** across multiple orchestrator outputs caught during V14 R1 review (`feedback_no_silent_descoping`, `feedback_grep_production_before_planning`, `feedback_dev_first_staging_manual`, `feedback_never_shortcut_review` — all had no backing `.md` files until Recommender V14 authored them inline). Earlier driver also: 6th recurrence 2026-05-20 from Recommender V13 R2 review of PR #156 (INT-J1-D1-DUP-PENDING-RACE) — F-GOV-PB-2 caught phantom `INT-J1-D1-SELF-PROMOTION-ROUTE-RATE-LIMIT-001` (subsequently filed as part of v1.3 fix-round closure). Instructional discipline (feedback memos) not holding across 7+ occurrences = oversight-class failure, not knowledge-gap. Mechanical pre-flight script enforcement warranted. **Promoted to P1 (from P2 in earlier draft) given meta-level recurrence affecting orchestrator citations**. Operator-paced; sequenced after WP-CT-GOV-002 base preflight script ships (CT PR #367, currently in operator review queue). |
| FUP-WP-CT-GOV-002-PRECEDENT-BUG-PREFLIGHT-001 | Dispatch precedent-bug preflight (third preflight expansion) | P2 | open | SCP-073, WP-CT-GOV-002, FUP-WP-CT-GOV-002-PHANTOM-CITATION-PREFLIGHT-001 | Extend WP-CT-GOV-002 preflight script family with a third check: when dispatch instruction tells Codex to MIRROR an existing code precedent (e.g., "mirror L407-414 overrideStaffRole race-tight pattern"), grep the cited precedent for known-bug patterns recorded in BACKLOG.md INT/FUP/TF entries. HARD-FAIL if the precedent has an OPEN INT/FUP/TF flagging a structural defect (e.g., missing filter, wrong type, race condition). Prevents Codex from mirroring an already-buggy precedent into new code, which then ships with structurally-bypassed defence. Driver: **2026-05-20 Recommender V14 INT #2 dispatch** — plan-doc told Codex to mirror L407-414 `overrideStaffRole` race-tight precedent which itself was missing `deleted_at: null` filter; INT-J1-OVERRIDE-RACE-TIGHT-COUNT-DRIFT-001 (P2) filed for the inherited precedent drift; without v1.1 catch Codex would have shipped structurally-bypassed race-tight defence. Same oversight-class failure family as phantom-citation + continuation-prompt-drift (mechanical-preflight-eligible). Distinct from PHANTOM-CITATION-PREFLIGHT-001 because it checks precedent CODE behaviour against open INT/FUP/TF flags, not citation EXISTENCE against backlog presence. Operator-paced; sequenced after PHANTOM-CITATION-PREFLIGHT-001 base script ships (shares infra). Filed via Recommender V14 INT #2 observation 2 (2026-05-20). |

## Not Before

Do **not** pull these forward into phase 1:

- screenshot or Figma analysis
- blocking CI thresholds
- product coherence scoring as an authoritative signal
- large model-dependent evaluator logic without deterministic baseline checks
- Control Tower runtime coupling
- docs-agent as a hard dependency for core rule selection
