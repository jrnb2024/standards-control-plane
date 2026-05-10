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

run_workflow_guard_case() {
  local fake_gh_dir="$1"
  local expected_exit="$2"
  local expected_stdout="$3"
  local expected_stderr="$4"
  local expected_output="${5:-}"
  local stdout_file stderr_file output_file status
  stdout_file="$(mktemp "${TMPDIR}/workflow-stdout.XXXXXX")"
  stderr_file="$(mktemp "${TMPDIR}/workflow-stderr.XXXXXX")"
  output_file="$(mktemp "${TMPDIR}/workflow-output.XXXXXX")"
  if (
    PATH="$fake_gh_dir:$PATH" \
    PR_NUMBER=99 \
    GITHUB_REPOSITORY="jrnb2024/standards-control-plane" \
    GITHUB_OUTPUT="$output_file" \
    bash -c '
      set -euo pipefail
      pr_files="$(gh pr diff "$PR_NUMBER" --name-only --repo "$GITHUB_REPOSITORY")"
      all_dispatch_notes="$(printf "%s\n" "$pr_files" | grep -E "^docs/reviews/WP-SCP-024/024[A-Za-z][^/]*/DISPATCH-NOTE.md$" || true)"
      log_modified_count="$(printf "%s\n" "$pr_files" | grep -c "^docs/reviews/WP-SCP-020/branch-protection-log.md$" || true)"
      if [ -z "$all_dispatch_notes" ]; then
        if [ "$log_modified_count" -gt 0 ]; then
          echo "ERROR: branch-protection-log.md was modified without a corresponding cascade-slice DISPATCH-NOTE update; cascade-status declaration required." >&2
          exit 1
        fi
        echo "No cascade-slice DISPATCH-NOTE found in PR diff; not a cohort cascade slice - nothing to enforce."
        printf "enforce=false\n" >> "$GITHUB_OUTPUT"
        exit 0
      fi
      cohort_dispatch_note="$(printf "%s\n" "$all_dispatch_notes" | grep -E "^docs/reviews/WP-SCP-024/024[C-F]/DISPATCH-NOTE.md$" | head -n1 || true)"
      if [ -n "$cohort_dispatch_note" ]; then
        dispatch_note="$cohort_dispatch_note"
      else
        dispatch_note="$(printf "%s\n" "$all_dispatch_notes" | head -n1)"
      fi
      slice_id="$(basename "$(dirname "$dispatch_note")")"
      case "$slice_id" in
        024A|024B-core|024B-extras|024G)
          echo "Tooling slice ($slice_id); no enforcement needed."
          printf "enforce=false\n" >> "$GITHUB_OUTPUT"
          exit 0
          ;;
      esac
      printf "enforce=true\n" >> "$GITHUB_OUTPUT"
      printf "dispatch_note=%s\n" "$dispatch_note" >> "$GITHUB_OUTPUT"
    '
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
    rm -f "$stdout_file" "$stderr_file" "$output_file"
    exit 1
  fi
  if [ -n "$expected_stdout" ]; then
    grep -Fq -- "$expected_stdout" "$stdout_file" || {
      printf 'expected stdout to contain: %s\n' "$expected_stdout" >&2
      printf 'stdout:\n' >&2
      cat "$stdout_file" >&2
      printf 'stderr:\n' >&2
      cat "$stderr_file" >&2
      rm -f "$stdout_file" "$stderr_file" "$output_file"
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
      rm -f "$stdout_file" "$stderr_file" "$output_file"
      exit 1
    }
  fi
  if [ -n "$expected_output" ]; then
    grep -Fq -- "$expected_output" "$output_file" || {
      printf 'expected GITHUB_OUTPUT to contain: %s\n' "$expected_output" >&2
      printf 'stdout:\n' >&2
      cat "$stdout_file" >&2
      printf 'stderr:\n' >&2
      cat "$stderr_file" >&2
      printf 'GITHUB_OUTPUT:\n' >&2
      cat "$output_file" >&2
      rm -f "$stdout_file" "$stderr_file" "$output_file"
      exit 1
    }
  fi
  rm -f "$stdout_file" "$stderr_file" "$output_file"
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
paginate=0
while [ $# -gt 0 ]; do
  case "$1" in
    --paginate)
      paginate=1
      shift
      ;;
    -X)
      method="${2:-GET}"
      shift 2
      ;;
    *)
      break
      ;;
  esac
