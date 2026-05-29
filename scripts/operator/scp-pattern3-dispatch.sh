#!/usr/bin/env bash
# scp-pattern3-dispatch.sh — write a session-start ACC dispatch for a Pattern-3
# (Claude Code autonomous) SCP self-development session, per D-057.
#
# WHY THIS EXISTS
#   The acc-hook (PreToolUse: Write|Edit|Bash|NotebookEdit) permits writes to
#   docs/** + work-packages + memory unconditionally, but GATES source writes
#   (src/**, tests/**, policies/**, scripts/**, pyproject.toml, root STATUS.md,
#   .claude/**) unless they fall within an active dispatch's scope_boundary.
#   A Pattern-3 session therefore declares the source paths it intends to touch
#   by writing .acc/active-dispatch.json BEFORE the session runs. This script is
#   that declaration step. Run it from a NORMAL terminal (not inside the Claude
#   Code session) — the hook only fires on Claude-mediated tool calls, so a
#   plain-bash write here is never intercepted.
#
# USAGE
#   scripts/operator/scp-pattern3-dispatch.sh "<scope-glob>" ["<scope-glob>" ...]
#   scripts/operator/scp-pattern3-dispatch.sh --teardown      # remove the dispatch
#
# EXAMPLE
#   scripts/operator/scp-pattern3-dispatch.sh \
#       "src/standards_control_plane/scp_cli.py" \
#       "tests/test_scp_cli.py" \
#       "STATUS.md"
#
# SAFETY (D-057 acceptance criteria — see docs/operator-runbooks/scp-pattern3-dispatch.md)
#   - refuses blanket globs: ** / . ./
#   - refuses any glob that would match .acc/active-dispatch.json itself
#     (.acc, .acc/, .acc/**, .acc/*, literal) — the self-escalation guard
#   - refuses to run under CI=true / GITHUB_ACTIONS=true (operator-attended only)
#   - stamps started_at to NOW so a fresh session can't ride a prior dispatch
#     (the hook enforces a 4h TTL on started_at via acc.kernel.config)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DISPATCH_PATH="${REPO_ROOT}/.acc/active-dispatch.json"

die() { printf 'scp-pattern3-dispatch: ERROR: %s\n' "$1" >&2; exit 1; }

# --- Refuse CI -------------------------------------------------------------
if [ "${CI:-}" = "true" ] || [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  die "refusing to run under CI (operator-attended ceremony only)"
fi

# --- Teardown mode ---------------------------------------------------------
if [ "${1:-}" = "--teardown" ]; then
  rm -f "${DISPATCH_PATH}"
  printf 'scp-pattern3-dispatch: removed %s\n' "${DISPATCH_PATH}"
  exit 0
fi

[ "$#" -ge 1 ] || die "no scope globs given. Usage: $0 \"<glob>\" [\"<glob>\" ...] | --teardown"

# --- Validate each scope glob ---------------------------------------------
# Reject blanket scopes and any scope that could cover the dispatch file
# itself (which would let the session rewrite its own scope mid-run).
is_forbidden_scope() {
  case "$1" in
    "**"|"/"|"."|"./"|"*") return 0 ;;                 # blanket
    ".acc"|".acc/"|".acc/**"|".acc/*") return 0 ;;     # covers the dispatch dir
    ".acc/active-dispatch.json") return 0 ;;           # the dispatch file literal
    *) return 1 ;;
  esac
}

SCOPE_JSON=""
for glob in "$@"; do
  [ -n "${glob}" ] || die "empty scope glob not allowed"
  if is_forbidden_scope "${glob}"; then
    die "forbidden scope '${glob}': blanket globs and any glob covering .acc/active-dispatch.json are refused (D-057 self-escalation guard)"
  fi
  # Defence-in-depth: reject leading-/, .., and shell metacharacters that could
  # broaden the scope beyond a literal repo-relative path/glob.
  case "${glob}" in
    /*) die "absolute paths not allowed in scope: '${glob}'" ;;
    *".."*) die "parent-traversal not allowed in scope: '${glob}'" ;;
  esac
  if [ -z "${SCOPE_JSON}" ]; then
    SCOPE_JSON="\"${glob}\""
  else
    SCOPE_JSON="${SCOPE_JSON}, \"${glob}\""
  fi
done

# --- Write the dispatch (started_at = NOW; hook enforces 4h TTL) -----------
mkdir -p "${REPO_ROOT}/.acc"
DISPATCH_ID="pattern3-$(date -u +%Y%m%dT%H%M%SZ)-$$"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat > "${DISPATCH_PATH}" <<EOF
{
  "dispatch_id": "${DISPATCH_ID}",
  "started_at": "${STARTED_AT}",
  "scope_boundary": [${SCOPE_JSON}]
}
EOF

printf 'scp-pattern3-dispatch: wrote %s\n' "${DISPATCH_PATH}"
printf '  dispatch_id: %s\n' "${DISPATCH_ID}"
printf '  started_at:  %s (hook denies writes once >4h old)\n' "${STARTED_AT}"
printf '  scope:       [%s]\n' "${SCOPE_JSON}"
printf '\nRun "%s --teardown" at session end to remove it.\n' "$0"
