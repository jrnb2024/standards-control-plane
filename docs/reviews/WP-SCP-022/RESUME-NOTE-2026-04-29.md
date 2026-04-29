# WP-SCP-022 — Resume note (2026-04-29)

## Where we paused

The autonomous-dispatch chain stopped at **6 of 16 implementation slices merged**. Two slices (020C + 021E) hit a recurring Codex-timeout pattern in the prior session and were paused at fix-round-1 with their dispatch packages on the feature branches but no implementation work committed.

## What's on `main`

Commits since the WP-SCP-022 v0.5 plan landed (PR #36):

| PR | Slice | Subject |
|----|-------|---------|
| #35 | — | docs: 2026-04-28 governance refresh |
| #36 | — | WP-SCP-022 implementation programme plan v0.5 (FIXPOINT at R5) |
| #37 | 021B | MCP server scaffold + Ed25519 keygen + PyPI extras |
| #38 | 020B | reusable policy-check workflow scaffold |
| #39 | 020B.1 | workflow integration test harness + policy-check.yml fixture-path input |
| #40 | 021C | MCP tools (7) + SCP-MCP-E0NN error taxonomy |
| #41 | 020B.2 | scripts/scp-policy-check local-repro CLI |
| #45 | 021D | MCP resources + domain-map + signing-keys |

Plus 3 dependabot PRs open from `.github/dependabot.yml` added in 020B.2: #42 (download-artifact), #43 (checkout), #44 (upload-artifact). Ignore-or-merge per usual triage.

## In-flight feature branches at pause (origin retains)

- **`feature/wp-scp-020c-rego-rules`** — slice 020C (3 starter Rego rules SCP-R-001/002/003 + policies/README.md + CODEOWNERS + workflow regal+opa-fmt steps).
  - Branch state: `dispatch-package.json` + `consolidation-r1.json` + 3× R1 review JSONs + `fix-round-1/dispatch-package.json` + `fix-round-1/dispatcher-result.json` (timeout).
  - R1 found 1 CRIT + 10 MAJ — see `docs/reviews/WP-SCP-022/dispatches/020c/consolidation-r1.json` on this branch.
  - Headline R1 issues to close in fr1: silent-bypass in `scp_r_002_is_waiver_payload` (any-non-object array passes); break-glass references missing `schemas/waivers-file.schema.json` (now exists on main but check the path); SCP-R-002 missing required `reason` field; deny payload uses `msg` not `message` (mismatch with `schemas/policy-check-summary.schema.json`); fixture coverage gaps for SCP-R-003 manifest types and SCP-R-001 deny paths; `opa test ≥90%` coverage AC has no CI enforcement gate.
  - Codex fr1 timeout cause: package size + complexity (3 Rego rules + tests + workflow + README all in one shot). Resume strategy: split or apply orchestrator-fix per WP-SCP-022 §4.3 (orchestrator-applied path used successfully on slices 020B.2 + 021D).

- **`feature/wp-scp-021e-propose-stub`** — slice 021E (propose() hardening: rate-limit + dedupe + silent-rot banner + envelope fields + U-21-f resolution).
  - Branch state: same shape as 020C — dispatch package + R1 evidence + fr1 timeout result.
  - R1 found 6 MAJ — `docs/reviews/WP-SCP-022/dispatches/021e/consolidation-r1.json`.
  - Headline R1 issues to close in fr1: rate-limit caller_id from `os.getpid()` resets on server restart (DoS vector); `_current_signing_key_id()` returns sentinel string `'unconfigured-signing-key'` silently when keyring missing — leaks into every proposal envelope; SIGKILL between proposal-write and branch-create leaves orphan; ProposeRequest body has no `max_length` cap; banner text diverges from AC#4 spec.

## Remaining slices in autonomous-run scope

Track 1 (8 slices remaining): 020C (in flight) → 020C.1 → 020J → 020K → 020D1 → 020H part 1 → 020E.a → **[USER-GATE-A0 release sign-off]** → 020H part 2 → 020D2 → **[USER-GATE-A]**.

Track 2 (1 slice remaining): 021E (in flight) → **[USER-GATE-C]**.

## Codex-timeout pattern — resume diagnosis

Six consecutive Codex timeouts in the back half of the prior session:
- 020B.2 fr3 (twice; orchestrator-applied)
- 021D fr3 (once; orchestrator-applied)
- 020C initial (resolved by longer timeout)
- 021E initial (resolved by longer timeout)
- 020C fr1 (40min; 0 files)
- 021E fr1 (40min; 0 files)

OAuth was confirmed live throughout (smoke tests passed). Hypothesis: codex sandbox compute degraded under sustained 8-hour load OR specific dispatch-package shapes (long instructions with assertion-based verify_commands that codex iterates against) trip a slow path. Fresh-session resume should warm a clean codex sandbox; if timeouts recur immediately, suspect rate-limit or quota.

## How to resume in a fresh session

1. **Open the existing `feature/wp-scp-020c-rego-rules` and `feature/wp-scp-021e-propose-stub` branches** as worktrees (origin has the dispatch packages + R1 evidence + fr1 dispatch packages already committed):
   ```bash
   git worktree add ~/Projects/scp-track1 feature/wp-scp-020c-rego-rules
   git worktree add ~/Projects/scp-track2 feature/wp-scp-021e-propose-stub
   ```
2. **OAuth smoke test** before any dispatch (per `reference_four_tier_dispatch.md`):
   ```bash
   codex exec "reply with just hello and nothing else"
   claude -p "reply with just hello and nothing else"
   ```
3. **Retry fr1 codex on each** with the `fix-round-1/dispatch-package.json` already on each branch. If timeouts recur immediately (within 5 minutes of dispatch), abandon Codex and switch to **orchestrator-applied per WP-SCP-022 §4.3** — open the consolidation-r1.json, read the findings, edit the files in the worktree directly, then run R2 review against the result.
4. After both slices fixpoint and merge, **continue chain** with next pair: Track 1 → 020C.1 (waiver-aware Rego + Python/Rego conflict-gate adapter), Track 2 → end-of-Track-2 `USER-GATE-C` (you commit `docs/reviews/WP-SCP-022/gates/USER-GATE-C.md`).

## Memory-derivable state

The memory file `~/.claude/projects/-Users-amplience-Projects-standards-control-plane/memory/project_wp_scp_022_plan.md` was last updated to v0.4 state (during the plan-fixpoint cycle). It does NOT yet reflect the 6 merged implementation slices. A fresh session should refresh it from this RESUME-NOTE + the merged commit log on `main`.

## Cumulative spend (rough)

~$80–110 across 14 dispatch-rounds (5 plan-review rounds + 6 slice-fixpoint cycles, including failed timeouts). Within the $300 aggregate cap from WP-SCP-022 §8 R-022-07.

## What's NOT broken / what's safe

- All 8 merged PRs are durable on main; no rollback risk.
- The federation primitive's reusable workflow (slice 020B), selftest harness (020B.1), and local-repro CLI (020B.2) are all on main and functional.
- The MCP server's stdio scaffold (021B), tools (021C), and resources (021D) are all on main and tested (66 pytest green).
- The two in-flight branches don't break anything on main; they're parked for resume.
- D-021 reservation slot honoured throughout; helper script `scripts/wp_scp_022_gate_check.sh --check-d021` confirms.

## Decisions made during the session, not pre-planned

- Cross-slice extension authorised in 020B.1 fr1: the `fixture-path` input was added to slice 020B's `policy-check.yml` (not in 020B's original AC) because 020B.1's fixture-isolation finding could not be closed otherwise. Plan amendment landed alongside.
- `WP-SCP-021 §13` Resolution column added during 021D fr3 closing U-21-a/b/c/e/g/h. U-21-d/f/i remain open until later slices.
- Orchestrator-applies-the-fix workaround established as a valid §4.3 path when Codex consistently times out: review still validates outcome.

## Suggested first action in resume session

Read this file. Then grep `consolidation-r1.json` on each in-flight branch for the canonical findings list. Decide: retry codex, or orchestrator-apply.
