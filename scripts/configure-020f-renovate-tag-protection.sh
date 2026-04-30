#!/usr/bin/env bash
# WP-SCP-022 slice 020F fix-round-1 — Renovate preset tag-protection
# applier (closes 020F R1 safety CRIT-SAFE-001).
#
# The 020J ruleset `scp-tag-protection-v` targets `refs/tags/v*`
# (literal v-prefix) and does NOT cover `refs/tags/renovate/v*`.
# Without this protection, an attacker with push access can silently
# force-push `renovate/v1.0.0` to a malicious commit and cascade
# adversarial Renovate config to every estate adopter on their next
# scheduled run.
#
# This script adds a parallel ruleset `scp-tag-protection-renovate-v`
# targeting `refs/tags/renovate/v*` with the same protections as 020J.
#
# Idempotent: re-running has no effect when the desired state is
# already in place.
#
# Authentication: requires `gh` authenticated with admin scope on
# the target repo.
#
# Reference: docs/DECISIONS.md D-034 (this slice's amending row);
# docs/security/branch-protection.md (renovate-v* section);
# WP-SCP-020 §4 020F + 020F R1 safety review CRIT-SAFE-001.

set -euo pipefail

REPO="${SCP_PROTECTION_REPO:-jrnb2024/standards-control-plane-}"
RULESET_NAME="${SCP_RENOVATE_RULESET_NAME:-scp-tag-protection-renovate-v}"
TAG_PATTERN="${SCP_RENOVATE_TAG_PATTERN:-renovate/v*}"

log() {
  printf '[020F] %s\n' "$*"
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
log "ruleset name: $RULESET_NAME"
log "tag pattern: $TAG_PATTERN"

apply_renovate_tag_protection() {
  log "ensuring tag-protection ruleset for pattern '$TAG_PATTERN'..."

  local rulesets
  rulesets="$(gh api -X GET "repos/${REPO}/rulesets" 2>/dev/null || echo '[]')"

  local existing_id
  existing_id="$(printf '%s' "$rulesets" | jq -r --arg name "$RULESET_NAME" \
    '.[] | select(.name == $name) | .id' | head -1)"

  if [ -n "$existing_id" ]; then
    log "tag-protection ruleset already exists (id=$existing_id); no-op"
  else
    log "creating tag-protection ruleset"
    gh api -X POST "repos/${REPO}/rulesets" \
      -H "Accept: application/vnd.github+json" \
      --input - <<JSON >/dev/null
{
  "name": "${RULESET_NAME}",
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
  final_id="$(printf '%s' "$rulesets" | jq -r --arg name "$RULESET_NAME" \
    '.[] | select(.name == $name) | .id' | head -1)"
  if [ -z "$final_id" ]; then
    echo "verification failed: tag-protection ruleset not found" >&2
    exit 1
  fi
  log "tag-protection ruleset present (id=$final_id) ✓"
}

apply_renovate_tag_protection

log "020F renovate-tag-protection applied. Verify via:"
log "  gh api repos/${REPO}/rulesets | jq '.[] | select(.name == \"${RULESET_NAME}\")'"
