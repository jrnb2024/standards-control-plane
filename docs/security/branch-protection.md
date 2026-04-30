# Branch and Tag Protection — SCP repo

This page documents the GitHub repository protections configured on the
SCP repo per WP-SCP-020 slice 020J. The protections are preconditions
for slice 020D1 (self-dogfood wrapper pinned at the v1.0.0-rc.1
commit-SHA) and 020D2 (required-status-check + v1.0.0 cut).

Reference: `docs/DECISIONS.md` D-030; `docs/plans/WP-SCP-020-policy-federation-primitive.md` §4 020J.

## Configured state (after 2026-04-30)

### Branch protection — `main`

- **`required_signatures: true`** — every commit reaching `main` must
  carry a verified signature.
  - GitHub-side squash-merges via the PR UI are auto-signed by
    GitHub's bot key (`noreply@github.com`), so PR-based merges
    remain frictionless and require no local GPG/SSH signing setup.
  - Direct un-attested commits to `main` are blocked at push time
    with the error `commit must be signed`.
  - The unsigned commit `bcfc706` (USER-GATE-C signoff, 2026-04-29) is
    grandfathered: required-signed-commits is forward-looking and
    only applies to new commits.

### Branch protection — `main` (added by 020D2 on 2026-04-30)

In addition to the 020J `required_signatures: true`, slice 020D2
applies the canonical promote-to-required posture per
WP-SCP-020 §4 020D2 + 020K personal-account closure:

- **`required_status_checks`** — `policy-check / scp/policy-check`
  is required with `strict: true` (PRs must be up-to-date with
  base before the check is evaluated). Closes governance B-2
  (the original reason SCP was built — a deterministic gate that
  adopters can pin and SCP itself is bound by).
  - **The required-context name is the rendered GitHub Actions
    check-run name**, NOT the bare `scp/policy-check` from
    WP-SCP-020 020B(xi). For SCP self, the wrapper workflow named
    `policy-check` calls the reusable workflow's job named
    `scp/policy-check`, which GitHub renders as
    `policy-check / scp/policy-check`. Adopters substitute their
    wrapper-workflow name. The bare `scp/policy-check` context
    matches only the readback status (a separate
    sibling-context post by the reusable workflow).
- **`enforce_admins: true`** — the admin (@jrnb2024) cannot
  bypass branch protection. Self-imposed discipline; the bus-
  factor-1 risk row in WP-SCP-020 §8 is acknowledged but not
  papered over.
- **`required_pull_request_reviews`** (personal-account /
  single-operator mode, per 020K U-k closure):
  - `required_approving_review_count: 0` — no review enforced.
    GitHub forbids PR authors from approving their own PRs;
    with @jrnb2024 as the only maintainer AND only CODEOWNER,
    `count >= 1` would lock the operator out of every PR
    (`gh pr merge --admin` is also blocked by `enforce_admins:
    true`). When a second maintainer onboards: flip to count=1
    + codeowner=true + non-author=true in one operation.
    CODEOWNERS still serves as documentation of who SHOULD
    approve.
  - `dismiss_stale_reviews: true` — preserves the discipline
    even when count=0; once any review IS recorded (e.g. from a
    future second maintainer), pushing new commits to a PR
    invalidates the prior approval.
  - `require_code_owner_reviews: false` — same single-operator
    reasoning as above.
  - `require_review_from_non_author: false` — same.

