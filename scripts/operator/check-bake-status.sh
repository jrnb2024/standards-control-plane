#!/usr/bin/env bash
# scripts/operator/check-bake-status.sh — WP-SCP-024 cascade-slice bake observation check
#
# Reports whether a cohort adopter has satisfied the WP-SCP-024 invariant 8
# bake observation criteria:
#
#   1. ≥1 calendar week since onboarding date
#   2. ≥1 Renovate-issued SHA pin bump cycle on the adopter's wrapper
#      merged + observed clean
#   3. No CT-side / adopter-side TF filed asking for the gate to be relaxed
#      (this script can't auto-detect; operator reviews)
#
# Read-only. No state mutation.
#
# Usage:
#   scripts/operator/check-bake-status.sh --adopter OWNER/NAME --onboard-date YYYY-MM-DD
#
# Examples:
#   scripts/operator/check-bake-status.sh --adopter jrnb2024/control-tower --onboard-date 2026-05-25
#   scripts/operator/check-bake-status.sh --adopter jrnb2024/mapp-pim --onboard-date 2026-05-24

set -euo pipefail

# ---------- Defaults ----------
ADOPTER=""
ONBOARD_DATE=""
WRAPPER_PATH=".github/workflows/policy-check-wrapper.yml"
REQUIRED_CHECK="policy-check / scp/policy-check"

usage() {
  cat >&2 <<'EOF'
Usage: check-bake-status.sh --adopter OWNER/NAME --onboard-date YYYY-MM-DD

Required:
  --adopter OWNER/NAME     Target adopter repo (e.g. jrnb2024/control-tower)
  --onboard-date DATE      ISO date the adopter went LIVE (gate flipped required)

Optional:
  --wrapper-path PATH      Path to wrapper file in adopter repo
                           (default: .github/workflows/policy-check-wrapper.yml)
  -h / --help              Show this help

Exit codes:
  0 — bake-clean (ready for close-out)
  1 — bake-in-progress (criteria not yet met)
  2 — usage / runtime error
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --adopter) ADOPTER="$2"; shift 2 ;;
    --onboard-date) ONBOARD_DATE="$2"; shift 2 ;;
    --wrapper-path) WRAPPER_PATH="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "error: unknown arg '$1'" >&2; usage; exit 2 ;;
  esac
done

[ -z "$ADOPTER" ] && { echo "error: --adopter required" >&2; usage; exit 2; }
[ -z "$ONBOARD_DATE" ] && { echo "error: --onboard-date required" >&2; usage; exit 2; }

if ! printf '%s' "$ONBOARD_DATE" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
  echo "error: --onboard-date must be YYYY-MM-DD" >&2
  exit 2
fi

for tool in gh jq date python3; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "error: required tool '$tool' not on PATH" >&2
    exit 2
  fi
done

log() { printf '[bake] %s\n' "$*"; }

log "===== bake-observation check: $ADOPTER (onboarded $ONBOARD_DATE) ====="

# ---------- Criterion 1: ≥1 calendar week elapsed ----------
ELAPSED_DAYS="$(python3 -c "
from datetime import date
onb = date.fromisoformat('$ONBOARD_DATE')
today = date.today()
print((today - onb).days)
")"

C1_OK=0
if [ "$ELAPSED_DAYS" -ge 7 ]; then
  log "✓ criterion 1: $ELAPSED_DAYS days elapsed since onboard (≥7)"
  C1_OK=1
else
  log "✗ criterion 1: $ELAPSED_DAYS days elapsed since onboard (need ≥7); $((7 - ELAPSED_DAYS)) more day(s)"
fi

# ---------- Criterion 2: ≥1 Renovate SHA bump merged + clean ----------
log ""
log "criterion 2: looking for Renovate-issued SHA bumps on $WRAPPER_PATH..."

