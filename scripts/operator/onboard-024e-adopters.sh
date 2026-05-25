#!/usr/bin/env bash
# scripts/operator/onboard-024e-adopters.sh — WP-SCP-024 024E paired cohort onboarding
#
# Runs the 4-step operator-attended ceremony for adopters #3 + #4 of the
# WP-SCP-024 cohort cascade:
#
#   - Adopter #3: jrnb2024/mapp-doc-agent (local clone: ~/Projects/mapp-doc-agent)
#   - Adopter #4: jrnb2024/mf-intent-os    (local clone: ~/Projects/Recommender)
#
# Per-adopter ceremony (matches CT 024D pattern executed 2026-05-25):
#   1. BROWSER — App `scp-federation-primitive` install on adopter repo
#      (Repository access scoped to standards-control-plane only)
#   2. CLI     — Adopter secrets propagation
#      (SCP_FEDERATION_APP_ID + SCP_FEDERATION_APP_PRIVATE_KEY — BOTH;
#       per TF-024D-001 enumeration)
#   3. CLI     — Smoke-test PR + wait for policy-check / scp/policy-check GREEN
#   4. CLI     — enable-required-check.sh --preserve-existing-contexts
#
# Refuses CI per SCP-operator-script convention.
# Idempotent on steps 2 + 4 (gh secret set + enable-required-check.sh
# tolerate re-runs); steps 1 + 3 are one-shot per adopter.
#
# Usage:
#   scripts/operator/onboard-024e-adopters.sh --private-key-file PATH [options]
#
# Examples:
#   # Run both adopters paired (default):
#   scripts/operator/onboard-024e-adopters.sh \
#     --private-key-file ~/secure/scp-federation-app.pem
#
#   # Skip mapp-doc-agent (e.g., already done):
#   scripts/operator/onboard-024e-adopters.sh \
#     --private-key-file ~/secure/scp-federation-app.pem \
#     --skip-adopter jrnb2024/mapp-doc-agent
#
#   # Stop after step 2 (App install + secrets only; no smoke-test or required-flip):
#   scripts/operator/onboard-024e-adopters.sh \
#     --private-key-file ~/secure/scp-federation-app.pem \
#     --secrets-only

set -euo pipefail

# ---------- CI refusal ----------
if [ "${CI:-}" = "true" ] || [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  echo "error: onboard-024e-adopters.sh is operator-attended; refusing CI environment (CI=${CI:-} GITHUB_ACTIONS=${GITHUB_ACTIONS:-})" >&2
  echo "       run from your interactive shell session" >&2
  exit 1
fi

# ---------- Defaults ----------
PRIVATE_KEY_FILE=""
SECRETS_ONLY=0
SKIP_ADOPTERS=()
SCP_APP_ID="3795720"
SCP_REPO="jrnb2024/standards-control-plane"

# Hardcoded adopter list for 024E paired slice.
# (macOS bash 3.2 doesn't support associative arrays — use case-stmt
# lookups instead per feedback_macos_bash_32_portability_traps.md.)
ADOPTERS=("jrnb2024/mapp-doc-agent" "jrnb2024/mf-intent-os")

local_path_for() {
  case "$1" in
    jrnb2024/mapp-doc-agent) printf '%s' "$HOME/Projects/mapp-doc-agent" ;;
    jrnb2024/mf-intent-os)   printf '%s' "$HOME/Projects/Recommender" ;;
    *) printf '' ;;
  esac
}

label_for() {
  case "$1" in
    jrnb2024/mapp-doc-agent) printf '%s' "#3 mapp-doc-agent" ;;
    jrnb2024/mf-intent-os)   printf '%s' "#4 Recommender (mf-intent-os)" ;;
    *) printf '%s' "$1" ;;
  esac
}

usage() {
  cat >&2 <<'EOF'
Usage: onboard-024e-adopters.sh --private-key-file PATH [options]

Required:
  --private-key-file PATH    Path to PEM file containing the
                             SCP_FEDERATION_APP_PRIVATE_KEY content
                             (same key in use on PIM + CT)

Optional:
  --secrets-only             Run steps 1 (App install pause) + 2 (secrets)
                             only; skip smoke-test + required-flip
  --skip-adopter OWNER/NAME  Skip this adopter (may repeat)
  -h / --help                Show this help

Exit codes:
  0 — both adopters fully onboarded (or secrets-only complete)
  1 — operator-aborted
  2 — usage / runtime error
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --private-key-file) PRIVATE_KEY_FILE="$2"; shift 2 ;;
    --secrets-only) SECRETS_ONLY=1; shift ;;
    --skip-adopter) SKIP_ADOPTERS+=("$2"); shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "error: unknown arg '$1'" >&2; usage; exit 2 ;;
  esac
