#!/usr/bin/env bash
# WP-SCP-020 slice 020G — adopter-side branch-protection helper.
#
# Configures a downstream adopter repo's default branch with the
# canonical SCP federation primitive required-status-check posture:
#
#   - required_status_checks.contexts = ["${SCP_REQUIRED_CONTEXT}"]
#     (default: "policy-check / scp/policy-check" — the rendered
#     check-run name from the canonical adopter wrapper at
#     ADOPT-001 §12)
#   - required_status_checks.strict = true (PR must be up-to-date
#     with base before evaluation)
#   - enforce_admins = true (no admin bypass)
#   - required_signatures = true (every commit verified-signed)
#
# This is the adopter-side analogue of SCP-self's
# `scripts/configure-020d2-required-check.sh`. Adopters with
# multi-maintainer teams MAY enable additional review gates
# (`required_pull_request_reviews`, `require_code_owner_reviews`,
# `require_review_from_non_author`) — those are out of scope for
# this script (intentionally).
#
# ## Acceptance per WP-SCP-020 §4 020G
#
# (i) Header asserts:
#     - `gh --version >= 2.40` (need rulesets API + recent flags)
#     - `jq` on PATH
#     - required fine-grained PAT scopes (`administration:write`
#       on the single target repo only — log-warn, don't block,
#       since the script can't introspect token scope without
#       making a call)
#
# (ii) Refuses without `--repo` and `--branch`. `--plan` flag
#      prints the PUT payload without applying. `--enforce-admins`
#      flag defaults true; `--no-enforce-admins` opts out
#      (escape hatch for break-glass).
#
# (iii) Logs invocation (script SHA + operator + timestamp +
#       target + before/after API response JSON) to
#       `docs/reviews/WP-SCP-020/branch-protection-log.md` —
#       the log commit is part of the invocation procedure.
#
# (iv) Bootstrap-only header declares this script is not run
#      unattended.
#
# Reference: docs/DECISIONS.md D-022 (federation-primitive
# adoption); WP-SCP-020 §4 020G; ADOPT-001 §12 (federation
# integration appendix — lands in 020H part 3).

set -euo pipefail

# ---------- (i) Header preconditions ----------

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

require_cmd gh
require_cmd jq
require_cmd git

assert_gh_version() {
  local raw major minor
  raw="$(gh --version 2>/dev/null | head -1 | awk '{print $3}')"
  if [ -z "$raw" ]; then
    echo "could not determine gh CLI version" >&2
    exit 1
  fi
  major="$(printf '%s' "$raw" | cut -d. -f1)"
  minor="$(printf '%s' "$raw" | cut -d. -f2)"
  if [ "$major" -lt 2 ] || { [ "$major" -eq 2 ] && [ "$minor" -lt 40 ]; }; then
    echo "gh CLI ${raw} too old: 2.40+ required (rulesets API + admin flags)" >&2
    exit 1
  fi
}

assert_gh_version

# ---------- (ii) Argument parsing ----------

REPO=""
BRANCH=""
REQUIRED_CONTEXT="${SCP_REQUIRED_CONTEXT:-policy-check / scp/policy-check}"
PLAN_ONLY=0
ENFORCE_ADMINS="true"

usage() {
  cat <<'EOF' >&2
Usage: enable-required-check.sh --repo OWNER/NAME --branch BRANCH [flags]

Required:
  --repo OWNER/NAME   Target repository (e.g. mapp-pim/mapp-pim).
  --branch BRANCH     Default branch to protect (typically `main`).

Flags:
  --required-check NAME    Override the required-check context name.
                           Default: "policy-check / scp/policy-check".
                           Set to your wrapper-workflow's rendered
                           check-run name if it differs.
  --plan                   Print the PUT payload without applying.
                           Use this first to verify intent.
  --no-enforce-admins      Disable enforce_admins (NOT recommended;
                           emits a warning).
  --help / -h              Show this help.

Environment overrides:
  SCP_REQUIRED_CONTEXT     Same as --required-check.

Bootstrap-only: this script is not run unattended. Operator
attention is required to confirm the target, review the plan,
and commit the invocation log to the SCP repo afterward.

Reference: docs/DECISIONS.md D-022; WP-SCP-020 §4 020G.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --required-check) REQUIRED_CONTEXT="$2"; shift 2 ;;
    --plan) PLAN_ONLY=1; shift ;;
    --enforce-admins) ENFORCE_ADMINS="true"; shift ;;
    --no-enforce-admins) ENFORCE_ADMINS="false"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown flag: $1" >&2; usage; exit 2 ;;
  esac
done

if [ -z "$REPO" ] || [ -z "$BRANCH" ]; then
  echo "error: --repo and --branch are both required" >&2
  usage
  exit 2
fi

if [ "$ENFORCE_ADMINS" != "true" ]; then
  echo "WARNING: --no-enforce-admins set; admin bypass is enabled. This is not the canonical SCP federation primitive posture." >&2
fi

log() {
  printf '[020G] %s\n' "$*"
}

log "target repo: $REPO"
log "target branch: $BRANCH"
log "required check: $REQUIRED_CONTEXT"
log "enforce_admins: $ENFORCE_ADMINS"
[ "$PLAN_ONLY" = "1" ] && log "MODE: plan-only (no API mutation)"

# ---------- Construct PUT payload ----------

