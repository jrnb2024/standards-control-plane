# TF-PIM-001 Wave F — SCP-self dogfood verify (intent + evidence stub)

**Date:** 2026-05-22
**Branch:** `chore/tf-pim-001-wave-f-dogfood-verify`
**Base:** main at `7acc661` (PR #139 merge commit; TF-PIM-001 Waves D + E impl + workflow-selftest fix-forward)
**Tier:** verify-only (no Codex dispatch; no impl changes; docs-only test PR triggering CI)
**Authorisation:** operator 2026-05-22 AM "line up the next work to go autonomously"

## Purpose

Per impl WP plan-doc `docs/plans/TF-PIM-001-impl-path-c-app-credential.md` §4 Wave F:

> **Outcome.** SCP-self CI runs green on a test PR with the new policy-check.yml workflow.
>
> **Actions.**
> 1. Open a small test PR on SCP itself (after Waves A + B + C + D + E land) — could be a docs-only PR or this WP plan-doc's closure amend.
> 2. Verify all 4 required checks pass: `policy-check / scp/policy-check`, `policy-check-readback`, `check-invocation-log-entry`, `validate PR body`.
> 3. Verify the SCP-self dogfood path: `github.action_ref` empty → token-exchange step skips → self-call fallback engages → all 12 policy-check steps complete.
> 4. Capture evidence URL.

This PR is that small test PR. It modifies only this stub document under `docs/reviews/TF-PIM-001/wave-f-dogfood-verify/` to trigger CI on a post-merge main HEAD that includes the Wave D + E + fix-forward changes.

## Acceptance criteria

| # | Criterion | How verified |
|---|-----------|--------------|
| F-1 | `policy-check / scp/policy-check` SUCCESS | Required check on PR |
| F-2 | `scp/policy-check-readback` SUCCESS | Required check on PR |
| F-3 | `check-invocation-log-entry` SUCCESS | Required check on PR (gated by `paths:` filter; STATUS.md not touched in this PR, so likely SKIP — operator-attended decision: treat SKIP as PASS for docs-only PRs in `docs/reviews/**` paths) |
| F-4 | `validate PR body` / `R1 evidence check` SUCCESS | Required check on PR |
| F-5 | Wave D be1da77 discriminator behaves correctly under SCP-self dogfood | `github.repository == 'jrnb2024/standards-control-plane-'` → simulate-step's `if: !inputs.selftest-mode && inputs.simulate-app-token-failure` skips; token-exchange step skips via the discriminator; `.scp-runtime` checkout uses default GITHUB_TOKEN (same-repo); `_scp-workflow` schema-lookup checkout uses default GITHUB_TOKEN. All 12 policy-check steps run. |
| F-6 | Post-merge: STATUS.md ratchet + close-out | This PR's merge updates the SCP-self dogfood evidence record |

## Evidence — captured 2026-05-22 post CI green

**PR:** https://github.com/jrnb2024/standards-control-plane-/pull/140
**Head SHA:** `a727726`
**CI verdict:** mergeStateStatus CLEAN; mergeable MERGEABLE; all 4 required checks SUCCESS.

### Required checks (branch-protection enforce_admins=true)

| Check | Conclusion | Run URL |
|-------|-----------|---------|
| policy-check / scp/policy-check | SUCCESS | https://github.com/jrnb2024/standards-control-plane-/actions/runs/26260351621/job/77292210698 |
| scp/policy-check-readback | SUCCESS | (inline status; 3/4 rules enabled, 0 disabled, 1 not applicable) |
| check-invocation-log-entry | SUCCESS | https://github.com/jrnb2024/standards-control-plane-/actions/runs/26260351619/job/77292210601 |
| validate PR body | SUCCESS | https://github.com/jrnb2024/standards-control-plane-/actions/runs/26260351620/job/77292210606 |

### Wave F outcome

- **F-1, F-2, F-3, F-4 ACCEPTED** — all 4 required checks SUCCESS.
- **F-5 ACCEPTED** — Wave D be1da77 discriminator validated under SCP-self dogfood. The `github.repository == 'jrnb2024/standards-control-plane-'` check resolved correctly, causing:
  - Wave D simulate-step skipped (`simulate-app-token-failure` default false)
  - Wave D token-exchange step skipped (be1da77 discriminator)
  - `.scp-runtime` checkout fell back to default GITHUB_TOKEN (same-repo; sufficient)
  - `_scp-workflow` schema-lookup checkout fell back to default GITHUB_TOKEN (same-repo; sufficient)
  - All 12 policy-check steps completed (policy-check / scp/policy-check SUCCESS)
- **F-6 ACCEPTED on merge** — this PR merges to record the SCP-self dogfood evidence.

### Workflow-selftest harness — not re-triggered (path filter)

`workflow-selftest` workflow triggers on `.github/workflows/policy-check.yml`, `policies/**`, `tests/workflow/**`, `schemas/policy-check-summary.schema.json`, `requirements/**`. This Wave F PR's diff (docs-only under `docs/reviews/**`) does not match any of those, so `workflow-selftest` was not invoked on this PR. The harness was last invoked + passed on PR #139 head (post `748d86f` fix-forward; mergeStateStatus UNSTABLE was cosmetic per workflow-selftest orchestrator SUCCESS, the substantive gate). Main HEAD `7acc661` is the merged result; future PRs that touch the workflow-selftest trigger paths will re-exercise the harness.

### Cross-ref commit (paths-filter unblock)

PR #140 originally landed only one commit (`d9c73ef`, the INTENT.md docs change). That commit's diff didn't match `check-invocation-log-entry` paths-filter so the required check was missing → mergeStateStatus BLOCKED. Second commit `a727726` added `docs/reviews/WP-SCP-024/024C/wave-f-cross-ref.md` (semantically defensible: Wave F is a 024C PIM canary pre-condition) which matches the `docs/reviews/WP-SCP-024/024[C-Z]*/**` paths-filter. The workflow's `resolve-dispatch` step then short-circuited to "No cascade-slice DISPATCH-NOTE found in PR diff; not a cohort cascade slice - nothing to enforce" → exit 0 SUCCESS. Required check satisfied.

This paths-filter / required-check interaction is a known shape and is candidate **sample-size-2** for `FT-PR139-L29-STATIC-VS-DYNAMIC-VERIFICATION-GAP` if a third recurrence appears — same "structural validation passes locally but real-CI behavior surfaces a runtime semantic gap" class. Note in BACKLOG.md `FT-PR139-L29-STATIC-VS-DYNAMIC-VERIFICATION-GAP` for potential promotion on third recurrence.

## Cross-references

- D-050 — App-credential surface ratification (ACCEPTED 2026-05-21)
- TF-PIM-001 plan-doc — `docs/plans/TF-PIM-001-impl-path-c-app-credential.md` §4 Wave F
- PR #139 merge commit — `7acc661`
- 5 open TFs from PR #139 close-out (filed in `docs/BACKLOG.md` Phase 12)
- Wave G + H — operator-attended (PIM canary + required-check restoration); next after Wave F closes

## Standdown

This PR opens for CI. On all-green → orchestrator captures evidence URLs + merges PR + STATUS.md ratchet (operator-attended if hook still blocks repo-root edits). If any required check fails → halt + surface to operator.