After 020D2, every PR to `main`:
1. Must pass `policy-check / scp/policy-check` (the federation
   primitive's gate).
2. Has no required-review enforcement (single-operator
   bus-factor-1 acceptance — see §8 of the plan).
3. Must have a verified signature on every commit (020J).
4. Cannot be bypassed by admin override.

Other knobs:

- **020G** — adopter-side branch-protection automation script
  (separate slice; this section documents SCP self only).

### Tag protection — `renovate/v*` pattern (added by 020F on 2026-04-30)

Parallel ruleset `scp-tag-protection-renovate-v` covering
`refs/tags/renovate/v*` — the SCP shared Renovate preset's tag
series. Closes 020F R1 safety review CRIT-SAFE-001 (preset
poisoning via force-pushed tag).

- Pattern: `refs/tags/renovate/v*` — matches every preset
  release tag.
- Rules: identical to the `v*` ruleset — `deletion`,
  `non_fast_forward`, `update` all blocked.
- `enforcement: active`, `bypass_actors: []`.
- Configured via `scripts/configure-020f-renovate-tag-protection.sh`.
  The script uses `jq --arg` for JSON construction (eliminates
  heredoc-interpolation injection surface) and asserts on the
  full ruleset state during verification (enforcement, all 3
  rule types, the include-pattern matches the expected value).

The two rulesets are siblings, not nested. The `v*` ruleset
covers federation-primitive release tags (`v1.0.0`, `v1.0.0-rc.1`).
The `renovate/v*` ruleset covers preset release tags
(`renovate/v1.0.0`). Both carry equal supply-chain weight: the
preset cascades Renovate config changes to every adopter that
extends it.

Reference: `docs/DECISIONS.md` D-034.

### Tag protection — `v*` pattern

Implemented as a Repository Ruleset named `scp-tag-protection-v`
(GitHub's legacy tag-protection API was deprecated 2024-08).

- Pattern: `refs/tags/v*` — matches every release tag.
- Rules:
  - `deletion` — release tags cannot be deleted.
  - `non_fast_forward` — release tags cannot be force-pushed (no
    history rewrite).
  - `update` — release tags cannot be updated to point at a different
    commit (re-tag).
- `enforcement: active` — applies to all actors including admins
  (`bypass_actors: []`). Single-operator mode acknowledged: the same
  admin who owns the `jrnb2024` account is the one publishing tags;
  the protection guards against accidental force-push, not against
  malicious admin action.

## Why these specifically

- **Tag mutation** is the supply-chain anchor. Adopters pin the
  reusable workflow as `@<commit-SHA>  # tag: v1.0.0`, where Renovate
  watches the tag for upgrade signals (slice 020F). If a tag could
  be silently re-pointed at a different commit, the comment-tag
  signal would falsely advertise a different release than the
  pinned SHA actually carries. The tag-protection rule prevents
  that drift.

- **Required-signed-commits** is the bootstrap-trust anchor. SCP's
  Rego bundle (`policies/**`) is the authoritative source of truth
  for downstream gates; its provenance must be cryptographically
  attested. PR-based squash-merges via GitHub satisfy this trivially;
  the rule blocks the failure mode where someone pushes an
  unattested change directly to `main`.

## How to apply / re-apply

Three idempotent appliers, one per slice. All three can be re-run
safely.

```bash
# 020J: required_signatures + tag-protection ruleset on `v*`
./scripts/configure-020j-protections.sh

# 020D2: required-status-check + enforce_admins + reviews on `main`
./scripts/configure-020d2-required-check.sh

# 020F: tag-protection ruleset on `renovate/v*` (preset releases)
./scripts/configure-020f-renovate-tag-protection.sh
```

All three require `gh` authenticated with admin scope on the SCP repo.
Env-var overrides:

- 020J: `SCP_PROTECTION_REPO`, `SCP_PROTECTION_BRANCH`,
  `SCP_PROTECTION_TAG_PATTERN` (defaults
  `jrnb2024/standards-control-plane-`, `main`, `v*`).
- 020D2: `SCP_PROTECTION_REPO`, `SCP_PROTECTION_BRANCH`,
  `SCP_REQUIRED_CONTEXT`, `SCP_REQUIRED_REVIEW_COUNT`,
  `SCP_REQUIRE_CODE_OWNER_REVIEWS` (defaults
  `jrnb2024/standards-control-plane-`, `main`,
  `policy-check / scp/policy-check`, `0`, `false`).
- 020F: `SCP_PROTECTION_REPO`, `SCP_RENOVATE_RULESET_NAME`,
  `SCP_RENOVATE_TAG_PATTERN` (defaults
  `jrnb2024/standards-control-plane-`,
  `scp-tag-protection-renovate-v`, `renovate/v*`).

## How to verify

```bash
# required_signatures on main
gh api repos/jrnb2024/standards-control-plane-/branches/main/protection/required_signatures \
  --jq '.enabled'
# expected: true

# 020J tag-protection ruleset (federation primitive release tags)
gh api repos/jrnb2024/standards-control-plane-/rulesets \
  --jq '.[] | select(.name == "scp-tag-protection-v") | {id, enforcement, target}'
# expected: a ruleset with target=tag, enforcement=active, non-empty id

# 020F tag-protection ruleset (Renovate preset release tags)
gh api repos/jrnb2024/standards-control-plane-/rulesets \
  --jq '.[] | select(.name == "scp-tag-protection-renovate-v") | {id, enforcement, target}'
# expected: a ruleset with target=tag, enforcement=active, non-empty id

# 020D2: required-status-check + enforce_admins + reviews
gh api repos/jrnb2024/standards-control-plane-/branches/main/protection \
  --jq '{
    enforce_admins: .enforce_admins.enabled,
    required_check: .required_status_checks.contexts,
    strict: .required_status_checks.strict,
    review_count: .required_pull_request_reviews.required_approving_review_count,
    dismiss_stale: .required_pull_request_reviews.dismiss_stale_reviews,
    codeowner_reviews: .required_pull_request_reviews.require_code_owner_reviews
  }'
# expected:
#   enforce_admins: true
#   required_check: ["policy-check / scp/policy-check"]
#   strict: true
#   review_count: 0
#   dismiss_stale: true
#   codeowner_reviews: false
```

## How to revert

If a critical incident requires temporarily disabling either
protection:

```bash
# disable required-signed-commits
gh api -X DELETE repos/jrnb2024/standards-control-plane-/branches/main/protection/required_signatures

# delete the tag-protection ruleset (replace <id> with the value from
# the verify command above)
gh api -X DELETE repos/jrnb2024/standards-control-plane-/rulesets/<id>
```

Document the revert in a fresh `D-NNN` decision row before applying.
The next quarterly review (per WP-SCP-020 §14 U-sec-2 single-operator
acknowledgement) reconciles the live state against the documented
state.

## Bus-factor-1 acknowledgement

Per the WP-SCP-020 §14 U-sec-2 closure, the SCP repo is
single-operator-owned (`@jrnb2024` admin). The configured protections
guard against accidental force-push and unsigned-commit drift, not
against deliberate admin override. Quarterly review cadence: every
2026 calendar quarter, the documented state in this file is
re-verified against the live repo state.

Next review: 2026-07-30.