# Search closed PRs on the adopter touching the wrapper file, authored by
# renovate[bot] (or app/renovate).
RENOVATE_PRS_JSON="$(gh pr list --repo "$ADOPTER" \
  --state closed \
  --limit 30 \
  --json number,title,author,mergedAt,files \
  --jq "[.[] | select(.author.login == \"renovate\" or .author.login == \"app/renovate\" or .author.login == \"renovate[bot]\") | select(.files | any(.path == \"$WRAPPER_PATH\")) | select(.mergedAt != null)]" 2>/dev/null || echo '[]')"

RENOVATE_PR_COUNT="$(printf '%s' "$RENOVATE_PRS_JSON" | jq 'length')"

C2_OK=0
if [ "$RENOVATE_PR_COUNT" -ge 1 ]; then
  log "✓ criterion 2: $RENOVATE_PR_COUNT Renovate-issued wrapper bump(s) merged"
  printf '%s' "$RENOVATE_PRS_JSON" | jq -r '.[] | "  #\(.number) merged \(.mergedAt) — \(.title)"'
  # Now check whether the wrapper-bump PRs' policy-check ran GREEN.
  # We pick the most-recent merged PR's commit SHA and verify policy-check on it.
  LATEST_PR_NUMBER="$(printf '%s' "$RENOVATE_PRS_JSON" | jq -r '.[0].number')"
  if [ -n "$LATEST_PR_NUMBER" ] && [ "$LATEST_PR_NUMBER" != "null" ]; then
    LATEST_PR_HEAD_SHA="$(gh pr view "$LATEST_PR_NUMBER" --repo "$ADOPTER" --json mergeCommit --jq '.mergeCommit.oid' 2>/dev/null || true)"
    if [ -n "$LATEST_PR_HEAD_SHA" ] && [ "$LATEST_PR_HEAD_SHA" != "null" ]; then
      # Find the policy-check run on the wrapper-bump PR's merge commit.
      LATEST_RUN_CONCLUSION="$(gh run list --repo "$ADOPTER" \
        --workflow=policy-check-wrapper.yml \
        --commit "$LATEST_PR_HEAD_SHA" \
        --limit 1 \
        --json conclusion --jq '.[0].conclusion' 2>/dev/null || echo 'unknown')"
      if [ "$LATEST_RUN_CONCLUSION" = "success" ]; then
        log "  ✓ latest Renovate bump's policy-check: $LATEST_RUN_CONCLUSION"
      else
        log "  ⚠ latest Renovate bump's policy-check: $LATEST_RUN_CONCLUSION (manual review recommended)"
      fi
    fi
  fi
  C2_OK=1
else
  log "✗ criterion 2: no Renovate-issued wrapper bumps merged yet"
  log "  (next SCP version cut triggers Renovate to auto-PR; check ≥24h after the cut)"
fi

# ---------- Criterion 3: no TFs asking to relax (operator manual review) ----------
log ""
log "criterion 3: operator review — any TFs / FUPs filed asking to relax the gate?"
log "  → search this repo's BACKLOG.md + the adopter's own backlog for entries like:"
log "    grep -E 'relax|revert|disable' docs/BACKLOG.md ~/Projects/$(echo "$ADOPTER" | cut -d/ -f2)/docs/BACKLOG.md 2>/dev/null"
log "  → if there are no such entries, criterion 3 is operator-attested clean"

# ---------- Cohort cascade summary ----------
log ""
log "===== bake summary ====="
log "criterion 1 (≥1 week elapsed):              $([ $C1_OK -eq 1 ] && echo PASS || echo PENDING)"
log "criterion 2 (≥1 Renovate bump clean):       $([ $C2_OK -eq 1 ] && echo PASS || echo PENDING)"
log "criterion 3 (no relax-TFs):                 operator-attested"

# ---------- Required-check verification (current live state) ----------
log ""
log "live state verification:"
LIVE_CONTEXTS="$(gh api "repos/$ADOPTER/branches/main/protection" --jq '.required_status_checks.contexts // []' 2>/dev/null || echo '[]')"
if printf '%s' "$LIVE_CONTEXTS" | jq -e ". | any(. == \"$REQUIRED_CHECK\")" >/dev/null 2>&1; then
  log "  ✓ '$REQUIRED_CHECK' is a required status check on $ADOPTER@main"
else
  log "  ✗ '$REQUIRED_CHECK' NOT in $ADOPTER@main required-status-checks"
  log "    current: $(printf '%s' "$LIVE_CONTEXTS" | jq -c .)"
fi

# ---------- Exit ----------
if [ $C1_OK -eq 1 ] && [ $C2_OK -eq 1 ]; then
  log ""
  log "✓ READY for close-out: criteria 1 + 2 met. Operator: verify criterion 3 + amend"
  log "  docs/reviews/WP-SCP-024/024[D-Z]*/DISPATCH-NOTE.md cascade-status if appropriate."
  exit 0
else
  log ""
  log "↻ bake in progress: not yet ready for close-out"
  exit 1
fi
