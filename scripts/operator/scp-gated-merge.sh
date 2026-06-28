#!/usr/bin/env bash
# scp-gated-merge.sh — merge a governed PR to standards-control-plane `main` past the
# enforce_admins + WP-SCP-024 `check-invocation-log-entry` gate, for changes that are NOT
# full WP-SCP-024 cohort-cascade work packages (e.g. key-ring bootstrap, proposal adjudication,
# operator-runbook edits). Temporarily drops ONLY the invocation-log required check, merges,
# and ALWAYS restores branch protection exactly (even on failure, via a trap).
#
# It is deliberately conservative:
#   - refuses unless `policy-check / scp/policy-check` is already GREEN on the PR
#     (so you can never merge a policy-failing change through this escape hatch)
#   - keeps `strict` + `enforce_admins` + `policy-check` required at all times
#   - restores the exact prior required_status_checks on EXIT no matter what
#
#   ./scripts/operator/scp-gated-merge.sh <PR_NUMBER>
#
# Use the normal WP-SCP-024 DISPATCH-NOTE flow for actual cohort-cascade work; this is the
# documented escape hatch for non-WP governed changes (see docs/operator-runbooks/adjudicate-proposal.md).
set -euo pipefail

REPO="jrnb2024/standards-control-plane"
DROP_CHECK="check-invocation-log-entry"
PR="${1:-}"

bold(){ printf '\033[1m%s\033[0m\n' "$*"; }
ok(){ printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn(){ printf '  \033[33m!\033[0m %s\n' "$*"; }
fail(){ printf '  \033[31m✗\033[0m %s\n' "$*" >&2; exit 1; }

[ -n "$PR" ] || fail "usage: $0 <PR_NUMBER>"
command -v gh >/dev/null || fail "gh CLI not found"
command -v jq >/dev/null || fail "jq not found"

PROT_PATH="repos/$REPO/branches/main/protection/required_status_checks"
BACKUP="$(mktemp)"; trap 'rm -f "$BACKUP"' EXIT

bold "1/5  Capture current branch protection"
gh api "$PROT_PATH" > "$BACKUP" || fail "could not read branch protection (need admin)"
orig_contexts="$(jq -c '.contexts' "$BACKUP")"
strict="$(jq -r '.strict' "$BACKUP")"
ok "required checks: $orig_contexts (strict=$strict)"
echo "$orig_contexts" | jq -e 'index("'"$DROP_CHECK"'")' >/dev/null || fail "$DROP_CHECK is not currently required — nothing to drop; merge normally."

# Restore is registered NOW so it runs on any exit path after this point.
restore_protection() {
  printf '{"strict": %s, "contexts": %s}\n' "$strict" "$orig_contexts" \
    | gh api -X PATCH "$PROT_PATH" --input - >/dev/null 2>&1 \
    && printf '  \033[32m✓\033[0m branch protection RESTORED (%s)\n' "$orig_contexts" \
    || printf '  \033[31m✗\033[0m FAILED TO RESTORE PROTECTION — restore manually:\n      echo %s | gh api -X PATCH %s --input -\n' \
         "$(printf '{"strict": %s, "contexts": %s}' "$strict" "$orig_contexts")" "$PROT_PATH" >&2
}
trap 'restore_protection; rm -f "$BACKUP"' EXIT

bold "2/5  Verify the PR's policy-check is GREEN (refuse otherwise)"
pc="$(gh pr checks "$PR" --repo "$REPO" 2>/dev/null | awk -F'\t' '/policy-check \/ scp\/policy-check/{print $2}' | head -1)"
[ "$pc" = "pass" ] || fail "policy-check is '$pc' (must be 'pass'). Fix the policy violation before merging."
ok "policy-check is green"

bold "3/5  Temporarily drop ONLY $DROP_CHECK"
kept="$(echo "$orig_contexts" | jq -c '[ .[] | select(. != "'"$DROP_CHECK"'") ]')"
printf '{"strict": %s, "contexts": %s}\n' "$strict" "$kept" | gh api -X PATCH "$PROT_PATH" --input - >/dev/null
ok "now required: $kept"

bold "4/5  Squash-merge PR #$PR"
gh pr merge "$PR" --repo "$REPO" --squash --delete-branch || fail "merge failed (protection will be restored on exit)"
ok "merged"

bold "5/5  Restore branch protection (also guaranteed on any error above)"
# The EXIT trap restores; do it explicitly here too so the verify below is accurate.
restore_protection
trap 'rm -f "$BACKUP"' EXIT
now="$(gh api "$PROT_PATH" --jq '.contexts' 2>/dev/null | jq -c .)"
[ "$now" = "$orig_contexts" ] && ok "verified: required checks match the pre-merge backup" \
  || warn "restored contexts ($now) differ from backup ($orig_contexts) — eyeball it"
ok "done"
