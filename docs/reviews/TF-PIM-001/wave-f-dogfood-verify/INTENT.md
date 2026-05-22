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

## Evidence — to be captured after CI completes

Will be appended to this document post-CI:

- CI rollup URL (`gh pr view <N> --json statusCheckRollup,mergeStateStatus`)
- Workflow run URLs for each of the 4 required checks
- Workflow-selftest harness orchestrator job URL (should be SUCCESS — preserves the post-PR-#139 fix-forward state)

## Cross-references

- D-050 — App-credential surface ratification (ACCEPTED 2026-05-21)
- TF-PIM-001 plan-doc — `docs/plans/TF-PIM-001-impl-path-c-app-credential.md` §4 Wave F
- PR #139 merge commit — `7acc661`
- 5 open TFs from PR #139 close-out (filed in `docs/BACKLOG.md` Phase 12)
- Wave G + H — operator-attended (PIM canary + required-check restoration); next after Wave F closes

## Standdown

This PR opens for CI. On all-green → orchestrator captures evidence URLs + merges PR + STATUS.md ratchet (operator-attended if hook still blocks repo-root edits). If any required check fails → halt + surface to operator.
