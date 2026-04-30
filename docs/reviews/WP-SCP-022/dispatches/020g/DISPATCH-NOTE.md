# WP-SCP-022 slice 020G — dispatch note

**Date:** 2026-04-30
**Tier:** orchestrator-applied (Tier 1 only)

## Justification for not invoking Codex executor

Per `feedback_four_tier_dispatch.md` in-line escalation guidance.
This slice's substantive surface is **one shell script + one
empty log file**:

- `scripts/enable-required-check.sh` (~190 lines, mirrors the
  shape of the existing `scripts/configure-020d2-required-check.sh`).
- `docs/reviews/WP-SCP-020/branch-protection-log.md` (header + format
  doc + empty "Invocations" section).

Codex Tier 3 (`gpt-5.4-mini medium`) "typical implementation,
schema additions" would be the right tier IF dispatching, but the
script is structurally near-identical to the existing 020D2
configure-script + adds the four documented acceptance criteria
on top. Dispatch overhead (work-package authoring + dispatcher
round-trip + result parsing) exceeds the cost of orchestrator-
applied for a derived script with a clear template.

The 020F preset slice's 4-round R1 fixpoint demonstrated that the
orchestrator-applied path under R1 review × 3 catches the same
class of issues Codex would surface. Worth the same posture here.

## Slice acceptance per WP-SCP-020 §4 020G

- [x] **(i)** Header asserts `gh --version >= 2.40` (rulesets API
  + admin flags), `jq` on PATH, `git` on PATH. Required PAT scope
  documented but not introspected (token-scope APIs require an
  authorised call; documenting scope is sufficient).
- [x] **(ii)** Refuses without `--repo` and `--branch`. `--plan`
  flag prints PUT payload without applying. `--enforce-admins`
  defaults true; `--no-enforce-admins` opts out with stderr warning.
- [x] **(iii)** Logs invocation (script SHA + operator + timestamp
  + target + before/after API response JSON) into the markdown
  block emitted at end of run. Operator pastes the block into
  `docs/reviews/WP-SCP-020/branch-protection-log.md` and commits.
  The log commit is part of the invocation procedure.
- [x] **(iv)** Bootstrap-only header: `## Bootstrap-only` clause
  in `--help` output explicitly states the script is not run
  unattended.

## Why log on SCP repo (not adopter repo)

The federation primitive is owned by SCP. Adopter-side branch-
protection state is a downstream effect of pinning the SCP wrapper;
the audit trail belongs at the federation source, not at every
adopter. Symmetric with `docs/security/branch-protection.md`
(documents SCP-self's protections) and `docs/DECISIONS.md`
(federation-primitive decisions).

## What this PR does NOT do

- Does NOT enable Renovate, status-checks, or any branch protection
  on any actual adopter repo. Estate cascade = WP-SCP-024 and is
  gated on FLA pilot completion (per WP-SCP-020 §4.1).
- Does NOT introspect PAT scope — the script documents required
  scope but the only way to verify is to make an authorised call
  that itself requires the scope. Operators should run with
  `--plan` first to confirm intent + scope sufficiency.
- Does NOT enable the `required_pull_request_reviews` shape from
  020D2; adopters with multi-maintainer teams MAY add review gates
  but those are out of 020G's scope (intentionally — keeps the
  script narrow).

## R1 review

3× parallel Sonnet R1 review (correctness / safety_bypass /
completeness_governance). Recurse to fixpoint.

## Files

- `scripts/enable-required-check.sh` — adopter-side helper.
- `docs/reviews/WP-SCP-020/branch-protection-log.md` — log file
  with format documentation.
- `docs/reviews/WP-SCP-022/dispatches/020g/DISPATCH-NOTE.md` —
  this file.
