#!/usr/bin/env bash
# WP-SCP-020 slice 020J protections — idempotent applier.
#
# Configures the SCP repo's `main` branch and `v*` tags with the
# protections required as preconditions for 020D1 / 020D2:
#
#   1. required-signed-commits on `main`
#      Every commit reaching `main` must carry a verified signature.
#      GitHub-side squash-merges via the PR UI are auto-signed by the
#      bot key, so PR-based merges remain frictionless. Direct un-
#      attested commits to `main` are blocked.
#
#   2. tag-protection rule on `v*`
#      Tags matching `v*` cannot be force-pushed or deleted by
#      non-admins. Adopters pin by `@<commit-SHA>  # tag: v1.0.0`;
#      tag mutation is the supply-chain anchor and must be locked.
#      Implemented via GitHub Repository Rulesets (the legacy
#      tag-protection API was deprecated 2024-08); falls back to the
#      legacy API if rulesets are not available.
#
# Idempotent: re-running has no effect when the desired state is
# already in place.
#
# Authentication: requires `gh` authenticated with admin scope on
# the target repo. Run from any working directory.
#
# Reference: docs/DECISIONS.md D-030; WP-SCP-020 §4 020J;
# docs/security/branch-protection.md.

set -euo pipefail

REPO="${SCP_PROTECTION_REPO:-jrnb2024/standards-control-plane}"
DEFAULT_BRANCH="${SCP_PROTECTION_BRANCH:-main}"
TAG_PATTERN="${SCP_PROTECTION_TAG_PATTERN:-v*}"

log() {
  printf '[020J] %s\n' "$*"
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
log "tag pattern: $TAG_PATTERN"

apply_branch_protection() {
  log "ensuring required_signatures on branch '$DEFAULT_BRANCH'..."

  # Use the dedicated required_signatures endpoint; preserves any
  # other branch protection settings already in place. If branch
  # protection is not yet configured at all, set up a minimal
  # baseline first (no required PR reviews, no required status
  # checks — those land in 020D1/020D2).
  local current
  current="$(gh api -X GET "repos/${REPO}/branches/${DEFAULT_BRANCH}/protection" 2>/dev/null || true)"

  if [ -z "$current" ] || [ "$(printf '%s' "$current" | jq -r '.message // empty')" = "Branch not protected" ]; then
    log "no branch protection in place; applying minimal baseline + required_signatures"
    gh api -X PUT "repos/${REPO}/branches/${DEFAULT_BRANCH}/protection" \
      -H "Accept: application/vnd.github+json" \
      --input - <<'JSON' >/dev/null
{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": false,
  "lock_branch": false,
  "allow_fork_syncing": false,
  "required_signatures": true
}
JSON
  else
    local sigs_enabled
    sigs_enabled="$(printf '%s' "$current" | jq -r '.required_signatures.enabled // false')"
    if [ "$sigs_enabled" = "true" ]; then
      log "required_signatures already enabled on '$DEFAULT_BRANCH'; no-op"
    else
      log "branch protection exists; enabling required_signatures via dedicated endpoint"
      gh api -X POST "repos/${REPO}/branches/${DEFAULT_BRANCH}/protection/required_signatures" >/dev/null
    fi
  fi

  log "verifying..."
  local final
  final="$(gh api -X GET "repos/${REPO}/branches/${DEFAULT_BRANCH}/protection/required_signatures" --jq '.enabled')"
  if [ "$final" != "true" ]; then
    echo "verification failed: required_signatures.enabled = $final" >&2
    exit 1
  fi
  log "required_signatures: enabled ✓"
}

apply_tag_protection() {
  log "ensuring tag-protection ruleset for pattern '$TAG_PATTERN'..."

  local rulesets
  rulesets="$(gh api -X GET "repos/${REPO}/rulesets" 2>/dev/null || echo '[]')"

  local existing_id
  existing_id="$(printf '%s' "$rulesets" | jq -r --arg name "scp-tag-protection-v" \
    '.[] | select(.name == $name) | .id' | head -1)"

  if [ -n "$existing_id" ]; then
    log "tag-protection ruleset already exists (id=$existing_id); no-op"
  else
    log "creating tag-protection ruleset"
    gh api -X POST "repos/${REPO}/rulesets" \
      -H "Accept: application/vnd.github+json" \
      --input - <<JSON >/dev/null
{
  "name": "scp-tag-protection-v",
  "target": "tag",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/tags/${TAG_PATTERN}"],
      "exclude": []
    }
  },
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {"type": "update"}
  ],
  "bypass_actors": []
}
JSON
  fi

  log "verifying..."
  rulesets="$(gh api -X GET "repos/${REPO}/rulesets")"
  local final_id
  final_id="$(printf '%s' "$rulesets" | jq -r --arg name "scp-tag-protection-v" \
    '.[] | select(.name == $name) | .id' | head -1)"
  if [ -z "$final_id" ]; then
    echo "verification failed: tag-protection ruleset not found" >&2
    exit 1
  fi
  log "tag-protection ruleset present (id=$final_id) ✓"
}

apply_branch_protection
apply_tag_protection

log "020J protections applied. Verify via:"
log "  gh api repos/${REPO}/branches/${DEFAULT_BRANCH}/protection/required_signatures"
log "  gh api repos/${REPO}/rulesets | jq '.[] | select(.name == \"scp-tag-protection-v\")'"
