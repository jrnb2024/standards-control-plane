# SCP next-session prompt — WP-SCP-026 Shape C SHIPPED; 026F observation window OPEN

**Drafted:** 2026-05-26 evening (end of CHECKPOINT-A v2 autonomous run)
**Predecessor:** `docs/continuation-prompts/2026-05-26-checkpoint-A-phases-3-8-resume-v2.md` (the resume prompt that drove this run)
**Session character:** Next operator-attended session. No autonomous work assumed.
**Cardinal pre-flight (read FIRST):** verify acc-hook RESTORED (it should be — Phase 8.2 of the v2 prompt restored it autonomously at end-of-run). If a write tool is refused, restoration succeeded. Confirm via `cat .claude/settings.json | python3 -c "import json,sys; print(list(json.load(sys.stdin).get('hooks',{}).keys()))"` — expect `['PreToolUse']` (the original entry) and NOT `[]`.

---

## What landed in the 2026-05-26 evening run (CHECKPOINT-A v2)

| PR | Slice | Merge SHA | Description |
|---|---|---|---|
| #180 | WP-SCP-026 026E | `5ae7537` | ADOPT-001 §13 MCP integration runbook (~380 lines; §13-§16 renumbered to §14-§17) |
| #181 | WP-SCP-026 026C | `eed09cc` | ACC-RI canary handoff RFC (`docs/coordination/2026-05-26-WP-SCP-026-026C-ACC-RI-canary-handoff.md`) |
| #182 | Phase 5 Bundle A | `34371ea` | Scripts + validation (3 FUPs closed): scaffolder post-emit verify + smoke-test-before-flip + scp-verify-adopter-secrets.sh + ADOPT-001 §12.7.16c |
| #183 | Phase 5 Bundle B | `e409f01` | BACKLOG sweep (5 FUPs flipped CLOSED) |
| #184 | Phase 5 Bundle C | `3595ef1` | Defer-with-disposition + Renovate options enumeration |
| #185 | Phase 6 | `7236d4b` | WP-SCP-026-Z CT-prerequisites memo |
| #186 (this) | Phase 7 | TBD | STATUS + memory + continuation prompt |

**FUP totals for the run:** 5 CLOSED + 9 DEFERRED-WITH-DISPOSITION + 3 HELD-PENDING-RECURRENCE. Meets both ≥6-closure + ≥3-deferred targets.

**Cure-worse triggers:** none hit. All R-cycles converged in 1 fix-round or ACCEPT-first-pass.

## Notable next moves (operator-paced)

### Immediate (this week or next)

1. **026F observation window** — 4 weeks from 026C merge `eed09cc` → close on 2026-06-23.
   - **Action:** monitor RI dispatch logs / ACC orchestrator output for `tool_scp_consult_rules` invocations. The success criterion is ≥1 real dispatch + agent output references ≥1 returned rule_id/pattern_id.
   - **Where:** RI dispatch artefacts at `~/Projects/ri-est-p-ws-2/.acc/dispatches/` (or ACC's orchestrator logs depending on ACC's surfaced state).
   - **Outcome decision (D-056 at close-out):** (a) advance to WP-SCP-027 if demand signal arrives; (b) hold indefinitely if criterion met without signal; (c) re-scope if criterion not met.
   - **Anti-criteria** (any one ⇒ re-scope): zero invocations / doc-vs-code divergence persists / adopter onboarding fails.

