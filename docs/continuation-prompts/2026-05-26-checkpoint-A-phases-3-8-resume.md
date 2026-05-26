# Autonomous-run resume — CHECKPOINT-A — WP-SCP-026 Phases 3-8

**Drafted:** 2026-05-26 PM (session checkpoint)
**Predecessor prompt:** `docs/continuation-prompts/2026-05-26-autonomous-WP-SCP-026-BCDE-FUP-sweep.md`
**Checkpoint trigger:** context budget reached the prompt's §"Acceptable split points" — after Phase 2 PR complete.

This prompt resumes the autonomous run from CHECKPOINT-A. Phases 0-2 are complete; Phases 3-8 remain.

---

## State at checkpoint

**PRs open from this session (both HOLD-FOR-OPERATOR):**
- **PR #176** — Phase 1 / 026B `scp-cli` shim. `Status: READY-FOR-OPERATOR-MERGE`. R1 + R2 R-FIXPOINT MET. 24 tests pass.
- **PR #177** — Phase 2 / 026D D-055 narrative reconciliation. `Status: READY-FOR-OPERATOR-MERGE`. 6 files / 25 lines retracted; D-055 ADR filed; scope expanded mid-Phase-2 per operator-decision Option 2.
- **This PR** (checkpoint bookkeeping) — autonomous-merge once CI green; 4 new FUPs filed + STATUS chain row + this resume prompt.

**Hook state:** acc-hook removed at session start; backup at `.claude/settings.json.acc-hook-backup`. Operator restore command in STATUS chain row. **Next session: hook state will determine whether autonomous writes work; if restored, the next session will need to re-disable OR establish an active dispatch.**