done

[ -z "$PRIVATE_KEY_FILE" ] && { echo "error: --private-key-file required" >&2; usage; exit 2; }
[ -f "$PRIVATE_KEY_FILE" ] || { echo "error: --private-key-file '$PRIVATE_KEY_FILE' not found" >&2; exit 2; }

if ! head -1 "$PRIVATE_KEY_FILE" | grep -qE '^-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----'; then
  echo "error: --private-key-file '$PRIVATE_KEY_FILE' does not appear to be a valid PEM private key (missing BEGIN PRIVATE KEY header)" >&2
  exit 2
fi

for tool in gh git python3; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "error: required tool '$tool' not on PATH" >&2
    exit 2
  fi
done

SCP_REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENABLE_SCRIPT="$SCP_REPO_DIR/scripts/enable-required-check.sh"
[ -x "$ENABLE_SCRIPT" ] || { echo "error: enable-required-check.sh not executable at $ENABLE_SCRIPT" >&2; exit 2; }

log() { printf '[024E] %s\n' "$*"; }
pause() { read -r -p "[024E] $* — press ENTER to continue, Ctrl-C to abort: " _; }
prompt_yn() {
  local msg="$1"
  read -r -p "[024E] $msg [y/N] " ans
  case "$ans" in
    [yY]|[yY][eE][sS]) return 0 ;;
    *) log "aborted by operator"; exit 1 ;;
  esac
}

is_skipped() {
  local adopter="$1"
  local skip
  # macOS bash 3.2 expansion of empty array under set -u needs the :- guard
  if [ "${#SKIP_ADOPTERS[@]}" -eq 0 ]; then
    return 1
  fi
  for skip in "${SKIP_ADOPTERS[@]}"; do
    [ "$skip" = "$adopter" ] && return 0
  done
  return 1
}

