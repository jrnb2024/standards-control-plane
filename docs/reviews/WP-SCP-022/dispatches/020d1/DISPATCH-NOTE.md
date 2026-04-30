# WP-SCP-022 slice 020D1 — dispatch note

**Date:** 2026-04-30
**Tier path:** orchestrator-applied (Tier 1 only)
**Justification for not invoking Codex executor (Tier 3 or 4):** per
`feedback_four_tier_dispatch.md` in-line escalation guidance. The
substantive deliverable is `~25 lines of CI YAML` (the
`policy-check-wrapper.yml` wrapper file); Codex Tier 4
(`gpt-5.3-codex-spark`, "boilerplate / fixtures / CI YAML") would be
the right tier IF dispatching, but dispatch overhead exceeds the
authoring cost on a 25-line file with a known template.

**Why this slice IS HIGH-RISK despite the small surface:** the risk is
not in authoring the wrapper but in the *post-merge CI behaviour* —
this is the first real-PR gating of SCP's own repo. Per the WP-SCP-022
2026-04-30 AM continuation prompt risk forecast: "Expect 2-4 follow-up
commits to fix coverage gaps." Categories anticipated:

1. Real PR file types not in selftest fixture set (lib filter accepts
   yml|yaml|json|toml|hcl|ini|properties|cue|edn|xml — files like .py,
   .rego, .md are silently skipped, which is correct but verify).
2. services.yml shape variations (SCP's own services.yml — verified
   pre-PR to have `mode.user_oidc` declared at scp.local; should pass
   SCP-R-001).
3. SCP-R-002's narrowed scope on real waivers.json (currently `[]` —
   array root → no findings).
4. Conflict-gate fixture coverage (6 fixtures, 2 per rule × 2 rules in
   corpus, SCP-R-003 excluded; should not block on the wrapper PR
   diff which is purely workflow-yaml addition).

The CI fixpoint loop is **tightly orchestrator-driven** — read CI
output, diagnose, commit fix, retry. Codex dispatch round-trip per
fix (5+ min per cycle including dispatch + return + commit) is slower
than orchestrator-applied iteration.

## Wrapper file

`.github/workflows/policy-check-wrapper.yml`. Calls the SCP reusable
workflow at `@<SHA-Y>` where SHA-Y is the latest main commit pre-this-
PR (post-020K merge). Per WP-SCP-020 §3 sequence, slice 020H.1 cuts
v1.0.0-rc.1 from this PR's merge commit; a follow-up slice 020D1.1
ratchets the wrapper pin from `@<SHA-Y>` → `@<v1.0.0-rc.1-SHA>`.

## Slice acceptance

Per WP-SCP-020 §4 020D1:

- [ ] Wrapper file `.github/workflows/policy-check-wrapper.yml` added.
- [ ] Wrapper pins reusable workflow by 40-char commit SHA (per 020B(v)).
- [ ] Wrapper triggers on `pull_request` to main only (refuses fork PRs
  via head/base repo equality check).
- [ ] Wrapper declares `permissions: contents: read, statuses: write`
  per D-029.
- [ ] Wrapper declares no `secrets:` (caller's GITHUB_TOKEN is the
  ceiling).
- [ ] No `${{ inputs.* }}` or `${{ github.event.* }}` inside any
  `run:` block (the wrapper has no `run:` blocks; this is satisfied
  vacuously).
- [ ] Branch protection on `main` does NOT yet include
  `scp/policy-check` as a required check (020D2 flips it).
- [ ] Merge commit signed (SSH signing live since 2026-04-30 morning).
- [ ] CI green on the wrapper PR (the workflow runs against its own
  PR diff; expect 0 findings since the PR adds only YAML).

## R1 review

3× parallel Sonnet R1 review (correctness / safety_bypass /
completeness_governance) to be invoked at PR-open per "full process"
mandate. Packages: `review-{correctness,safety,completeness}-package.json`
in this dir; results: `review-{lens}.json`.
