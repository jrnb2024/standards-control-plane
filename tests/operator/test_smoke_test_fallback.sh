#!/usr/bin/env bash
# TDD — smoke-test-before-flip fallback (catch-22 fix) for enable-required-check.sh.
#
# WHY: the canonical adopter wrapper (templates/adopter-wrapper.yml.tmpl) triggers on
# `pull_request` ONLY, so policy-check-wrapper.yml NEVER runs on the default branch.
# The smoke-test originally queried `--branch=<default>` only and refused the flip when
# it found no green run there — an impossible-to-satisfy gate that forced every adopter
# (SA, acc) onto --skip-smoke-test-i-understand-this-blocks-main. The fix: when there is
# no green run on the default branch, FALL BACK to a recent green wrapper run on ANY
# branch (the wrapper file is CODEOWNERS-protected + SHA-pinned, so a recent green run
# still proves "no silent startup_failure" — what this gate guards).
#
# This test stubs `gh` and runs the script with --plan (which exits before any mutation).
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../../scripts/enable-required-check.sh"
fails=0

run_case() {
  local name="$1" branch_json="$2" any_json="$3" expect_pass="$4"
  local tmp; tmp="$(mktemp -d)"
  # Fake gh: distinguishes the branch-scoped run-list query from the any-branch
  # fallback query, and answers the protection GET so --plan can complete.
  {
    printf '%s\n' '#!/usr/bin/env bash'
    printf '%s\n' 'a="$*"'
    printf '%s\n' 'case "$a" in'
    printf '%s\n' "  *--version*)            printf 'gh version 2.95.0 (2026-06-01)\\n' ;;"
    printf '%s\n' "  *'run list'*--branch=*) printf '%s' '${branch_json}' ;;"
    printf '%s\n' "  *'run list'*)           printf '%s' '${any_json}' ;;"
    printf '%s\n' "  *api*GET*protection*)   printf '%s' '{\"required_status_checks\":{\"strict\":false,\"contexts\":[\"ok\"]},\"enforce_admins\":{\"enabled\":false},\"required_signatures\":{\"enabled\":false},\"required_pull_request_reviews\":null}' ;;"
    printf '%s\n' "  *)                       printf '%s' '{}' ;;"
    printf '%s\n' 'esac'
    printf '%s\n' 'exit 0'
  } > "$tmp/gh"
  chmod +x "$tmp/gh"

  local out
  out="$(env -u CI -u GITHUB_ACTIONS PATH="$tmp:$PATH" bash "$SCRIPT" \
    --repo test/repo --branch main --preserve-existing-contexts --plan 2>&1)"
  local passed=0
  echo "$out" | grep -qi "smoke-test-before-flip check:.*proceeding" && passed=1

  if [ "$passed" = "$expect_pass" ]; then
    echo "PASS: $name"
  else
    echo "FAIL: $name (expected_pass=$expect_pass got_pass=$passed)"
    echo "$out" | grep -i "smoke-test" | head -3
    fails=$((fails + 1))
  fi
  rm -rf "$tmp"
}

GREEN='[{"conclusion":"success","status":"completed","databaseId":1,"headSha":"abc1234def"}]'
REDONLY='[{"conclusion":"failure","status":"completed","databaseId":2,"headSha":"def5678abc"}]'
EMPTY='[]'

# Catch-22: NO runs on default branch, GREEN run on a PR branch → MUST proceed (fallback).
run_case "catch22_fallback_green_any_branch" "$EMPTY" "$GREEN" 1
# Genuinely no green run anywhere → MUST still refuse.
run_case "no_green_anywhere_refuses" "$EMPTY" "$REDONLY" 0
# Backward-compat: green run ON the default branch → proceed without needing fallback.
run_case "green_on_default_branch" "$GREEN" "$EMPTY" 1
# gh query failure / malformed JSON on both paths → degrade to 0 green → MUST refuse (fail-closed).
MALFORMED='{"error":"could not query Actions API"}'
run_case "gh_query_failure_fails_closed" "$MALFORMED" "$MALFORMED" 0

if [ "$fails" -eq 0 ]; then echo "ALL PASS"; exit 0; else echo "$fails CASE(S) FAILED"; exit 1; fi