2. **Z.2 fire pending CT prerequisites** (per PR #185 memo).
   - **CT-team action:** publish `control-tower/config/estate_repos.yaml` + `control-tower/governance/published/cosignal-manifest.json` + CT cosignal Ed25519 PUBLIC key.
   - **Operator decision D-1:** manifest signing-key custody — recommendation = local-machine for v1 (acknowledges D-031 bus-factor-1 + quarterly rotation per existing 2026-07-21/2026-07-30 review cadence).
   - **Operator decision D-2:** ACC SA UUID value — confirm with ACC team.
   - **Operator decision D-3:** sequencing — recommendation = CT-publishes-first then Z.2 fires.
   - **Z.2 itself is Tier 2 kernel-dangerous** and operator-attended; not for autonomous runs.

3. **Recommender (mf-intent-os) 024E resume** — FUP-024E-RECOMMENDER-DEFER-MANIFEST-STALE-001.
   - **Action:** resolve CT contract `manifest-verify` `ErrManifestStale` (CT contract refresh — operator-owned).
   - **Then:** `gh pr reopen 194 --repo jrnb2024/mf-intent-os` + push empty commit + wait all 4 required GREEN + merge + `scripts/enable-required-check.sh --repo jrnb2024/mf-intent-os --branch main --preserve-existing-contexts --require-recent-green-wrapper-run` (Bundle A's new flag).
   - **Then:** file DISPATCH-NOTE + branch-protection-log entry on SCP-side close-out PR; advances cohort cascade to 4 LIVE.

4. **shopify-app cohort cascade onboarding** (adopter #5 of 5) — FUP-WP-SCP-024-SHOPIFY-APP-ONBOARDING-001.
   - **Pre-flight:** confirm shopify-app local clone path + remote (probable `jrnb2024/shopify-app`); confirm no Recommender-style `manifest-verify` blocker.
   - **Ceremony:** same 4-step as mapp-doc-agent + Recommender; the new `scp-verify-adopter-secrets.sh` (Bundle A PR #182) gives a pre-flight one-liner to confirm both secrets present.
   - **Once shipped + bake observation clear:** cohort cascade complete (5 of 5 LIVE) → Threshold A close-out → WP-SCP-024 can FINAL-CLOSE.

### Medium-term (next 1-3 weeks)

5. **Renovate / Dependabot decision for SCP-wrapper auto-bump** — FUP-WP-SCP-024-RENOVATE-MARKER-ESTATE-WIDE-001 body now enumerates 3 options:
   - **(a) Renovate App org-wide** (Mend premium needed for postUpgradeTasks)
   - **(b) Dependabot per-repo** (matches SCP-self; no postUpgradeTasks support; 5× config)
   - **(c) Drop marker + operator-attended monthly bump cycle** (recommendation for v1)
   - **Decision is operator-attended; no autonomous default.**

6. **WP-SCP-EST series** (P1 in BACKLOG; operator-paced D-NNN ADRs):
   - WP-SCP-EST-001 (per-repo MCP proxy for SCP-self) — design after 026F observation outcome.
   - WP-SCP-EST-002 (self-orchestrate pattern: ACC vs Pattern 3 vs hybrid) — strategic ADR; depends on operator authoring.
   - WP-SCP-EST-003 (hook re-enablement) — depends on -002.

### Longer-term / observation-only

7. **2026-05-31** — D-021 atomic workday (per WP-SCP-019 hygiene reservation). Pre-written draft at `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`. SCP-022 §4.7 gate helper detects collisions.
8. **2026-07-02** — Phase 2 notice for WP-SCP-019 mode.bearer_legacy.
9. **2026-07-21** + **2026-07-30** — bus-factor-1 reviews per D-031.
10. **2026-09-30** — bearer-legacy close (operational; per project_d019_option_b_slide memory).

## Verification before any new work

Per `feedback_continuation_prompt_drift_vs_canonical_sources.md`:

1. Re-read `STATUS.md` (header + at-a-glance + 2026-05-26 evening chain rows).
2. Re-read `docs/decisions/D-054-wp-scp-026-shape-c-ratification-2026-05-25.md` + `D-055-WP-SCP-026-narrative-reconciliation-2026-05-26.md` (both should now be ACCEPTED post-merge).
3. Re-read `docs/plans/WP-SCP-026-mcp-consumer-integration-v1.md` §5 slice plan + §6 reservations.
4. Re-read `docs/coordination/2026-05-26-WP-SCP-026-026C-ACC-RI-canary-handoff.md` + `docs/coordination/2026-05-26-WP-SCP-026-Z-CT-prerequisites.md`.
5. Re-read `~/.claude/projects/-Users-amplience-Projects-standards-control-plane/memory/project_wp_scp_026_state.md` (refreshed 2026-05-26 evening).
6. `gh pr list --state open` to confirm no in-flight PRs from this run.
7. Verify acc-hook restoration: `cat .claude/settings.json | python3 -c "import json,sys; print(list(json.load(sys.stdin).get('hooks',{}).keys()))"`.

## Operator action required from this autonomous run

**None beyond reviewing the merged PRs at leisure.** All merges were autonomous per Phase 5/6/7 standard discipline; D-055 ADR + 026B CLI surface were operator-merged in session 1 before this resume run started.

## Halt conditions encountered

None. All phases completed inside the v2 prompt's success criterion.

## Cumulative WP-SCP-026 deliverable

**Shape C is COMPLETE.** SCP's MCP `consult_rules` tool now has:
- A working CLI shim (`scp-cli consult`) shipped + on PyPI install path.
- A canonical first-consumer pattern documented (RI canary) + cross-verified end-to-end.
- An adopter-facing runbook (ADOPT-001 §13) covering both integration paths.
- A retracted aspirational narrative (HTTP transport + signed receipts) parked under WP-SCP-027 with operator-attended demand-signal trigger.
- A coordination contract published for the ACC team.
- A 4-week observation window opening 2026-05-26 → 2026-06-23 to surface either real adoption signal (advance) or evidence-of-no-adoption (re-scope).

**Bus-factor-1 acknowledged + mitigated** per D-031 + D-040 + the existing quarterly review cadence.

🤖 Generated 2026-05-26 evening by [Claude Code](https://claude.com/claude-code) — CHECKPOINT-A v2 end-of-run continuation prompt for SCP session
