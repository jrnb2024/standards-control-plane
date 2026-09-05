# Continuation prompt — 2026-05-20 — D-049 + RULE-002 amendment fold MERGED + TF-PIM-001 chain-through

**Audience:** clean-context SCP session restart.
**Authored:** 2026-05-20 immediately after PR #125 self-merge.
**Live as of:** SCP main HEAD `71a6e41` (PR #125 squash-merged).
**Active branch:** *none* — `draft/d-049-design-system-and-rule-002` auto-deleted on merge. Next work opens a new branch.

This prompt lives in-repo (NOT `/tmp/`) per the 2026-05-20 estate-wide discipline shift surfaced after an unexpected system restart wiped a `/tmp/`-resident continuation. Apply going forward: continuation prompts always at `docs/continuation-prompts/YYYY-MM-DD-<topic>.md`.

---

## What just happened (single session 2026-05-20)

PR #125 D-049 + RULE-002 design-system policy-layer adoption — DRAFT 2026-05-19, MERGED 2026-05-20 with all 9 operator-authorised amendments folded inline. Merge commit `71a6e41`. Branch auto-deleted.

The 9 amendments resolved:

- **D1 — §Sequencing.** SCP-R-005 ships v1.3.0 warn-baseline **self-dogfood-only**. Adopter cascade consumption gated on **TF-PIM-001** fix (cross-repo `actions/checkout` auth). Artefact-gate, not time-bake per `feedback_artefact_gates_not_time_bakes.md`.
- **D2 — Token-package floor v1.4.0+.** Design-team-paced; decoupled from federation-primitive release cadence. v1.3.0 carries SCP-R-005 + dogfood only.
- **D3 — First deny-gate target = Recommender.** 5-bullet rationale captured in D-049 §"Decision points" item 3: Phase 2 slice 12 / Week 27 alignment; J1-INT non-conflict (backend/DB only vs SCP-R-005 frontend globs); ACC deferred as future deny-gate showcase; NOT-PIM-first per TF-PIM-001 relax; per-adopter glob caveat = `["frontend/**", "shopify-app/app/**"]`.
- **D4 — `dpbm-scoped: true` explicit opt-in confirmed.** Rejects auto-detection on `docs/design/` directory presence per `cardinal-rule-1` + `cascade-status: onboarded` parallel.
- **Q1 — ONE-of-three artefact** + threshold-overrides as per-adopter tightening lever (cardinal-rule-2 3-lens + D-040 risk-scaled parallel).
- **Q2 — Default globs `["frontend/**"]`** (single-element; operator grep-check 5/5 cohort use top-level `frontend/`; 0/5 use `src/components/`).
- **Q3 — Narrow workflow-glob** (`docs/design/**`) over full `input.repo_tree`. Workflow filters → Rego evaluates; matches existing federation-primitive `input.changed_files` pattern.
- **Q4 — `threshold-overrides` enum `{warn, deny, disable, off}`** + silent config-load migration from existing `disable: true` per-rule waiver.
- **TF-PIM-001 cross-ref** added to D-049 §Cross-references + RULE-002 §6.

Concurrent: BACKLOG.md Phase 12 gained **`FUP-WP-CT-GOV-002-PHANTOM-INT-CITATION-PREFLIGHT-001`** (P2, open) — plan-doc INT/FUP/TF citation preflight extending the WP-CT-GOV-002 dispatch preflight script concept. Filed 2026-05-20 from 6th-recurrence escalation of `feedback_int_pre_grep_at_plan_ready` violation surfaced during Recommender V13 R2 review of PR #156.

PR body fully rewritten with proper `## R1 evidence` 3-lens block (correctness / safety_bypass / completeness_governance) — closes 3rd-recurrence escalation of `feedback_r1_surface_must_cite_ci.md`. Validate-PR-body CI green on push.

All 4 required CI checks green on the merge commit: `policy-check / scp/policy-check` ✅, `policy-check-readback` ✅, `check-invocation-log-entry` ✅, `validate PR body` ✅. `mergeStateStatus: CLEAN` at merge.

## Current SCP-side state

| Surface | State |
|---|---|
| Main HEAD | `71a6e41` (PR #125 D-049 + RULE-002 + BACKLOG Phase 12 phantom-INT FUP) |
| Active branch | *none* |
| D-049 status (DECISIONS.md row) | `DRAFT` in file at merge; flips ACCEPTED at next status-bookkeeping commit per ADR ceremony |
| RULE-002 status | DRAFT in file; will flip UNDER-REVIEW when the rule-RFC review-lifecycle slice opens (impl slice for v1.3.0 + SCP-R-005.rego) |
| Open Phase 12 P0/P1 blockers | **TF-PIM-001** (P0); **FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001** (P1) |
| WP-SCP-024 cascade state | 024C closed 2026-05-17 (PIM canary onboarded with `cascade-status: onboarded`); PIM required-check `policy-check / scp/policy-check` operator-attended-relaxed 2026-05-19 pending TF-PIM-001 |
| WP-SCP-025 (design-system cascade) | Authoring-mode only; does NOT open as active work-package until 024G Threshold A signs |

## Next priorities — per operator standdown semantics 2026-05-20

Real triggers (NOT aesthetic) for stand-down:

1. CRIT arch-scope question (operator-attended ASC)
2. Cure-worse-than-disease (R3 ship-proposal)
3. Real context window degradation
4. ASC needing operator authorisation
5. Genuine resource constraint (Sonnet quota)

If none fire, chain through. Candidates by leverage:

1. **TF-PIM-001 fix authoring** (P0; **highest-leverage** per operator 2026-05-20). Cross-repo `actions/checkout` authentication for SCP federation adopters. Multi-day SCP-side work. Unblocks: (a) every external adopter of WP-SCP-024 cascade; (b) the deny-gate-on-Recommender path D-049 D3 commits to; (c) PIM main re-enabling the relaxed `policy-check / scp/policy-check` required-check. Two canonical fix paths per BACKLOG row: (a) PAT/GitHub-App token via `secrets: inherit` for cross-repo `actions/checkout`; (b) SCP repo public/org-owned so default `GITHUB_TOKEN` suffices.

2. **v1.3.0 release authoring** (carries SCP-R-005 ship per D-049 D1). Slice writes: `policies/SCP-R-005.rego` + tests; `scp_common.rego` helper additions (`glob_match`, `file_in_tree`, `scp_threshold_override_deny`); `schemas/rule-config.schema.json` extension for the three new keys; `.github/workflows/policy-check.yml` narrow-glob `repo_tree` materialisation per RULE-002 §3.4 Implementation note. Independent of TF-PIM-001 in the codebase — but the rule's *adopter consumption* is gated on TF-PIM-001 closing. Possible to do in parallel with TF-PIM-001 fix authoring; the two release together.

3. **WP-SCP-024 024D–024F cohort planning** — held under DO-NOT guardrail per 2026-05-17 dispatch (Phase 2 dispatch ~2026-08-23+). Do NOT pull forward.

## Hard "do NOT" list (carry-forward from 2026-05-17)

- **No pre-emptive SCP-R-005 deny flip.** Phase 4 Week ~41 (calendar ~2027-02-27) is canonical. Per-adopter ramp via `threshold-overrides: { SCP-R-005: deny }` is the only sanctioned promotion path.
- **No canonical-SDK-versions.yaml content.** Phase 1C ships this.
- **No cascade beyond 024C** until Phase 2 dispatch authorises (Wks 14-29 = calendar ~2026-08-23 onwards).
- **No token-package release before v1.4.0.** Design-team-paced.
- **No cost framing** (programme / opportunity / capacity / calendar-irreversibility). Per `feedback_no_cost_decision_gates.md`.
- **No FUP-SCP-V1-0-0-SHA-NAMING-001 hygiene cleanup.** P3 deferred until post-Phase-4 deny-flip.

## Auth-surface deviation check (per orchestrator dispatch 2026-05-16)

If TF-PIM-001 fix work introduces any auth-surface change at the BFF / token / cookie layer (it MIGHT — the canonical fix path (a) introduces a PAT or GitHub-App token via `secrets: inherit`, which is an auth-surface change at the federation-primitive layer), **plan-stage 3-agent review is mandatory** per `feedback_orchestrator_auth_surface_plan_review_default.md`. Surface to orchestrator before opening the TF-PIM-001 fix slice.

The fix path (b) — making the SCP repo public — has different surface area (visibility change; no token surface added) but introduces its own concerns (public exposure of policy logic, vendoring patterns, etc.). Either fix path is non-trivial and warrants the orchestrator-attended plan review at the dispatch-ready stage.

## Cross-tree memory paths

- `~/.claude/projects/-Users-amplience-Projects/memory/feedback_artefact_gates_not_time_bakes.md` — anchored citation in D-049 §Sequencing.
- `~/.claude/projects/-Users-amplience-Projects/memory/feedback_no_cost_decision_gates.md` — estate-wide retroactive per 2026-05-17 operator direction.
- `~/.claude/projects/-Users-amplience-Projects/memory/feedback_r1_surface_must_cite_ci.md` — applied to PR #125 body rewrite.
- `~/.claude/projects/-Users-amplience-Projects/memory/feedback_int_pre_grep_at_plan_ready.md` — 6th-recurrence escalation captured in BACKLOG.md Phase 12 phantom-INT FUP.

## Sanity check before chain-through

- [ ] `git checkout main` succeeds + `git pull origin main --ff-only` succeeds
- [ ] `git log --oneline -1` shows `71a6e41` at HEAD
- [ ] `gh pr view 125 --json state` returns `{"state":"MERGED"}`
- [ ] `gh api repos/jrnb2024/standards-control-plane/branches/main/protection --jq '.required_status_checks.contexts'` returns `["policy-check / scp/policy-check", "check-invocation-log-entry"]`
- [ ] BACKLOG.md Phase 12 has 3 rows (TF-PIM-001, FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001, FUP-WP-CT-GOV-002-PHANTOM-INT-CITATION-PREFLIGHT-001)
- [ ] No worktree contains uncommitted work (`git status` on main + on `~/Projects/scp-track1` both clean — note `scp-track1` is a STALE worktree from 2026-05-04; upstream gone)

Once sanity checks pass, the natural next action is **TF-PIM-001 fix authoring** — open a plan-doc, then orchestrator-attended plan-stage 3-agent review (auth-surface deviation), then dispatch.
