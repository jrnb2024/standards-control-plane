# Continuation prompt — 2026-05-17 — 024C PIM canary Phase 1 AUTHORISED + Phase 2 stand-down

**Audience:** clean-context SCP session restart.
**Authored:** 2026-05-17 after Phase 0 ratification + PIM clean signal.
**Live as of:** SCP main HEAD `5ac9e65` (PR #119 OVERVIEW.md merged).
**Active branch:** `feature/wp-scp-024-024c-pim-canary` at `68d0b68` (fix-round-3); PR #118 ready-for-review (CI gate failing by design on `cascade-status: PENDING` until Phase 3 close).

---

## What just happened (cross-session orchestrator-mediated)

1. **PR #119 (docs OVERVIEW.md) merged** at `5ac9e65` 2026-05-17. Estate-visible canonical SCP documentation now lives at `docs/OVERVIEW.md` (441-line integrated reference: what / architecture / logical flows / platform-service integrations / current scope / future scope). README.md updated to point to it.

2. **PLAN-AUTH-FOUNDATION-007 Phase 0 RATIFIED 2026-05-16** at CT main HEAD `cb53268`. Both PRs merged: #343 (Phase 0 autonomous deliverables: 8 workstreams = REQ + STRAT + 5 ADRs/specs/runbooks) + #344 (Phase 0 close-out). 20/20 G-decisions ratified (G4 = canonical 0.7.1 on 2026-05-17). WS-0.23 cost-reauth COLLAPSED per operator direction "Cost is not an issue".
   - Full Phase 0 record (parent tree): `~/.claude/projects/-Users-amplience-Projects/memory/project_auth_foundation_phase0_2026_05_16.md`
   - SCP-slice mirror: `memory/project_auth_foundation_phase0_ratified_2026_05_16.md`
   - CT close-out doc: `~/Projects/control-tower/docs/programme/PHASE-0-CLOSEOUT.md`

3. **SCP-side WS-0.4 satisfied.** All 3 WP-SCP-024 §6 preconditions for 024C are closed:
   - (1) 024B-extras-1 merged ✅ `d7b16d0` 2026-05-12 (PR #113)
   - (2) FUP-ACC-INSTALL-TARGET-REPO-001 closed ✅ 2026-05-15 (ACC PRs #199 + #202)
   - (3) TF-024B-REQCHECK-ENABLE-001 closed ✅ 2026-05-13 (live API verified `["policy-check / scp/policy-check", "check-invocation-log-entry"]`)

4. **PIM-clean signal CONFIRMED 2026-05-17.** PIM main HEAD `9d3d695` (Phase C close-out); worktree clean, no branches/PRs in flight; no coordination-collision race window between PIM auto-merge cadence and 024C required-check enablement.

5. **024C Phase 1 AUTHORISED.** Operator-gated execution unblocked.

## Current SCP-side state

| Surface | State |
|---|---|
| Main HEAD | `5ac9e65` (OVERVIEW.md) |
| 024C branch | `feature/wp-scp-024-024c-pim-canary` at `68d0b68` (fix-round-3: scaffolder realigned to 41a5299 + Renovate auth-SDK exclusion + STATUS.md chain entries) |
| PR #118 | ready-for-review (flipped from DRAFT 2026-05-16); `mergeStateStatus: BLOCKED` BY DESIGN (`check-invocation-log-entry` fails on `cascade-status: PENDING` — finalises at Phase 3 close) |
| Scaffolder output | `~/Projects/scp-scaffolds/024c-pim/` (4 files: wrapper YAML @41a5299 + CODEOWNERS snippet + CASCADE-PR-BODY.md + MANIFEST.json) |
| CT cascade-start notification | `~/Projects/control-tower/governance/docs/notifications/SCP-ESTATE-CASCADE-START-2026-05-15.md` (drafted; operator-commits to CT main when convenient) |

## Sequence (run sequentially in fresh session)

### Step 1: Verify state before firing

```bash
cd /Users/amplience/Projects/standards-control-plane
git fetch origin
git checkout feature/wp-scp-024-024c-pim-canary
git status -sb
gh pr view 118 --repo jrnb2024/standards-control-plane --json state,mergeStateStatus,mergeable,isDraft,statusCheckRollup
# Expect: state OPEN, isDraft false, mergeStateStatus BLOCKED (CI fail on cascade-status PENDING by design), other checks pass

# Verify §6 preconditions still hold:
gh api repos/jrnb2024/standards-control-plane/branches/main/protection --jq '.required_status_checks.contexts'
# Expect: ["policy-check / scp/policy-check", "check-invocation-log-entry"]

# Verify scaffolder output still has correct pin:
grep "uses:" ~/Projects/scp-scaffolds/024c-pim/.github/workflows/policy-check-wrapper.yml
# Expect: uses: jrnb2024/standards-control-plane/.github/workflows/policy-check.yml@41a529908ef5355b82ca924ef0502fa5ec2fcc11
```

### Step 2: Operator-attended Phase 1 — PIM-side ceremony

Per WP-SCP-024 invariant 2 + `feedback_cross_project_coordination_patterns.md` Pattern 4: `enable-required-check.sh` is **bootstrap-only** (refuses CI=true). Operator-mediated invocation is mandatory at Step 2c.

**Step 2a — Install ACC kernel hook on PIM checkout.** Prerequisite: PIM repo cloned locally at `/path/to/pim` (replace placeholder).

```bash
TARGET_PIM=$(realpath /path/to/pim)
echo "TARGET_PIM resolves to: $TARGET_PIM"
git -C "$TARGET_PIM" rev-parse --git-dir >/dev/null && echo "git repo: OK"
[ -w "$TARGET_PIM" ] && echo "writable: OK"
[ ! -d "$TARGET_PIM/.acc" ] && echo "no existing .acc/: OK"
# All three checks must echo OK before proceeding
cd ~/Projects/acc
sudo bash scripts/install_acc_hook.sh --target-repo "$TARGET_PIM"
```

ACC PR #199 (`--target-repo PATH` mode) + PR #202 (dispatcher direct-write fallback) already shipped; operator-smoke-verified on Recommender + RI before merge.

**Step 2b — Open adopter PR on `mapp-pim/mapp-pim`.**

```bash
cd /path/to/pim
git checkout -b feat/scp-federation-primitive-adoption
cp -r ~/Projects/scp-scaffolds/024c-pim/.github/workflows/policy-check-wrapper.yml .github/workflows/
# Substitute CODEOWNERS placeholder BEFORE appending:
sed 's/@<adopter-CODEOWNERS-account>/@jrnb2024/' \
  ~/Projects/scp-scaffolds/024c-pim/.github/CODEOWNERS-snippet.txt \
  >> .github/CODEOWNERS
git add -A
git commit -m "feat: adopt SCP federation primitive (policy-check wrapper @ v1.0.0)"
git push -u origin feat/scp-federation-primitive-adoption
gh pr create --base main --head feat/scp-federation-primitive-adoption \
  --title "feat: adopt SCP federation primitive (policy-check wrapper)" \
  --body-file ~/Projects/scp-scaffolds/024c-pim/CASCADE-PR-BODY.md
```

Wait for CI to pass on the adopter PR (purely additive; wrapper should pass against PIM's existing code). Self-merge per single-operator mode.

**Step 2c — Enable required-check on PIM + log invocation.** Operator-attended (script refuses CI=true).

```bash
cd ~/Projects/standards-control-plane
scripts/enable-required-check.sh --repo mapp-pim/mapp-pim --branch main --plan   # dry-run first
scripts/enable-required-check.sh --repo mapp-pim/mapp-pim --branch main          # apply
```

Script emits invocation log markdown block. Paste verbatim into `docs/reviews/WP-SCP-020/branch-protection-log.md` as new entry. Commit to 024C branch + push.

**Step 2d — Post-merge live-state verification** (closes R1 SAF-001 log-forgery surface; per `feedback_r1_surface_must_cite_ci.md` citation discipline applies here too):

```bash
gh api repos/mapp-pim/mapp-pim/branches/main/protection \
  | jq '{required_status_checks: .required_status_checks.contexts, enforce_admins: .enforce_admins.enabled, required_signatures: .required_signatures.enabled}'
```

Output MUST show `"policy-check / scp/policy-check"` in `required_status_checks` + `enforce_admins.enabled = true`. Paste JSON into DISPATCH-NOTE under `## Live-state verification (Phase 1 close)` subsection. Commit + push.

### Step 3: Finalise cascade-status + ratify D-045

After Phase 1 + bake observation (artefact-based per CT reconciliation 2026-05-16 v0.2 — "treat the canary as proven"; no time-based gate), choose ONE of:

- **`cascade-status: onboarded`** (happy path): adopter PR merged + invocation log entry present + (eventually) Renovate cycle clean.
- **`cascade-status: onboarded-operator-bump`** (R-024-07 fallback): PIM has Renovate disabled; operator-bumped manually. Requires `TF-024X-renovate-mapp-pim-mapp-pim` row in STATUS.md matching the §5.2 regex spec.
- **`cascade-status: blocked-on-adopter-conflict`** (invariant 10): PIM has pre-existing conflicting workflow. Requires `TF-024X-conflict-mapp-pim-mapp-pim` reference in DISPATCH-NOTE.

Update `docs/reviews/WP-SCP-024/024C/DISPATCH-NOTE.md` → replace `PENDING` with finalised value.

File D-045 row in `docs/DECISIONS.md` per the ratification text already drafted in the DISPATCH-NOTE.

### Step 4: Post-impl R1 with citation pair

Per `feedback_r1_surface_must_cite_ci.md` third-recurrence escalation. Surface back to operator with BOTH citations:

```bash
# Citation 1 — CI run URL with terminal step green:
gh run list --repo jrnb2024/standards-control-plane --branch feature/wp-scp-024-024c-pim-canary --limit 3 --json conclusion,url,workflowName,status

# Citation 2 — PR-level aggregate gate:
gh pr view 118 --repo jrnb2024/standards-control-plane --json mergeStateStatus,statusCheckRollup
```

Both citations REQUIRED. Local pytest counts alone are not R1 evidence.

3-lens minimum per cardinal rule 2 (correctness / safety_bypass / completeness_governance).

### Step 5: Self-merge + Threshold A surface

```bash
gh pr merge 118 --squash --delete-branch --repo jrnb2024/standards-control-plane
```

After merge, surface terminal state. Threshold A criteria:
- ≥3 of 5 cohort adopters have `policy-check / scp/policy-check` as required-check on default branch
- Each onboarded has invocation log entry under branch-protection-log.md (or matching TF for blocked-on-adopter-conflict)
- Each onboarded survived ≥1 Renovate cycle merged clean (R-024-07 fallback bumps don't count)
- USER-GATE-E artefact signed

024C alone doesn't reach Threshold A (1 of 5). Threshold A surfaces at terminal Phase 2 close per PLAN-AUTH-FOUNDATION-007 (12-slice cascade Wks 14-29).

### Step 6: Stand down

Updated stand-down language:

> SCP clean + 024C cascade at Threshold A. Auth-foundation Phase 0 ratified 2026-05-16 (CT main HEAD cb53268; PRs #343 + #344 merged). Standing by for Phase 2 cascade slice schedule; SCP is the gating-rule authority for SCP-R-005 (Phase 4) and will receive a dedicated WS-1.6 SVC-003 amendment dispatch when CT Phase 1 reaches sub-phase 1C (Weeks 5-7 elapsed).

## Hard "do NOT" list (per orchestrator dispatch 2026-05-16)

- **No pre-emptive SCP-R-005 deny flip.** Phase 4 Week ~41 (calendar ~2027-02-27) is canonical.
- **No canonical-SDK-versions.yaml content.** Phase 1C ships this.
- **No cascade beyond 024C** until Phase 2 dispatch authorises (Wks 14-29 = calendar ~2026-08-23 onwards).
- **No FUP-SCP-V1-0-0-SHA-NAMING-001 hygiene cleanup.** P3 deferred per PLAN-AUTH-FOUNDATION-007 in-flight (defer until post-Phase 4 deny-flip).
- **No strawman amendment / move from CT canonical location.** CT-side concern.
- **No cost framing** (programme / opportunity / capacity / calendar-irreversibility). Per `feedback_no_cost_decision_gates.md` — operator direction "Cost is not an issue".

## Auth-surface deviation check (per orchestrator dispatch note 2)

If 024C Phase 1 introduces any auth-surface change at the BFF / token / cookie layer (it shouldn't — cascade install is Renovate preset + branch protection + federation primitive distribution, all governance), **STOP and surface to orchestrator**. Plan-stage 3-agent review on any auth-surface deviation per `feedback_orchestrator_auth_surface_plan_review_default.md` (parent tree).

## Cross-tree memory paths

For full discipline rule bodies (SCP memory carries pointer-mirrors):
- `~/.claude/projects/-Users-amplience-Projects/memory/feedback_no_cost_decision_gates.md`
- `~/.claude/projects/-Users-amplience-Projects/memory/feedback_r1_surface_must_cite_ci.md`
- `~/.claude/projects/-Users-amplience-Projects/memory/feedback_cross_project_coordination_patterns.md`
- `~/.claude/projects/-Users-amplience-Projects/memory/project_auth_foundation_phase0_2026_05_16.md`

## Sanity check before firing

- [ ] `git checkout feature/wp-scp-024-024c-pim-canary` succeeds
- [ ] `git status -sb` shows clean working tree
- [ ] `git log --oneline -3` shows `68d0b68 fix(024C): fix-round-3 …` at HEAD
- [ ] `gh pr view 118 --json isDraft` returns `{"isDraft":false}` (already flipped 2026-05-16)
- [ ] `gh api repos/jrnb2024/standards-control-plane/branches/main/protection --jq '.required_status_checks.contexts'` returns `["policy-check / scp/policy-check", "check-invocation-log-entry"]`
- [ ] Scaffolder output at `~/Projects/scp-scaffolds/024c-pim/` pins @41a5299
- [ ] PIM main HEAD = `9d3d695` (Phase C close-out 2026-05-17; verify via `git -C /path/to/pim log --oneline -1`)

Once sanity checks pass, fire Step 2 (operator-attended Phase 1).
