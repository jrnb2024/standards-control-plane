#!/usr/bin/env bash
# WP-SCP-020 slice 020D2 protections — idempotent applier.
#
# Promotes `scp/policy-check` from advisory to a required status
# check on `main`, enables enforce_admins, and sets the personal-
# account / single-operator branch-protection shape resolved at
# 020K (U-k closure): one approving review required, stale reviews
# dismissed, non-author-review NOT required (the operator self-
# approves; `require_review_from_non_author=true` is unsatisfiable
# in single-operator mode).
#
# Idempotent: re-running has no effect when the desired state is
# already in place.
#
# Authentication: requires `gh` authenticated with admin scope on
# the target repo. Run from any working directory.
#
# Once applied, every PR to `main` must:
#   1. Pass `scp/policy-check` (the federation primitive's gate).
#   2. Have at least one approving review (self-approval is the
#      only option in single-operator mode).
#   3. Have a verified signature on every commit (020J).
#   4. Pass under enforce_admins — admin override is OFF.
#
# Reference: docs/DECISIONS.md D-032; WP-SCP-020 §4 020D2; this
# slice's PR.

set -euo pipefail

REPO="${SCP_PROTECTION_REPO:-jrnb2024/standards-control-plane-}"
DEFAULT_BRANCH="${SCP_PROTECTION_BRANCH:-main}"
# Per WP-SCP-022 020D2.1 reconciliation (2026-04-30):
# The required-check context is the rendered GitHub Actions check-run
# name, NOT the bare context from WP-SCP-020 020B(xi). For a wrapper
# that calls the reusable workflow via `uses:`, the rendered name is
# `<wrapper-workflow-name> / <reusable-job-name>`. SCP self uses
# `policy-check / scp/policy-check`. Adopters use whatever wrapper
# workflow name they choose. The bare `scp/policy-check` context
# matches only the readback status posted by the reusable workflow's
# commit-status step.
REQUIRED_CONTEXT="${SCP_REQUIRED_CONTEXT:-policy-check / scp/policy-check}"
# Per WP-SCP-022 020D2.1 reconciliation: in personal-account /
# single-operator mode (per 020K U-k closure + D-031), GitHub
# forbids PR authors from approving their own PRs. With only one
# CODEOWNER (@jrnb2024) and only one operator, count=1 + codeowner
# review locks the operator out of every PR. Set count=0 (no review
# enforced) and code-owner reviews to false. CODEOWNERS still serves
# as documentation of who SHOULD approve when a second maintainer
# arrives. When that happens, flip count=1 + codeowner=true +
# require_review_from_non_author=true in one operation.
REQUIRED_REVIEW_COUNT="${SCP_REQUIRED_REVIEW_COUNT:-0}"
REQUIRE_CODE_OWNER_REVIEWS="${SCP_REQUIRE_CODE_OWNER_REVIEWS:-false}"

