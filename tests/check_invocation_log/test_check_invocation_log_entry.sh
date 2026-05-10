#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SCRIPT="${REPO_ROOT}/scripts/check-invocation-log-entry.sh"
RESTORE_SCRIPT="${REPO_ROOT}/scripts/enable-required-check.sh"

TMPDIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMPDIR"
}
trap cleanup EXIT INT TERM

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

init_case_repo() {
  local repo_dir="$1"
  mkdir -p "$repo_dir/docs/reviews/WP-SCP-020"
  git -C "$repo_dir" init -q
  git -C "$repo_dir" config user.name "Codex Test"
  git -C "$repo_dir" config user.email "codex@example.com"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded
- **Target:** jrnb2024/base
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
# (no TF rows)
EOF
  : >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md"
  git -C "$repo_dir" add .
  git -C "$repo_dir" commit -qm "base"
  git -C "$repo_dir" branch -f base HEAD
}

commit_case() {
  local repo_dir="$1"
  local message="$2"
  git -C "$repo_dir" add .
  git -C "$repo_dir" commit -qm "$message"
}

run_case() {
  local repo_dir="$1"
  local expected_exit="$2"
  local expected_stdout="$3"
  local expected_stderr="$4"
  local branch_protection_log="${5:-docs/reviews/WP-SCP-020/branch-protection-log.md}"
  if [ $# -ge 5 ]; then
    shift 5  # consume positional 1-5; remaining $@ are extra script flags (e.g. --allow-not-applicable)
  else
    shift 4  # consume positional 1-4 when the optional branch-protection-log argument is omitted
  fi
  local stdout_file stderr_file status
  stdout_file="$(mktemp "${TMPDIR}/stdout.XXXXXX")"
  stderr_file="$(mktemp "${TMPDIR}/stderr.XXXXXX")"
  if (cd "$repo_dir" && "$SCRIPT" --diff-base base --dispatch-note DISPATCH-NOTE.md --status-md STATUS.md --branch-protection-log "$branch_protection_log" "$@") >"$stdout_file" 2>"$stderr_file"; then
    status=0
  else
    status=$?
  fi
  if [ "$status" -ne "$expected_exit" ]; then
    printf 'unexpected exit code: expected %s got %s\n' "$expected_exit" "$status" >&2
    printf 'stdout:\n' >&2
    cat "$stdout_file" >&2
    printf 'stderr:\n' >&2
    cat "$stderr_file" >&2
    rm -f "$stdout_file" "$stderr_file"
    exit 1
  fi
  if [ -n "$expected_stdout" ]; then
    grep -Fq -- "$expected_stdout" "$stdout_file" || {
      printf 'expected stdout to contain: %s\n' "$expected_stdout" >&2
      printf 'stdout:\n' >&2
      cat "$stdout_file" >&2
      printf 'stderr:\n' >&2
      cat "$stderr_file" >&2
      rm -f "$stdout_file" "$stderr_file"
      exit 1
    }
  fi
  if [ -n "$expected_stderr" ]; then
    grep -Fq -- "$expected_stderr" "$stderr_file" || {
      printf 'expected stderr to contain: %s\n' "$expected_stderr" >&2
      printf 'stdout:\n' >&2
      cat "$stdout_file" >&2
      printf 'stderr:\n' >&2
      cat "$stderr_file" >&2
      rm -f "$stdout_file" "$stderr_file"
      exit 1
    }
  fi
  rm -f "$stdout_file" "$stderr_file"
}

run_pr_case() {
  local repo_dir="$1"
  local fake_gh_dir="$2"
  local expected_exit="$3"
  local expected_stdout="$4"
  local expected_stderr="$5"
  local branch_protection_log="${6:-docs/reviews/WP-SCP-020/branch-protection-log.md}"
  if [ $# -ge 6 ]; then
    shift 6  # consume positional 1-6; remaining $@ are extra script flags for PR-mode tests
  else
    shift 5  # consume positional 1-5 when the optional branch-protection-log argument is omitted
  fi
  local stdout_file stderr_file status
  stdout_file="$(mktemp "${TMPDIR}/stdout.XXXXXX")"
  stderr_file="$(mktemp "${TMPDIR}/stderr.XXXXXX")"
  if (
    cd "$repo_dir" &&
    PATH="$fake_gh_dir:$PATH" \
    "$SCRIPT" --pr 99 --dispatch-note DISPATCH-NOTE.md --status-md STATUS.md --branch-protection-log "$branch_protection_log" "$@"
  ) >"$stdout_file" 2>"$stderr_file"; then
    status=0
  else
    status=$?
  fi
  if [ "$status" -ne "$expected_exit" ]; then
    printf 'unexpected exit code: expected %s got %s\n' "$expected_exit" "$status" >&2
    printf 'stdout:\n' >&2
    cat "$stdout_file" >&2
    printf 'stderr:\n' >&2
    cat "$stderr_file" >&2
    rm -f "$stdout_file" "$stderr_file"
    exit 1
  fi
  if [ -n "$expected_stdout" ]; then
    grep -Fq -- "$expected_stdout" "$stdout_file" || {
      printf 'expected stdout to contain: %s\n' "$expected_stdout" >&2
      printf 'stdout:\n' >&2
      cat "$stdout_file" >&2
      printf 'stderr:\n' >&2
      cat "$stderr_file" >&2
      rm -f "$stdout_file" "$stderr_file"
      exit 1
    }
  fi
  if [ -n "$expected_stderr" ]; then
    grep -Fq -- "$expected_stderr" "$stderr_file" || {
      printf 'expected stderr to contain: %s\n' "$expected_stderr" >&2
      printf 'stdout:\n' >&2
      cat "$stdout_file" >&2
      printf 'stderr:\n' >&2
      cat "$stderr_file" >&2
      rm -f "$stdout_file" "$stderr_file"
      exit 1
    }
  fi
  rm -f "$stdout_file" "$stderr_file"
}

make_restore_fake_gh() {
  local fake_gh_dir="$1"
  mkdir -p "$fake_gh_dir/tag-refs"
  cat >"$fake_gh_dir/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

FAKE_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_FILE="${FAKE_DIR}/state"
CALLS_FILE="${FAKE_DIR}/calls.log"
PUT_BODY_FILE="${FAKE_DIR}/put-body.json"
REPO_JSON_FILE="${FAKE_DIR}/repo.json"
WORKFLOWS_FILE="${FAKE_DIR}/workflows.json"
RUNS_FILE="${FAKE_DIR}/runs.json"
TAGS_FILE="${FAKE_DIR}/tags.json"
DEFAULT_BRANCH_FALLBACK="main"

log_call() {
  printf '%s\n' "$*" >>"$CALLS_FILE"
}

read_body() {
  local body=""
  if ! body="$(cat)"; then
    body=""
  fi
  printf '%s' "$body"
}

if [ "${1:-}" = "--version" ]; then
  echo "gh version 2.40.0"
  exit 0
fi

if [ "${1:-}" != "api" ]; then
  printf 'unexpected gh invocation: %s\n' "$*" >&2
  exit 1
fi

shift
method="GET"
if [ "${1:-}" = "-X" ]; then
  method="${2:-GET}"
  shift 2
fi

endpoint="${1:-}"
shift || true
jq_expr=""
read_input=0
while [ $# -gt 0 ]; do
  case "$1" in
    --jq)
      jq_expr="${2:-}"
      shift 2
      ;;
    --input)
      read_input=1
      if [ "${2:-}" = "-" ]; then
        shift 2
      else
        shift
      fi
      ;;
    -H)
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

repo_path=""
case "$endpoint" in
  repos/*)
    repo_path="${endpoint#repos/}"
    repo_path="${repo_path%%/*}"
    ;;
esac

if [ -z "${repo_path}" ] && [ "${endpoint}" != "user" ]; then
  printf 'unexpected gh api endpoint: %s\n' "$endpoint" >&2
  exit 1
fi

case "$endpoint" in
  user)
    if [ -n "$jq_expr" ]; then
      if [ "$jq_expr" = ".login" ]; then
        echo "tester"
      else
        echo '{"login":"tester"}'
      fi
    else
      echo '{"login":"tester"}'
    fi
    ;;
  repos/*/actions/workflows?per_page=100)
    if [ -n "$jq_expr" ]; then
      jq -r --arg path ".github/workflows/policy-check-wrapper.yml" '.workflows[] | select(.path == $path) | .id' "$WORKFLOWS_FILE"
    else
      cat "$WORKFLOWS_FILE"
    fi
    ;;
  repos/*/actions/runs?workflow_id=*)
    if [[ "$endpoint" == *"branch="* ]]; then
      printf 'unexpected branch filter in workflow-runs request: %s\n' "$endpoint" >&2
      exit 1
    fi
    workflow_id="${endpoint#*workflow_id=}"
    workflow_id="${workflow_id%%&*}"
    if [ -f "${FAKE_DIR}/runs-${workflow_id}.json" ]; then
      cat "${FAKE_DIR}/runs-${workflow_id}.json"
    elif [ -f "$RUNS_FILE" ]; then
      cat "$RUNS_FILE"
    else
      printf '{"workflow_runs":[]}'
    fi
    ;;
  repos/*/branches/*/protection/required_signatures)
    log_call "${method} required_signatures"
    if [ "${method}" = "POST" ] && [ -f "${FAKE_DIR}/post_required_signatures_fail" ]; then
      cat "${FAKE_DIR}/post_required_signatures_fail" >&2
      exit 1
    fi
    if [ "${method}" = "DELETE" ] && [ -f "${FAKE_DIR}/delete_required_signatures_fail" ]; then
      cat "${FAKE_DIR}/delete_required_signatures_fail" >&2
      exit 1
    fi
    if [ "${method}" = "POST" ] && [ -f "${FAKE_DIR}/post_required_signatures_404" ]; then
      cat "${FAKE_DIR}/post_required_signatures_404" >&2
      exit 1
    fi
    if [ "${method}" = "DELETE" ] && [ -f "${FAKE_DIR}/delete_required_signatures_404" ]; then
      cat "${FAKE_DIR}/delete_required_signatures_404" >&2
      exit 1
    fi
    ;;
  repos/*/branches/*/protection)
    case "$method" in
      GET)
        if [ "$(cat "$STATE_FILE" 2>/dev/null || printf 'before')" = "after" ] && [ -f "$FAKE_DIR/after.json" ]; then
          cat "$FAKE_DIR/after.json"
        else
          cat "$FAKE_DIR/before.json"
        fi
        ;;
      PUT)
        body="$(read_body)"
        printf '%s' "$body" >"$PUT_BODY_FILE"
        log_call "PUT protection"
        if [ -f "$FAKE_DIR/put_fail" ]; then
          cat "$FAKE_DIR/put_fail" >&2
          exit 1
        fi
        printf 'after' >"$STATE_FILE"
        ;;
      *)
        printf 'unexpected protection method: %s\n' "$method" >&2
        exit 1
        ;;
    esac
    ;;
  repos/jrnb2024/standards-control-plane-/git/refs/tags?per_page=100)
    if [ -f "$TAGS_FILE" ]; then
      cat "$TAGS_FILE"
    else
      printf '[]'
    fi
    ;;
  repos/jrnb2024/standards-control-plane-/git/ref/tags/*)
    tag_name="${endpoint##*/}"
    if [ -f "${FAKE_DIR}/tag-refs/${tag_name}.json" ]; then
      if [ "${jq_expr}" = ".object.sha" ]; then
        jq -r '.object.sha' "${FAKE_DIR}/tag-refs/${tag_name}.json"
      else
        cat "${FAKE_DIR}/tag-refs/${tag_name}.json"
      fi
    else
      printf 'missing tag ref fixture for %s\n' "$tag_name" >&2
      exit 1
    fi
    ;;
  repos/*)
    if [ -n "$jq_expr" ] && [ "$jq_expr" = ".default_branch" ]; then
      if [ -f "$REPO_JSON_FILE" ]; then
        jq -r '.default_branch // "'"$DEFAULT_BRANCH_FALLBACK"'"' "$REPO_JSON_FILE"
      else
        echo "$DEFAULT_BRANCH_FALLBACK"
      fi
    else
      if [ -f "$REPO_JSON_FILE" ]; then
        cat "$REPO_JSON_FILE"
      else
        printf '{"default_branch":"%s"}' "$DEFAULT_BRANCH_FALLBACK"
      fi
    fi
    ;;
  *)
    printf 'unexpected gh api endpoint: %s\n' "$endpoint" >&2
    exit 1
    ;;
esac
EOF
  chmod +x "$fake_gh_dir/gh"
}

run_restore_case() {
  local repo_dir="$1"
  local fake_gh_dir="$2"
  local expected_exit="$3"
  local expected_stdout="$4"
  local expected_stderr="$5"
  if [ $# -ge 6 ]; then
    shift 5
  else
    shift 5
  fi
  local stdout_file stderr_file status
  stdout_file="$(mktemp "${TMPDIR}/restore-stdout.XXXXXX")"
  stderr_file="$(mktemp "${TMPDIR}/restore-stderr.XXXXXX")"
  if (
    cd "$repo_dir" &&
    PATH="$fake_gh_dir:$PATH" \
    "$RESTORE_SCRIPT" \
      --repo jrnb2024/pim \
      --branch main \
      --restore pre-state.json \
      "$@"
  ) >"$stdout_file" 2>"$stderr_file"; then
    status=0
  else
    status=$?
  fi
  if [ "$status" -ne "$expected_exit" ]; then
    printf 'unexpected exit code: expected %s got %s\n' "$expected_exit" "$status" >&2
    printf 'stdout:\n' >&2
    cat "$stdout_file" >&2
    printf 'stderr:\n' >&2
    cat "$stderr_file" >&2
    rm -f "$stdout_file" "$stderr_file"
    exit 1
  fi
  if [ -n "$expected_stdout" ]; then
    grep -Fq -- "$expected_stdout" "$stdout_file" || {
      printf 'expected stdout to contain: %s\n' "$expected_stdout" >&2
      printf 'stdout:\n' >&2
      cat "$stdout_file" >&2
      printf 'stderr:\n' >&2
      cat "$stderr_file" >&2
      rm -f "$stdout_file" "$stderr_file"
      exit 1
    }
  fi
  if [ -n "$expected_stderr" ]; then
    grep -Fq -- "$expected_stderr" "$stderr_file" || {
      printf 'expected stderr to contain: %s\n' "$expected_stderr" >&2
      printf 'stdout:\n' >&2
      cat "$stdout_file" >&2
      printf 'stderr:\n' >&2
      cat "$stderr_file" >&2
      rm -f "$stdout_file" "$stderr_file"
      exit 1
    }
  fi
  rm -f "$stdout_file" "$stderr_file"
}

run_enable_case() {
  local repo_dir="$1"
  local fake_gh_dir="$2"
  local expected_exit="$3"
  local expected_stdout="$4"
  local expected_stderr="$5"
  if [ $# -ge 6 ]; then
    shift 5
  else
    shift 5
  fi
  local stdout_file stderr_file status
  stdout_file="$(mktemp "${TMPDIR}/enable-stdout.XXXXXX")"
  stderr_file="$(mktemp "${TMPDIR}/enable-stderr.XXXXXX")"
  if (
    cd "$repo_dir" &&
    PATH="$fake_gh_dir:$PATH" \
    "$RESTORE_SCRIPT" \
      --repo jrnb2024/pim \
      --branch main \
      "$@"
  ) >"$stdout_file" 2>"$stderr_file"; then
    status=0
  else
    status=$?
  fi
  if [ "$status" -ne "$expected_exit" ]; then
    printf 'unexpected exit code: expected %s got %s\n' "$expected_exit" "$status" >&2
    printf 'stdout:\n' >&2
    cat "$stdout_file" >&2
    printf 'stderr:\n' >&2
    cat "$stderr_file" >&2
    rm -f "$stdout_file" "$stderr_file"
    exit 1
  fi
  if [ -n "$expected_stdout" ]; then
    grep -Fq "$expected_stdout" "$stdout_file" || {
      printf 'expected stdout to contain: %s\n' "$expected_stdout" >&2
      printf 'stdout:\n' >&2
      cat "$stdout_file" >&2
      printf 'stderr:\n' >&2
      cat "$stderr_file" >&2
      rm -f "$stdout_file" "$stderr_file"
      exit 1
    }
  fi
  if [ -n "$expected_stderr" ]; then
    grep -Fq "$expected_stderr" "$stderr_file" || {
      printf 'expected stderr to contain: %s\n' "$expected_stderr" >&2
      printf 'stdout:\n' >&2
      cat "$stdout_file" >&2
      printf 'stderr:\n' >&2
      cat "$stderr_file" >&2
      rm -f "$stdout_file" "$stderr_file"
      exit 1
    }
  fi
  rm -f "$stdout_file" "$stderr_file"
}

main() {
  local repo_dir

  grep -Eq 'not applicable.*tooling slices ONLY|tooling slices.*ONLY' "$SCRIPT" || fail "script missing not-applicable tooling-slice documentation"

  repo_dir="$TMPDIR/case1"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 1"
  run_case "$repo_dir" 0 'OK: cascade-status=onboarded; 2 checks passed' ''

  repo_dir="$TMPDIR/case2"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded
- **Target:** jrnb2024/pim
EOF
  commit_case "$repo_dir" "case 2"
  run_case "$repo_dir" 1 '' 'ERROR: branch-protection-log.md was not modified for cascade-status=onboarded'

  repo_dir="$TMPDIR/case3"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/wrong@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 3"
  run_case "$repo_dir" 1 '' "ERROR: log entry target 'jrnb2024/wrong' does not match DISPATCH-NOTE target 'jrnb2024/pim'"

  repo_dir="$TMPDIR/case3b"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded
- **Target:** jrnb2024/wrong
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/wrong@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 3b"
  run_case "$repo_dir" 1 '' 'ERROR: expected exactly one **Target:** match in DISPATCH-NOTE, found 2: jrnb2024/wrong, jrnb2024/pim'

  # Plan-doc §2 invariant 2 worked-example matrix plus the operator-bump
  # unmodified-log negative guard.

  repo_dir="$TMPDIR/case4a"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-pim** (open): Renovate disabled on PIM; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 4a"
  run_case "$repo_dir" 0 'OK: cascade-status=onboarded-operator-bump; 3 checks passed' ''

  repo_dir="$TMPDIR/case4a-negative"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-pim** (open): Renovate disabled on PIM; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.
EOF
  commit_case "$repo_dir" "case 4a-negative"
  run_case "$repo_dir" 1 '' 'ERROR: branch-protection-log.md was not modified for cascade-status=onboarded-operator-bump'

  repo_dir="$TMPDIR/case4a-target-mismatch"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-pim** (open): Renovate disabled on PIM; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/wrong@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 4a-target-mismatch"
  run_case "$repo_dir" 1 '' "ERROR: log entry target 'jrnb2024/wrong' does not match DISPATCH-NOTE target 'jrnb2024/pim'"

  repo_dir="$TMPDIR/case4b"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.
EOF
  commit_case "$repo_dir" "case 4b"
  run_case "$repo_dir" 0 'OK: cascade-status=blocked-on-adopter-conflict; 2 checks passed' ''

  repo_dir="$TMPDIR/case4c"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-pim**
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 4c"
  run_case "$repo_dir" 1 '' 'ERROR: STATUS.md missing required TF-024X-renovate row for the adopter target'

  repo_dir="$TMPDIR/case4d"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-pim** (open):
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 4d"
  run_case "$repo_dir" 1 '' 'ERROR: STATUS.md missing required TF-024X-renovate row for the adopter target'

  repo_dir="$TMPDIR/case4e"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-pim** (open):                    
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 4e"
  run_case "$repo_dir" 1 '' 'ERROR: STATUS.md missing required TF-024X-renovate row for the adopter target'

  repo_dir="$TMPDIR/case4f"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-pim** (open): short
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 4f"
  run_case "$repo_dir" 1 '' 'ERROR: STATUS.md missing required TF-024X-renovate row for the adopter target'

  repo_dir="$TMPDIR/case4g"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-pim** (open): --------------------
EOF
  # Passes by design: the regex is only a syntactic floor; semantic content is
  # still a human-review control.
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 4g"
  run_case "$repo_dir" 0 'OK: cascade-status=onboarded-operator-bump; 3 checks passed' ''

  repo_dir="$TMPDIR/case4h"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/repo.foo_bar
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-repo-foo-bar** (open): Renovate disabled on repo.foo_bar; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/repo.foo_bar@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 4h"
  run_case "$repo_dir" 0 'OK: cascade-status=onboarded-operator-bump; 3 checks passed' ''

  repo_dir="$TMPDIR/case4h-dup"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/repo.foo_bar
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-repo-foo-bar** (open): Renovate disabled on repo.foo_bar; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.
- **TF-024X-renovate-jrnb2024-repo-foo-bar** (open): Renovate disabled on repo.foo_bar; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/repo.foo_bar@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 4h-dup"
  run_case "$repo_dir" 1 '' 'found 2'

  repo_dir="$TMPDIR/case4i"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded
- **Target:** jrnb2024/target
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-10T12:00:00Z — jrnb2024/decoy@main — jrnb2024/target@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 4i"
  stdout_file="$(mktemp "${TMPDIR}/stdout.XXXXXX")"
  stderr_file="$(mktemp "${TMPDIR}/stderr.XXXXXX")"
  if (cd "$repo_dir" && "$SCRIPT" --diff-base base --dispatch-note DISPATCH-NOTE.md --status-md STATUS.md --branch-protection-log docs/reviews/WP-SCP-020/branch-protection-log.md) >"$stdout_file" 2>"$stderr_file"; then
    status=0
  else
    status=$?
  fi
  if [ "$status" -ne 1 ]; then
    printf 'unexpected exit code: expected 1 got %s\n' "$status" >&2
    printf 'stdout:\n' >&2
    cat "$stdout_file" >&2
    printf 'stderr:\n' >&2
    cat "$stderr_file" >&2
    rm -f "$stdout_file" "$stderr_file"
    exit 1
  fi
  if grep -Fq "ERROR: log entry target 'jrnb2024/decoy' does not match DISPATCH-NOTE target 'jrnb2024/target'" "$stderr_file"; then
    :
  elif grep -Fq 'ERROR: expected exactly one log entry target match, found' "$stderr_file"; then
    :
  else
    printf 'expected stderr to contain a parse-error or target-mismatch message\n' >&2
    printf 'stdout:\n' >&2
    cat "$stdout_file" >&2
    printf 'stderr:\n' >&2
    cat "$stderr_file" >&2
    rm -f "$stdout_file" "$stderr_file"
    exit 1
  fi
  rm -f "$stdout_file" "$stderr_file"

  repo_dir="$TMPDIR/case4j"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded
- **Target:** jrnb2024/target
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-10T12:00:00Z --- jrnb2024/target@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 4j"
  run_case "$repo_dir" 1 '' 'ERROR: found log entry header but em-dash separator is missing; expected exactly one log entry target match, found 0: []'

  repo_dir="$TMPDIR/case15c"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded
cascade-status: onboarded
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 15c"
  run_case "$repo_dir" 1 '' 'expected exactly one cascade-status match, found 2: onboarded, onboarded'

  repo_dir="$TMPDIR/case9"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.
EOF
  commit_case "$repo_dir" "case 9"
  run_case "$repo_dir" 0 'OK: cascade-status=blocked-on-adopter-conflict; 2 checks passed' ''

  repo_dir="$TMPDIR/case10"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 10"
  run_case "$repo_dir" 1 '' 'ERROR: branch-protection-log.md was modified for cascade-status=blocked-on-adopter-conflict'

  repo_dir="$TMPDIR/case10c"
  init_case_repo "$repo_dir"
  mkdir -p "$repo_dir/scripts"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 10c"
  stdout_file="$(mktemp "${TMPDIR}/stdout.XXXXXX")"
  stderr_file="$(mktemp "${TMPDIR}/stderr.XXXXXX")"
  if (
    cd "$repo_dir/scripts" &&
    "$SCRIPT" --diff-base base --dispatch-note ../DISPATCH-NOTE.md --status-md ../STATUS.md --branch-protection-log ../docs/reviews/WP-SCP-020/branch-protection-log.md
  ) >"$stdout_file" 2>"$stderr_file"; then
    status=0
  else
    status=$?
  fi
  if [ "$status" -ne 1 ]; then
    printf 'unexpected exit code for subdirectory invocation: expected 1 got %s\n' "$status" >&2
    printf 'stdout:\n' >&2
    cat "$stdout_file" >&2
    printf 'stderr:\n' >&2
    cat "$stderr_file" >&2
    rm -f "$stdout_file" "$stderr_file"
    exit 1
  fi
  grep -Fq 'ERROR: branch-protection-log.md was modified for cascade-status=blocked-on-adopter-conflict' "$stderr_file" || {
    printf 'expected stderr to contain subdirectory diff guard failure\n' >&2
    printf 'stdout:\n' >&2
    cat "$stdout_file" >&2
    printf 'stderr:\n' >&2
    cat "$stderr_file" >&2
    rm -f "$stdout_file" "$stderr_file"
    exit 1
  }
  rm -f "$stdout_file" "$stderr_file"

  repo_dir="$TMPDIR/case10b"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 10b seed"
  git -C "$repo_dir" branch -f base HEAD
  : >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md"
  commit_case "$repo_dir" "case 10b remove"
  run_case "$repo_dir" 1 '' 'ERROR: branch-protection-log.md was modified for cascade-status=blocked-on-adopter-conflict'

  repo_dir="$TMPDIR/case11"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See policy-check conflict discussion; awaiting rename PR.
EOF
  commit_case "$repo_dir" "case 11"
  run_case "$repo_dir" 1 '' 'ERROR: DISPATCH-NOTE missing required TF-024X-conflict reference for the adopter target'

  repo_dir="$TMPDIR/case11b"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See TF-024X-conflict-jrnb2024-pim
EOF
  commit_case "$repo_dir" "case 11b"
  run_case "$repo_dir" 1 '' 'ERROR: DISPATCH-NOTE missing required TF-024X-conflict reference for the adopter target'

  repo_dir="$TMPDIR/case11c"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See TF-024X-conflict-jrnb2024-pim (pending):
EOF
  commit_case "$repo_dir" "case 11c"
  run_case "$repo_dir" 1 '' 'ERROR: DISPATCH-NOTE missing required TF-024X-conflict reference for the adopter target'

  repo_dir="$TMPDIR/case11d"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See TF-024X-conflict-jrnb2024-pim (pending):                    
EOF
  commit_case "$repo_dir" "case 11d"
  run_case "$repo_dir" 1 '' 'ERROR: DISPATCH-NOTE missing required TF-024X-conflict reference for the adopter target'

  repo_dir="$TMPDIR/case11e"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See TF-024X-conflict-jrnb2024-pim (pending): short
EOF
  commit_case "$repo_dir" "case 11e"
  run_case "$repo_dir" 1 '' 'ERROR: DISPATCH-NOTE missing required TF-024X-conflict reference for the adopter target'

  repo_dir="$TMPDIR/case11f-dup"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.
See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.
EOF
  commit_case "$repo_dir" "case 11f-dup"
  run_case "$repo_dir" 1 '' 'found 2'

  repo_dir="$TMPDIR/case12"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
- **Target:** jrnb2024/pim
EOF
  commit_case "$repo_dir" "case 12"
  run_case "$repo_dir" 1 '' 'ERROR: expected exactly one cascade-status match, found 0: []'

  repo_dir="$TMPDIR/case13"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: invalid-value
- **Target:** jrnb2024/pim
EOF
  commit_case "$repo_dir" "case 13"
  run_case "$repo_dir" 2 '' 'FAIL-CLOSED: cascade-status field absent or unrecognised; must be one of {onboarded, onboarded-operator-bump, blocked-on-adopter-conflict}; not applicable requires --allow-not-applicable for tooling slices only'

  repo_dir="$TMPDIR/case14"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
  cascade-status: onboarded
cascade-status: onboarded
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 14"
  run_case "$repo_dir" 0 'OK: cascade-status=onboarded; 2 checks passed' ''

  repo_dir="$TMPDIR/case15"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/pim
EOF
  commit_case "$repo_dir" "case 15"
  run_case "$repo_dir" 1 '' 'ERROR: expected exactly one cascade-status match, found 2: onboarded, onboarded-operator-bump'

  repo_dir="$TMPDIR/case15b"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: not applicable
slice-type: tooling
- **Target:** jrnb2024/pim
Worked example: cascade-status: onboarded
Worked example: cascade-status: blocked-on-adopter-conflict
See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-pim** (open): Renovate disabled on PIM; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.
EOF
  commit_case "$repo_dir" "case 15b"
  # Without --allow-not-applicable flag → exit 2 per fix-round-3 SAFE-MAJ-001 closure (technical guard for cohort-slice misuse).
  run_case "$repo_dir" 2 '' 'ERROR: cascade-status: not applicable found, but --allow-not-applicable was not passed.'
  # With --allow-not-applicable + a valid tooling-slice-id → exit 0 (tooling-slice opt-in).
  run_case "$repo_dir" 0 'OK: DISPATCH-NOTE declares cascade-status: not applicable; not a cohort cascade slice — nothing to enforce' '' "" --allow-not-applicable --tooling-slice-id 024B-core

  repo_dir="$TMPDIR/case15b-crlf"
  init_case_repo "$repo_dir"
  printf 'cascade-status: onboarded\r\n- **Target:** jrnb2024/pim\r\n' >"$repo_dir/DISPATCH-NOTE.md"
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 15b-crlf"
  run_case "$repo_dir" 0 'OK: cascade-status=onboarded; 2 checks passed' ''

  repo_dir="$TMPDIR/case15b-missing-slice-id"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: not applicable
slice-type: tooling
- **Target:** jrnb2024/pim
EOF
  commit_case "$repo_dir" "case 15b-missing-slice-id"
  run_case "$repo_dir" 2 '' 'ERROR: --allow-not-applicable requires --tooling-slice-id <id> where <id> ∈ {024A, 024B-core, 024B-extras, 024G}' "" --allow-not-applicable

  repo_dir="$TMPDIR/case15c-dup"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: not applicable
- **Target:** jrnb2024/pim
EOF
  commit_case "$repo_dir" "case 15c"
  run_case "$repo_dir" 2 '' "ERROR: --allow-not-applicable requires DISPATCH-NOTE to declare 'slice-type: tooling'. Found: MISSING. Cohort cascade slices (024C/D/E/F) MUST NOT pass --allow-not-applicable." "" --allow-not-applicable

  repo_dir="$TMPDIR/case15d"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: not applicable
slice-type: cohort
- **Target:** jrnb2024/pim
EOF
  commit_case "$repo_dir" "case 15d"
  run_case "$repo_dir" 2 '' "ERROR: --allow-not-applicable requires DISPATCH-NOTE to declare 'slice-type: tooling'. Found: cohort. Cohort cascade slices (024C/D/E/F) MUST NOT pass --allow-not-applicable." "" --allow-not-applicable --tooling-slice-id 024C

  repo_dir="$TMPDIR/case15f"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: not applicable
slice-type: tooling
- **Target:** jrnb2024/pim
EOF
  commit_case "$repo_dir" "case 15f"
  run_case "$repo_dir" 2 '' 'ERROR: --allow-not-applicable requires --tooling-slice-id <id> where <id> ∈ {024A, 024B-core, 024B-extras, 024G}' "" --allow-not-applicable --tooling-slice-id 024C

  repo_dir="$TMPDIR/case15e"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 15e"
  run_case "$repo_dir" 2 '' "ERROR: --allow-not-applicable was passed but cascade-status is 'onboarded'" "" --allow-not-applicable

  repo_dir="$TMPDIR/case18b"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-pim** (open): Renovate disabled on PIM; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  fake_gh_dir="$TMPDIR/fake-gh-case18b"
  mkdir -p "$fake_gh_dir"
  cat >"$fake_gh_dir/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

case "$*" in
  "pr view 99 --json body --jq .body")
    exit 0
    ;;
  "pr diff 99 --patch -- docs/reviews/WP-SCP-020/branch-protection-log.md")
    cat <<'PATCH'
diff --git a/docs/reviews/WP-SCP-020/branch-protection-log.md b/docs/reviews/WP-SCP-020/branch-protection-log.md
--- a/docs/reviews/WP-SCP-020/branch-protection-log.md
+++ b/docs/reviews/WP-SCP-020/branch-protection-log.md
@@
+### 2026-05-09T00:00:00Z — jrnb2024/pim@main
PATCH
    ;;
  *)
    printf 'unexpected gh args: %s\n' "$*" >&2
    exit 1
    ;;
esac
EOF
  chmod +x "$fake_gh_dir/gh"
  run_pr_case "$repo_dir" "$fake_gh_dir" 0 'OK: cascade-status=onboarded-operator-bump; 3 checks passed' ''

  repo_dir="$TMPDIR/case18c"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-pim** (open): Renovate disabled on PIM; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  fake_gh_dir="$TMPDIR/fake-gh-case18c"
  mkdir -p "$fake_gh_dir"
  cat >"$fake_gh_dir/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

case "$*" in
  "pr view 99 --json body --jq .body")
    exit 1
    ;;
  *)
    printf 'unexpected gh args: %s\n' "$*" >&2
    exit 1
    ;;
esac
EOF
  chmod +x "$fake_gh_dir/gh"
  run_pr_case "$repo_dir" "$fake_gh_dir" 2 '' 'ERROR: gh pr view failed for PR 99; check gh auth and PR existence'

  repo_dir="$TMPDIR/case19b"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.
EOF
  commit_case "$repo_dir" "case 19b"
  fake_gh_dir="$TMPDIR/fake-gh-case19b"
  mkdir -p "$fake_gh_dir"
  cat >"$fake_gh_dir/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

case "$*" in
  "pr view 99 --json body --jq .body")
    exit 0
    ;;
  "pr diff 99 --patch -- docs/reviews/WP-SCP-020/branch-protection-log.md")
    exit 0
    ;;
  *)
    printf 'unexpected gh args: %s\n' "$*" >&2
    exit 1
    ;;
esac
EOF
  chmod +x "$fake_gh_dir/gh"
  run_pr_case "$repo_dir" "$fake_gh_dir" 0 'OK: cascade-status=blocked-on-adopter-conflict; 2 checks passed' ''

  repo_dir="$TMPDIR/case20b"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.
EOF
  commit_case "$repo_dir" "case 20b"
  fake_gh_dir="$TMPDIR/fake-gh-case20b"
  mkdir -p "$fake_gh_dir"
  cat >"$fake_gh_dir/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

case "$*" in
  "pr view 99 --json body --jq .body")
    exit 0
    ;;
  "pr diff 99 --patch -- docs/reviews/WP-SCP-020/branch-protection-log.md")
    cat <<'PATCH'
diff --git a/docs/reviews/WP-SCP-020/branch-protection-log.md b/docs/reviews/WP-SCP-020/branch-protection-log-renamed.md
similarity index 93%
rename from docs/reviews/WP-SCP-020/branch-protection-log.md
rename to docs/reviews/WP-SCP-020/branch-protection-log-renamed.md
@@
+### 2026-05-09T00:00:00Z — jrnb2024/pim@main
PATCH
    ;;
  *)
    printf 'unexpected gh args: %s\n' "$*" >&2
    exit 1
    ;;
esac
EOF
  chmod +x "$fake_gh_dir/gh"
  run_pr_case "$repo_dir" "$fake_gh_dir" 1 '' 'ERROR: branch-protection-log.md was modified for cascade-status=blocked-on-adopter-conflict'

  repo_dir="$TMPDIR/case16"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  fake_gh_dir="$TMPDIR/fake-gh-case16"
  mkdir -p "$fake_gh_dir"
  cat >"$fake_gh_dir/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

case "$*" in
  "pr view 99 --json body --jq .body")
    exit 0
    ;;
  "pr diff 99 --name-only")
    printf '%s\n' \
      "docs/reviews/WP-SCP-020/branch-protection-log.md" \
      "other-file.txt"
    ;;
  "pr diff 99 --patch -- docs/reviews/WP-SCP-020/branch-protection-log.md")
    cat <<'PATCH'
diff --git a/docs/reviews/WP-SCP-020/branch-protection-log.md b/docs/reviews/WP-SCP-020/branch-protection-log.md
--- a/docs/reviews/WP-SCP-020/branch-protection-log.md
+++ b/docs/reviews/WP-SCP-020/branch-protection-log.md
@@
+### 2026-05-09T00:00:00Z — jrnb2024/pim@main
PATCH
    ;;
  "pr diff 99 --patch")
    cat <<'PATCH'
diff --git a/other-file.txt b/other-file.txt
--- a/other-file.txt
+++ b/other-file.txt
@@
+### 2026-05-09T00:00:00Z — jrnb2024/spoofed@main
diff --git a/docs/reviews/WP-SCP-020/branch-protection-log.md b/docs/reviews/WP-SCP-020/branch-protection-log.md
--- a/docs/reviews/WP-SCP-020/branch-protection-log.md
+++ b/docs/reviews/WP-SCP-020/branch-protection-log.md
@@
+### 2026-05-09T00:00:00Z — jrnb2024/wrong@main
PATCH
    ;;
  *)
    printf 'unexpected gh args: %s\n' "$*" >&2
    exit 1
    ;;
esac
EOF
  chmod +x "$fake_gh_dir/gh"
  run_pr_case "$repo_dir" "$fake_gh_dir" 0 'OK: cascade-status=onboarded; 2 checks passed' ''

  repo_dir="$TMPDIR/case17"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/phantom@main

- **Operator:** @tester
~~~
EOF
  fake_gh_dir="$TMPDIR/fake-gh-case17"
  mkdir -p "$fake_gh_dir"
  cat >"$fake_gh_dir/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

case "$*" in
  "pr view 99 --json body --jq .body")
    exit 0
    ;;
  "pr diff 99 --name-only")
    printf '%s\n' "docs/reviews/WP-SCP-020/branch-protection-log.md"
    ;;
  "pr diff 99 --patch -- docs/reviews/WP-SCP-020/branch-protection-log.md")
    cat <<'PATCH'
diff --git a/docs/reviews/WP-SCP-020/branch-protection-log.md b/docs/reviews/WP-SCP-020/branch-protection-log.md
--- a/docs/reviews/WP-SCP-020/branch-protection-log.md
+++ b/docs/reviews/WP-SCP-020/branch-protection-log.md
@@
+### 2026-05-09T00:00:00Z — jrnb2024/pim@main
+### 2026-05-09T00:00:00Z — jrnb2024/phantom@main
PATCH
    ;;
  *)
    printf 'unexpected gh args: %s\n' "$*" >&2
    exit 1
    ;;
esac
EOF
  chmod +x "$fake_gh_dir/gh"
  run_pr_case "$repo_dir" "$fake_gh_dir" 1 '' 'ERROR: expected exactly one log entry target match, found 2: jrnb2024/pim, jrnb2024/phantom'

  repo_dir="$TMPDIR/case18"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 18"
  run_case "$repo_dir" 0 'OK: cascade-status=onboarded; 2 checks passed' '' 'docs/reviews/WP-SCP-020//branch-protection-log.md'
  run_case "$repo_dir" 0 'OK: cascade-status=onboarded; 2 checks passed' '' "$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md"

  repo_dir="$TMPDIR/case19"
  init_case_repo "$repo_dir"
  outsider_log="$(mktemp "${TMPDIR}/outside.XXXXXX")"
  run_case "$repo_dir" 2 '' 'ERROR: --branch-protection-log must resolve inside repository root' "$outsider_log"

  repo_dir="$TMPDIR/case19a"
  init_case_repo "$repo_dir"
  outsider_dispatch_note="$(mktemp "${TMPDIR}/outside-dispatch.XXXXXX")"
  dispatch_stdout_file="$(mktemp "${TMPDIR}/dispatch-stdout.XXXXXX")"
  dispatch_stderr_file="$(mktemp "${TMPDIR}/dispatch-stderr.XXXXXX")"
  if (
    cd "$repo_dir" &&
    env -i PATH="$PATH" HOME="$HOME" \
      "$SCRIPT" \
      --diff-base base \
      --dispatch-note "$outsider_dispatch_note" \
      --status-md STATUS.md \
      --branch-protection-log docs/reviews/WP-SCP-020/branch-protection-log.md
  ) >"$dispatch_stdout_file" 2>"$dispatch_stderr_file"; then
    dispatch_status=0
  else
    dispatch_status=$?
  fi
  if [ "$dispatch_status" -ne 2 ]; then
    printf 'unexpected exit code: expected 2 got %s\n' "$dispatch_status" >&2
    printf 'stdout:\n' >&2
    cat "$dispatch_stdout_file" >&2
    printf 'stderr:\n' >&2
    cat "$dispatch_stderr_file" >&2
    exit 1
  fi
  grep -Fq 'ERROR: --dispatch-note must resolve inside repository root' "$dispatch_stderr_file" || fail "dispatch-note containment check did not fire"
  rm -f "$dispatch_stdout_file" "$dispatch_stderr_file" "$outsider_dispatch_note"

  repo_dir="$TMPDIR/case19b-status"
  init_case_repo "$repo_dir"
  outsider_status_md="$(mktemp "${TMPDIR}/outside-status.XXXXXX")"
  status_stdout_file="$(mktemp "${TMPDIR}/status-stdout.XXXXXX")"
  status_stderr_file="$(mktemp "${TMPDIR}/status-stderr.XXXXXX")"
  if (
    cd "$repo_dir" &&
    env -i PATH="$PATH" HOME="$HOME" \
      "$SCRIPT" \
      --diff-base base \
      --dispatch-note DISPATCH-NOTE.md \
      --status-md "$outsider_status_md" \
      --branch-protection-log docs/reviews/WP-SCP-020/branch-protection-log.md
  ) >"$status_stdout_file" 2>"$status_stderr_file"; then
    status_case_status=0
  else
    status_case_status=$?
  fi
  if [ "$status_case_status" -ne 2 ]; then
    printf 'unexpected exit code: expected 2 got %s\n' "$status_case_status" >&2
    printf 'stdout:\n' >&2
    cat "$status_stdout_file" >&2
    printf 'stderr:\n' >&2
    cat "$status_stderr_file" >&2
    exit 1
  fi
  grep -Fq 'ERROR: --status-md must resolve inside repository root' "$status_stderr_file" || fail "status-md containment check did not fire"
  rm -f "$status_stdout_file" "$status_stderr_file" "$outsider_status_md"

  repo_dir="$TMPDIR/case22"
  init_case_repo "$repo_dir"
  invalid_diff_base_stdout="$(mktemp "${TMPDIR}/invalid-diff-base.stdout.XXXXXX")"
  invalid_diff_base_stderr="$(mktemp "${TMPDIR}/invalid-diff-base.stderr.XXXXXX")"
  if (
    cd "$repo_dir" &&
    env -i PATH="$PATH" HOME="$HOME" \
      "$SCRIPT" \
      --diff-base does-not-exist \
      --dispatch-note DISPATCH-NOTE.md \
      --status-md STATUS.md \
      --branch-protection-log docs/reviews/WP-SCP-020/branch-protection-log.md
  ) >"$invalid_diff_base_stdout" 2>"$invalid_diff_base_stderr"; then
    invalid_diff_base_status=0
  else
    invalid_diff_base_status=$?
  fi
  if [ "$invalid_diff_base_status" -ne 2 ]; then
    printf 'unexpected exit code: expected 2 got %s\n' "$invalid_diff_base_status" >&2
    printf 'stdout:\n' >&2
    cat "$invalid_diff_base_stdout" >&2
    printf 'stderr:\n' >&2
    cat "$invalid_diff_base_stderr" >&2
    exit 1
  fi
  grep -Fq "ERROR: could not compute diff for diff-base 'does-not-exist'; is this a valid git ref?" "$invalid_diff_base_stderr" || fail "invalid diff-base did not produce controlled diagnostic"
  rm -f "$invalid_diff_base_stdout" "$invalid_diff_base_stderr"

  repo_dir="$TMPDIR/case23"
  init_case_repo "$repo_dir"
  head_stdout_file="$(mktemp "${TMPDIR}/head-stdout.XXXXXX")"
  head_stderr_file="$(mktemp "${TMPDIR}/head-stderr.XXXXXX")"
  if (
    cd "$repo_dir" &&
    env -i PATH="$PATH" HOME="$HOME" \
      "$SCRIPT" \
      --diff-base HEAD \
      --dispatch-note DISPATCH-NOTE.md \
      --status-md STATUS.md \
      --branch-protection-log docs/reviews/WP-SCP-020/branch-protection-log.md
  ) >"$head_stdout_file" 2>"$head_stderr_file"; then
    head_status=0
  else
    head_status=$?
  fi
  if [ "$head_status" -ne 2 ]; then
    printf 'unexpected exit code: expected 2 got %s\n' "$head_status" >&2
    printf 'stdout:\n' >&2
    cat "$head_stdout_file" >&2
    printf 'stderr:\n' >&2
    cat "$head_stderr_file" >&2
    exit 1
  fi
  grep -Fq 'ERROR: --diff-base resolves to HEAD — diff is trivially empty; provide the PR base commit or origin/main instead' "$head_stderr_file" || fail "HEAD diff-base did not produce controlled diagnostic"
  rm -f "$head_stdout_file" "$head_stderr_file"

  repo_dir="$TMPDIR/case20"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
  cascade-status: not applicable
cascade-status: onboarded
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 20"
  run_case "$repo_dir" 0 'OK: cascade-status=onboarded; 2 checks passed' ''

  repo_dir="$TMPDIR/restore-transform"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/pre-state.json" <<'EOF'
{
  "_links": {"html": "https://example.invalid"},
  "url": "https://api.github.com/repos/jrnb2024/pim/branches/main/protection",
  "checks": [{"url": "https://example.invalid/check"}],
  "required_signatures": {"enabled": true},
  "required_status_checks": {
    "_links": {"self": "https://example.invalid/self"},
    "checks": [],
    "strict": true,
    "contexts": ["policy-check / scp/policy-check"]
  },
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null
}
EOF
  fake_gh_dir="$TMPDIR/fake-gh-restore-transform"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":1,"path":".github/workflows/policy-check.yml"},{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-1.json" <<'EOF'
{"workflow_runs":[]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"main"}]}
EOF
  cat >"$fake_gh_dir/before.json" <<'EOF'
{
  "required_status_checks": {"strict": false, "contexts": []},
  "enforce_admins": {"enabled": false},
  "required_pull_request_reviews": null,
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  cat >"$fake_gh_dir/after.json" <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["policy-check / scp/policy-check"]
  },
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": true}
}
EOF
  cat >"$fake_gh_dir/tags.json" <<'EOF'
[]
EOF
  commit_case "$repo_dir" "restore transform"
  run_restore_case "$repo_dir" "$fake_gh_dir" 0 'verification passed ✓' ''
  jq -e '
    (has("_links") | not) and
    (has("url") | not) and
    (has("checks") | not) and
    (has("required_signatures") | not) and
    (.enforce_admins | type == "boolean") and
    (.enforce_admins == true) and
    (.required_status_checks | has("_links") | not) and
    (.required_status_checks | has("checks") | not) and
    (.required_status_checks.strict == true) and
    (.required_status_checks.contexts[0] == "policy-check / scp/policy-check")
  ' "$fake_gh_dir/put-body.json" >/dev/null || fail "restore transform did not strip GET-only fields or coerce enforce_admins to boolean"
  grep -Fq 'POST required_signatures' "$fake_gh_dir/calls.log" || fail "restore transform case did not invoke required_signatures POST"

  repo_dir="$TMPDIR/restore-put-fail"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/pre-state.json" <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["policy-check / scp/policy-check"]
  },
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": true}
}
EOF
  fake_gh_dir="$TMPDIR/fake-gh-restore-put-fail"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"main"}]}
EOF
  cat >"$fake_gh_dir/before.json" <<'EOF'
{
  "required_status_checks": {"strict": true, "contexts": ["policy-check / scp/policy-check"]},
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": true}
}
EOF
  cat >"$fake_gh_dir/after.json" <<'EOF'
{
  "required_status_checks": {"strict": true, "contexts": ["policy-check / scp/policy-check"]},
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": true}
}
EOF
  cat >"$fake_gh_dir/put_fail" <<'EOF'
boom
EOF
  commit_case "$repo_dir" "restore put fail"
  run_restore_case "$repo_dir" "$fake_gh_dir" 1 '- **Restore mode:** yes' 'ERROR: unified PUT failed'

  repo_dir="$TMPDIR/restore-admin-ack"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/pre-state.json" <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["policy-check / scp/policy-check"]
  },
  "enforce_admins": {"enabled": false},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  fake_gh_dir="$TMPDIR/fake-gh-restore-admin-ack"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"main"}]}
EOF
  cat >"$fake_gh_dir/before.json" <<'EOF'
{
  "required_status_checks": {"strict": true, "contexts": ["policy-check / scp/policy-check"]},
  "enforce_admins": {"enabled": false},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  cat >"$fake_gh_dir/after.json" <<'EOF'
{
  "required_status_checks": {"strict": true, "contexts": ["policy-check / scp/policy-check"]},
  "enforce_admins": {"enabled": false},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  commit_case "$repo_dir" "restore admin ack"
  run_restore_case "$repo_dir" "$fake_gh_dir" 2 '' 'restore target removes admin enforcement'
  run_restore_case "$repo_dir" "$fake_gh_dir" 0 'verification passed ✓' '' --i-understand-restore-removes-admin-enforcement

  repo_dir="$TMPDIR/restore-checks-ack"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/pre-state.json" <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": []
  },
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  fake_gh_dir="$TMPDIR/fake-gh-restore-checks-ack"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"main"}]}
EOF
  cat >"$fake_gh_dir/before.json" <<'EOF'
{
  "required_status_checks": {"strict": true, "contexts": []},
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  cat >"$fake_gh_dir/after.json" <<'EOF'
{
  "required_status_checks": {"strict": true, "contexts": []},
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  commit_case "$repo_dir" "restore checks ack"
  run_restore_case "$repo_dir" "$fake_gh_dir" 2 '' 'restore target removes required status checks'
  run_restore_case "$repo_dir" "$fake_gh_dir" 0 'verification passed ✓' '' --i-understand-restore-removes-required-checks

  repo_dir="$TMPDIR/restore-delete-404"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/pre-state.json" <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["policy-check / scp/policy-check"]
  },
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  fake_gh_dir="$TMPDIR/fake-gh-restore-delete-404"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"main"}]}
EOF
  cat >"$fake_gh_dir/before.json" <<'EOF'
{
  "required_status_checks": {"strict": true, "contexts": ["policy-check / scp/policy-check"]},
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  cat >"$fake_gh_dir/after.json" <<'EOF'
{
  "required_status_checks": {"strict": true, "contexts": ["policy-check / scp/policy-check"]},
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  cat >"$fake_gh_dir/delete_required_signatures_404" <<'EOF'
404 Not Found
EOF
  commit_case "$repo_dir" "restore delete 404"
  run_restore_case "$repo_dir" "$fake_gh_dir" 0 'required_signatures DELETE already in desired state (404 suppressed)' ''

  repo_dir="$TMPDIR/restore-post-404"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/pre-state.json" <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["policy-check / scp/policy-check"]
  },
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": true}
}
EOF
  fake_gh_dir="$TMPDIR/fake-gh-restore-post-404"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"main"}]}
EOF
  cat >"$fake_gh_dir/before.json" <<'EOF'
{
  "required_status_checks": {"strict": true, "contexts": ["policy-check / scp/policy-check"]},
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": true}
}
EOF
  cat >"$fake_gh_dir/after.json" <<'EOF'
{
  "required_status_checks": {"strict": true, "contexts": ["policy-check / scp/policy-check"]},
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": true}
}
EOF
  cat >"$fake_gh_dir/post_required_signatures_404" <<'EOF'
404 Not Found
EOF
  commit_case "$repo_dir" "restore post 404"
  run_restore_case "$repo_dir" "$fake_gh_dir" 0 'required_signatures POST already in desired state (404 suppressed)' ''

  repo_dir="$TMPDIR/enable-expected-sha"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-10T12:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
- **Restore mode:** yes
- **Restoring TO:**
```json
{"restore":"evidence"}
```
~~~
EOF
  fake_gh_dir="$TMPDIR/fake-gh-enable-expected-sha"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":1,"path":".github/workflows/policy-check.yml"},{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-1.json" <<'EOF'
{"workflow_runs":[]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"main"}]}
EOF
  cat >"$fake_gh_dir/before.json" <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["policy-check / scp/policy-check"]
  },
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": true}
}
EOF
  cat >"$fake_gh_dir/after.json" <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["policy-check / scp/policy-check"]
  },
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": true}
}
EOF
  cat >"$fake_gh_dir/tags.json" <<'EOF'
[{"ref":"refs/tags/v1.2.3"}]
EOF
  cat >"$fake_gh_dir/tag-refs/v1.2.3.json" <<'EOF'
{"object":{"sha":"1111111111111111111111111111111111111111"}}
EOF
  commit_case "$repo_dir" "enable expected sha"
  printf '%s\n' \
    '---' \
    '' \
    '## Invocation log entry' \
    '' \
    '~~~markdown' \
    '### 2026-05-10T12:00:00Z — jrnb2024/pim@main' \
    '' \
    '- **Operator:** @tester' \
    '- **Restore mode:** yes' \
    '- **Restoring TO:**' \
    '```json' \
    '{"restore":"evidence"}' \
    '```' \
    '~~~' >>"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md"
  run_enable_case "$repo_dir" "$fake_gh_dir" 0 'expected wrapper SHA validated against release tag' '' --expected-wrapper-sha 1111111111111111111111111111111111111111

  repo_dir="$TMPDIR/enable-expected-sha-arbitrary"
  init_case_repo "$repo_dir"
  fake_gh_dir="$TMPDIR/fake-gh-enable-expected-sha-arbitrary"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"main"}]}
EOF
  cat >"$fake_gh_dir/tags.json" <<'EOF'
[{"ref":"refs/tags/v1.2.3"}]
EOF
  cat >"$fake_gh_dir/tag-refs/v1.2.3.json" <<'EOF'
{"object":{"sha":"1111111111111111111111111111111111111111"}}
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-10T12:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
- **Restore mode:** yes
- **Restoring TO:**
```json
{"restore":"evidence"}
```
~~~
EOF
  commit_case "$repo_dir" "enable arbitrary sha"
  printf '%s\n' \
    '---' \
    '' \
    '## Invocation log entry' \
    '' \
    '~~~markdown' \
    '### 2026-05-10T12:00:00Z — jrnb2024/pim@main' \
    '' \
    '- **Operator:** @tester' \
    '- **Restore mode:** yes' \
    '- **Restoring TO:**' \
    '```json' \
    '{"restore":"evidence"}' \
    '```' \
    '~~~' >>"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md"
  run_enable_case "$repo_dir" "$fake_gh_dir" 2 '' 'was not found in the release-tag SHA cache' --expected-wrapper-sha 2222222222222222222222222222222222222222

  repo_dir="$TMPDIR/enable-sha-mutex"
  init_case_repo "$repo_dir"
  fake_gh_dir="$TMPDIR/fake-gh-enable-sha-mutex"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"main"}]}
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-10T12:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
- **Restore mode:** yes
- **Restoring TO:**
```json
{"restore":"evidence"}
```
~~~
EOF
  commit_case "$repo_dir" "enable sha mutex"
  run_enable_case "$repo_dir" "$fake_gh_dir" 2 '' 'cannot be combined with --i-understand-this-repo-has-no-prior-green-ci' --expected-wrapper-sha 1111111111111111111111111111111111111111 --i-understand-this-repo-has-no-prior-green-ci
}

main
