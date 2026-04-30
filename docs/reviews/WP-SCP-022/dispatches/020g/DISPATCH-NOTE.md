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

- [x] **(i)** Header asserts `gh --version >= 2.40` (the unified
  branch-protection PUT shape used here has been stable since
  gh 2.x; 2.40 is a safety-margin floor — fix-round-1 corrected
  the original incorrect "rulesets API + admin flags" reasoning),
  `jq` on PATH, `git` on PATH, `python3` on PATH, `shasum` on
  PATH. Required PAT scope (`administration:write`) documented
  AND log-warned via stderr WARNING block before any mutation
  (per fix-round-1 COMP-002 closure).
- [x] **(ii)** Refuses without `--repo` and `--branch`. `--plan`
  flag prints both current branch-protection state AND proposed
  PUT payload (per fix-round-1 SAF-004 closure). `--enforce-admins`
  defaults true. `--no-enforce-admins` is silently ignored
  unless paired with `--i-understand-this-bypasses-the-gate`
  (per fix-round-1 SAF-003 closure); when both are set, a
  5-second pause + stderr warning gives the operator a chance
  to abort. `--i-understand-this-bypasses-the-gate` without
  `--no-enforce-admins` is rejected with an error (per
  fix-round-2 CORR2-003 closure).
- [x] **(iii)** Logs invocation (script SHA + operator + timestamp
  + target + before/after API response JSON) into the markdown
  block emitted at end of run. Operator pastes the block into
  `docs/reviews/WP-SCP-020/branch-protection-log.md` and commits.
  The log commit is part of the invocation procedure.
- [x] **(iv)** Bootstrap-only header: `## Bootstrap-only` clause
  in `--help` output explicitly states the script is not run
  unattended.

## Tracked-forward items (TF-020G-NNN)

- **TF-020G-001** (was SAF-007 acknowledged-deferred at fix-round-1):
  no interactive confirmation prompt at apply time. `--plan` is
  the documented confirmation step. Re-evaluate during 2026-07-21
  bus-factor-1 quarterly review: if the single-operator working
  pattern includes typo-prone targets (e.g. multiple adopter
  repos in one session), add an interactive confirmation prompt.
- **TF-020G-002** (from R2 safety SAF-R2-005): broaden CI guard
  to detect Jenkins (`JENKINS_URL`), Azure Pipelines
  (`TF_BUILD`), Bamboo (`bamboo_buildKey`). Most CI systems also
  set `CI=true`; the gap is theoretical. Add at WP-SCP-024 estate
  cascade time.
- **TF-020G-003** (from R2 safety SAF-R2-003): on stock macOS
  without GNU coreutils, `readlink -f` is unavailable; the
  fallback to bare `$0` reduces SHA256-self-hash reliability when
  the script is invoked relatively. Resolution: install coreutils,
  or invoke the script via absolute path. Documented; not a
  blocking issue.

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