**Phases 3-8 deferred:**
- Phase 3 — 026E ADOPT-001 §13 MCP integration runbook (doc-only; autonomous-merge)
- Phase 4 — 026C ACC RI canary coordination RFC (doc-only; autonomous-merge; depends on PR #176 merge)
- Phase 5 — FUP closure bundles A/B/C (scripts + docs; autonomous-merge; ≥6 FUP closure target)
- Phase 6 — WP-SCP-026-Z CT-prerequisites memo (doc-only; autonomous-merge)
- Phase 7/8 — STATUS + memory + final continuation prompt

---

## Pre-flight (do this FIRST in the resume session)

1. **Verify hook state.** Check `cat .claude/settings.json` — does the `hooks.PreToolUse` block contain the acc-hook command? If yes: either (a) re-disable per operator authorisation (re-run the disable ceremony), or (b) establish an active dispatch in `.acc/run/` so the hook accepts writes, or (c) escalate to operator.

2. **Verify Phase 1 + Phase 2 PR state.** `gh pr view 176 --json state,mergeStateStatus,statusCheckRollup` + same for 177. If both still OPEN and HOLD-FOR-OPERATOR, proceed with Phases 3+. If 177 merged (D-055 ACCEPTED), proceed normally. If 176 merged (`scp-cli` in main), Phase 4 is unblocked.

3. **Read state docs.** STATUS.md (chain rows 5+6+7 from 2026-05-26 PM) + the predecessor prompt (`docs/continuation-prompts/2026-05-26-autonomous-WP-SCP-026-BCDE-FUP-sweep.md`) Phases 3-6 sections.

4. **Re-read the cardinal disciplines.** PR workflow estate-wide; no direct commits to main. 3-agent R1 on code/plan PRs (doc-only PRs allow lighter 3-lens). STATUS chain row catch-22 mitigation. Verify branch + staged set before commit.

---

## Phase 3 — WP-SCP-026 026E ADOPT-001 §13 MCP integration runbook [2-3h]

**Goal:** New §13 in `docs/adoption/ADOPT-001-project-onboarding.md` documenting how adopters wire SCP MCP into their repo. Shape C pattern: stdio MCP, no receipt validation, `scp-cli` wrapper.

**CRITICAL pre-flight (per `feedback_verbatim_claim_diff_verification.md`):** Read `~/Projects/ri-est-p-ws-2/.acc/mcp_server.py:298-340` to verify the canonical example's accuracy. If the example would diverge from real RI code, file SHIP-PROPOSAL + HALT (same class as the PyNaCl-snippet trap D-054 retracted).

**Section outline** (per the predecessor prompt §Phase 3):
- §13.1 Overview — 8 MCP tools via stdio; Shape C ratified per D-054/D-055; two paths (direct CLI vs per-repo MCP server)
- §13.2 Path (a) Direct CLI — `scp-cli consult --domain example` + expected JSON output
- §13.3 Path (b) Per-repo MCP server — `.mcp.json` registration + tool invocation example matching RI's actual pattern
- §13.4 No receipt validation in v1 — explicit statement; reference D-054 + D-055; forward-link to WP-SCP-027
- §13.5 First-consumer pattern (RI canary) — reference 026C coordination doc + ACC's PLAN-EST-P §3.3
- §13.6 Receipt validation as future-scope (WP-SCP-027) — forward-link + demand-signal mechanism

**R-cycle:** 3-lens doc-only R1 (correctness / safety_bypass / completeness_governance). R-FIXPOINT MET = all 3 ACCEPT or FIRE-WITH-FIXES.

**Files touched:**
1. `docs/adoption/ADOPT-001-project-onboarding.md` — new §13 (~200-300 lines)
2. `STATUS.md` — chain row (path-trigger)

**Merge:** AUTONOMOUS (doc-only; R1 evidence + CI sufficient per predecessor prompt §Operator-attended gates).

**Stand-down conditions:**
- RI verification reveals canonical example diverges from real RI code → SHIP-PROPOSAL + HALT (per `feedback_verbatim_claim_diff_verification.md`)
- Phase 2 PR #177 still OPEN at run-time → Phase 3 still proceeds (different file; no merge-conflict risk)

---

## Phase 4 — WP-SCP-026 026C ACC RI canary coordination RFC [30 min, AFTER Phase 1 merges]

**Goal:** Coordination RFC on SCP repo documenting the ACC-RI canary handoff contract for `scp-cli`. Does NOT touch ACC repo.

**Blocker:** Phase 1 PR #176 must merge first (RFC references `scp-cli` as a real shipped binary). If #176 still OPEN at run-time, defer Phase 4 to next session.

**File:** `docs/coordination/2026-05-26-WP-SCP-026-026C-ACC-RI-canary-handoff.md` (NEW)

**Content outline** (per predecessor prompt §Phase 4):
- Contract: `scp-cli consult --domain <X>` returns single-element JSON list wrapping `ConsultRulesResponse` dict
- Installation: `pip install standards-control-plane==1.4.0+` (post-026B release-tag-cut) OR staging Docker image
- ACC-side action: ACC team modifies `ri-est-p-ws-2/.acc/mcp_server.py:298-338` `tool_scp_consult_rules` to handle the dict output shape (it currently does — single-element list per RI's `isinstance(parsed, list)` check + the dict inside)
- Success criterion (026F observation, 4-week window): ≥1 real RI dispatch uses `tool_scp_consult_rules` + agent's output references ≥1 returned rule

**R-cycle:** light 2-lens (completeness + governance; coordination-only).

**Files touched:**
1. `docs/coordination/2026-05-26-WP-SCP-026-026C-ACC-RI-canary-handoff.md` (NEW)
2. `STATUS.md` — chain row

**Merge:** AUTONOMOUS.

---

## Phase 5 — FUP closure bundles A/B/C [6-8h, sequential]

**Per predecessor prompt §Phase 5.** ≥6 FUP closure target; ≥3 deferred-with-disposition.

### Bundle A — Scripts + validation [2-3h]
- `FUP-WP-SCP-024-SCAFFOLDER-EMIT-PREFLIGHT-001`: gh-api wrapper-repo check at end of `scripts/scaffold-downstream.sh`
- `FUP-WP-SCP-024-SMOKE-TEST-BEFORE-FLIP-001`: `--require-recent-green-wrapper-run` flag in `scripts/enable-required-check.sh`
- `TF-024D-001-ADOPT-001-12.7.16A-SECRETS-CEREMONY-ENUMERATE`: ADOPT-001 §12.7.16a + new `scripts/scp-verify-adopter-secrets.sh`

### Bundle B — Docs hygiene + BACKLOG sweep [1-2h]
- `SCP-073.sec`: create `SECURITY.md`
- BACKLOG closed-FUP sweep: verify + flip `FUP-CLEANUP-2-001-SCP-SELF-WRAPPER-BUMP` + any others flagged

### Bundle C — Defer + memo [<1h]
- Move sample-size-1 + post-incident FUPs to BACKLOG.md Phase 12 "Held / Defer-to-incident" subsection
- Update `FUP-WP-SCP-024-RENOVATE-MARKER-ESTATE-WIDE-001` with operator-decision-pending options
- Add deferral table per predecessor prompt §Bundle C

**R-cycle:** 3-lens R1 on each bundle PR (correctness / safety_bypass / completeness_governance).

**Merge:** AUTONOMOUS per standard discipline.

---

## Phase 6 — WP-SCP-026-Z CT-prerequisites memo [1-2h]

**Per predecessor prompt §Phase 6.** Doc-only memo documenting what CT must publish before Z.2 can fire.

**File:** `docs/coordination/2026-05-26-WP-SCP-026-Z-CT-prerequisites.md` (NEW)

**Content outline:**
- §1: What needs to exist on CT-side (`control-tower/config/estate_repos.yaml` + `control-tower/governance/published/cosignal-manifest.json` + CT cosignal Ed25519 PUBLIC key)
- §2: Operator decision points (manifest signing-key custody / ACC SA UUID / sequencing)
- §3: Recommended path (CT publishes first 1-2 days, THEN Z.2 fires)
- §4: Until Z.2 fires — SCP-R-006 stays inert (vacuous-pass on adopters who set `acc-cross-repo-caller-scoped: false`)

**R-cycle:** light 2-lens (completeness + governance; coordination-only).

**Files touched:**
1. `docs/coordination/2026-05-26-WP-SCP-026-Z-CT-prerequisites.md` (NEW)
2. `STATUS.md` — chain row

**Merge:** AUTONOMOUS.

---

## Phase 7 — STATUS + memory + continuation prompt [1h]

- STATUS.md at-a-glance updates for WP-SCP-026 (slices B/C/D/E shipped; F = 4-week observation post-026C merge)
- Memory updates at `~/.claude/projects/-Users-amplience-Projects-standards-control-plane/memory/`:
  - `project_wp_scp_026_state.md` (NEW) — current state of WP-SCP-026 across 6 slices
  - Update existing memories that reference receipt-signing or HTTP MCP transport — mark them as superseded by D-055
- `docs/continuation-prompts/2026-05-26-evening-WP-SCP-026-shipped.md` (NEW) — handoff for next operator session

---

## Phase 8 — Final summary PR [<30 min]

If any STATUS / memory / continuation-prompt updates didn't go in earlier phases, bundle into a single bookkeeping PR. Otherwise close-out.

**Operator action at end-of-run:**
- Click-merge PR #176 (Phase 1 / 026B `scp-cli`) when ready
- Click-merge PR #177 (Phase 2 / 026D D-055) when ready
- Restore acc-hook: `cp .claude/settings.json.acc-hook-backup .claude/settings.json && rm .claude/settings.json.acc-hook-backup`

---

## Cardinal disciplines (re-read these; they apply throughout)

- PR workflow estate-wide; no direct commits to main
- 3-agent R1 on code/plan PRs; doc-only PRs allow lighter 3-lens
- No silent descope; file forward
- No demo-scope thinking
- Cure-worse trigger discipline (per-WP)
- R1 evidence regex format on PR body (no bold tags on lens labels)
- STATUS.md chain row catch-22 mitigation
- Verify branch + staged set before commit
- Grep production before claiming
- HOLD-FOR-OPERATOR tags on Phase 1 + Phase 2 PRs — DO NOT MERGE AUTONOMOUSLY

---

## Halting conditions for the resume session

- Phase 3 RI verification reveals example divergence → SHIP-PROPOSAL + HALT (per `feedback_verbatim_claim_diff_verification.md`)
- Phase 4 PR #176 not yet merged → defer Phase 4 to next session
- Any cure-worse R2 trigger in Phases 3-6 → SHIP-PROPOSAL + HALT
- Context budget approaches 80% again → checkpoint after the in-flight PR completes; write STATUS + memory + nested checkpoint continuation prompt; stop cleanly

---

## Success criterion for the resume run

- ✓ ADOPT-001 §13 shipped (Phase 3 PR merged)
- ✓ ACC RI handoff RFC shipped (Phase 4 PR merged if PR #176 has merged; else deferred)
- ✓ 3 FUP bundle PRs shipped (Phase 5)
- ✓ WP-SCP-026-Z prerequisites memo shipped (Phase 6 PR merged)
- ✓ STATUS + memory + evening continuation prompt updated (Phase 7/8)
- ✓ ≥6 FUPs closed via the bundle PRs
- ✓ ≥3 FUPs deferred-with-disposition

🤖 Generated 2026-05-26 PM by [Claude Code](https://claude.com/claude-code) — CHECKPOINT-A resume prompt
