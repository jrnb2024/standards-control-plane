#!/usr/bin/env bash
# shellcheck shell=bash
# WP-SCP-024 slice 024B invocation-log CI enforcer.
#
# Enforces the cascade-status contract defined by WP-SCP-024 plan-doc
# §5.2 and invariant 2. Supports either PR-driven checks or a local
# diff-base comparison. "not applicable" is for tooling slices ONLY
# (024A plan-doc; 024B-core; 024B-extras; 024G Threshold A telemetry).
# Cohort cascade slices (024C/D/E/F) MUST declare one of the 3
# enforcement values; the CLI cannot detect slice type, so this is an
# operator-responsibility carve-out per plan-doc §2 invariant 2.
#
# Reference: docs/plans/WP-SCP-024-estate-cascade.md §5.2 / §6;
# docs/reviews/WP-SCP-024/024B-core/DISPATCH-NOTE.md; docs/DECISIONS.md D-044.

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: check-invocation-log-entry.sh --pr <number> | --diff-base <ref> --dispatch-note <path> [--status-md <path>] [--branch-protection-log <path>] [--allow-not-applicable]

Required:
  --pr <number>                  Check a PR via gh.
  --diff-base <ref>              Check the current branch against a git ref.
  --dispatch-note <path>         Slice DISPATCH-NOTE.md path.

Optional:
  --status-md <path>             STATUS.md path (default: STATUS.md).
  --branch-protection-log <path> Branch-protection log path.
                                 Default: docs/reviews/WP-SCP-020/branch-protection-log.md
  --allow-not-applicable         Allow cascade-status: not applicable.
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
ALLOW_NOT_APPLICABLE=0

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
    --allow-not-applicable)
      ALLOW_NOT_APPLICABLE=1
      shift
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
  python3 -c 'import os, sys; print(os.path.normpath(sys.argv[1]))' "$1"
}

canonicalize_adopter_slug() {
  # Canonical slugs are a normalization aid, not a collision-resistant ID.
  # Cohort adopter repo names must remain unique after canonicalization.
  printf '%s' "$1" | python3 -c 'import re, sys
s = sys.stdin.read().strip().lower()
s = re.sub(r"[^a-z0-9-]+", "-", s.replace("/", "-"))
s = re.sub(r"-+", "-", s).strip("-")
print(s)'
}

DISPATCH_NOTE="$(normalize_path "$DISPATCH_NOTE")"
STATUS_MD="$(normalize_path "$STATUS_MD")"
BRANCH_PROTECTION_LOG="$(normalize_path "$BRANCH_PROTECTION_LOG")"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$REPO_ROOT" ]; then
  die "ERROR: could not resolve repository root"
fi
REPO_ROOT="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$REPO_ROOT")"
DISPATCH_NOTE_REAL="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$DISPATCH_NOTE")"
STATUS_MD_REAL="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$STATUS_MD")"
BRANCH_PROTECTION_LOG_REAL="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$BRANCH_PROTECTION_LOG")"

