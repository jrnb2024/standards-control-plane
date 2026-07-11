# Continuation prompt — TF-PIM-001 Wave D dispatch JSON authoring (clean-context resume)

**Audience:** clean-context SCP session restart authorising Wave D dispatch JSON authoring.
**Authored:** 2026-05-21 PM post Wave A operator-attended completion.
**Live as of:** SCP main HEAD `194c17e` (D-050 ACCEPTED flip via PR #137).
**Wave A state:** ✅ COMPLETE — App ID `3795720`; `SCP_FEDERATION_APP_PRIVATE_KEY` + `SCP_FEDERATION_APP_ID` secrets stored + verified; `.pem` defensibly deleted per 4-step `.pem` discipline.

This prompt is the canonical fire-able artefact for Wave D dispatch JSON authoring. Per operator authorisation 2026-05-21 (Reading A), this is **autonomous-scope** work; first Codex Tier 2 fire remains operator-attended (excluded from this prompt's scope).

---

## Execute the following 7-step sequence

### 1. Author Wave D dispatch JSON

**Target path:** `docs/governance/work-packages/tf-pim-001-wave-d-policy-check-yaml-token-exchange.json`

**Scope:** per impl WP plan-doc v0.4 `docs/plans/TF-PIM-001-impl-path-c-app-credential.md` §4 Wave D. Include:

- **"Obtain SCP federation App installation token" step** using `actions/create-github-app-token@<SHA>` (PRIMARY per v0.2 strategic-review refinement #3; `tibdex/github-app-token@<SHA>` FALLBACK documented with engagement criterion = documented blocker at SHA-pin time per §12.7.13 supply-chain decision rule)
- **SHA-pin to specific commit** (per WP-SCP-020 020B(v) — adopters MUST pin by SHA, never by branch or tag name)
- **`secrets:`** `SCP_FEDERATION_APP_ID` + `SCP_FEDERATION_APP_PRIVATE_KEY` (stored in Wave A; App ID 3795720)
- **`owner: jrnb2024`**
- **`repositories: standards-control-plane-`**
- **Cross-repo `actions/checkout`** at `policy-check.yml` lines 107 + 1149 use `token: ${{ steps.scp-app-token.outputs.token }}` (token output from the App-token-generation step)
- **`persist-credentials: false`** preserved on all checkout steps
- **SCP-self dogfood case** (`github.action_ref` empty): token-exchange step SKIPS via `if: github.action_ref != ''` guard; self-call fallback engages unchanged
- **12 `verify_commands` minimum** + **`scope_boundary` precisely-pinned** (avoid bracket-glob trap per ACC PR #249 — bracket globs may match more than intended; use explicit file paths or anchor with `^`/`$`)
- **L26 verbatim-claim diff verification** — every CLAIM in the dispatch JSON about specific file content must be verifiable via `git diff` against a named SHA reference
- **L27 runnable-not-decorative probes** — every `verify_command` must actually execute + produce a checkable result (no aspirational placeholders)
- **L28 anchored awk** for line ranges — when extracting line ranges, use `awk 'NR>=N && NR<=M'` anchored explicitly to start/end line numbers, not unanchored patterns

### 2. Preflight grep — MANDATORY before opening PR

Per `feedback_dispatch_scope_omission_pre_flight_check` + `feedback_int_pre_grep_at_plan_ready` (10-cycle held-discipline streak — load-bearing):

```bash
grep -oE "(INT-|FUP-|TF-|ASC-|D-)[A-Za-z0-9_-]+" docs/governance/work-packages/tf-pim-001-wave-d-policy-check-yaml-token-exchange.json | sort -u
# Cross-check each citation against BACKLOG.md (INT/FUP/TF) OR docs/decisions/ (D-NNN) OR estate-level memory dir (feedback_*)
# HARD-FAIL on phantom citation
```

If ANY citation has no backing artefact, fold filing inline into the dispatch JSON as a v0.2 amend before R1 dispatch fires.

### 3. 3-lens R1 plan-stage review

Dispatch via **`claude -p`** Sonnet sub-agents in **per-lens worktree** with **DO-NOT-EDIT mandate** per `feedback_subagent_review_only_scope_must_be_enforced`. 10-cycle ZERO-violation streak holding from Recommender V15 + V14 Phase 1; explicit-incident-citation pattern remains load-bearing.

**Sample-size-3 incident citation in lens prompts** (verbatim):
- CT c565fd0
- Recommender V14 INT #2
- `docs/ESTATE-CONVERGENCE.md` (PR #131 history)

Use **Plan agent type** (read-only by design; lacks Edit/Write/NotebookEdit tools — mandate enforced at tool-availability layer, not just instruction layer).

### 4. Auth-adjacent lens shape

TF-PIM-001 IS the auth-surface. Use **sec / arch-skeptic / pragmatist** lenses per `feedback_orchestrator_auth_surface_plan_review_default` (matches the TF-PIM-001 path-ratification 3-agent review precedent). Reuse lens prompts from `docs/reviews/TF-PIM-001/shortlist-A-C-D/` if convenient (adapt for dispatch-JSON-stage review rather than path-choice review).

Lens domains:
- **sec:** does the dispatch JSON preserve §12.7.10 invariant under code change? Are App-token handling steps tight (no token persisted to artefact; `persist-credentials: false`)? Does the SHA-pinned token-action's supply-chain posture hold?
- **arch-skeptic:** does the workflow change architecturally fit the existing federation-primitive shape? Reversibility check? New failure surface < failure removed?
- **pragmatist:** can the dispatch JSON be executed by Codex Tier 2 cleanly? Are the verify_commands runnable in CI? Is scope_boundary tight enough to avoid Codex over-reach?

### 5. R-cycle to R-fixpoint MET

Per established pattern:

- R1 fires; collect findings; fold into v0.2 of dispatch JSON
- R2 fires against v0.2; collect findings; fold into v0.3 if material
- Continue until R-fixpoint MET (no new significant findings on a fresh round)
- **Cure-worse trigger + Option A R4 mechanical override at R3 if diminishing-returns** matches `feedback_asymptotic_trajectory_split.md` (precedent: TF-PIM-001 impl WP plan-doc v0.4 invoked Option A at R2 DIMINISHING-RETURNS; same shape applies here)

R-cycle evidence files at `docs/reviews/TF-PIM-001/wave-d-dispatch-R-cycle/R{1,2,3?}/{sec,arch-skeptic,pragmatist}-lens-r{1,2,3}.md` + synthesis per round.

### 6. Open PR for operator-paced review

After R-fixpoint MET:

- Open PR with full R1 evidence block (3-lens — `correctness` / `safety_bypass` / `completeness_governance` — to satisfy validate-PR-body)
- Reference the per-lens evidence files in PR body
- CI must go green (policy-check + policy-check-readback + check-invocation-log-entry + validate-PR-body)
- STATUS.md touch required to fire check-invocation-log-entry on a docs/governance path

### 7. DO NOT fire Codex Tier 2 dispatch yet

**Stand down at PR-opened terminal state.** Operator-attended fire mandatory per four-tier dispatch pattern + Reading A explicit exclusion: "First Codex fire in a new WP class" remains operator-paced. Operator authorises Wave D fire when bandwidth allows (tomorrow or next session).

---

## Sanity check before chain-through

- [ ] `git checkout main && git pull origin main --ff-only` succeeds
- [ ] `git log --oneline -1` shows `194c17e` or later (PR #137 D-050 ACCEPTED flip)
- [ ] `gh api repos/jrnb2024/standards-control-plane/actions/secrets --paginate --jq '.secrets[].name' | grep -E "SCP_FEDERATION_APP_(ID|PRIVATE_KEY)"` returns BOTH names (Wave A secrets stored)
- [ ] `grep -E "ACCEPTED.*D-050" docs/DECISIONS.md` returns ≥ 1 (D-050 ACCEPTED per PR #137)
- [ ] `cat docs/plans/TF-PIM-001-impl-path-c-app-credential.md | head -30` shows v0.4 R-fixpoint MET status
- [ ] `ls docs/reviews/TF-PIM-001/impl-WP-R-cycle/R{1,2}/` shows 4 evidence files each
- [ ] `mkdir -p docs/governance/work-packages/` (create if absent — first dispatch JSON in this path-set)
- [ ] `mkdir -p docs/reviews/TF-PIM-001/wave-d-dispatch-R-cycle/R1/` (R-cycle evidence dir)

## Hard "do NOT" list (carry-forward)

- **NO Codex Tier 2 fire from this prompt.** Stand down at PR-opened state per step 7. Operator-attended fire only.
- **NO `secrets: inherit` anywhere** — §12.7.10 invariant preserved; App key in SCP-repo secrets (workflow's own context); never via caller `secrets:` block.
- **NO sub-agent scope-breach** — DO-NOT-EDIT mandate; Plan agent type only; tool-availability-layer enforcement; sample-size-3 incident citation in lens prompts.
- **NO bracket-glob trap** in `scope_boundary` field — per ACC PR #249 lesson; use anchored file paths.
- **NO unanchored awk** for line-range extraction — per L28 discipline.
- **NO aspirational placeholders** in `verify_commands` — per L27 runnable-not-decorative discipline.
- **NO phantom citations** in dispatch JSON or lens prompts — preflight grep MANDATORY before R1 dispatch fires.

## Continuation-prompt discipline (carry-forward)

If standdown fires mid-R-cycle (e.g. context window degradation OR cure-worse trigger requiring operator authorisation), author the next continuation prompt at:

```
/Users/amplience/Projects/standards-control-plane/docs/continuation-prompts/2026-05-21-tf-pim-001-wave-d-r-cycle-resume.md
```

NOT `/tmp/`. Per restart-survival discipline established 2026-05-20.

## Standdown semantics (unchanged)

Real triggers only:

1. CRIT arch-scope question (operator-attended ASC)
2. Cure-worse-than-disease (R3 ship-proposal trigger)
3. Real context window degradation
4. ASC needing operator authorisation
5. Genuine resource constraint (Sonnet quota)

If implementation surfaces an architectural-scope question on the App-token surface OR the `actions/create-github-app-token` action SHA selection (e.g., upstream blocker forcing fallback engagement; CVE in candidate SHA), file ASC + stand down. Otherwise chain through to R-fixpoint MET + PR-opened terminal state.

## Cross-tree memory citations (verbatim — use in lens prompts)

- `feedback_orchestrator_auth_surface_plan_review_default` — 3-lens dispatch shape mandate
- `feedback_subagent_review_only_scope_must_be_enforced` — DO-NOT-EDIT mandate
- `feedback_asymptotic_trajectory_split` — cure-worse + Option A R4 mechanical override
- `feedback_r1_surface_must_cite_ci` — citation pair on R1 evidence block
- `feedback_int_pre_grep_at_plan_ready` — preflight grep MANDATORY
- `feedback_dispatch_scope_omission_pre_flight_check` — scope omission gate
- `feedback_no_cost_decision_gates` — programme / capacity cost framing prohibited

## Reference state (clean-context inputs)

- `docs/plans/TF-PIM-001-impl-path-c-app-credential.md` — impl WP plan-doc v0.4 R-FIXPOINT MET (§4 Wave D spec is the canonical scope for the dispatch JSON)
- `docs/decisions/D-050-tf-pim-001-app-credential-surface-2026-05-21.md` — ACCEPTED ADR ratifying Path C
- `docs/adoption/ADOPT-001-project-onboarding.md` §12.7.13 (supply-chain — action SHA-pin selection rule) + §12.7.16 (App-install ceremony — already documented)
- `.github/workflows/policy-check.yml` lines 107 + 1149-1154 (cross-repo `actions/checkout` sites Wave D modifies)
- `docs/reviews/TF-PIM-001/shortlist-A-C-D/` — 4 path-ratification lens evidence files (reuse prompt shape)
- `docs/reviews/TF-PIM-001/impl-WP-R-cycle/{R1,R2}/` — 8 impl-WP R-cycle evidence files (full lens-prompt + R-fixpoint precedent)

---

**End of continuation prompt.** Fire this when ready; standdown at PR-opened state for operator-attended Codex Tier 2 dispatch.
