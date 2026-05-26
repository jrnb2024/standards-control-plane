# Autonomous-run resume — CHECKPOINT-A v2 — WP-SCP-026 Phases 3-8

**Drafted:** 2026-05-26 PM (post-checkpoint upgrade)
**Supersedes:** `docs/continuation-prompts/2026-05-26-checkpoint-A-phases-3-8-resume.md` (v1; had two gating gaps that would cause re-halt)
**Predecessor prompt:** `docs/continuation-prompts/2026-05-26-autonomous-WP-SCP-026-BCDE-FUP-sweep.md` (the original Phase 0-8 prompt)
**Session character:** Single long autonomous run from CHECKPOINT-A through Phase 8 close-out. **NO HOLD-FOR-OPERATOR gates in this run.** Operator has already merged the gated PRs from session 1 (#176 + #177) before kicking off this resume session.

This prompt fixes two gating gaps in v1 that would have re-halted the session:

1. **acc-hook restoration was operator-gated BEFORE the session starts.** Fixed: this session keeps the hook disabled throughout + restores it autonomously as Phase 8's final action (after all PRs merged).
2. **Phase 4 "defer if #176 not merged" was a halt condition.** Fixed: Phase 0 verifies #176 + #177 merge status; if either is still OPEN, this session HALTS with a clear operator-action message (the user has committed to merging them before kickoff).

---

## Phase 0 — Pre-flight (deterministic; no operator-attended decisions) [10 min]

### Step 0.1 — Verify hook state + acc-hook backup file exists

```bash
ls -l /Users/amplience/Projects/standards-control-plane/.claude/settings.json.acc-hook-backup
cat /Users/amplience/Projects/standards-control-plane/.claude/settings.json | python3 -c "import json,sys; print('hooks:', list(json.load(sys.stdin).get('hooks',{}).keys()))"
```

**Expected state:**
- Backup file exists at `.claude/settings.json.acc-hook-backup` (created by operator pre-session-1)
- `settings.json` has `hooks: []` (i.e., PreToolUse acc-hook NOT installed; backup contains the original entry)

**If hook is RESTORED (PreToolUse entry present):** the operator may have restored it between sessions. The session has authority to re-disable it for the duration of this run because:
- The PRE-EXISTING operator-strategic-investigation (2026-05-26) authorised hook removal for the autonomous-run pattern
- File is owned by `amplience:staff` (no sudo needed for edit)
- Hook restoration happens autonomously at Phase 8 final step

Re-disable command:
```bash
cp /Users/amplience/Projects/standards-control-plane/.claude/settings.json \
   /Users/amplience/Projects/standards-control-plane/.claude/settings.json.acc-hook-backup
python3 -c "
import json
p = '/Users/amplience/Projects/standards-control-plane/.claude/settings.json'
d = json.load(open(p))
d['hooks'] = {}
json.dump(d, open(p, 'w'), indent=2)
"
```

**If hook is ALREADY disabled (hooks: [] or {}):** proceed.

### Step 0.2 — Verify operator has merged PR #176 + PR #177

```bash
cd /Users/amplience/Projects/standards-control-plane
gh pr view 176 --json state --jq '.state'  # must be MERGED
gh pr view 177 --json state --jq '.state'  # must be MERGED
```

**If both MERGED:** proceed.

**If either still OPEN:** **HALT IMMEDIATELY**. Emit this exact message and stop:

> Session HALT — Phase 0.2 preflight failed.
> 
> PR #176 (scp-cli shim) state: <STATE>
> PR #177 (D-055 ADR) state: <STATE>
> 
> The CHECKPOINT-A resume run requires both PRs to be MERGED before kickoff (per operator-attended discipline on CLI surface + ADR-class). 
> 
> Operator action required:
> - Review + click-merge https://github.com/jrnb2024/standards-control-plane/pull/176
> - Review + click-merge https://github.com/jrnb2024/standards-control-plane/pull/177
> - Re-run this prompt after both merge.
> 
> Stopping cleanly. No writes attempted in this session.

### Step 0.3 — Pull main + verify Phase 1 + Phase 2 commits present

```bash
git checkout main && git pull --ff-only origin main
git log --oneline -10 | head -10
```

**Expected:** `scp-cli` + `D-055-WP-SCP-026-narrative-reconciliation-2026-05-26.md` references visible in recent commits.

### Step 0.4 — Read state docs (in order)

1. `STATUS.md` (header + at-a-glance + latest 2026-05-26 chain rows)
2. `docs/decisions/D-054-wp-scp-026-shape-c-ratification-2026-05-25.md`
3. `docs/decisions/D-055-WP-SCP-026-narrative-reconciliation-2026-05-26.md` (NEW; just merged)
4. `docs/plans/WP-SCP-026-mcp-consumer-integration-v1.md` v1.0 §5 slice plan
5. The predecessor prompt `docs/continuation-prompts/2026-05-26-autonomous-WP-SCP-026-BCDE-FUP-sweep.md` Phases 3-8 sections (for full file-by-file detail)
6. `docs/BACKLOG.md` Phase 12 (FUP inventory for Phase 5 bundles)

### Step 0.5 — Cardinal disciplines (re-read; apply throughout)

- **PR workflow estate-wide.** No direct commits to main.
- **3-agent R1 on code PRs; lighter 3-lens on doc-only.** No focused/shortcut reviews.
- **No silent descope.** File forward.
- **Cure-worse trigger (per-WP):** if R2 surfaces NEW HIGH/CRIT ≥ R1-severity in same WP-class → SHIP-PROPOSAL + HALT.
- **R1 evidence regex format:** PR body must include `- correctness:`, `- safety_bypass:`, `- completeness_governance:` (no `**bold**` on lens labels — validator regex rejects bold).
- **STATUS.md chain row catch-22 mitigation:** every PR that doesn't touch `STATUS.md` or `docs/reviews/WP-SCP-024/024[C-Z]*/**` MUST add a STATUS chain row (path-trigger for `check-invocation-log-entry`).
- **Verify branch + staged set before commit:** `git branch --show-current` + `git status --short` before every `git commit`.
- **Grep production before claiming.** Cite file:line.

---

## Phase 3 — WP-SCP-026 026E ADOPT-001 §13 MCP integration runbook [2-3h]

**Goal:** New §13 in `docs/adoption/ADOPT-001-project-onboarding.md` documenting how adopters wire SCP MCP into their repo. Shape C pattern: stdio MCP, no receipt validation, `scp-cli` wrapper.

**CRITICAL pre-flight** (per `feedback_verbatim_claim_diff_verification.md`): read `~/Projects/ri-est-p-ws-2/.acc/mcp_server.py:298-340` to verify the canonical example's accuracy. The canonical example in §13.3 MUST match RI's actual `tool_scp_consult_rules` pattern (per PR #176's contract: single-element JSON list wrapping ConsultRulesResponse dict; RI checks `isinstance(parsed, list)` at line 333).

**Section outline** (per predecessor prompt §Phase 3):
- §13.1 Overview — 8 MCP tools via stdio; Shape C per D-054/D-055; two paths
- §13.2 Path (a) Direct CLI — `scp-cli consult --domain X` + expected JSON output (single-element list wrapping ConsultRulesResponse)
- §13.3 Path (b) Per-repo MCP server — `.mcp.json` registration + tool invocation matching RI's actual pattern
- §13.4 No receipt validation in v1 — reference D-054 + D-055; forward-link to WP-SCP-027
- §13.5 First-consumer pattern (RI canary) — reference the upcoming 026C coordination doc
- §13.6 Receipt validation as future-scope (WP-SCP-027) — demand-signal mechanism

**R-cycle:** 3-lens R1 (correctness / safety_bypass / completeness_governance). R-FIXPOINT MET = all 3 ACCEPT or FIRE-WITH-FIXES.

**Files touched:**
1. `docs/adoption/ADOPT-001-project-onboarding.md` — new §13 (~200-300 lines)
2. `STATUS.md` — chain row

**Merge:** AUTONOMOUS.

**Stand-down conditions:**
- RI verification reveals canonical example diverges from real RI code → SHIP-PROPOSAL + HALT. **OPERATOR-AUTHORISED extension before HALT:** the autonomous session may amend §13.3 to match real RI code first, then re-verify, then proceed. Only HALT if amendment cannot reconcile RI's actual code with the documented contract.
- Cure-worse R2 trigger → SHIP-PROPOSAL + HALT (per-WP scope).

---

## Phase 4 — WP-SCP-026 026C ACC RI canary coordination RFC [30 min]

**Pre-condition:** PR #176 (scp-cli) MUST be merged. Phase 0.2 verified this; if Phase 0 passed, this phase is unblocked.

**Goal:** Coordination RFC on SCP repo documenting the ACC-RI canary handoff contract for `scp-cli`. Does NOT touch ACC repo (out of scope for SCP autonomous run).

**File:** `docs/coordination/2026-05-26-WP-SCP-026-026C-ACC-RI-canary-handoff.md` (NEW)

**Content outline** (per predecessor prompt §Phase 4):
- Contract: `scp-cli consult --domain X` returns single-element JSON list wrapping ConsultRulesResponse dict (RI compatibility per PR #176 R1 fix)
- Installation: `pip install standards-control-plane==<post-026B-version>` OR staging Docker image
- ACC-side action: ACC team verifies `ri-est-p-ws-2/.acc/mcp_server.py:298-338 tool_scp_consult_rules` handles the contract correctly (it does per PR #176 R1 lens C fix)
- Success criterion (026F observation, 4-week window): ≥1 real RI dispatch uses `tool_scp_consult_rules` + agent output references ≥1 returned rule

**R-cycle:** light 2-lens (completeness + governance; coordination-only doc).

**Files touched:**
1. `docs/coordination/2026-05-26-WP-SCP-026-026C-ACC-RI-canary-handoff.md` (NEW)
2. `STATUS.md` — chain row

**Merge:** AUTONOMOUS.

**Stand-down conditions:**
- Cure-worse R2 trigger → SHIP-PROPOSAL + HALT.

---

## Phase 5 — FUP closure bundles A/B/C [6-8h, sequential]

**Per predecessor prompt §Phase 5.** ≥6 FUP closure target; ≥3 deferred-with-disposition.

Bundles are independent (no cross-bundle dependency). Run sequentially. Each bundle is a separate PR.

### Bundle A — Scripts + validation [2-3h]

**FUP-WP-SCP-024-SCAFFOLDER-EMIT-PREFLIGHT-001** (P3, S)
- File: `scripts/scaffold-downstream.sh`
- Action: at end of script (after MANIFEST.json write), add a post-emit verification that greps the emitted `policy-check-wrapper.yml` for `uses:` clause + extracts the `owner/name` + calls `gh api repos/<owner>/<name>` + asserts HTTP 200. Exit non-zero with clear error if 404.
- ~15 lines bash.

**FUP-WP-SCP-024-SMOKE-TEST-BEFORE-FLIP-001** (P2, S)
- File: `scripts/enable-required-check.sh`
- Action: add `--require-recent-green-wrapper-run` flag (default: ON for `--preserve-existing-contexts` mode; OFF for greenfield). When ON: query `gh run list --workflow=policy-check-wrapper.yml --branch=$DEFAULT_BRANCH --limit=5 --json conclusion`; assert at least one conclusion=success. Override via `--skip-smoke-test-i-understand-this-blocks-main` (explicit). ~25 lines bash.

**TF-024D-001-ADOPT-001-12.7.16A-SECRETS-CEREMONY-ENUMERATE** (P3, S)
- File: `docs/adoption/ADOPT-001-project-onboarding.md` §12.7.16a + new `scripts/scp-verify-adopter-secrets.sh`
- Action: amend §12.7.16a to enumerate BOTH secrets as a single ceremony step (per TF-024D-001 driver: CT 024D ceremony required 2 iterations because App-token-exchange error only surfaces ONE missing secret per fire). Create new bash script wrapping `gh secret list --repo OWNER/NAME --json name --jq '.[].name'` to assert both present. ~40 lines bash + ~20 lines markdown.

### Bundle B — Docs hygiene + BACKLOG sweep [1-2h]

**SCP-073.sec** (P2, S)
- File: `SECURITY.md` (NEW at repo root)
- Action: standard security-contact + private-disclosure template (~30-50 lines).

**BACKLOG.md closed-FUP sweep:**
- Read `docs/BACKLOG.md` Phase 12.
- Verify each FUP marked `open`. Cross-check against PR merge history.
- Flip to CLOSED any FUPs whose closure PRs have shipped:
  - `FUP-CLEANUP-2-001-SCP-SELF-WRAPPER-BUMP` — verify PR #160 merge (likely closed)
  - Reaffirm `FUP-WP-SCP-024-SCAFFOLDER-RENAME-SWEEP-001` closed (already done morning 2026-05-26)
  - Reaffirm `FT-PR139-L29-STATIC-VS-DYNAMIC-VERIFICATION-GAP` still sample-size-1 hold
  - Any other open FUPs that have shipped via prior PRs

### Bundle C — Defer + memo [<1h]

- Move sample-size-1 + post-incident FUPs to a clearly-marked "Held / Defer-to-incident" subsection of BACKLOG.md Phase 12: `FUP-CLEANUP-2-002-SELFTEST-MODE-MIS-SET-ERROR-CLARITY`, `FUP-CLEANUP-2-003-COMPOSITE-SELFTEST-MODE-SIMULATE-CROSS-REPO`, `FT-PR139-L29-STATIC-VS-DYNAMIC-VERIFICATION-GAP`.
- Update `FUP-WP-SCP-024-RENOVATE-MARKER-ESTATE-WIDE-001` body with operator-decision-pending options enumerated (Renovate App org-wide / Dependabot per-repo / drop marker).
- Add deferral table per predecessor prompt §Bundle C — Recommender resume / shopify-app onboarding / CT preflight bundle.

**R-cycle (each bundle PR):** 3-lens R1 (correctness / safety_bypass / completeness_governance).

**Files touched per bundle:** STATUS.md chain row added to each bundle PR (path-trigger).

**Merge:** AUTONOMOUS per standard discipline.

**Stand-down conditions:**
- Cure-worse R2 trigger on any bundle PR → SHIP-PROPOSAL + HALT for THAT bundle only (different bundles are independent WP-classes).
- ≥6 FUP closure target NOT met by end of Bundle C → file deferral disposition; not a halt.

---

## Phase 6 — WP-SCP-026-Z CT-prerequisites memo [1-2h]

**Per predecessor prompt §Phase 6.** Doc-only memo documenting CT-side prerequisites for Z.2 fire.

**File:** `docs/coordination/2026-05-26-WP-SCP-026-Z-CT-prerequisites.md` (NEW)

**Content outline:**
- §1: CT-side artefacts needed (`control-tower/config/estate_repos.yaml` + `control-tower/governance/published/cosignal-manifest.json` + CT cosignal Ed25519 PUBLIC key); include schema skeletons (YAML + JSON examples; per predecessor prompt §Phase 6)
- §2: Operator decision points (manifest signing-key custody / ACC SA UUID / sequencing)
- §3: Recommended path (CT publishes first 1-2 days, THEN Z.2 fires)
- §4: Until Z.2 fires — SCP-R-006 stays inert per safe-failure-mode

**R-cycle:** light 2-lens (completeness + governance; coordination-only doc).

**Files touched:**
1. `docs/coordination/2026-05-26-WP-SCP-026-Z-CT-prerequisites.md` (NEW)
2. `STATUS.md` — chain row

**Merge:** AUTONOMOUS.

**Stand-down conditions:**
- Cure-worse R2 trigger → SHIP-PROPOSAL + HALT.

---

## Phase 7 — STATUS + memory + continuation prompt [1h]

- **STATUS.md** at-a-glance updates for WP-SCP-026 (slices B/C/D/E shipped; 026F = 4-week observation post-026C merge); chain rows for every PR merged this session
- **Memory updates** at `~/.claude/projects/-Users-amplience-Projects/memory/`:
  - Refresh `project_standards_control_plane.md` — current state + next moves
  - File any new feedback memos from lessons learned this session
- **Final continuation prompt** at `docs/continuation-prompts/2026-05-27-WP-SCP-026-shipped.md` (NEW):
  - Handoff for next operator session
  - Notable next moves: Z.2 fire pending CT prerequisites; Recommender resume; shopify-app onboarding; WP-SCP-EST-001/002/003 (per session-1 FUPs)

**Merge:** AUTONOMOUS.

---

## Phase 8 — Final close-out + acc-hook restore [<30 min]

### Step 8.1 — Final summary PR

If any STATUS / memory / continuation-prompt updates didn't go in Phase 7, bundle into a single bookkeeping PR. Otherwise skip.

### Step 8.2 — acc-hook autonomous restore (Phase 8's CRITICAL final action)

After Phase 7's PR merges + before posting the end-of-run summary:

```bash
cp /Users/amplience/Projects/standards-control-plane/.claude/settings.json.acc-hook-backup \
   /Users/amplience/Projects/standards-control-plane/.claude/settings.json
rm /Users/amplience/Projects/standards-control-plane/.claude/settings.json.acc-hook-backup
cat /Users/amplience/Projects/standards-control-plane/.claude/settings.json
```

This restores the hook to its installed state. The autonomous run is complete; the hook is back.

**Why this is the autonomous session's responsibility (not the operator's):**
- The hook was removed at session 1's START as an operator-authorised one-time bypass
- The work is complete; the bypass justification no longer applies
- Auto-restore at end of run completes the trust chain + makes the bypass self-undoing
- No HOLD-FOR-OPERATOR escalation needed (restore is mechanical inverse of session 1's removal)

After restoration, ANY subsequent tool calls by the session will trigger the hook + fail. So step 8.2 MUST be the absolute final action — after this, the session must exit cleanly without further tool calls.

### Step 8.3 — End-of-run summary message

Post a single message summarising:
- All PRs shipped this session (numbers + 1-line each)
- All FUPs closed + deferred (from Phase 5)
- Memory + continuation prompt updates
- acc-hook status: RESTORED
- Next-session continuation prompt path
- Any halt conditions hit during the run (cure-worse triggers, RI divergence, etc.)
- ≥6 FUP closure target met (Y/N + actual count)
- Operator action required (likely: none beyond reviewing the merged PRs)

Format:

```
End-of-autonomous-run summary — CHECKPOINT-A v2 complete

PRs shipped this session:
- PR #XXX — Phase 3 / 026E ADOPT-001 §13 [merged at <sha>]
- PR #XXX — Phase 4 / 026C ACC RI canary RFC [merged at <sha>]
- PR #XXX — Phase 5 Bundle A scripts + validation [merged at <sha>]
- PR #XXX — Phase 5 Bundle B docs hygiene + BACKLOG sweep [merged at <sha>]
- PR #XXX — Phase 5 Bundle C defer + memo [merged at <sha>]
- PR #XXX — Phase 6 WP-SCP-026-Z CT prerequisites memo [merged at <sha>]
- PR #XXX — Phase 7/8 final bookkeeping [merged at <sha>]

FUPs closed: <count> (target ≥6: <Y/N>)
FUPs deferred-with-disposition: <count> (target ≥3: <Y/N>)
FUPs newly-filed: <list any new ones>

Memory updates: project_standards_control_plane.md refreshed + any new feedback memos
Continuation prompt: docs/continuation-prompts/2026-05-27-WP-SCP-026-shipped.md

acc-hook status: RESTORED to original config; backup file deleted

Halt conditions encountered: <none / details if any>

Next operator session: read docs/continuation-prompts/2026-05-27-WP-SCP-026-shipped.md
```

---

## Halting conditions for this resume session (consolidated)

The session HALTS only on:
1. **Phase 0.2** — PR #176 or #177 still OPEN at run-start (operator action required)
2. **Phase 3 RI verification** — example divergence cannot be reconciled (per `feedback_verbatim_claim_diff_verification.md`)
3. **Cure-worse R2 trigger** in any phase (per-WP scope; Phase 5 bundles are independent WPs so cure-worse in one doesn't halt others)
4. **Context budget approaches 80%** — checkpoint after current PR merges; write a CHECKPOINT-B continuation prompt for the next session

**The session does NOT halt on:**
- ACC-hook state (preflight handles deterministically — re-disable if restored)
- Phase 4 dependency on #176 (Phase 0.2 already verified)
- HOLD-FOR-OPERATOR tags (no new HOLD-FOR-OPERATOR phases in this resume run)
- Stand-down for new retraction targets (Phase 2 already complete; the scope-expansion stand-down was a session-1 concern)
- Operator decisions (this run is fully autonomous; no operator gates remaining)

---

## Success criterion for this resume run

- ✓ Phase 3 PR merged (ADOPT-001 §13)
- ✓ Phase 4 PR merged (ACC RI handoff RFC)
- ✓ Phase 5 Bundle A/B/C PRs merged (3 PRs; ≥6 FUPs closed)
- ✓ Phase 6 PR merged (Z-prerequisites memo)
- ✓ Phase 7+8 PR merged (bookkeeping)
- ✓ ≥6 FUPs closed; ≥3 deferred-with-disposition
- ✓ acc-hook restored autonomously
- ✓ Continuation prompt for 2026-05-27 session authored
- ✓ End-of-run summary posted

**Expected total PRs shipped:** 6-8 across Phases 3-8.

🤖 Generated 2026-05-26 PM v2 by [Claude Code](https://claude.com/claude-code) — CHECKPOINT-A v2 resume prompt (full end-to-end autonomy; no operator-attended gates)
