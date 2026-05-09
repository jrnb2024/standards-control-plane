#!/usr/bin/env bash
# shellcheck shell=bash
# WP-SCP-024 slice 024B invocation-log CI enforcer.
#
# Enforces the cascade-status contract defined by WP-SCP-024 plan-doc
# §5.2 and invariant 2. Supports either PR-driven checks or a local
# diff-base comparison.
#
# Reference: docs/plans/WP-SCP-024-estate-cascade.md §5.2 / §6;
# docs/reviews/WP-SCP-024/024B/DISPATCH-NOTE.md; docs/DECISIONS.md D-044.

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: check-invocation-log-entry.sh --pr <number> | --diff-base <ref> --dispatch-note <path> [--status-md <path>] [--branch-protection-log <path>]

Required:
  --pr <number>                  Check a PR via gh.
  --diff-base <ref>              Check the current branch against a git ref.
  --dispatch-note <path>         Slice DISPATCH-NOTE.md path.

Optional:
  --status-md <path>             STATUS.md path (default: STATUS.md).
  --branch-protection-log <path> Branch-protection log path.
                                 Default: docs/reviews/WP-SCP-020/branch-protection-log.md
  --help / -h                    Show this help.
EOF
}

die() {
  printf '%s\n' "$1" >&2
  exit "${2:-1}"
}

PR=""
DIFF_BASE=""
DISPATCH_NOTE=""
STATUS_MD="STATUS.md"
BRANCH_PROTECTION_LOG="docs/reviews/WP-SCP-020/branch-protection-log.md"

while [ $# -gt 0 ]; do
  case "$1" in
    --pr)
      [ $# -ge 2 ] || die "ERROR: --pr requires a value" 2
      PR="$2"
      shift 2
      ;;
    --diff-base)
      [ $# -ge 2 ] || die "ERROR: --diff-base requires a value" 2
      DIFF_BASE="$2"
      shift 2
      ;;
    --dispatch-note)
      [ $# -ge 2 ] || die "ERROR: --dispatch-note requires a value" 2
      DISPATCH_NOTE="$2"
      shift 2
      ;;
    --status-md)
      [ $# -ge 2 ] || die "ERROR: --status-md requires a value" 2
      STATUS_MD="$2"
      shift 2
      ;;
    --branch-protection-log)
      [ $# -ge 2 ] || die "ERROR: --branch-protection-log requires a value" 2
      BRANCH_PROTECTION_LOG="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "ERROR: unknown flag: $1" 2
      ;;
  esac
done

if [ -n "$PR" ] && [ -n "$DIFF_BASE" ]; then
  die "ERROR: --pr and --diff-base are mutex" 2
fi
if [ -z "$PR" ] && [ -z "$DIFF_BASE" ]; then
  die "ERROR: one of --pr or --diff-base is required" 2
fi
if [ -z "$DISPATCH_NOTE" ]; then
  die "ERROR: --dispatch-note is required" 2
fi

normalize_path() {
  printf '%s' "$1" | sed 's#^\./##'
}

DISPATCH_NOTE="$(normalize_path "$DISPATCH_NOTE")"
STATUS_MD="$(normalize_path "$STATUS_MD")"
BRANCH_PROTECTION_LOG="$(normalize_path "$BRANCH_PROTECTION_LOG")"

[ -f "$DISPATCH_NOTE" ] || die "ERROR: DISPATCH-NOTE not found: $DISPATCH_NOTE" 2
[ -f "$STATUS_MD" ] || die "ERROR: STATUS.md not found: $STATUS_MD" 2
[ -f "$BRANCH_PROTECTION_LOG" ] || die "ERROR: branch-protection log not found: $BRANCH_PROTECTION_LOG" 2

cascade_status="$(
  python3 - "$DISPATCH_NOTE" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
match = re.search(r'^\s*cascade-status:\s+([a-z-]+)\s*$', text, re.M)
if match:
    print(match.group(1).strip())
PY
)"

if [ -z "$cascade_status" ]; then
  die "FAIL-CLOSED: cascade-status field absent or unrecognised; must be one of {onboarded, onboarded-operator-bump, blocked-on-adopter-conflict}"
fi

case "$cascade_status" in
  onboarded|onboarded-operator-bump|blocked-on-adopter-conflict)
    ;;
  *)
    die "FAIL-CLOSED: cascade-status field absent or unrecognised; must be one of {onboarded, onboarded-operator-bump, blocked-on-adopter-conflict}"
    ;;