done

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
    --paginate)
      paginate=1
      shift
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
  repos/*/actions/runs?*workflow_id=*)
    log_call "workflow-runs ${endpoint}"
    if [[ "$endpoint" == *"branch="* ]]; then
      printf 'unexpected branch filter in workflow-runs request: %s\n' "$endpoint" >&2
      exit 1
    fi
    if [[ "$endpoint" == *"created>="* || "$endpoint" == *"created>"* ]]; then
      printf 'unexpected malformed created filter in workflow-runs request: %s\n' "$endpoint" >&2
      exit 1
    fi
    if [[ "$endpoint" != *"created=%3E%3D"* ]]; then
      printf 'missing encoded created filter in workflow-runs request: %s\n' "$endpoint" >&2
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
    if [ "$paginate" -eq 1 ] && [ -f "${FAKE_DIR}/tags-pages.json" ]; then
      log_call "paginate tags"
      cat "${FAKE_DIR}/tags-pages.json"
    elif [ -f "$TAGS_FILE" ]; then
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
  local restore_path="pre-state.json"
  if [ $# -ge 6 ]; then
    case "${6:-}" in
      --*) ;;
      *)
        restore_path="$6"
        shift 1
        ;;
    esac
  fi
  shift 5
  local restore_script
  restore_script="$repo_dir/scripts/enable-required-check.sh"
  mkdir -p "$(dirname "$restore_script")"
  cp "$RESTORE_SCRIPT" "$restore_script"
  chmod +x "$restore_script"
  local stdout_file stderr_file status
  stdout_file="$(mktemp "${TMPDIR}/restore-stdout.XXXXXX")"
  stderr_file="$(mktemp "${TMPDIR}/restore-stderr.XXXXXX")"
  if (
    cd "$repo_dir" &&
    unset CI GITHUB_ACTIONS &&
    PATH="$fake_gh_dir:$PATH" \
    "$restore_script" \
      --repo jrnb2024/pim \
      --branch main \
      --restore "$restore_path" \
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
  shift 5
  local restore_script
  restore_script="$repo_dir/scripts/enable-required-check.sh"
  mkdir -p "$(dirname "$restore_script")"
  cp "$RESTORE_SCRIPT" "$restore_script"
  chmod +x "$restore_script"
  local stdout_file stderr_file status
  stdout_file="$(mktemp "${TMPDIR}/enable-stdout.XXXXXX")"
  stderr_file="$(mktemp "${TMPDIR}/enable-stderr.XXXXXX")"
  if (
    cd "$repo_dir" &&
    unset CI GITHUB_ACTIONS &&
    PATH="$fake_gh_dir:$PATH" \
    "$restore_script" \
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

run_enable_case_at_cwd() {
  local workdir="$1"
  local fake_gh_dir="$2"
  local repo="$3"
  local branch="$4"
  local expected_exit="$5"
  local expected_stdout="$6"
  local expected_stderr="$7"
  local script_path="${RESTORE_SCRIPT}"
  if [ $# -ge 8 ]; then
    case "${8:-}" in
      --*) shift 7 ;;
      *) script_path="$8"; shift 8 ;;
    esac
  else
    shift 7
  fi
  local stdout_file stderr_file status
  stdout_file="$(mktemp "${TMPDIR}/enable-cwd-stdout.XXXXXX")"
  stderr_file="$(mktemp "${TMPDIR}/enable-cwd-stderr.XXXXXX")"
  if (
    cd "$workdir" &&
    unset CI GITHUB_ACTIONS &&
    PATH="$fake_gh_dir:$PATH" \
    "$script_path" \
      --repo "$repo" \
      --branch "$branch" \
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

run_restore_admin_posture_case() {
  local repo_dir="$1"
  local fake_gh_dir="$2"
  local enabled_literal="$3"
  local expected_exit="$4"
  local expected_stdout="$5"
  local expected_stderr="$6"
  local extra_flag="${7:-}"
  local after_enabled

  init_case_repo "$repo_dir"
  cat >"$repo_dir/pre-state.json" <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["policy-check / scp/policy-check"]
  },
  "enforce_admins": {"enabled": ${enabled_literal}},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
EOF
  case "$enabled_literal" in
    1|true) after_enabled=true ;;
    *) after_enabled=false ;;
  esac
  cat >"$fake_gh_dir/before.json" <<EOF
{
  "required_status_checks": {"strict": true, "contexts": ["policy-check / scp/policy-check"]},
  "enforce_admins": {"enabled": ${enabled_literal}},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  cat >"$fake_gh_dir/after.json" <<EOF
{
  "required_status_checks": {"strict": true, "contexts": ["policy-check / scp/policy-check"]},
  "enforce_admins": {"enabled": ${after_enabled}},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  cat >"$fake_gh_dir/tags.json" <<'EOF'
[]
EOF
  commit_case "$repo_dir" "restore admin posture ${enabled_literal}"
  if [ -n "$extra_flag" ]; then
    run_restore_case "$repo_dir" "$fake_gh_dir" "$expected_exit" "$expected_stdout" "$expected_stderr" "$extra_flag"
  else
    run_restore_case "$repo_dir" "$fake_gh_dir" "$expected_exit" "$expected_stdout" "$expected_stderr"
  fi
}

run_restore_posture_flag_case() {
  local repo_dir="$1"
  local fake_gh_dir="$2"
  local field_name="$3"
  local enabled_literal="$4"
  local expected_exit="$5"
  local expected_stdout="$6"
  local expected_stderr="$7"
  local extra_flag="${8:-}"
  local field_value

  init_case_repo "$repo_dir"
  cat >"$repo_dir/pre-state.json" <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["policy-check / scp/policy-check"]
  },
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false},
  "${field_name}": ${enabled_literal}
}
EOF
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
EOF
  field_value="false"
  case "$enabled_literal" in
    1|true) field_value="true" ;;
  esac
  cat >"$fake_gh_dir/before.json" <<EOF
{
  "required_status_checks": {"strict": true, "contexts": ["policy-check / scp/policy-check"]},
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false},
  "${field_name}": ${field_value}
}
EOF
  cat >"$fake_gh_dir/after.json" <<EOF
{
  "required_status_checks": {"strict": true, "contexts": ["policy-check / scp/policy-check"]},
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false},
  "${field_name}": ${field_value}
}
EOF
  cat >"$fake_gh_dir/tags.json" <<'EOF'
[]
EOF
  commit_case "$repo_dir" "restore ${field_name} ${enabled_literal}"
  if [ -n "$extra_flag" ]; then
    run_restore_case "$repo_dir" "$fake_gh_dir" "$expected_exit" "$expected_stdout" "$expected_stderr" "$extra_flag"
  else
    run_restore_case "$repo_dir" "$fake_gh_dir" "$expected_exit" "$expected_stdout" "$expected_stderr"
  fi
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
  "enforcement_level": "off",
  "required_signatures": {"enabled": true},
  "required_status_checks": {
    "_links": {"self": "https://example.invalid/self"},
    "checks": [],
    "contexts_url": "https://example.invalid/contexts",
    "enforcement_level": "off",
    "url": "https://example.invalid/status-checks",
    "strict": true,
    "contexts": ["policy-check / scp/policy-check"]
  },
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "url": "https://example.invalid/reviews",
    "dismissal_restrictions": {
      "url": "https://example.invalid/reviews/dismissal",
      "users_url": "https://example.invalid/reviews/users",
      "teams_url": "https://example.invalid/reviews/teams",
      "apps_url": "https://example.invalid/reviews/apps"
    }
  },
  "restrictions": {
    "url": "https://example.invalid/restrictions",
    "users_url": "https://example.invalid/restrictions/users",
    "teams_url": "https://example.invalid/restrictions/teams",
    "apps_url": "https://example.invalid/restrictions/apps",
    "users": [
      {"login": "alice", "id": 1, "type": "User", "site_admin": false},
      {"login": "bob", "id": 2, "type": "User", "site_admin": true}
    ],
    "teams": [
      {"slug": "platform", "id": 10, "permission": "push"}
    ],
    "apps": [
      {"slug": "octobot", "id": 99}
    ]
  }
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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
    (has("enforcement_level") | not) and
    (has("required_signatures") | not) and
    (.enforce_admins | type == "boolean") and
    (.enforce_admins == true) and
    (.required_status_checks | has("_links") | not) and
    (.required_status_checks | has("url") | not) and
    (.required_status_checks | has("checks") | not) and
    (.required_status_checks | has("contexts_url") | not) and
    (.required_status_checks | has("enforcement_level") | not) and
    (.required_status_checks.strict == true) and
    (.required_status_checks.contexts[0] == "policy-check / scp/policy-check") and
    (.required_pull_request_reviews | has("url") | not) and
    (.required_pull_request_reviews.dismissal_restrictions | has("url") | not) and
    (.required_pull_request_reviews.dismissal_restrictions | has("users_url") | not) and
    (.required_pull_request_reviews.dismissal_restrictions | has("teams_url") | not) and
    (.required_pull_request_reviews.dismissal_restrictions | has("apps_url") | not) and
    (.restrictions | has("url") | not) and
    (.restrictions | has("users_url") | not) and
    (.restrictions | has("teams_url") | not) and
    (.restrictions | has("apps_url") | not) and
    (.restrictions.users == ["alice", "bob"]) and
    (.restrictions.teams == ["platform"]) and
    (.restrictions.apps == ["octobot"])
  ' "$fake_gh_dir/put-body.json" >/dev/null || fail "restore transform did not strip GET-only fields or coerce enforce_admins to boolean"
  grep -Fq 'POST required_signatures' "$fake_gh_dir/calls.log" || fail "restore transform case did not invoke required_signatures POST"

  repo_dir="$TMPDIR/restore-transform-absolute"
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
  fake_gh_dir="$TMPDIR/fake-gh-restore-transform-absolute"
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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  abs_pre_state="$repo_dir/pre-state.json"
  commit_case "$repo_dir" "restore transform absolute path"
  run_restore_case "$repo_dir" "$fake_gh_dir" 0 'verification passed ✓' '' "$abs_pre_state"

  repo_dir="$TMPDIR/restore-log-sanitization"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/pre-state.json" <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["legit-check`\nattacker line"]
  },
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": true}
}
EOF
  fake_gh_dir="$TMPDIR/fake-gh-restore-log-sanitization"
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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
EOF
  cat >"$fake_gh_dir/before.json" <<'EOF'
{
  "required_status_checks": {"strict": false, "contexts": []},
  "enforce_admins": {"enabled": false},
  "required_pull_request_reviews": null,
  "restrictions": null,
  "required_signatures": {"enabled": true}
}
EOF
  cat >"$fake_gh_dir/after.json" <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["legit-check`\nattacker line"]
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
  commit_case "$repo_dir" "restore log sanitization"
  # shellcheck disable=SC2016
  run_restore_case "$repo_dir" "$fake_gh_dir" 0 '- **Required check:** `legit-check\` attacker line`' ''

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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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

  repo_dir="$TMPDIR/restore-incompat"
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
  fake_gh_dir="$TMPDIR/fake-gh-restore-incompat"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  "required_status_checks": {"strict": true, "contexts": []},
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  cat >"$fake_gh_dir/tags.json" <<'EOF'
[]
EOF
  commit_case "$repo_dir" "restore incompatibilities"
  run_restore_case "$repo_dir" "$fake_gh_dir" 2 '' 'cannot be combined with --plan' --plan
  run_restore_case "$repo_dir" "$fake_gh_dir" 2 '' 'cannot be combined with --no-enforce-admins' --no-enforce-admins
  run_restore_case "$repo_dir" "$fake_gh_dir" 2 '' 'cannot be combined with --i-understand-this-bypasses-the-gate' --i-understand-this-bypasses-the-gate
  run_restore_case "$repo_dir" "$fake_gh_dir" 2 '' 'cannot be combined with --expected-wrapper-sha' --expected-wrapper-sha 1111111111111111111111111111111111111111
  run_restore_case "$repo_dir" "$fake_gh_dir" 2 '' 'cannot be combined with --i-understand-this-repo-has-no-prior-green-ci' --i-understand-this-repo-has-no-prior-green-ci
  run_restore_case "$repo_dir" "$fake_gh_dir" 2 '' 'cannot be combined with --i-understand-no-gate-2-verification' --i-understand-no-gate-2-verification

  run_restore_admin_posture_case "$TMPDIR/restore-admin-zero" "$TMPDIR/fake-gh-restore-admin-zero" 0 2 '' 'restore target removes admin enforcement'
  run_restore_admin_posture_case "$TMPDIR/restore-admin-zero-ack" "$TMPDIR/fake-gh-restore-admin-zero-ack" 0 0 'verification passed ✓' '' --i-understand-restore-removes-admin-enforcement
  run_restore_admin_posture_case "$TMPDIR/restore-admin-false" "$TMPDIR/fake-gh-restore-admin-false" false 2 '' 'restore target removes admin enforcement'
  run_restore_admin_posture_case "$TMPDIR/restore-admin-one" "$TMPDIR/fake-gh-restore-admin-one" 1 0 'verification passed ✓' ''
  run_restore_admin_posture_case "$TMPDIR/restore-admin-true" "$TMPDIR/fake-gh-restore-admin-true" true 0 'verification passed ✓' ''
  run_restore_admin_posture_case "$TMPDIR/restore-admin-null" "$TMPDIR/fake-gh-restore-admin-null" null 2 '' 'restore target removes admin enforcement'

  repo_dir="$TMPDIR/restore-admin-string-false"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/pre-state.json" <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["policy-check / scp/policy-check"]
  },
  "enforce_admins": {"enabled": "false"},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  fake_gh_dir="$TMPDIR/fake-gh-restore-admin-string-false"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  "required_status_checks": {"strict": true, "contexts": []},
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  commit_case "$repo_dir" "restore admin string false"
  run_restore_case "$repo_dir" "$fake_gh_dir" 2 '' 'enforce_admins.enabled must be a boolean'

  run_restore_posture_flag_case "$TMPDIR/restore-force-pushes" "$TMPDIR/fake-gh-restore-force-pushes" allow_force_pushes true 2 '' 'restore target re-enables allow_force_pushes'
  run_restore_posture_flag_case "$TMPDIR/restore-force-pushes-ack" "$TMPDIR/fake-gh-restore-force-pushes-ack" allow_force_pushes true 0 'CAUTION: restore target re-enables allow_force_pushes' '' --i-understand-restore-re-enables-force-pushes
  jq -e '.allow_force_pushes == true' "$TMPDIR/fake-gh-restore-force-pushes-ack/put-body.json" >/dev/null || fail "restore force_pushes ack did not preserve allow_force_pushes=true in PUT body"
  run_restore_posture_flag_case "$TMPDIR/restore-deletions" "$TMPDIR/fake-gh-restore-deletions" allow_deletions true 2 '' 'restore target re-enables allow_deletions'
  run_restore_posture_flag_case "$TMPDIR/restore-deletions-ack" "$TMPDIR/fake-gh-restore-deletions-ack" allow_deletions true 0 'CAUTION: restore target re-enables allow_deletions' '' --i-understand-restore-re-enables-deletions
  jq -e '.allow_deletions == true' "$TMPDIR/fake-gh-restore-deletions-ack/put-body.json" >/dev/null || fail "restore deletions ack did not preserve allow_deletions=true in PUT body"

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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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

  repo_dir="$TMPDIR/restore-null-status-checks"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/pre-state.json" <<'EOF'
{
  "required_status_checks": null,
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  fake_gh_dir="$TMPDIR/fake-gh-restore-null-status-checks"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  "required_status_checks": {"strict": false, "contexts": []},
  "enforce_admins": {"enabled": true},
  "required_pull_request_reviews": {"dismiss_stale_reviews": true},
  "restrictions": null,
  "required_signatures": {"enabled": false}
}
EOF
  commit_case "$repo_dir" "restore null required_status_checks"
  run_restore_case "$repo_dir" "$fake_gh_dir" 0 'verification passed ✓' '' --i-understand-restore-removes-required-checks
  jq -e '
    (.required_status_checks.strict == false) and
    (.required_status_checks.contexts | length == 0)
  ' "$fake_gh_dir/put-body.json" >/dev/null || fail "restore null required_status_checks did not coerce to PUT-safe empty shape"

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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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

  repo_dir="$TMPDIR/restore-delete-fail"
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
  fake_gh_dir="$TMPDIR/fake-gh-restore-delete-fail"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  cat >"$fake_gh_dir/delete_required_signatures_fail" <<'EOF'
boom
EOF
  commit_case "$repo_dir" "restore delete fail"
  run_restore_case "$repo_dir" "$fake_gh_dir" 1 '- **Restore mode:** yes' 'ERROR: required_signatures DELETE failed; status-checks/admins/reviews are set but signatures are NOT'

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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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

  repo_dir="$TMPDIR/restore-post-fail"
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
  fake_gh_dir="$TMPDIR/fake-gh-restore-post-fail"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  cat >"$fake_gh_dir/post_required_signatures_fail" <<'EOF'
boom
EOF
  commit_case "$repo_dir" "restore post fail"
  run_restore_case "$repo_dir" "$fake_gh_dir" 1 '- **Restore mode:** yes' 'ERROR: required_signatures POST failed; status-checks/admins/reviews are set but signatures are NOT'

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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  grep -Fq 'workflow-runs repos/jrnb2024/pim/actions/runs?status=success&created=%3E%3D' "$fake_gh_dir/calls.log" || fail "workflow-runs query did not use URL-encoded created filter"

  repo_dir="$TMPDIR/enable-expected-sha-paginated"
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
  fake_gh_dir="$TMPDIR/fake-gh-enable-expected-sha-paginated"
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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  cat >"$fake_gh_dir/tags-pages.json" <<'EOF'
[{"ref":"refs/tags/v0.0.1"}]
[{"ref":"refs/tags/v1.2.3"}]
EOF
  cat >"$fake_gh_dir/tag-refs/v0.0.1.json" <<'EOF'
{"object":{"sha":"0000000000000000000000000000000000000000"}}
EOF
  cat >"$fake_gh_dir/tag-refs/v1.2.3.json" <<'EOF'
{"object":{"sha":"1111111111111111111111111111111111111111"}}
EOF
  commit_case "$repo_dir" "enable expected sha paginated"
  run_enable_case "$repo_dir" "$fake_gh_dir" 0 'expected wrapper SHA validated against release tag' '' --expected-wrapper-sha 1111111111111111111111111111111111111111
  grep -Fq 'paginate tags' "$fake_gh_dir/calls.log" || fail "expected wrapper SHA tag lookup did not paginate"

  repo_dir="$TMPDIR/enable-expected-sha-cross-target"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-10T12:00:00Z — jrnb2024/recommender@main

- **Operator:** @tester
- **Restore mode:** yes
- **Restoring TO:**
```json
{"restore":"evidence"}
```
~~~
EOF
  fake_gh_dir="$TMPDIR/fake-gh-enable-expected-sha-cross-target"
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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  commit_case "$repo_dir" "enable expected sha cross-target"
  run_enable_case "$repo_dir" "$fake_gh_dir" 2 '' '--expected-wrapper-sha requires prior --restore evidence for jrnb2024/pim@main in docs/reviews/WP-SCP-020/branch-protection-log.md' --expected-wrapper-sha 1111111111111111111111111111111111111111

  repo_dir="$TMPDIR/enable-forward-json-substring-no-prior-restore"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-10T12:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
- **Restore mode:** no
- **After:**
```json
{"note":"Restoring TO: old-gate"}
```
~~~
EOF
  fake_gh_dir="$TMPDIR/fake-gh-enable-forward-json-substring-no-prior-restore"
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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  commit_case "$repo_dir" "enable forward json substring without prior restore"
  run_enable_case "$repo_dir" "$fake_gh_dir" 0 'verification passed ✓' ''

  # arbitrary SHA -> exit 2, because it is not anchored to any release tag.
  repo_dir="$TMPDIR/enable-expected-sha-arbitrary-release-tag"
  init_case_repo "$repo_dir"
  fake_gh_dir="$TMPDIR/fake-gh-enable-expected-sha-arbitrary-release-tag"
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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  commit_case "$repo_dir" "enable arbitrary release-tag sha"
  run_enable_case "$repo_dir" "$fake_gh_dir" 2 '' 'was not found in the release-tag SHA cache' --expected-wrapper-sha 2222222222222222222222222222222222222222

  repo_dir="$TMPDIR/enable-target-anchored"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-10T12:00:00Z — jrnb2024/pim@main-legacy

- **Operator:** @tester
- **Restore mode:** yes
- **Restoring TO:**
```json
{"restore":"legacy"}
```
~~~

## Invocation log entry

~~~markdown
### 2026-05-10T12:30:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  fake_gh_dir="$TMPDIR/fake-gh-enable-target-anchored"
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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  commit_case "$repo_dir" "enable target anchored"
  run_enable_case "$repo_dir" "$fake_gh_dir" 0 '' ''

  repo_dir="$TMPDIR/enable-bypass-happy-path"
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
  fake_gh_dir="$TMPDIR/fake-gh-enable-bypass-happy-path"
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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  commit_case "$repo_dir" "enable bypass happy path"
  run_enable_case "$repo_dir" "$fake_gh_dir" 0 'CAUTION: Gate 2 verification bypassed via --i-understand-no-gate-2-verification' '' --i-understand-no-gate-2-verification

  repo_dir="$TMPDIR/enable-sha-gate2-mutex"
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
  fake_gh_dir="$TMPDIR/fake-gh-enable-sha-gate2-mutex"
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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  commit_case "$repo_dir" "enable sha gate2 mutex"
  sha_mutex_stdout="$(mktemp "${TMPDIR}/sha-mutex-stdout.XXXXXX")"
  sha_mutex_stderr="$(mktemp "${TMPDIR}/sha-mutex-stderr.XXXXXX")"
  if (
    cd "$repo_dir" &&
    PATH="$fake_gh_dir:$PATH" \
    "$RESTORE_SCRIPT" \
      --repo jrnb2024/pim \
      --branch main \
      --expected-wrapper-sha 1111111111111111111111111111111111111111 \
      --i-understand-no-gate-2-verification
  ) >"$sha_mutex_stdout" 2>"$sha_mutex_stderr"; then
    sha_mutex_status=0
  else
    sha_mutex_status=$?
  fi
  if [ "$sha_mutex_status" -ne 2 ]; then
    printf 'unexpected exit code: expected 2 got %s\n' "$sha_mutex_status" >&2
    printf 'stdout:\n' >&2
    cat "$sha_mutex_stdout" >&2
    printf 'stderr:\n' >&2
    cat "$sha_mutex_stderr" >&2
    exit 1
  fi
  grep -Fq 'cannot be combined with --i-understand-no-gate-2-verification' "$sha_mutex_stderr" || fail "expected-wrapper-sha + gate-2 bypass mutex did not fire"
  if grep -Fq 'CAUTION: Gate 2 verification bypassed via --i-understand-no-gate-2-verification' "$sha_mutex_stdout"; then
    fail "gate-2 caution emitted before the expected-wrapper-sha mutex error"
  fi
  rm -f "$sha_mutex_stdout" "$sha_mutex_stderr"

  fake_gh_dir="$TMPDIR/fake-gh-workflow-guard-log"
  mkdir -p "$fake_gh_dir"
  cat >"$fake_gh_dir/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

case "$*" in
  "pr diff 99 --name-only --repo jrnb2024/standards-control-plane")
    printf '%s\n' "docs/reviews/WP-SCP-020/branch-protection-log.md"
    ;;
  *)
    printf 'unexpected gh args: %s\n' "$*" >&2
    exit 1
    ;;
esac
EOF
  chmod +x "$fake_gh_dir/gh"
  run_workflow_guard_case "$fake_gh_dir" 1 '' 'ERROR: branch-protection-log.md was modified without a corresponding cascade-slice DISPATCH-NOTE update; cascade-status declaration required.'

  fake_gh_dir="$TMPDIR/fake-gh-workflow-guard-status"
  mkdir -p "$fake_gh_dir"
  cat >"$fake_gh_dir/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

case "$*" in
  "pr diff 99 --name-only --repo jrnb2024/standards-control-plane")
    printf '%s\n' "STATUS.md"
    ;;
  *)
    printf 'unexpected gh args: %s\n' "$*" >&2
    exit 1
    ;;
esac
EOF
  chmod +x "$fake_gh_dir/gh"
  run_workflow_guard_case "$fake_gh_dir" 0 'No cascade-slice DISPATCH-NOTE found in PR diff; not a cohort cascade slice - nothing to enforce.' '' 'enforce=false'

  fake_gh_dir="$TMPDIR/fake-gh-workflow-guard-tooling"
  mkdir -p "$fake_gh_dir"
  cat >"$fake_gh_dir/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

case "$*" in
  "pr diff 99 --name-only --repo jrnb2024/standards-control-plane")
    printf '%s\n' "docs/reviews/WP-SCP-024/024B-extras/DISPATCH-NOTE.md"
    ;;
  *)
    printf 'unexpected gh args: %s\n' "$*" >&2
    exit 1
    ;;
esac
EOF
  chmod +x "$fake_gh_dir/gh"
  run_workflow_guard_case "$fake_gh_dir" 0 'Tooling slice (024B-extras); no enforcement needed.' '' 'enforce=false'

  fake_gh_dir="$TMPDIR/fake-gh-workflow-guard-mixed"
  mkdir -p "$fake_gh_dir"
  cat >"$fake_gh_dir/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

case "$*" in
  "pr diff 99 --name-only --repo jrnb2024/standards-control-plane")
    printf '%s\n' \
      "docs/reviews/WP-SCP-024/024B-extras/DISPATCH-NOTE.md" \
      "docs/reviews/WP-SCP-024/024C/DISPATCH-NOTE.md"
    ;;
  *)
    printf 'unexpected gh args: %s\n' "$*" >&2
    exit 1
    ;;
esac
EOF
  chmod +x "$fake_gh_dir/gh"
  run_workflow_guard_case "$fake_gh_dir" 0 '' '' 'dispatch_note=docs/reviews/WP-SCP-024/024C/DISPATCH-NOTE.md'

  repo_dir="$TMPDIR/enable-working-tree-prior-restore"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-10T12:30:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  fake_gh_dir="$TMPDIR/fake-gh-enable-working-tree-prior-restore"
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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
    '{"restore":"working-tree"}' \
    '```' \
  '~~~' >>"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md"
  run_enable_case "$repo_dir" "$fake_gh_dir" 2 '' 'prior --restore evidence detected' 

  repo_dir="$TMPDIR/enable-committed-history-prior-restore"
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
{"restore":"history"}
```
~~~
EOF
  commit_case "$repo_dir" "enable committed history restore evidence"
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-10T12:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "enable committed history restore deletion"
  fake_gh_dir="$TMPDIR/fake-gh-enable-committed-history-prior-restore"
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
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  run_enable_case "$repo_dir" "$fake_gh_dir" 2 '' 'prior --restore evidence detected'

  repo_dir="$TMPDIR/enable-forward-no-workflow"
  init_case_repo "$repo_dir"
  fake_gh_dir="$TMPDIR/fake-gh-enable-forward-no-workflow"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":1,"path":".github/workflows/policy-check.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-1.json" <<'EOF'
{"workflow_runs":[]}
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
  run_enable_case "$repo_dir" "$fake_gh_dir" 2 '' 'no workflow with path' 

  repo_dir="$TMPDIR/enable-forward-no-runs"
  init_case_repo "$repo_dir"
  fake_gh_dir="$TMPDIR/fake-gh-enable-forward-no-runs"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[]}
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
  run_enable_case "$repo_dir" "$fake_gh_dir" 2 '' 'no successful workflow runs'

  repo_dir="$TMPDIR/enable-forward-bypass-no-runs"
  init_case_repo "$repo_dir"
  fake_gh_dir="$TMPDIR/fake-gh-enable-forward-bypass-no-runs"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[]}
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
  run_enable_case "$repo_dir" "$fake_gh_dir" 0 'safety check bypassed via --i-understand-this-repo-has-no-prior-green-ci' '' --i-understand-this-repo-has-no-prior-green-ci

  repo_dir="$TMPDIR/enable-forward-prior-restore-from-tmp"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-10T12:30:00Z — jrnb2024/pim@main

- **Operator:** @tester
- **Restore mode:** yes
- **Restoring TO:**
```json
{"restore":"cwd"}
```
~~~
EOF
  commit_case "$repo_dir" "enable forward prior restore from tmp"
  fake_gh_dir="$TMPDIR/fake-gh-enable-forward-prior-restore-from-tmp"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"feature/pim-adopt"}]}
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
  mkdir -p "$repo_dir/scripts"
  cp "$RESTORE_SCRIPT" "$repo_dir/scripts/enable-required-check.sh"
  chmod +x "$repo_dir/scripts/enable-required-check.sh"
  run_enable_case_at_cwd /tmp "$fake_gh_dir" "jrnb2024/pim" "main" 2 '' 'incompatible with prior restore evidence' "$repo_dir/scripts/enable-required-check.sh" --i-understand-this-repo-has-no-prior-green-ci

  repo_dir="$TMPDIR/enable-regex-escape-plan"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-10T12:00:00Z — org/test.repo@main

- **Operator:** @tester
- **Restore mode:** yes
- **Restoring TO:**
```json
{"restore":"literal-dot"}
```
~~~
EOF
  fake_gh_dir="$TMPDIR/fake-gh-enable-regex-escape-plan"
  make_restore_fake_gh "$fake_gh_dir"
  cat >"$fake_gh_dir/repo.json" <<'EOF'
{"default_branch":"main"}
EOF
  cat >"$fake_gh_dir/workflows.json" <<'EOF'
{"workflows":[{"id":2,"path":".github/workflows/policy-check-wrapper.yml"}]}
EOF
  cat >"$fake_gh_dir/runs-2.json" <<'EOF'
{"workflow_runs":[{"head_branch":"feature/test-repo"}]}
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
  commit_case "$repo_dir" "enable regex escape plan"
  mkdir -p "$repo_dir/scripts"
  cp "$RESTORE_SCRIPT" "$repo_dir/scripts/enable-required-check.sh"
  chmod +x "$repo_dir/scripts/enable-required-check.sh"
  run_enable_case_at_cwd "$repo_dir" "$fake_gh_dir" "org/test-repo" "main" 0 'MODE: plan-only (no API mutation)' '' "$repo_dir/scripts/enable-required-check.sh" --plan

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