case "$DISPATCH_NOTE_REAL" in
  "$REPO_ROOT"|"$REPO_ROOT"/*) ;;
  *) die "ERROR: --dispatch-note must resolve inside repository root: $DISPATCH_NOTE" 2 ;;
esac
case "$STATUS_MD_REAL" in
  "$REPO_ROOT"|"$REPO_ROOT"/*) ;;
  *) die "ERROR: --status-md must resolve inside repository root: $STATUS_MD" 2 ;;
esac
case "$BRANCH_PROTECTION_LOG_REAL" in
  "$REPO_ROOT"|"$REPO_ROOT"/*) ;;
  *) die "ERROR: --branch-protection-log must resolve inside repository root: $BRANCH_PROTECTION_LOG" 2 ;;
esac

DISPATCH_NOTE="$DISPATCH_NOTE_REAL"
STATUS_MD="$STATUS_MD_REAL"
BRANCH_PROTECTION_LOG="$BRANCH_PROTECTION_LOG_REAL"
BRANCH_PROTECTION_LOG_REPO_REL="$(python3 -c 'import os, sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))' "$BRANCH_PROTECTION_LOG" "$REPO_ROOT")"

[ -f "$DISPATCH_NOTE" ] || die "ERROR: DISPATCH-NOTE not found: $DISPATCH_NOTE" 2
[ -f "$STATUS_MD" ] || die "ERROR: STATUS.md not found: $STATUS_MD" 2
[ -f "$BRANCH_PROTECTION_LOG" ] || die "ERROR: branch-protection log not found: $BRANCH_PROTECTION_LOG" 2

cascade_status="$(
  python3 - "$DISPATCH_NOTE" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
matches = re.findall(r'^cascade-status:\s+([^\r\n]+?)\s*$', text, re.M)
if len(matches) != 1:
    joined = ", ".join(matches) if matches else "[]"
    print(f"ERROR: expected exactly one cascade-status match, found {len(matches)}: {joined}", file=sys.stderr)
    sys.exit(1)
print(matches[0])
PY
)"

case "$cascade_status" in
  onboarded|onboarded-operator-bump|blocked-on-adopter-conflict)
    ;;
  "not applicable")
    # Operator responsibility: the slice type is not machine-detectable.
    # "not applicable" is reserved for tooling slices ONLY; cohort
    # cascade slices must use one of the three enforcement values.
    if [ "$ALLOW_NOT_APPLICABLE" -ne 1 ]; then
      die "ERROR: cascade-status: not applicable found, but --allow-not-applicable was not passed. This carve-out is for tooling slices ONLY (024A, 024B-core, 024B-extras, 024G); cohort cascade slices 024C/D/E/F MUST NOT use it. If this is a tooling slice, pass --allow-not-applicable explicitly." 2
    fi
    printf 'OK: DISPATCH-NOTE declares cascade-status: not applicable; not a cohort cascade slice — nothing to enforce\n'
    exit 0
    ;;
  *)
    die "FAIL-CLOSED: cascade-status field absent or unrecognised; must be one of {onboarded, onboarded-operator-bump, blocked-on-adopter-conflict, not applicable}"
    ;;
esac

if ! target_repo="$(
  python3 - "$DISPATCH_NOTE" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
matches = re.findall(r'^[ \t]*-[ \t]+\*\*Target:\*\*[ \t]+([a-zA-Z0-9._/-]+)[ \t]*$', text, re.M)
if len(matches) != 1:
    joined = ", ".join(matches) if matches else "[]"
    # grep probe anchor: expected exactly one *Target* match in DISPATCH-NOTE
    print(f"ERROR: expected exactly one **Target:** match in DISPATCH-NOTE, found {len(matches)}: {joined}", file=sys.stderr)
    sys.exit(1)
print(matches[0])
PY
)"
then
  exit 1
fi

adopter_slug="$(canonicalize_adopter_slug "$target_repo")"

if [ "$PR" != "" ]; then
  gh pr view "$PR" --json body --jq '.body' >/dev/null
  if branch_log_patch="$(gh pr diff "$PR" --patch -- "$BRANCH_PROTECTION_LOG_REPO_REL" 2>/dev/null)"; then
    :
  else
    # grep anchor for the fix-round sanity check: gh pr diff exit|ERROR: gh pr diff failed
    gh_pr_diff_status=$?
    die "ERROR: gh pr diff failed with exit ${gh_pr_diff_status}; cannot determine branch-protection-log diff status. Re-run when gh API is available." 2
  fi
else
  if ! branch_log_patch="$(git diff --unified=0 "${DIFF_BASE}..HEAD" -- "$BRANCH_PROTECTION_LOG_REPO_REL")"; then
    die "ERROR: could not compute diff for diff-base '${DIFF_BASE}'; is this a valid git ref?" 2
  fi
fi

branch_log_modified=0
if [ -n "$branch_log_patch" ]; then
  branch_log_modified=1
fi

parse_entry_repo() {
  # Expected branch-protection-log line format:
  # ### <timestamp> — <owner/repo>@<branch>
  # The separator is U+2014 (em dash); keep this in sync with the
  # branch-protection log emitter in 024B-extras.
  python3 -c 'import re, sys
patch = sys.stdin.read().splitlines()
matched = []
for line in patch:
    if line.startswith("+### "):
        match = re.search(r"^###\s+.+\s+—\s+([A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)?)@([A-Za-z0-9._/-]+)$", line[1:])
        if match:
            matched.append(match.group(1))
if len(matched) != 1:
    values = ", ".join(matched) if matched else "[]"
    print("ERROR: expected exactly one log entry target match, found {}: {}".format(len(matched), values), file=sys.stderr)
    sys.exit(1)
print(matched[0])
' 
}

entry_repo=""
if [ "$branch_log_modified" -eq 1 ]; then
  if ! entry_repo="$(printf '%s' "$branch_log_patch" | parse_entry_repo)"; then
    exit 1
  fi
fi

case "$cascade_status" in
  onboarded)
    [ "$branch_log_modified" -eq 1 ] || die "ERROR: branch-protection-log.md was not modified for cascade-status=onboarded"
    [ "$entry_repo" = "$target_repo" ] || die "ERROR: log entry target '$entry_repo' does not match DISPATCH-NOTE target '$target_repo'"
    printf 'OK: cascade-status=%s; 2 checks passed\n' "$cascade_status"
    ;;
  onboarded-operator-bump)
    [ "$branch_log_modified" -eq 1 ] || die "ERROR: branch-protection-log.md was not modified for cascade-status=onboarded-operator-bump"
    [ "$entry_repo" = "$target_repo" ] || die "ERROR: log entry target '$entry_repo' does not match DISPATCH-NOTE target '$target_repo'"
    python3 - "$STATUS_MD" "$adopter_slug" <<'PY' || die "ERROR: STATUS.md missing required TF-024X-renovate row for the adopter target"
import re
import sys
from pathlib import Path

status_path, slug = sys.argv[1:3]
text = Path(status_path).read_text(encoding="utf-8")
pattern = rf'TF-024X-renovate-{re.escape(slug)}(?:\*\*)? \((open|pending|in-progress|closed)\): \S.{{19,}}'
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