esac

target_repo="$(
  python3 - "$DISPATCH_NOTE" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
match = re.search(r'^[ \t]*-[ \t]+\*\*Target:\*\*[ \t]+([a-zA-Z0-9._/-]+)[ \t]*$', text, re.M)
if not match:
    sys.exit(1)
print(match.group(1))
PY
)" || die "ERROR: could not extract target from DISPATCH-NOTE" 2

adopter_slug="$(printf '%s' "$target_repo" | tr '[:upper:]' '[:lower:]' | tr '/' '-')"

if [ "$PR" != "" ]; then
  gh pr view "$PR" --json body --jq '.body' >/dev/null
  changed_files="$(gh pr diff "$PR" --name-only)"
  branch_log_patch="$(gh pr diff "$PR" --patch 2>/dev/null || true)"
else
  changed_files="$(git diff --name-only "${DIFF_BASE}..HEAD")"
  branch_log_patch="$(git diff --unified=0 "${DIFF_BASE}..HEAD" -- "$BRANCH_PROTECTION_LOG")"
fi

branch_log_modified=0
if grep -Fxq "$BRANCH_PROTECTION_LOG" <<<"$changed_files"; then
  branch_log_modified=1
fi

parse_entry_repo() {
  python3 -c 'import re, sys
patch = sys.stdin.read().splitlines()
last_repo = ""
for line in patch:
    if line.startswith("+### "):
        match = re.search(r"^###\s+.+\s+—\s+([A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)?)@([A-Za-z0-9._./-]+)$", line[1:])
        if match:
            last_repo = match.group(1)
if last_repo:
    print(last_repo)
' 
}

entry_repo=""
if [ "$branch_log_modified" -eq 1 ]; then
  entry_repo="$(printf '%s' "$branch_log_patch" | parse_entry_repo || true)"
fi

case "$cascade_status" in
  onboarded)
    [ "$branch_log_modified" -eq 1 ] || die "ERROR: branch-protection-log.md was not modified for cascade-status=onboarded"
    [ -n "$entry_repo" ] || die "ERROR: could not parse the log entry target from the branch-protection diff"
    [ "$entry_repo" = "$target_repo" ] || die "ERROR: log entry target '$entry_repo' does not match DISPATCH-NOTE target '$target_repo'"
    printf 'OK: cascade-status=%s; 2 checks passed\n' "$cascade_status"
    ;;
  onboarded-operator-bump)
    [ "$branch_log_modified" -eq 1 ] || die "ERROR: branch-protection-log.md was not modified for cascade-status=onboarded-operator-bump"
    [ -n "$entry_repo" ] || die "ERROR: could not parse the log entry target from the branch-protection diff"
    [ "$entry_repo" = "$target_repo" ] || die "ERROR: log entry target '$entry_repo' does not match DISPATCH-NOTE target '$target_repo'"
    python3 - "$STATUS_MD" "$adopter_slug" <<'PY' || die "ERROR: STATUS.md missing required TF-024X-renovate row for the adopter target"
import re
import sys
from pathlib import Path

status_path, slug = sys.argv[1:3]
text = Path(status_path).read_text(encoding="utf-8")
pattern = rf'(?m)^- \*\*TF-024X-renovate-{re.escape(slug)}(?:\*\*)? \((open|pending|in-progress|closed)\): \S.{{19,}}$'
if not re.search(pattern, text):
    sys.exit(1)
PY
    printf 'OK: cascade-status=%s; 3 checks passed\n' "$cascade_status"
    ;;
  blocked-on-adopter-conflict)
    [ "$branch_log_modified" -eq 0 ] || die "ERROR: branch-protection-log.md was modified for cascade-status=blocked-on-adopter-conflict"
    python3 - "$DISPATCH_NOTE" "$adopter_slug" <<'PY' || die "ERROR: DISPATCH-NOTE missing required TF-024X-conflict reference for the adopter target"
import re
import sys
from pathlib import Path

dispatch_path, slug = sys.argv[1:3]
text = Path(dispatch_path).read_text(encoding="utf-8")
pattern = rf'TF-024X-conflict-{re.escape(slug)}(?:\*\*)? \((open|pending|in-progress|closed)\): \S.{{19,}}'
if not re.search(pattern, text):
    sys.exit(1)
PY
    printf 'OK: cascade-status=%s; 2 checks passed\n' "$cascade_status"
    ;;
esac
