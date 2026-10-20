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

REPO="${SCP_PROTECTION_REPO:-jrnb2024/standards-control-plane}"
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

  # Closes 020F R4 safety NEW-R4-SAFE-002: refuse to operate when
  # multiple rulesets share the same name. R3 fixed head -1 on the
  # POST path (NEW-R3-SAFE-003) but left it unchanged here. Now
  # asserting count <= 1 instead of silently selecting head -1.
  local matching_ids
  matching_ids="$(printf '%s' "$rulesets" | jq -r --arg name "$RULESET_NAME" \
    '[.[] | select(.name == $name) | .id]')"
  local match_count
  match_count="$(printf '%s' "$matching_ids" | jq 'length')"
  if [ "$match_count" -gt 1 ]; then
    echo "verification failed: ${match_count} rulesets share name '${RULESET_NAME}' — manual reconciliation required" >&2
    exit 1
  fi
  local existing_id
  existing_id="$(printf '%s' "$matching_ids" | jq -r '.[0] // empty')"

  local final_id
  if [ -n "$existing_id" ]; then
    log "tag-protection ruleset already exists (id=$existing_id); no-op"
    final_id="$existing_id"
  else
    log "creating tag-protection ruleset"
    # Closes 020F R2 safety NEW-R2-SAFE-002: jq --arg quoting
    # structurally separates env-var values from JSON structure,
    # eliminating heredoc interpolation as a command-injection
    # surface. The previous heredoc form was vulnerable to a
    # tainted RULESET_NAME containing JSON metacharacters; jq
    # --arg always emits well-formed JSON strings.
    local payload
    payload="$(jq -n \
      --arg name "$RULESET_NAME" \
      --arg pattern "refs/tags/$TAG_PATTERN" \
      '{
         name: $name,
         target: "tag",
         enforcement: "active",
         conditions: {
           ref_name: { include: [$pattern], exclude: [] }
         },
         rules: [
           {type: "deletion"},
           {type: "non_fast_forward"},
           {type: "update"}
         ],
         bypass_actors: []
       }')"
    # Closes 020F R3 safety NEW-R3-SAFE-003: capture the ID from
    # the POST response rather than re-listing and selecting by
    # name + head -1, which is non-deterministic when a duplicate-
    # name ruleset pre-exists.
    local create_response
    create_response="$(printf '%s' "$payload" | gh api -X POST "repos/${REPO}/rulesets" \
      -H "Accept: application/vnd.github+json" \
      --input -)"
    final_id="$(printf '%s' "$create_response" | jq -r '.id')"
    if [ -z "$final_id" ] || [ "$final_id" = "null" ]; then
      echo "verification failed: POST response did not include a ruleset id" >&2
      exit 1
    fi
  fi

  log "verifying ruleset id=${final_id}..."
  # Closes 020F R2 correctness COR-R2-001 + safety NEW-R2-SAFE-002 +
  # R3 safety NEW-R3-SAFE-001/002/004: ruleset-by-name existence is
  # necessary but not sufficient. Read the full ruleset back via
  # the per-ruleset endpoint and assert:
  #   (a) target == "tag"  (R3 NEW-R3-SAFE-004)
  #   (b) enforcement == "active"
  #   (c) the rule-type set is exactly {deletion, non_fast_forward, update}
  #   (d) conditions.ref_name.include contains the expected pattern
  #   (e) conditions.ref_name.exclude is empty  (R3 NEW-R3-SAFE-002)
  #   (f) bypass_actors is empty  (R3 NEW-R3-SAFE-001)
  local detail
  detail="$(gh api -X GET "repos/${REPO}/rulesets/${final_id}")"

  local target_val
  target_val="$(printf '%s' "$detail" | jq -r '.target // "unknown"')"
  if [ "$target_val" != "tag" ]; then
    echo "verification failed: ruleset id=${final_id} target=${target_val} (expected tag)" >&2
    exit 1
  fi

  local enforcement
  enforcement="$(printf '%s' "$detail" | jq -r '.enforcement // "unknown"')"
  if [ "$enforcement" != "active" ]; then
    echo "verification failed: ruleset id=${final_id} enforcement=${enforcement} (expected active)" >&2
    exit 1
  fi

  local rule_types
  rule_types="$(printf '%s' "$detail" | jq -r '[.rules[].type] | sort | join(",")')"
  if [ "$rule_types" != "deletion,non_fast_forward,update" ]; then
    echo "verification failed: ruleset id=${final_id} rules=${rule_types} (expected deletion,non_fast_forward,update)" >&2
    exit 1
  fi

  # Closes 020F R4 safety NEW-R4-SAFE-001: the `update` rule supports
  # an `update_allows_fetch_and_merge` parameter; if true, fast-
  # forward updates to the protected tag are silently allowed,
  # which would weaken the protection. We don't set this in the
  # creation payload (default is null/absent), so any non-default
  # value is drift. Assert it's absent or false.
  local update_param
  update_param="$(printf '%s' "$detail" | jq -r '
    [.rules[] | select(.type == "update") | .parameters.update_allows_fetch_and_merge // false][0] // false')"
  if [ "$update_param" != "false" ]; then
    echo "verification failed: ruleset id=${final_id} update.parameters.update_allows_fetch_and_merge=${update_param} (expected false/absent)" >&2
    exit 1
  fi

  local include_match
  include_match="$(printf '%s' "$detail" | jq -r --arg pattern "refs/tags/$TAG_PATTERN" \
    '.conditions.ref_name.include | index($pattern) // -1')"
  if [ "$include_match" = "-1" ]; then
    echo "verification failed: ruleset id=${final_id} does not include refs/tags/${TAG_PATTERN}" >&2
    exit 1
  fi

  local exclude_count
  exclude_count="$(printf '%s' "$detail" | jq '.conditions.ref_name.exclude | length')"
  if [ "$exclude_count" != "0" ]; then
    echo "verification failed: ruleset id=${final_id} has ${exclude_count} exclude pattern(s) (expected 0)" >&2
    exit 1
  fi

  local bypass_count
  bypass_count="$(printf '%s' "$detail" | jq '.bypass_actors | length')"
  if [ "$bypass_count" != "0" ]; then
    echo "verification failed: ruleset id=${final_id} has ${bypass_count} bypass actor(s) (expected 0)" >&2
    exit 1
  fi

  log "tag-protection ruleset verified ✓"
  log "  id:                          ${final_id}"
  log "  target:                      ${target_val}"
  log "  enforcement:                 ${enforcement}"
  log "  rules:                       ${rule_types}"
  log "  include pattern:             refs/tags/${TAG_PATTERN}"
  log "  exclude count / bypass count: ${exclude_count} / ${bypass_count}"
}

apply_renovate_tag_protection

log "020F renovate-tag-protection applied. Verify via:"
log "  gh api repos/${REPO}/rulesets | jq '.[] | select(.name == \"${RULESET_NAME}\")'"