# ============================================================================
# Per-adopter ceremony function
# ============================================================================
onboard_one() {
  local adopter="$1"
  local label
  local local_path
  label="$(label_for "$adopter")"
  local_path="$(local_path_for "$adopter")"

  log "=========================================================="
  log "Adopter $label  ($adopter)"
  log "Local clone: $local_path"
  log "=========================================================="

  # --------------------------------------------------------------------------
  # Step 1 — Browser pause: App install
  # --------------------------------------------------------------------------
  log ""
  log "STEP 1 / 4 — App install (BROWSER)"
  log ""
  log "  Open: https://github.com/apps/scp-federation-primitive/installations/new"
  log "    OR: https://github.com/settings/installations  (then 'scp-federation-primitive' -> Configure)"
  log ""
  log "  Action:"
  log "    - Install the App on the @jrnb2024 organisation (if not already)"
  log "    - Under 'Repository access' for $adopter:"
  log "        * App identity Repository access stays = standards-control-plane only"
  log "        * (The App reads FROM adopter context to mint a SCP-repo-scoped token;"
  log "         the adopter installation grants the right to request that token, not"
  log "         grant the App access to adopter contents)"
  log ""

  if prompt_yn "Confirm App install configured for $adopter?"; then
    log "OK: App install confirmed for $adopter"
  fi

  # --------------------------------------------------------------------------
  # Step 2 — Adopter secrets (CLI; idempotent)
  # --------------------------------------------------------------------------
  log ""
  log "STEP 2 / 4 — Adopter secrets (CLI; gh secret set)"
  log ""

  log "Setting SCP_FEDERATION_APP_ID..."
  echo -n "$SCP_APP_ID" | gh secret set SCP_FEDERATION_APP_ID --repo "$adopter"
  log "  -> SCP_FEDERATION_APP_ID set on $adopter"

  log "Setting SCP_FEDERATION_APP_PRIVATE_KEY..."
  gh secret set SCP_FEDERATION_APP_PRIVATE_KEY --repo "$adopter" < "$PRIVATE_KEY_FILE"
  log "  -> SCP_FEDERATION_APP_PRIVATE_KEY set on $adopter"

  log "Verifying both secrets present..."
  if ! gh secret list --repo "$adopter" --json name --jq '.[].name' | grep -q "^SCP_FEDERATION_APP_ID$"; then
    echo "error: SCP_FEDERATION_APP_ID secret not visible after set on $adopter" >&2
    exit 2
  fi
  if ! gh secret list --repo "$adopter" --json name --jq '.[].name' | grep -q "^SCP_FEDERATION_APP_PRIVATE_KEY$"; then
    echo "error: SCP_FEDERATION_APP_PRIVATE_KEY secret not visible after set on $adopter" >&2
    exit 2
  fi
  log "  -> both secrets verified present"

  if [ "$SECRETS_ONLY" -eq 1 ]; then
    log ""
    log "  --secrets-only — skipping steps 3 + 4 for $adopter"
    return 0
  fi

  # --------------------------------------------------------------------------
  # Step 3 — Smoke-test PR + wait for GREEN
  # --------------------------------------------------------------------------
  log ""
  log "STEP 3 / 4 — Smoke-test PR (CLI; verifies policy-check fires end-to-end)"
  log ""

  [ -d "$local_path" ] || { echo "error: local clone not found at $local_path" >&2; exit 2; }

  cd "$local_path"

  log "Working tree state in $local_path:"
  git status --short | head -10 || true
  log ""
  if [ -n "$(git status --porcelain)" ]; then
    log "WARNING: working tree has uncommitted changes / untracked files."
    log "         The smoke-test will be opened from a fresh branch off main;"
    log "         untracked files stay in working tree (not committed)."
    if ! prompt_yn "Proceed with smoke-test PR anyway?"; then
      log "skipping smoke-test for $adopter at operator request"
      return 0
    fi
  fi

  local current_branch
  current_branch="$(git rev-parse --abbrev-ref HEAD)"
  log "current branch: $current_branch"

  # Stash if needed
  local stashed=0
  if [ -n "$(git status --porcelain)" ]; then
    log "Stashing uncommitted/untracked changes (will be restored at end)..."
    git stash push -u -m "024e-onboarding-temporary-stash-$(date +%s)" >/dev/null
    stashed=1
  fi

  log "Switching to main..."
  git checkout main 2>&1 | tail -1
  git pull --ff-only origin main 2>&1 | tail -2

  local smoke_branch="chore/scp-024e-smoke-test"
  if git rev-parse --verify "$smoke_branch" >/dev/null 2>&1; then
    log "smoke-test branch $smoke_branch already exists — deleting + recreating"
    git branch -D "$smoke_branch"
  fi
  git checkout -b "$smoke_branch"

  # Make a trivial change to a non-load-bearing file. README.md is the
  # safest target — every repo has one, and appending a comment-style
  # markdown line is invisible to consumers.
  local target_file="README.md"
  [ -f "$target_file" ] || target_file="$(ls *.md 2>/dev/null | head -1)"
  [ -f "$target_file" ] || { echo "error: no .md file to append to for smoke-test" >&2; exit 2; }

  local marker
  marker="<!-- WP-SCP-024 024E smoke-test marker $(date +%Y-%m-%dT%H:%M:%SZ) -->"
  printf '\n%s\n' "$marker" >> "$target_file"

  git add "$target_file"
  git commit -m "test: smoke-test SCP policy-check (WP-SCP-024 024E)" \
             -m "Adds a 1-line HTML-comment marker to $target_file to verify" \
             -m "the SCP federation primitive's policy-check / scp/policy-check" \
             -m "fires end-to-end on this adopter post-wrapper-landing." \
             -m "" \
             -m "This is the 024E smoke-test PR — same pattern as CT 024D PR #429." \
             -m "" \
             -m "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"

  log "Pushing smoke-test branch + opening PR..."
  git push -u origin "$smoke_branch" 2>&1 | tail -3

  local pr_url
  pr_url="$(gh pr create \
    --repo "$adopter" \
    --title "test: smoke-test SCP policy-check (WP-SCP-024 024E)" \
    --body "## Summary
WP-SCP-024 024E adopter onboarding smoke-test. Verifies SCP federation primitive's \`policy-check / scp/policy-check\` fires end-to-end on this adopter post-wrapper-landing + post-App-install + post-secrets-propagation.

Same pattern as CT 024D PR [jrnb2024/control-tower#429](https://github.com/jrnb2024/control-tower/pull/429).

## Changes
1-line HTML-comment marker appended to \`$target_file\`. Non-load-bearing; invisible to consumers.

## R1 evidence
- correctness: 1-line markdown comment marker; no semantic change.
- safety_bypass: no policy / workflow / config touched.
- completeness_governance: 024E adopter onboarding ceremony step 3 of 4 per \`scripts/operator/onboard-024e-adopters.sh\`.

## Test plan
- [ ] policy-check / scp/policy-check GREEN
- [ ] (operator merges + proceeds to step 4 = enable-required-check.sh flip)

🤖 Generated with [Claude Code](https://claude.com/claude-code)" 2>&1 | grep -oE 'https://github.com[^[:space:]]+')"

  log "smoke-test PR opened: $pr_url"
  local pr_number
  pr_number="$(printf '%s' "$pr_url" | grep -oE '[0-9]+$')"

  log ""
  log "Waiting for policy-check / scp/policy-check to appear + complete..."
  log "(GitHub Actions takes ~30s to register the new workflow now that the wrapper is on main)"
  sleep 15

  # Poll for the policy-check check to appear AND complete
  local deadline=$(($(date +%s) + 600))   # 10 min cap
  local conclusion=""
  while true; do
    local status
    status="$(gh pr checks "$pr_number" --repo "$adopter" --json name,bucket,conclusion --jq '.[] | select(.name=="policy-check / scp/policy-check") | "\(.bucket) \(.conclusion)"' 2>/dev/null || true)"
    if [ -z "$status" ]; then
      log "  (still waiting for policy-check to register...)"
    else
      local bucket
      bucket="$(printf '%s' "$status" | awk '{print $1}')"
      conclusion="$(printf '%s' "$status" | awk '{print $2}')"
      log "  policy-check bucket=$bucket conclusion=$conclusion"
      if [ "$bucket" != "pending" ]; then
        break
      fi
    fi
    if [ "$(date +%s)" -gt "$deadline" ]; then
      log "timeout waiting for policy-check to complete (10 min)"
      log "inspect manually: $pr_url"
      exit 2
    fi
    sleep 20
  done

  if [ "$conclusion" != "success" ] && [ "$conclusion" != "SUCCESS" ]; then
    log ""
    log "WARNING: policy-check / scp/policy-check did NOT complete GREEN ($conclusion)"
    log "         inspect: $pr_url"
    log ""
    if ! prompt_yn "Continue anyway (e.g., known transient — manually re-run)?"; then
      log "aborted at smoke-test failure for $adopter"
      exit 1
    fi
  else
    log "  -> policy-check / scp/policy-check GREEN on $adopter smoke-test"
  fi

  log ""
  log "Merging smoke-test PR..."
  gh pr merge "$pr_number" --repo "$adopter" --squash --delete-branch
  log "  -> smoke-test PR merged"

  # Restore previous branch + stash
  log "Restoring previous branch state on $local_path..."
  git checkout "$current_branch" 2>&1 | tail -1 || git checkout main 2>&1 | tail -1
  if [ "$stashed" -eq 1 ]; then
    git stash pop 2>&1 | tail -3 || log "  (stash pop had conflicts; inspect $local_path manually)"
  fi

  # --------------------------------------------------------------------------
  # Step 4 — enable-required-check.sh
  # --------------------------------------------------------------------------
  log ""
  log "STEP 4 / 4 — Flip policy-check / scp/policy-check to REQUIRED on $adopter@main"
  log ""

  cd "$SCP_REPO_DIR"
  log "Running: $ENABLE_SCRIPT --repo $adopter --branch main --preserve-existing-contexts"
  "$ENABLE_SCRIPT" --repo "$adopter" --branch main --preserve-existing-contexts

  log ""
  log "$adopter ceremony COMPLETE."
}

# ============================================================================
# Main loop
# ============================================================================
log "===== WP-SCP-024 024E paired cohort onboarding ====="
log "adopters: ${ADOPTERS[*]}"
log "private key: $PRIVATE_KEY_FILE"
log "secrets-only: $SECRETS_ONLY"
log "skip: ${SKIP_ADOPTERS[*]:-(none)}"
log ""

for adopter in "${ADOPTERS[@]}"; do
  if is_skipped "$adopter"; then
    log "[skip] $adopter (per --skip-adopter)"
    continue
  fi
  onboard_one "$adopter"
done

log ""
log "===== all adopters processed ====="
log ""
log "Next:"
log "  - Verify required-status-checks live state on each adopter@main"
log "  - Each adopter's bake observation begins NOW; target close >=$(date -v+7d +%Y-%m-%d 2>/dev/null || date -d '+7 days' +%Y-%m-%d) (>=1 calendar week)"
log "  - Check bake status anytime via:"
log "      scripts/operator/check-bake-status.sh --adopter $adopter --onboard-date $(date +%Y-%m-%d)"
log "  - Operator: file per-adopter close-out PRs with DISPATCH-NOTEs (cascade-status: onboarded) at convenience"
