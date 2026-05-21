# PR #139 close-out pickup — workflow-selftest cascade resolved + ready to merge

**Date:** 2026-05-21 (post fix-forward cycle)
**Branch:** `chore/tf-pim-001-wave-d-dispatch-authoring`
**Head SHA:** `748d86f`
**Status:** required CI green, mergeStateStatus UNSTABLE (cosmetic), MERGEABLE
**Authored by:** CT orchestrator (Opus 4.7) handing back to SCP session for close-out
**Operator authorisation:** "Hand back to SCP session for close-out + merge" (2026-05-21)

## What happened while you were stood down

Your stand-down surface reported workflow-selftest `startup_failure` on bc8b292 + flagged the SURFACE invariant. CT orchestrator picked up diagnosis from operator-attended side (not hook-bound). Found three cascading issues that compounded into a workflow-selftest fix-forward cycle.

### Fix-forward commits (all already pushed)

| SHA | What | Authored by |
|---|---|---|
| `bc8b292` | Wave D + E impl (your push) | SCP session |
| `c38c9c3` | `fix(workflow-selftest)`: grant attestations + id-token permissions on reusable-workflow callers — unblocked the **pre-existing-since-2026-05-03 startup_failure (100+ red runs estate-wide)** introduced by WP-SCP-023 023B's `attest-scorecard` job. GHA validates reusable-workflow caller permissions at startup BEFORE `if:` conditions are evaluated, so callers must grant the permissions the callee declares on every job — including `if:`-gated jobs that won't actually run. TF-023B-001 captured "workflow-selftest fixture" at 023B time but missed this structural permissions-grant requirement. | CT orchestrator |
| `1f104af` | `fix(policy-check)`: correct App-token-exchange guard for local reusable workflow context (attempt #1, used `github.action_repository` — turned out wrong, that variable doesn't apply to reusable workflows, only composite/JS actions). Documented the wrong path for future reviewers; same commit produced the next CI re-run that confirmed the discriminator failed. | CT orchestrator |
| `be1da77` | `fix(policy-check)`: correct self-call discriminator (hardcoded `github.repository != 'jrnb2024/standards-control-plane-'` — attempt #2, correct). Wave D's original `if: github.action_ref != ''` assumption was wrong (GHA sets action_ref to calling workflow's HEAD SHA for local reusable workflow calls too). Hardcoded path is brittle to repo rename but `repositories: standards-control-plane-` immediately below already hardcodes the same; both would break together. TF to switch to explicit `selftest-mode` workflow_call input is needed (see "TFs to file" below). | CT orchestrator |
| `748d86f` | `fix(workflow-selftest)`: add `if: always()` to fixture-simulate so it runs after by-design fixture-fail. With the if-guard fix, fixture-pass-policy-check went green for the first time in 100+ runs, exposing the next cascading issue: Wave E's new fixture-simulate-token-exchange-failure-policy-check job depended on fixture-fail (by-design failer) for sequencing without `if: always()`, so cascading-skipped → orchestrator's assertion failed on 'skipped' result. | CT orchestrator |

## Current CI state (head 748d86f)

```
Required checks (branch protection enforce_admins=true):
  ✓ policy-check / scp/policy-check          SUCCESS
  ✓ check-invocation-log-entry               SUCCESS

workflow-selftest harness inner jobs:
  ✓ validate-selftest-config                              success
  ✓ fixture-pass-policy-check / scp/policy-check          success ← first time in 100+ runs!
  ✓ stash-fixture-pass-summary                            success
  - fixture-pass / scp/attest-scorecard                   skipped (gated, correct)
  ✗ fixture-fail-policy-check / scp/policy-check          failure (BY DESIGN per workflow comment)
  - fixture-fail / scp/attest-scorecard                   skipped (gated, correct)
  ✗ fixture-simulate-token-exchange-failure-policy-check  failure (BY DESIGN — NEW fixture exercising end-to-end)
  - fixture-simulate / scp/attest-scorecard               skipped (gated, correct)
  ✓ workflow-selftest (orchestrator)                      SUCCESS ← THE SUBSTANTIVE GATE
```

`mergeStateStatus: UNSTABLE` is cosmetic GHA UI state (caused by inner by-design failures aggregating into workflow-overall conclusion=failure). Per workflow-selftest.yml's own comments since WP-SCP-022 020D1: "The substantive gate is the orchestrator's `workflow-selftest` job; green there means both fixtures behaved as expected."

`mergeable: MERGEABLE` and required checks are SUCCESS, so PR #139 merges via standard `gh pr merge` (no admin-merge bypass needed).

## Your pickup queue

### STEP 1 — Update PR #139 body
Append a section to the PR body documenting the fix-forward cycle. Suggested shape:

```markdown
## Fix-forward cycle (2026-05-21 post-impl)

Operator-attended Wave D + E dispatches landed clean (verify_commands 21/21 + 37/37 green;
scope_violations [] for both). Post-push CI surfaced workflow-selftest startup_failure
which diagnosed to pre-existing-since-2026-05-03 estate-wide regression (100+ red runs)
introduced by WP-SCP-023 023B's `attest-scorecard` job (caller-permissions validation
gap). Fold-in fixes authorised per cure-worse cardinal-rule-2 surface to operator.

- c38c9c3 — `fix(workflow-selftest)`: grant attestations+id-token on reusable-workflow callers
- 1f104af — `fix(policy-check)`: first if-guard attempt (`action_repository` discriminator wrong)
- be1da77 — `fix(policy-check)`: hardcoded discriminator (`github.repository != 'jrnb2024/...'`) ✓
- 748d86f — `fix(workflow-selftest)`: `if: always()` on fixture-simulate to handle by-design sibling failure

workflow-selftest orchestrator job now SUCCESS — first time in 100+ runs (sample-size-100+
estate-wide regression closed as a side-benefit of Wave D/E impl + fix-forward).
```

### STEP 2 — File 2 new P3 TFs
At `docs/tracked-forwards/` (or wherever your repo files TFs):

- **FT-PR139-selftest-mode-input-discriminator** (P3): Switch the hardcoded `github.repository != 'jrnb2024/standards-control-plane-'` discriminator in policy-check.yml (lines 139 + 159) to an explicit `selftest-mode` workflow_call input. Repo-rename-resilient + clearer intent. Requires: add input to policy-check.yml workflow_call, change both if-guards to `if: !inputs.selftest-mode`, pass `selftest-mode: true` from all 3 workflow-selftest caller jobs.
- **FT-PR139-L29-static-vs-dynamic-verification-gap** (P3, sample-size-1 candidate): The Wave D fix-forward cycle demonstrated that static verify_commands (L26+L27+L28 family) compound on structural correctness but plateau on dynamic-runtime semantics. Wave D's 21 grep-based probes all passed but missed: (a) `github.action_ref` semantic for local reusable workflows; (b) `github.action_repository` non-applicability to reusable workflows; (c) missing `if: always()` on a job sequenced after a by-design failer. Real-runtime exercise (working selftest harness) is what surfaced each. L29 candidate would address structural-vs-dynamic verification gap. **Promote to estate memo on second-cycle recurrence**.

### STEP 3 — Acknowledge/close your existing 3 R1 TFs
Your stand-down listed 3 TFs filed (`.acc/` gitignore + 2 MAJ doc-precision findings). Confirm those are still open at their paths; .acc/ gitignore should be addressed as part of close-out (it's a per-worktree state file from the kernel-hook install — see commit message of c38c9c3 context).

### STEP 4 — Close-out doc (optional but per established 4-doc shape)
If your discipline includes a close-out doc per PR, author one at the usual path with the fix-forward narrative + L29 candidate notation.

### STEP 5 — Merge PR #139
Standard merge (NOT admin-merge — required checks green):
```
gh pr merge 139 --squash --repo jrnb2024/standards-control-plane- \
  --subject "impl(TF-PIM-001 Wave D + Wave E): App token-exchange + selftest mock coverage + workflow-selftest fix-forward" \
  --body-file <(gh pr view 139 --repo jrnb2024/standards-control-plane- --json body --jq .body)
```

(Or via web UI — same outcome since required checks pass.)

### STEP 6 — Post-merge cleanup
- Delete branch (gh pr merge --delete-branch flag or web UI)
- Update STATUS.md: TF-PIM-001 Waves D + E DISCHARGED; workflow-selftest estate-wide regression closed
- Surface to operator: PR #139 merged; TF-PIM-001 Wave F (dogfood) ready for plan-doc authoring; 2 new P3 TFs filed

## Hook-state caveat

You reported being hook-bound for Edit/Write/python3-c/redirection in your stand-down. If still blocked:
- `gh pr edit --body` MIGHT be in your allowlist (different from `gh run view`) — try it
- If blocked, fire a Tier 3 Codex dispatch with scope_boundary covering the PR body + TF files + STATUS.md
- OR surface back to operator to set active-dispatch state manually

## Estate findings (separate orchestrator notes)

Two estate-impacting observations from this cycle, for your awareness (not your work):
1. **workflow-selftest broken estate-wide since 2026-05-03** — every PR merged since then was admin-merged or merged against the broken-selftest baseline (since workflow-selftest isn't in required-checks). The regression is now CLOSED for SCP-self-invocation context. Adopter cross-repo context untested but the changes are scoped to local-call paths so cross-repo behavior is unchanged.
2. **Sample-size 100+ confirms** the workflow-selftest harness has been non-functional at startup-level for ~3 weeks across all branches including dependabot. Worth a STATUS.md note + maybe a retroactive TF capturing "what should we have caught at 023B time" for methodology improvement.

Continue.
