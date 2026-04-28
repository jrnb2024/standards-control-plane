# ProgrammePlan — WP-SCP-022 Implementation Programme (federation primitive + MCP server)

**Work Package:** `WP-SCP-022`
**Version:** 0.1 (initial draft — pending 3-round adversarial review)
**Status:** Draft — ready for Gate C 3-agent review.
**Date:** 2026-04-28
**Branch:** `feature/wp-scp-022-implementation-programme-plan`
**Programme Refs:** SCP-073 (federation primitive backlog row, WP-SCP-020), SCP-075 (MCP server backlog row, WP-SCP-021)
**Decisions introduced:** D-026 (autonomous-dispatch protocol for SCP implementation slices), D-027 (parallel-track execution policy for WP-SCP-020 + WP-SCP-021), D-028 (SCP-side adoption of D-048 / ADR-016 Design Parity Build Method)
**Predecessors:**
- `WP-SCP-020` plan v0.6 (PR #31, commit `d502bc2`) — federation primitive design.
- `WP-SCP-021` plan v0.3 (PR #32, commit `3b198a1`) — MCP server design.
- `ARCH-005` (PR #34, commit `cccd042`) — canonical event-stream rule, prerequisite for the rule-library work in 020C.

## 1. Purpose

WP-SCP-020 and WP-SCP-021 ratified the *what* — they describe the federation
primitive and the MCP server in design detail. Neither plan specifies the
*how* of implementation: the order in which slices run, the dispatch contract
each slice flows through, the review protocol applied to each slice, the
fix-round budget before escalation, or where the autonomous chain pauses for
human review.

`WP-SCP-022` ratifies the implementation programme. It:

1. Orders the WP-SCP-020 and WP-SCP-021 implementation slices into two
   parallel autonomous-dispatch tracks.
2. Names the per-slice dispatch package contract — input, scope boundary,
   verify commands, evidence persistence — bound to the canonical
   `codex_work_package.schema.json` (ACC repo).
3. Names the per-slice review protocol — 3× Sonnet R1 in three lenses
   (correctness / safety_bypass / completeness_governance), parallel-dispatch
   with 500 ms stagger, fix rounds R(F), R(F+1), … recursing to fixpoint per
   `feedback_recursive_adversarial_review.md`.
4. Names the user-gate checkpoints where the autonomous chain pauses.
5. Names the failure-mode handling — fix-round budget, OAuth-refresh path,
   escalation when fixpoint can't be reached.
6. Names the stability prereqs for the *first canary* gate (020E.a) without
   blocking the rest of the programme on them.

This plan is a **process artefact** — it does not deepen the rule library,
ship code, or change estate adoption posture. It is the canonical reference
that subsequent slice dispatches cite for their dispatch shape.

## 2. Invariants and what this is NOT

### Invariants

1. **Every implementation slice flows through four-tier dispatch.** Opus
   orchestrator (this agent) prepares the dispatch package; Codex executor
   tier runs the slice; 3× parallel Sonnet R1 reviewers apply the three
   adversarial lenses; Opus consolidates verdicts and orchestrates fix
   rounds. No slice merges without 3× APPROVED (or APPROVED_WITH_FINDINGS
   where every finding is mitigated in the same PR).
2. **Adversarial review never descopes.** Per
   `feedback_recursive_adversarial_review.md`, recurse until no new
   blockers; reviewers never recommend descoping.
3. **Reusable workflow (020B) ships SHA-pinned, not version-pinned, by
   default.** `@v1` shorthand is documented but the canonical guidance in
   ADOPT-001 §12 is SHA pin + Renovate to bump.
4. **OPA Rego rules and existing Python evaluators are both authoritative
   in their own domain.** Disagreement blocks merge pending human
   adjudication (per WP-SCP-020 §C.1.iii / D-022 rationale). This invariant
   is inherited verbatim, not redefined.
5. **MCP receipts are advisory, never gating.** Per WP-SCP-021 D-025
   invariant: federation gate (WP-SCP-020) is server-side authority;
   client-side hooks consuming MCP receipts catch agents that don't
   consult, but a receipt is never a gate bypass.
6. **Tracks are independent.** Track 1 (WP-SCP-020 implementation) and
   Track 2 (WP-SCP-021 implementation) progress in parallel; no slice in
   one track blocks a slice in the other.
7. **User-gate checkpoints pause the chain.** The chain does not blow
   through 020D2 → 020H or through 020H → 020E.a without explicit user
   acknowledgement.
8. **Evidence persists in-repo.** Every dispatch's stdout, structured
   review JSON, and consolidation note land under
   `docs/reviews/WP-SCP-022/dispatches/<slice-id>/` so the audit trail
   survives across sessions.

### What this is NOT

- Not a redefinition of WP-SCP-020 or WP-SCP-021 scope. Slice content,
  decision records, and acceptance criteria are inherited from the parent
  plans. WP-SCP-022 only governs *how the slices run*.
- Not a new rule. No rules added, removed, or amended. ARCH-005 is a
  prerequisite already on main.
- Not an estate-rollout WP. Estate cascade is `WP-SCP-024`, deferred.
- Not a new dispatcher. Uses the canonical scripts at
  `~/Projects/acc/scripts/{codex_dispatch.py,claude_dispatch.py}`. If the
  dispatcher itself needs changes (e.g. new flags), that's an ACC-repo PR
  out-of-scope here.
- Not a substitute for direct human review on user-gate checkpoints. The
  pause points exist precisely because the artefacts produced there
  (v1.0.0 release tag; first canary PR) have downstream contracts that
  outlive the autonomous run.

## 3. Programme protocol position

Follows `PROG-SCP-001-autonomous-execution-plan.md`, with the following
amendments specific to WP-SCP-022:

- **One PR per slice, not one PR per WP.** The parent plans (020 / 021)
  already specified per-slice PRs (020 §9.15). WP-SCP-022 makes that
  concrete: each slice is its own merged PR; the WP-SCP-022 plan PR itself
  closes when this document is merged.
- **Slices run on dedicated `feature/wp-scp-0NN<slice-id>-<short-name>`
  branches.** Branch names are deterministic so the dispatcher can recreate
  them; e.g. `feature/wp-scp-020b-reusable-workflow`.
- **Evidence directory is `docs/reviews/WP-SCP-022/dispatches/<slice-id>/`**
  containing: `dispatch-package.json`, `codex-stdout.txt`, `verify-output.txt`,
  `review-correctness.json`, `review-safety.json`, `review-completeness.json`,
  `consolidation.md`, `fix-round-N-package.json` (one per round) and a
  terminal `fixpoint.md` recording APPROVED.

### Slice ordering — Track 1 (WP-SCP-020 federation primitive)

Order is canonical; slices may not be reordered without amending this plan.

1. **020B** — Reusable GitHub workflow scaffold (`.github/workflows/policy-check.yml`).
2. **020B.1** — Selftest harness (workflow runs against a fixture repo and
   asserts expected pass/fail outcomes).
3. **020B.2** — Local repro CLI so adopters can replicate the workflow
   evaluation outside CI.
4. **020C** — OPA/Conftest rule library — exactly 3 rules in v1.0.0 per
   WP-SCP-020 §4 invariant.
5. **020C.1** — Waiver-aware evaluation + Python/Rego conflict gate.
6. **020J** — Tag-protection + signed-commits enforcement (personal Pro
   account path per WP-SCP-020 §14 U-sec-2 resolution).
7. **020D1** — Self-dogfood wrapper part 1: SCP repo opts into its own
   reusable workflow.
8. **020D2** — Self-dogfood wrapper part 2: SCP CI green on the federated
   gate; selftest fixtures committed to repo.

**[USER GATE A]** — Pause for review. Confirms self-dogfood is real before
proceeding to v1.0.0 release.

9. **020H part 1** — Release candidate `v1.0.0-rc.1` + ADOPT-001 §12 adopter
   guide.
10. **020H part 2** — `v1.0.0` release tag.
11. **020H part 3** — Renovate digest pinning instructions for adopters.

**[USER GATE B]** — Pause before first canary. Confirms stability prereqs
(see §7) before pinning a downstream repo.

12. **020E.a** — First canary: FLA pin + branch protection.
13. **020F** — Renovate shared preset for cascading the SCP pin bump.
14. **020G** — Branch-protection automation pattern (one-shot script for
    adopters).
15. **020H.1** — Versioning policy + rule-RFC process + rollback detection.

### Slice ordering — Track 2 (WP-SCP-021 MCP server)

Independent of Track 1; runs in parallel.

1. **021B** — MCP server scaffold via Python `mcp` SDK + Ed25519 keygen +
   PyPI publish as `standards-control-plane[mcp]` extra.
2. **021C** — Tools (`consult_rules`, `check_waiver`, `list_open_decisions`,
   `check_finding`, `audit_changed`, `resolve_domain`, `propose`) + error
   taxonomy (SCP-MCP-E0NN).
3. **021D** — Resources (`scp://rules/registry`, `scp://decisions`,
   `scp://findings/open`, `scp://waivers`, `scp://status`,
   `scp://security/signing-keys`, etc.) + domain-map.
4. **021E** — `propose()` stub with anti-spam + silent-rot banner.

**[USER GATE C]** — Pause for review. Confirms MCP scaffold + tools +
resources are coherent before exposing to adopters.

5. **021F** — ADOPT-001 §13 adopter guide for MCP client-side hook.
6. **021G** — ACC integration stub (hooks SCP MCP into ACC dispatcher's
   plan-decompose step at `~/Projects/acc/src/acc/broker/dispatcher.py`).

(Slices 021H — HTTP transport, 021I — auth + token rotation, 021J —
hash-chained observability, 021K — self-consume evidence are deferred to
the post-self-dogfood phase per the user's autonomy bound.)

### Autonomous run scope (this WP)

Per the user's 2026-04-28 decision: the chain runs to **self-dogfood landing**.
That is:

- Track 1: through **020D2** then **[USER GATE A]**.
- Track 2: through **021E** then **[USER GATE C]**.

Slices after the gates (020H releases, 020E.a canary, 021F adopter guide,
021G ACC integration) require explicit user resumption.

## 4. Scope

### 4.1 Per-slice dispatch package contract

Each slice produces exactly one dispatch package conforming to
`~/Projects/acc/schemas/codex_work_package.schema.json`. Required fields and
their slice-level conventions:

- **`package_id`** — `wp-scp-<NNN><slice-id>` (lower-snake), e.g.
  `wp-scp-020b-reusable-workflow`. Deterministic so logs land in
  predictable paths.
- **`instruction`** — narrative task definition. Cites the parent slice
  text (e.g. "Implement WP-SCP-020 §4 slice 020B as defined in
  `docs/plans/WP-SCP-020-policy-federation-primitive.md` lines 61–102").
  Includes the explicit acceptance criteria from the parent plan.
- **`spec_paths`** — array of repo-relative paths Codex must read first.
  Always includes the parent WP plan, the relevant ADOPT-001 sections, and
  any rule files the slice references.
- **`scope_boundary`** — fnmatch globs listing every file Codex may
  create/modify/delete. Tight scoping is mandatory; over-broad scoping
  fails review (see §4.2 lens 2).
- **`verify_commands`** — non-empty array. Always includes `pytest` for
  the relevant test path; for workflow slices includes `act` or a
  workflow-syntax linter; for Rego slices includes `conftest verify`.
- **`timeout_seconds`** — default 1800 (30 min); kernel-dangerous slices
  (020J tag-protection) use 3600.
- **`reasoning_effort`** — `medium` for scaffolding slices; `high` for
  slices touching Rego semantics (020C, 020C.1) or signing (021B Ed25519);
  `xhigh` reserved for any slice that touches branch-protection automation
  (020G).
- **`model`** — null (Codex default `gpt-5.4`) for all slices in this WP.
- **`project_name`** — `"standards-control-plane"`.

Dispatch packages live at
`docs/reviews/WP-SCP-022/dispatches/<slice-id>/dispatch-package.json` and
are committed to the slice's feature branch *before* dispatch (so the
package is part of the audit trail).

### 4.2 Per-slice review protocol

After Codex returns a successful dispatch, the orchestrator builds three
review packages:

- **Lens 1 — correctness.** Does the slice implement the parent plan's
  acceptance criteria? Are tests adequate? Are edge cases covered?
- **Lens 2 — safety_bypass.** Can an adopter (intentionally or not)
  bypass the gate? Are scope boundaries respected? Are secrets/keys
  handled correctly? Can a malicious workflow input subvert the
  evaluator?
- **Lens 3 — completeness_governance.** Are decision records updated?
  Is documentation in sync with code? Is the slice consistent with the
  parent plan's invariants? Are downstream slices' assumptions still
  valid after this change?

Each review package is dispatched via `claude_dispatch.py` with a 500 ms
stagger between launches:

```
claude_dispatch.py --package /tmp/codex-wp/review-correctness.json --cwd /Users/amplience/Projects/standards-control-plane &
sleep 0.5
claude_dispatch.py --package /tmp/codex-wp/review-safety.json --cwd /Users/amplience/Projects/standards-control-plane &
sleep 0.5
claude_dispatch.py --package /tmp/codex-wp/review-completeness.json --cwd /Users/amplience/Projects/standards-control-plane &
wait
```

Each reviewer returns a `SonnetReviewResult` JSON conforming to
`~/Projects/acc/schemas/sonnet_review_result.schema.json`.

### 4.3 Verdict consolidation and fix-round protocol

After all three reviews return, the orchestrator consolidates:

- **All three APPROVED** → fixpoint reached, slice merges.
- **Any CHANGES_REQUESTED, or APPROVED_WITH_FINDINGS where any CRIT or
  unmitigated MAJ exists** → fix round R(F).
- **Fix round R(F)** dispatches a new Codex package with the consolidated
  findings list and `resume_session_id` set to the original dispatch's
  session id, so Codex picks up where it left off rather than restarting.
- **After R(F)**, the same three reviewers re-run their lens against the
  fixed code. Reviewers do not see the fix-round narrative — only the
  resulting code — to preserve adversarial independence.
- **Recurse** R(F+1), R(F+2), … until all three return APPROVED.

**Fix-round budget:** 5 rounds. After 5 rounds without fixpoint, the slice
is escalated to user review (paused, not merged). The 020A and 021A plan
slices reached fixpoint in 5 and 3 rounds respectively, so 5 is generous
for implementation slices but caps runaway loops.

### 4.4 Track parallelism

Tracks 1 and 2 run concurrently from the start. Concretely: 020B and 021B
are dispatched in the same wall-clock window; both proceed independently;
their reviews run in parallel against each other. Concurrent-dispatch
limit: 4 active Codex sessions across both tracks (1 active slice per
track + 3 review-side claude sessions per track is well within rate
limits per the field report 2026-04-22).

### 4.5 Evidence persistence

For each slice the following lands in
`docs/reviews/WP-SCP-022/dispatches/<slice-id>/`:

- `dispatch-package.json` — exact package handed to Codex.
- `codex-stdout.txt` — Codex full transcript.
- `verify-output.txt` — `verify_commands` output.
- `review-{correctness,safety,completeness}.json` — each reviewer's
  structured output.
- `consolidation-r0.md` — orchestrator's verdict consolidation for the
  initial review pass.
- `fix-round-N/dispatch-package.json` + `fix-round-N/codex-stdout.txt` +
  `fix-round-N/review-*.json` + `fix-round-N/consolidation.md` for each
  fix round.
- `fixpoint.md` — terminal record: round count, total wall time, links
  to all artefacts.

### 4.6 D-048 / DPBM SCP-side adoption

The Design Parity Build Method estate doctrine (CT D-048, ACC ADR-016)
opens 2026-04-28. SCP files **D-028** as part of this WP, adopting DPBM as
a contract input for any slice that produces designed visual output.
Within WP-SCP-022, no slices produce visual output (they are workflow,
Rego, MCP-server, and CI work), so D-028 is a forward-looking declaration
rather than an immediate operational change. D-028 lands when CT PR #202
and ACC PR #106 have both merged and the canonical doctrine path is
stable.

## 5. Out of scope

- Estate-wide rollout beyond SCP self-dogfood (= `WP-SCP-024`).
- Second/third canary repos beyond FLA (`WP-SCP-024`).
- MCP server HTTP transport, OAuth, hash-chained observability, error UX
  expansion (021H/I/J/K — slated for post-pause continuation WP).
- Proposal-queue adjudication workflow (= `WP-SCP-022-proposal-queue`,
  separately tracked).
- Cross-repo decision-record aggregation (= `SCP-075-crossrepo`).
- Scorecards dashboard (= `WP-SCP-023`).
- Any change to the four-tier dispatch scripts in ACC. If a change is
  needed, file an ACC PR; this WP uses the dispatch scripts as-is.

## 6. External dependencies

- **`~/Projects/acc/scripts/codex_dispatch.py`** at HEAD (verified executable
  as of 2026-04-27 02:57 mtime).
- **`~/Projects/acc/scripts/claude_dispatch.py`** at HEAD.
- **`~/Projects/acc/schemas/codex_work_package.schema.json`** — input
  contract.
- **`~/Projects/acc/schemas/sonnet_review_result.schema.json`** — review
  output contract.
- **`codex` CLI** — OAuth session live (verified 2026-04-28 via smoke
  test).
- **`claude` CLI** — OAuth session live (verified 2026-04-28).
- **GitHub Actions** — for the reusable workflow slice (020B); requires
  the SCP repo's existing GitHub App or PAT configuration.
- **OPA/Conftest** — installable from `open-policy-agent/conftest`
  releases; pin via Renovate digest.

If `codex` or `claude` OAuth expires mid-run, the chain pauses and emits
a notification to refresh sessions per
`reference_four_tier_dispatch.md` smoke-test commands.

## 7. Rollout prerequisites for estate-wide adoption (not required for this WP)

These prereqs gate `WP-SCP-024` (estate cascade), not WP-SCP-022. They
remain explicitly captured here so that the user-gate B (before 020E.a
first canary) can verify them.

1. **FLA economical** — close but not absolutely there as of 2026-04-28
   (active INFRA-058 through INFRA-063 work).
2. **`ct-auth` Go SDK landed** — `ct-events-go` SDK transplanted into
   Recommender 2026-04-28 (CT PR #201) is the second SDK iteration; the
   `ct-auth` Go SDK specifically is still pending.
3. **CT implementation lessons absorbed** — covered by the ongoing CT
   Phase 2/3 events programme post-mortem.

WP-SCP-022 builds the primitive and self-dogfoods regardless. Only the
020E.a first canary slice (post-USER-GATE-B) waits on these prereqs.

## 8. Risks (specification, not reassurance)

- **R-022-01 — OAuth session expires mid-run.** Both Codex and Claude
  OAuth tokens have finite lifetimes. Mitigation: pause-on-401, emit
  notification, require user `codex login` / interactive `claude` to
  resume. Run-state preserved via `resume_session_id` in dispatch
  package.
- **R-022-02 — Reviewer drift.** A reviewer may give a soft APPROVED on
  later rounds because it sees its own prior findings closed. Mitigation:
  reviewer prompts include "you have not reviewed this code before;
  apply the lens fresh"; review packages do not include prior findings.
- **R-022-03 — Codex over-broad edits.** A scope-boundary glob set too
  loose could let Codex edit files outside intent. Mitigation: dispatch
  packages cite both file globs *and* the parent-plan slice text;
  `codex_dispatch.py` enforces scope boundary natively (per schema:
  "any touched file outside this set → dispatch fails with
  `scope_violation`").
- **R-022-04 — Concurrent track race.** Tracks 1 and 2 may both modify
  shared files (e.g. `pyproject.toml`, `docs/STATUS.md`). Mitigation:
  STATUS.md is touched only at slice merge time, not during Codex
  execution; `pyproject.toml` is partitioned (Track 1 owns
  `[tool.scp.federation]` keys, Track 2 owns
  `[project.optional-dependencies.mcp]`).
- **R-022-05 — Fix-round explosion.** A pathological slice runs the 5-
  round fix budget with no convergence. Mitigation: budget cap pauses
  the chain. The user is asked to either re-scope the slice, raise the
  budget for that slice with explicit reasoning, or escalate to direct
  Opus implementation.
- **R-022-06 — Plan staleness.** WP-SCP-020 / 021 reference rules,
  decisions, or files that have moved between plan land (2026-04-21) and
  slice dispatch. Mitigation: each slice's dispatch package re-reads the
  parent plan's spec_paths first; if a referenced path is missing, the
  slice fails verify_commands and pauses.
- **R-022-07 — Review-cost runaway.** Three reviewers per slice ×
  potentially 5 fix rounds × 13 slices = up to 195 review dispatches.
  Mitigation: budget bookkeeping in fixpoint.md; if cumulative review
  spend exceeds a per-WP cap (TBD with user at user-gate A), pause.
- **R-022-08 — Two open PRs collide on `docs/STATUS.md`.** PR #35
  (governance refresh) and the WP-SCP-022 plan PR (this PR) both touch
  STATUS.md. Mitigation: WP-SCP-022 plan PR rebases on top of #35 once
  #35 lands; or vice versa. Either order is reconcilable as the diffs
  do not overlap line-by-line.

## 9. Acceptance criteria

WP-SCP-022 is **plan-complete and ready to merge** when:

- [ ] Plan reaches fixpoint via 3-round (minimum) Sonnet R1 adversarial
      review with all CRIT/MAJ findings closed.
- [ ] Plan PR opened against `main`.
- [ ] `docs/DECISIONS.md` updated with D-026, D-027, D-028.
- [ ] `docs/BACKLOG.md` Phase 11 row added: `SCP-077` —
      WP-SCP-022 implementation programme.
- [ ] `docs/reviews/WP-SCP-022/` directory committed (review pack +
      dispatch evidence skeleton).

WP-SCP-022 is **autonomous-run-complete** (the chain pauses cleanly) when:

- [ ] Track 1 has merged 020B → 020B.1 → 020B.2 → 020C → 020C.1 → 020J
      → 020D1 → 020D2 to main (8 PRs).
- [ ] Track 2 has merged 021B → 021C → 021D → 021E to main (4 PRs).
- [ ] User-gate A (Track 1 self-dogfood) and User-gate C (Track 2
      MCP scaffold + tools + resources + propose-stub) reached.
- [ ] All evidence in
      `docs/reviews/WP-SCP-022/dispatches/<slice-id>/` for every
      merged slice.

## 10. Decisions introduced by this WP

- **D-026 (2026-04-28):** Autonomous-dispatch protocol for SCP
  implementation slices. Each slice flows through four-tier dispatch
  (Opus orchestrator + Codex executor + 3× parallel Sonnet R1 review)
  with the lens set, fix-round protocol, evidence persistence, and
  fix-round budget defined in §4. Mandatory for all WP-SCP-020 and
  WP-SCP-021 implementation slices.
- **D-027 (2026-04-28):** Parallel-track execution for WP-SCP-020 and
  WP-SCP-021 implementation. The two tracks run concurrently from
  dispatch-zero to user-gate. Justification: parent plans declare them
  independent; serial execution would defer MCP availability for ~2×
  wall-clock time without quality gain.
- **D-028 (2026-04-28):** SCP adopts D-048 / ADR-016 Design Parity
  Build Method (DPBM) as a contract input for any future slice that
  produces designed visual output. Within WP-SCP-022 itself no slices
  match the DPBM "applies" criteria; D-028 is forward-looking and lands
  once CT PR #202 + ACC PR #106 have merged. WP-SCP-024 estate cascade
  inherits D-028; FLA, ACC, RI canary-onboarding instructions reference
  the DPBM contract layer.

## 11. Review evidence

`docs/reviews/WP-SCP-022/` is created in slice 022A (this plan slice) and
contains:

- `r1-correctness/` — first-round correctness lens output.
- `r1-safety/` — first-round safety_bypass lens output.
- `r1-completeness/` — first-round completeness_governance lens output.
- `consolidation-r1.md` — orchestrator's consolidation of R1 verdicts.
- `fix-round-N/` (one per round) — Codex fix transcript + re-review
  outputs.
- `fixpoint.md` — terminal record.

This same directory layout is replicated for each implementation slice
under `docs/reviews/WP-SCP-022/dispatches/<slice-id>/`.

## 12. Next WP candidates (not opened here)

- `WP-SCP-024` — estate cascade (FLA + canary 2 + canary 3); gated on
  user-gate B (stability prereqs §7 met) post-WP-SCP-022.
- `WP-SCP-025` — MCP server post-self-dogfood completion (021H / I / J /
  K — HTTP transport, OAuth, observability, self-consume evidence).
- `WP-SCP-022-proposal-queue` — `propose()` adjudication workflow (move
  #4 in the MVCP).
- `WP-SCP-023` — scorecards dashboard (move #5).

## 13. Open unknowns (must close before specific slice)

- **U-022-01 (close before USER-GATE-A):** review-cost cap for the
  programme. R-022-07 mitigation requires a number; default proposal
  $TBD per-slice budget, $TBD aggregate. Decided at user-gate A based
  on observed first-half spend.
- **U-022-02 (close before slice 020J):** confirm personal-Pro account
  signed-commit configuration. WP-SCP-020 §14 resolved this for
  tag-protection; need to verify the same configuration covers required-
  signed-commits on the SCP repo's main branch.
- **U-022-03 (close before slice 021B):** PyPI publishing path. Personal
  user-namespace per WP-SCP-020 §14 U-k resolution; confirm `pyproject.toml`
  publish target is `standards-control-plane` (not `standards-control-plane-`
  matching the GitHub repo's trailing-dash slug).
- **U-022-04 (close before USER-GATE-C):** ACC integration target. Slice
  021G hooks into `~/Projects/acc/src/acc/broker/dispatcher.py`; verify
  this file exists and the integration point (plan-decompose step) is
  stable as of slice dispatch time.

---

**End of plan.** Awaiting Gate C 3-agent adversarial review.