log() {
  printf '[020D2] %s\n' "$*"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

require_cmd gh
require_cmd jq

log "target repo: $REPO"
log "target branch: $DEFAULT_BRANCH"
log "required check context: $REQUIRED_CONTEXT"
log "required approving reviews: $REQUIRED_REVIEW_COUNT"

apply_full_protection() {
  log "applying full 020D2 branch protection on '$DEFAULT_BRANCH'..."

  # Use the unified protection endpoint to set every required field
  # in one call. The required_signatures field is preserved by the
  # dedicated endpoint (set in 020J); we re-assert it here so a
  # single API call leaves the branch in the canonical 020D2 state
  # regardless of starting state.
  gh api -X PUT "repos/${REPO}/branches/${DEFAULT_BRANCH}/protection" \
    -H "Accept: application/vnd.github+json" \
    --input - <<JSON >/dev/null
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["${REQUIRED_CONTEXT}"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": ${REQUIRED_REVIEW_COUNT},
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": ${REQUIRE_CODE_OWNER_REVIEWS},
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": false,
  "lock_branch": false,
  "allow_fork_syncing": false
}
JSON

  # Closes 020G R2 correctness CORR2-004: required_signatures is
  # NOT a documented field of the unified branch-protection PUT
  # body — it's a dedicated sub-resource. Calling POST on the
  # /required_signatures endpoint is the canonical shape. SCP-self
  # already had required_signatures enabled (via 020J's separate
  # call), so the prior buggy unified-PUT inclusion was a no-op
  # latent bug — this slice corrects it for symmetry with 020G's
  # adopter helper and to ensure idempotent re-runs of the 020D2
  # script don't rely on prior 020J state. Re-asserting via POST
  # is itself idempotent.
  gh api -X POST "repos/${REPO}/branches/${DEFAULT_BRANCH}/protection/required_signatures" >/dev/null

  log "verifying..."

  local current
  current="$(gh api -X GET "repos/${REPO}/branches/${DEFAULT_BRANCH}/protection")"

  local checks_strict
  checks_strict="$(printf '%s' "$current" | jq -r '.required_status_checks.strict // false')"
  local checks_contexts
  checks_contexts="$(printf '%s' "$current" | jq -r '.required_status_checks.contexts | join(",")')"
  local enforce_admins
  enforce_admins="$(printf '%s' "$current" | jq -r '.enforce_admins.enabled // false')"
  local sigs_enabled
  sigs_enabled="$(printf '%s' "$current" | jq -r '.required_signatures.enabled // false')"
  local review_count
  review_count="$(printf '%s' "$current" | jq -r '.required_pull_request_reviews.required_approving_review_count // 0')"
  local dismiss_stale
  dismiss_stale="$(printf '%s' "$current" | jq -r '.required_pull_request_reviews.dismiss_stale_reviews // false')"
  local codeowner_reviews
  codeowner_reviews="$(printf '%s' "$current" | jq -r '.required_pull_request_reviews.require_code_owner_reviews // false')"

  local fail=0
  if [ "$enforce_admins" != "true" ]; then
    echo "verification failed: enforce_admins.enabled = $enforce_admins (expected true)" >&2
    fail=1
  fi
  if [ "$checks_strict" != "true" ]; then
    echo "verification failed: required_status_checks.strict = $checks_strict (expected true)" >&2
    fail=1
  fi
  if ! printf '%s' "$checks_contexts" | grep -q -F "$REQUIRED_CONTEXT"; then
    echo "verification failed: required_status_checks.contexts does not include '$REQUIRED_CONTEXT' (got '$checks_contexts')" >&2
    fail=1
  fi
  if [ "$sigs_enabled" != "true" ]; then
    echo "verification failed: required_signatures.enabled = $sigs_enabled (expected true)" >&2
    fail=1
  fi
  if [ "$review_count" -lt "$REQUIRED_REVIEW_COUNT" ]; then
    echo "verification failed: required_approving_review_count = $review_count (expected ≥ $REQUIRED_REVIEW_COUNT)" >&2
    fail=1
  fi
  if [ "$dismiss_stale" != "true" ]; then
    echo "verification failed: dismiss_stale_reviews = $dismiss_stale (expected true)" >&2
    fail=1
  fi
  if [ "$codeowner_reviews" != "$REQUIRE_CODE_OWNER_REVIEWS" ]; then
    echo "verification failed: require_code_owner_reviews = $codeowner_reviews (expected $REQUIRE_CODE_OWNER_REVIEWS)" >&2
    fail=1
  fi

  if [ "$fail" -ne 0 ]; then
    exit 1
  fi

  log "branch protection verified ✓"
  log "  enforce_admins:                 $enforce_admins"
  log "  required check:                 $checks_contexts (strict=$checks_strict)"
  log "  required_signatures:            $sigs_enabled"
  log "  approving review count:         $review_count"
  log "  dismiss_stale_reviews:          $dismiss_stale"
  log "  require_code_owner_reviews:     $codeowner_reviews"
  log "  require_review_from_non_author: false (per 020K personal-account closure; not enforced in API)"
}

apply_full_protection

log "020D2 protections applied. Verify via:"
log "  gh api repos/${REPO}/branches/${DEFAULT_BRANCH}/protection"
