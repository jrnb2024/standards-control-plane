# WP-SCP-022 continuation prompt — 2026-04-29 (afternoon, post-context-restart)

## Read first

- `~/.claude/projects/-Users-amplience-Projects-standards-control-plane/memory/MEMORY.md` and the linked memories.
- `STATUS.md` for top-level state.
- `docs/plans/WP-SCP-022-implementation-programme-plan.md` (v0.5 FIXPOINT) for the meta-plan.
- This file.

## Where the chain paused

Active slice: **020C.1 — waiver-aware Rego + rego-vs-python conflict-gate**.

Branch: `feature/wp-scp-020c1-waiver-aware-conflict-gate` on the `scp-track1` worktree at `/Users/amplience/Projects/scp-track1/`.

The slice was split into two parallel tracks per WP-SCP-022 §4.3 orchestrator-applied path:

### Track A — orchestrator-applied (LANDED at commit `cd0fd91`)

Sub-criteria (iii) + (iv): rego-vs-python conflict-gate adapter + fixtures + CI job + integration doctrine. Already committed and pushed:

- `tests/conflict_gate/{__init__,adapter,test_conflict_gate}.py`
- `tests/conflict_gate/fixtures/SCP-R-00{1,2}/{allow,deny}/`
- `docs/integrations/conflict-gate.md`
- `.github/workflows/conflict-gate.yml`

Local pytest: 4 SKIPPED (opa not on local PATH; CI runs them green).

### Track B — codex slim dispatch (IN FLIGHT when context closed)

Sub-criteria (i) + (v) + (vi): waiver-aware Rego, caller-side `.scp/rule-config.yaml` override, read-back to JSON summary + commit-status.

- Package: `docs/reviews/WP-SCP-022/dispatches/020c1/dispatch-package-slim.json`
- Package id: `wp-scp-020c1-rego-overlay-and-readback`
- Started: 2026-04-29 17:17 BST
- Timeout ceiling: 5400s (90 min) → expected to complete by ~18:47 BST
- Dispatcher PID at handoff: 20910 (zsh wrapper) / 20914 (codex_dispatch.py) — those processes were running independently of the Claude session, so they keep going across context restart.
- Result file: `/Users/amplience/Projects/scp-track1/docs/reviews/WP-SCP-022/dispatches/020c1/dispatcher-result-slim.json` — was 0 bytes at handoff; will populate when dispatch completes.

## First action on resume

Run these in parallel to determine codex outcome:

```bash
ps -ef | grep -E "codex_dispatch.py.*020c1" | grep -v grep
stat -f "%Sm %z bytes" /Users/amplience/Projects/scp-track1/docs/reviews/WP-SCP-022/dispatches/020c1/dispatcher-result-slim.json
git -C /Users/amplience/Projects/scp-track1 status
```

Three possible states:

### State 1 — codex completed cleanly (result file > 0 bytes, no codex process running, working tree has new staged/unstaged Rego + workflow + schema edits)

1. Read `dispatcher-result-slim.json` to confirm `status` field.
2. Inspect the working-tree diff: `git -C /Users/amplience/Projects/scp-track1 diff --stat`.
3. Run the slim package's verify_commands locally to sanity-check (paths in package_id slim).
4. Commit on the same branch:
   ```
   WP-SCP-022 slice 020C.1 (rule overlay + read-back): waiver-aware Rego + rule-config + commit-status
   ```
5. Push, then build R1 review packages (3× lenses: correctness, safety_bypass, completeness_governance) and dispatch via Sonnet R1. Pattern: copy `docs/reviews/WP-SCP-022/dispatches/020c/review-correctness-package.json` and adapt context_paths to include `tests/conflict_gate/`, all three rego files, the new schema, and the workflow.
6. Recurse to fixpoint per `feedback_recursive_adversarial_review.md`.
7. Open PR; merge to main.

### State 2 — codex still running

Wait or schedule a check. The codex process is independent of the Claude session, so just `ps -ef | grep codex_dispatch` to see if it's still alive. When the result file is non-empty, proceed as State 1.

### State 3 — codex failed / timed out (result file > 0 bytes with status="failed" or "timeout"; or process is dead and result file is still 0 bytes)

Per WP-SCP-022 §4.3, switch to orchestrator-applied for the rule overlay too. Estimated 60–90 min of careful Rego edits across `policies/SCP-R-001.rego`, `_002.rego`, `_003.rego` plus `policies/tests/` extensions, `schemas/rule-config.schema.json` (new), `schemas/policy-check-summary.schema.json` (extend), and `.github/workflows/policy-check.yml` (waivers + rule-config inputs). The slim dispatch package contains the full instruction text — use it as the orchestrator-applied spec.

## After 020C.1 lands

Track 1 remaining slices in order:

1. **020J** — Renovate shared preset
2. **020K** — adopter onboarding doc + ADOPT-005 self-cert
3. **020D1** — required-status-check `scp/policy-check` on SCP main
4. **020H pt 1** — observability metrics emit
5. **020E.a** — gate-helper hardening (already partly done at PR #50)
6. **USER-GATE-A0** — first paused human signoff (use the existing `scripts/wp_scp_022_gate_check.sh`; the operator email allowlist now includes `james.brooke@mapp.com`)
7. **020H pt 2** — observability dashboards
8. **020D2** — turn the gate from advisory to required + cut v1.0.0 tag
9. **USER-GATE-A** — Threshold A signoff: SCP gates itself on its own main

Track 2 (MCP server) slices 021B–021E have all landed. Slice 021F (HTTP transport) and 021G (signed-receipt verification client) remain — order them in after Track 1 hits Threshold A.

## Memories to revisit if anything feels wrong

- `feedback_protocol_over_shortcuts.md` — four-tier dispatch + 3× review is non-negotiable.
- `feedback_recursive_adversarial_review.md` — recurse review until fixpoint, no descoping.
- `feedback_dispatcher_compute_is_subscription_not_api.md` — don't quote dollar costs.
- `feedback_four_tier_dispatch.md` — the canonical pattern.
- `project_wp_scp_022_plan.md` — meta-plan summary.

## Threshold A definition (for goal-tracking)

SCP gates itself on its own `main` via the federation primitive's reusable workflow with a required-status-check, all three v1.0.0 Rego rules enforcing, conflict-gate green on every PR, and a v1.0.0 release tag cut. That's the user's stated finish line for "actually useful."
