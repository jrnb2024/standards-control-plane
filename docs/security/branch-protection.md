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

Other branch protection knobs (`required_status_checks`,
`required_pull_request_reviews`, `enforce_admins`) are deliberately
NOT set in 020J. They land in:

- **020D1** — adds the wrapper that calls `policy-check.yml` reusable
  workflow at the v1.0.0-rc.1 commit-SHA, but does NOT yet make the
  resulting `scp/policy-check` context required.
- **020D2** — promotes `scp/policy-check` to required and cuts the
  `v1.0.0` tag.
- **020G** — branch-protection automation script for adopter
  onboarding.

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

The protections are configured via `scripts/configure-020j-protections.sh`,
which is idempotent (re-runs are no-ops when the desired state is
already in place):

```bash
./scripts/configure-020j-protections.sh
```

Requires `gh` authenticated with admin scope on the SCP repo. The
script reads `SCP_PROTECTION_REPO`, `SCP_PROTECTION_BRANCH`, and
`SCP_PROTECTION_TAG_PATTERN` env vars when set; defaults are
`jrnb2024/standards-control-plane-`, `main`, and `v*` respectively.

## How to verify

```bash
# required_signatures on main
gh api repos/jrnb2024/standards-control-plane-/branches/main/protection/required_signatures \
  --jq '.enabled'
# expected: true

# tag-protection ruleset
gh api repos/jrnb2024/standards-control-plane-/rulesets \
  --jq '.[] | select(.name == "scp-tag-protection-v") | {id, enforcement, target}'
# expected: a ruleset with target=tag, enforcement=active, non-empty id
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