build_payload() {
  jq -n \
    --arg context "$REQUIRED_CONTEXT" \
    --argjson admins "$ENFORCE_ADMINS" \
    '{
       required_status_checks: {
         strict: true,
         contexts: [$context]
       },
       enforce_admins: $admins,
       required_pull_request_reviews: null,
       restrictions: null,
       required_linear_history: false,
       allow_force_pushes: false,
       allow_deletions: false,
       block_creations: false,
       required_conversation_resolution: false,
       lock_branch: false,
       allow_fork_syncing: false,
       required_signatures: true
     }'
}

PAYLOAD="$(build_payload)"

if [ "$PLAN_ONLY" = "1" ]; then
  log "plan (would PUT to repos/${REPO}/branches/${BRANCH}/protection):"
  printf '%s\n' "$PAYLOAD" | jq .
  log "to apply, re-run without --plan"
  exit 0
fi

# ---------- (iii) Capture before-state ----------

log "capturing before-state..."
BEFORE_JSON="$(gh api -X GET "repos/${REPO}/branches/${BRANCH}/protection" 2>/dev/null || echo '{"_note":"no protection currently configured"}')"

# ---------- Apply ----------

log "applying branch protection..."
printf '%s' "$PAYLOAD" | gh api -X PUT "repos/${REPO}/branches/${BRANCH}/protection" \
  -H "Accept: application/vnd.github+json" \
  --input - >/dev/null

# ---------- (iii) Capture after-state + verify ----------

log "verifying..."
AFTER_JSON="$(gh api -X GET "repos/${REPO}/branches/${BRANCH}/protection")"

CHECKS_STRICT="$(printf '%s' "$AFTER_JSON" | jq -r '.required_status_checks.strict // false')"
CHECKS_CONTEXTS="$(printf '%s' "$AFTER_JSON" | jq -r '.required_status_checks.contexts | join(",")')"
APPLIED_ADMINS="$(printf '%s' "$AFTER_JSON" | jq -r '.enforce_admins.enabled // false')"
SIGS_ENABLED="$(printf '%s' "$AFTER_JSON" | jq -r '.required_signatures.enabled // false')"

FAIL=0
[ "$CHECKS_STRICT" = "true" ] || { echo "verify FAIL: required_status_checks.strict=${CHECKS_STRICT}" >&2; FAIL=1; }
printf '%s' "$CHECKS_CONTEXTS" | grep -q -F "$REQUIRED_CONTEXT" || { echo "verify FAIL: contexts missing ${REQUIRED_CONTEXT} (got: ${CHECKS_CONTEXTS})" >&2; FAIL=1; }
[ "$APPLIED_ADMINS" = "$ENFORCE_ADMINS" ] || { echo "verify FAIL: enforce_admins=${APPLIED_ADMINS} (expected ${ENFORCE_ADMINS})" >&2; FAIL=1; }
[ "$SIGS_ENABLED" = "true" ] || { echo "verify FAIL: required_signatures=${SIGS_ENABLED}" >&2; FAIL=1; }

if [ "$FAIL" -ne 0 ]; then
  echo "verification failed; see message(s) above" >&2
  exit 1
fi

log "verification passed ✓"
log "  required check:        ${CHECKS_CONTEXTS} (strict=${CHECKS_STRICT})"
log "  enforce_admins:        ${APPLIED_ADMINS}"
log "  required_signatures:   ${SIGS_ENABLED}"

# ---------- (iii) Emit invocation log line ----------

SCRIPT_SHA="$(git -C "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" log -1 --format=%H -- scripts/enable-required-check.sh 2>/dev/null || echo unknown)"
OPERATOR="$(gh api user --jq '.login' 2>/dev/null || echo unknown)"
TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

LOG_FILE="docs/reviews/WP-SCP-020/branch-protection-log.md"
SCP_REPO_ROOT="${SCP_REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

cat <<EOF
---

## Invocation log entry

Append the block below to ${LOG_FILE} on the SCP repo (NOT
${REPO}; this log lives at the SCP federation-primitive home),
commit on a feature branch, open PR, merge:

\`\`\`markdown
### ${TS} — ${REPO}@${BRANCH}

- **Operator:** @${OPERATOR}
- **Script SHA:** \`${SCRIPT_SHA}\`
- **Required check:** \`${REQUIRED_CONTEXT}\`
- **enforce_admins:** ${ENFORCE_ADMINS}
- **Plan-only:** no
- **Before:** \`\`\`json
$(printf '%s' "$BEFORE_JSON" | python3 -m json.tool 2>/dev/null || printf '%s' "$BEFORE_JSON")
\`\`\`
- **After:** \`\`\`json
$(printf '%s' "$AFTER_JSON" | python3 -m json.tool 2>/dev/null || printf '%s' "$AFTER_JSON")
\`\`\`
\`\`\`

To automate the log commit (run from the SCP repo root):

    cd "${SCP_REPO_ROOT}"
    git checkout -b chore/branch-protection-log-${REPO//\//-}-$(date -u +%Y%m%d)
    # paste the markdown block above into ${LOG_FILE}
    git add ${LOG_FILE}
    git commit -m "docs: 020G branch-protection log entry — ${REPO}@${BRANCH}"
    git push -u origin HEAD
    gh pr create --title "020G branch-protection log: ${REPO}@${BRANCH}" --fill

The log commit is part of the invocation procedure (per WP-SCP-020
§4 020G(iii)); without it the apply is unrecorded.
EOF
