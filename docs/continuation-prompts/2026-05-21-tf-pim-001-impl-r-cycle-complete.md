# Continuation prompt — 2026-05-21 — TF-PIM-001 impl WP R-fixpoint MET + session sweep complete

**Audience:** clean-context SCP session restart after 2026-05-20 / 2026-05-21 session arc.
**Authored:** 2026-05-21 PM after end-to-end execution of 10+ PRs + 4 R-cycle rounds on the TF-PIM-001 impl WP plan-doc.
**Live as of:** SCP main HEAD `02db884` (PR #106 docs CT D-035 ack — most recent merge in today's session-close sweep).
**Active branch:** `chore/2026-05-21-session-close` (this prompt's branch; PR opens after this commit).

This prompt lives in-repo per the 2026-05-20 estate-wide discipline shift — survives unexpected restart. Apply going forward: continuation prompts always at `docs/continuation-prompts/YYYY-MM-DD-<topic>.md`.

---

## Session arc — 2026-05-20 (cont.) → 2026-05-21

10 PRs landed across the two-day arc:

| Date | PR | Commit | Scope |
|---|---|---|---|
| 2026-05-20 | #125 | `71a6e41` | D-049 + RULE-002 9-amendment fold (DPBM design-system role) |
| 2026-05-20 | #127 | `e49dcb4` | In-repo continuation prompt + restart-survival discipline |
| 2026-05-20 | #129 | `3d3996a` | D-049 follow-on (SA bullet + FUP rename/expand/promote) |
| 2026-05-20 | #128 | `f137403` | TF-PIM-001 plan-doc + A/C/D shortlist + §10 escalation path |
| 2026-05-20 | #130 | `747e2ad` | 3-agent A/C/D review evidence landing (non-convergent 2-1) |
| 2026-05-20 | #131 | `66d5e41` | Estate convergence pointer (orchestrator-filed) |
| 2026-05-20 | #132 | `3b4a121` | FUP-WP-CT-GOV-002-PRECEDENT-BUG-PREFLIGHT-001 |
| 2026-05-20 | #133 | `dceab0c` | TF-PIM-001 plan-doc closure (Path C RATIFIED) |
| 2026-05-21 | #134 | `89e645c` | TF-PIM-001 impl WP plan-doc v0.4 (R-fixpoint MET) |
| 2026-05-21 | #95 | `a4b53e6` | market-feed → PIM substitution (stale 2026-05-02 PR) |
| 2026-05-21 | #106 | `02db884` | CT D-035 ack notification (stale 2026-05-09 PR) |

Closed-not-merged: **PR #124** (Dependabot SHA bump 41a5299→750c79c) — blocked on **TF-023E-002** (`attest-scorecard` permission-ceiling validation at workflow startup; documented inline at `policy-check-wrapper.yml` lines 56-79). Resolution path: TF-023E-002 closure (restructure `policy-check.yml` so `attest-scorecard` lives in separate top-level workflow).

Still open: 3 canary PRs (#59 / #67 / #81) — explicit DO-NOT-MERGE permanent fixtures.

## Current state — TF-PIM-001 impl WP

**Path C ratified 2026-05-21.** GitHub App with `repository_permissions: { contents: read }` scoped to `jrnb2024/standards-control-plane` only. 8-wave structure authored:

| Wave | Outcome | Tier |
|---|---|---|
| A | GitHub App authoring + 4-step `.pem` discipline (`.gitignore` check / pre-commit hook / `--paginate` post-upload audit / `shred -u` secure delete) | operator-attended ceremony |
| B | D-050 ADR drafting + operator-attended merge (ADR-class) | operator-paced + attended |
| C | ADOPT-001 §12.7 updates (new §12.7.16 + §12.7.5 amend + §12.7.10 reaffirm + §12.7.13 amend) | operator-paced doc-add |
| D | Reusable workflow change — token-exchange step + `token:` parameter on cross-repo `actions/checkout` | **Tier 2 Codex dispatch** (kernel-dangerous; operator-attended fire) |
| E | Workflow-selftest harness coverage (mock-based for v0.1; real-API TF for follow-up); SAME-PR-COUPLED with Wave D | Tier 2 Codex (same PR) |
| F | SCP-self dogfood verification | operator-attended verify-only |
| G | External-adopter cross-repo verification (PIM canary; denial-free test PR by design) | operator-attended |
| H | PIM main required-check restoration + TF-PIM-001 closure | operator-attended |

**Recommended operator-attended gate batching** (per impl WP §8.1): Session 1 = Wave A + Wave B (if ADR pre-drafted); Session 2 = Wave D Tier 2 dispatch fire (standalone); Session 3 = Wave G + Wave H. Mechanical Wave F verify between Sessions 2 and 3.

**R-cycle complete:**
- v0.1 → v0.2: 10 operator strategic-review refinements
- v0.2 → v0.3: 12 R1 findings (2 MAJ + 7 MIN + 3 NIT) all closed
- v0.3 → v0.4: 1 R2 finding (ARCH-MIN-001-R2 — §7.5a rollback PATCH jq-extraction) closed
- **R-FIXPOINT MET** via Option A R4 mechanical override at R2 DIMINISHING-RETURNS signal (per `feedback_asymptotic_trajectory_split.md` + operator authorisation)

6 lens evidence files + 2 synthesis files at `docs/reviews/TF-PIM-001/impl-WP-R-cycle/{R1,R2}/`.

## Next priorities

**Immediate next chain (operator-paced):**

1. **Wave A — GitHub App authoring.** Operator-attended GitHub UI ceremony. 4-step `.pem` discipline (see impl WP §4 Wave A Actions steps 0a, 0b, 1-10). Creates `scp-federation-primitive` App in @jrnb2024; stores private key in SCP repo secret `SCP_FEDERATION_APP_PRIVATE_KEY`; stores App ID in `SCP_FEDERATION_APP_ID`; commits rotation SOP file at `docs/security/app-key-rotation-sop.md`.

2. **Wave B — D-050 ADR drafting.** Author at `docs/decisions/D-050-tf-pim-001-app-credential-surface-YYYY-MM-DD.md`. Captures: App-credential scope decision; §12.7.10 invariant preservation rationale (App token inside SCP-controlled code, never `secrets: inherit`); key-custody posture under D-031; reversal mechanism. Operator-attended merge mandatory (NO mechanical auto-merge for ADR-class).

3. **Wave C — ADOPT-001 §12.7 updates.** New §12.7.16 (App-install ceremony per adopter); §12.7.5 amend (App-installation revocation on de-adoption); §12.7.10 reaffirmation; §12.7.13 supply-chain amend (`generate-app-token` action SHA-pin + fallback decision rule).

4. **Wave D — Reusable workflow change (Tier 2 Codex dispatch).** Pin `actions/create-github-app-token@<SHA>` PRIMARY (`tibdex/github-app-token@<SHA>` FALLBACK only with documented blocker); add token-exchange step to `policy-check.yml`; update cross-repo `actions/checkout` at lines 107 + 1149-1154 to use App installation token via `token:` param; preserve `persist-credentials: false`. Wave E env-var injection (`SCP_TEST_SIMULATE_APP_TOKEN_FAILURE`) MUST same-PR-couple with Wave D.

5. **Wave E — Workflow-selftest harness coverage.** Mock-based for v0.1 (`SCP_TEST_SIMULATE_APP_TOKEN_FAILURE=1` env-var). Real-API coverage as TF-PIM-001-ARCH-002 follow-up.

6. **Wave F — SCP-self dogfood verify.** Open small test PR on SCP; verify all 4 required checks PASS.

7. **Wave G — PIM canary cross-repo verify.** Operator-attended App install on PIM; open denial-free canary PR (avoid all SCP-R-* evaluation surface); verify all 12 policy-check steps complete with PASS verdict (NOT just "ran to completion" — clarified in v0.3 AC #1 + §7.6 Branch 4).

8. **Wave H — PIM main required-check restoration + TF-PIM-001 closure.** Operator runs `enable-required-check.sh --preserve-existing-contexts`; verify; write invocation-log entry; close TF-PIM-001 + FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001 unblock signal.

## Open TF-PIM-001 P0/P1 surface (snapshot)

- **TF-PIM-001** (P0) — Path C ratified; impl WP plan-doc R-fixpoint MET; Wave A operator-attended ceremony pending
- **FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001** (P1) — unblocks at Wave G PIM canary green; immediate fix path (a) from BACKLOG; separate impl slice opens at Wave H closure
- **TF-023E-002** (open; blocks PR #124) — `attest-scorecard` permission-ceiling at workflow startup; restructure `policy-check.yml` so `attest-scorecard` lives in separate top-level workflow

## Hard "do NOT" list (carry-forward)

- **No pre-emptive SCP-R-005 deny flip.** Phase 4 Week ~41 (calendar ~2027-02-27) is canonical. Per-adopter ramp via `threshold-overrides: { SCP-R-005: deny }` is the only sanctioned promotion path.
- **No canonical-SDK-versions.yaml content.** Phase 1C ships this.
- **No cascade beyond 024C** until Phase 2 dispatch authorises (Wks 14-29 = calendar ~2026-08-23 onwards).
- **No token-package release before v1.4.0.** Design-team-paced.
- **No cost framing** (programme / opportunity / capacity / calendar-irreversibility). Per `feedback_no_cost_decision_gates.md`.
- **No mechanical auto-merge for D-050 ADR.** Operator-attended merge mandatory per Wave B Tier (ADR-class precedent established at D-049).
- **No PR #124 Dependabot bump merge** until TF-023E-002 closes (causes `startup_failure` per `policy-check-wrapper.yml` inline doc).

## Auth-surface deviation check

Wave D introduces a token-exchange step in `policy-check.yml`. This IS auth-surface code change. The R-cycle to R-fixpoint MET (R1 + R2 sub-agent dispatches) has been completed per `feedback_orchestrator_auth_surface_plan_review_default.md`. The plan-doc is now ready for Wave D Codex dispatch authorisation (operator-attended fire mandatory).

If Wave D dispatch surfaces a NEW architectural-scope question (beyond what's captured in the plan-doc + evidence files), file ASC + stand down for operator authorisation.

## Cross-tree memory paths

- `~/.claude/projects/-Users-amplience-Projects/memory/feedback_orchestrator_auth_surface_plan_review_default.md` — review dispatch shape
- `~/.claude/projects/-Users-amplience-Projects/memory/feedback_subagent_review_only_scope_must_be_enforced.md` — DO-NOT-EDIT mandate (sample-size-3: CT c565fd0 + Recommender V14 INT #2 + docs/ESTATE-CONVERGENCE.md)
- `~/.claude/projects/-Users-amplience-Projects/memory/feedback_asymptotic_trajectory_split.md` — cure-worse + Option A R4 mechanical override
- `~/.claude/projects/-Users-amplience-Projects/memory/feedback_r1_surface_must_cite_ci.md` — citation pair discipline
- `~/.claude/projects/-Users-amplience-Projects/memory/feedback_no_cost_decision_gates.md`

## Sanity check before chain-through

- [ ] `git checkout main` + `git pull origin main --ff-only`
- [ ] `git log --oneline -1` shows `02db884` or later
- [ ] `gh pr view 134 --json state` returns `{"state":"MERGED"}`
- [ ] `cat docs/plans/TF-PIM-001-impl-path-c-app-credential.md | head -20` shows v0.4 R-fixpoint MET status
- [ ] `ls docs/reviews/TF-PIM-001/impl-WP-R-cycle/R{1,2}/` shows 4 evidence files in each round dir
- [ ] `gh api repos/jrnb2024/standards-control-plane/branches/main/protection --jq '.required_status_checks.contexts'` returns `["policy-check / scp/policy-check", "check-invocation-log-entry"]`
- [ ] `cat docs/DECISIONS.md | grep -c "D-049.*ACCEPTED"` returns ≥ 1 (D-049 flip landed)

Once sanity checks pass, the natural next action is **Wave A — GitHub App authoring** (operator-attended GitHub UI ceremony per impl WP §4 Wave A Actions).
