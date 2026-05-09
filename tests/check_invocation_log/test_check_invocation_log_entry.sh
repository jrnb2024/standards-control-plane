#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SCRIPT="${REPO_ROOT}/scripts/check-invocation-log-entry.sh"

TMPDIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMPDIR"
}
trap cleanup EXIT

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
- **TF-024X-renovate-jrnb2024-base** (open): placeholder base row for repo setup.
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
  local stdout_file stderr_file status
  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  if (cd "$repo_dir" && "$SCRIPT" --diff-base base --dispatch-note DISPATCH-NOTE.md --status-md STATUS.md --branch-protection-log docs/reviews/WP-SCP-020/branch-protection-log.md) >"$stdout_file" 2>"$stderr_file"; then
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

run_pr_case() {
  local repo_dir="$1"
  local fake_gh_dir="$2"
  local expected_exit="$3"
  local expected_stdout="$4"
  local expected_stderr="$5"
  local stdout_file stderr_file status
  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  if (
    cd "$repo_dir" &&
    PATH="$fake_gh_dir:$PATH" \
    "$SCRIPT" --pr 99 --dispatch-note DISPATCH-NOTE.md --status-md STATUS.md --branch-protection-log docs/reviews/WP-SCP-020/branch-protection-log.md
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

run_restore_case() {
  local restore_json="$1"
  local fake_gh_dir="$2"
  local expected_exit="$3"
  local expected_stdout="$4"
  local expected_stderr="$5"
  shift 5
  local stdout_file stderr_file status
  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  if (
    PATH="$fake_gh_dir:$PATH" \
    "$REPO_ROOT/scripts/enable-required-check.sh" --restore "$restore_json" "$@"
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

  repo_dir="$TMPDIR/case4"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
See TF-024X-renovate-jrnb2024-pim (open): Renovate disabled on PIM; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.
EOF
  cat >"$repo_dir/docs/reviews/WP-SCP-020/branch-protection-log.md" <<'EOF'
---

## Invocation log entry

~~~markdown
### 2026-05-09T00:00:00Z — jrnb2024/pim@main

- **Operator:** @tester
~~~
EOF
  commit_case "$repo_dir" "case 4"
  run_case "$repo_dir" 0 'OK: cascade-status=onboarded-operator-bump; 3 checks passed' ''

  repo_dir="$TMPDIR/case4b"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: onboarded-operator-bump
- **Target:** jrnb2024/pim
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-pim** (open): Renovate disabled on PIM; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.
EOF
  commit_case "$repo_dir" "case 4b"
  run_case "$repo_dir" 1 '' 'ERROR: branch-protection-log.md was not modified for cascade-status=onboarded-operator-bump'

  repo_dir="$TMPDIR/case5"
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
  commit_case "$repo_dir" "case 5"
  run_case "$repo_dir" 1 '' 'ERROR: STATUS.md missing required TF-024X-renovate row for the adopter target'

  repo_dir="$TMPDIR/case6"
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
  commit_case "$repo_dir" "case 6"
  run_case "$repo_dir" 1 '' 'ERROR: STATUS.md missing required TF-024X-renovate row for the adopter target'

  repo_dir="$TMPDIR/case7"
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
  commit_case "$repo_dir" "case 7"
  run_case "$repo_dir" 1 '' 'ERROR: STATUS.md missing required TF-024X-renovate row for the adopter target'

  repo_dir="$TMPDIR/case8"
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
  commit_case "$repo_dir" "case 8"
  run_case "$repo_dir" 1 '' 'ERROR: STATUS.md missing required TF-024X-renovate row for the adopter target'

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

  repo_dir="$TMPDIR/case11"
  init_case_repo "$repo_dir"
  cat >"$repo_dir/DISPATCH-NOTE.md" <<'EOF'
cascade-status: blocked-on-adopter-conflict
- **Target:** jrnb2024/pim
See policy-check conflict discussion; awaiting rename PR.
EOF
  commit_case "$repo_dir" "case 11"
  run_case "$repo_dir" 1 '' 'ERROR: DISPATCH-NOTE missing required TF-024X-conflict reference for the adopter target'

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
  run_case "$repo_dir" 1 '' 'FAIL-CLOSED: cascade-status field absent or unrecognised; must be one of {onboarded, onboarded-operator-bump, blocked-on-adopter-conflict}'

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

  local restore_case_dir restore_json restore_degraded_json fake_restore_gh_dir
  local restore_put_capture restore_degraded_capture restore_failed_capture

  make_restore_fake_gh() {
    local fake_gh_dir="$1"
    local before_response="$2"
    local after_response="$3"
    local put_capture="$4"
    local put_exit="$5"
    local get_count_file="$6"
    local before_q after_q capture_q exit_q count_q

    mkdir -p "$fake_gh_dir"
    printf -v before_q '%q' "$before_response"
    printf -v after_q '%q' "$after_response"
    printf -v capture_q '%q' "$put_capture"
    printf -v exit_q '%q' "$put_exit"
    printf -v count_q '%q' "$get_count_file"
    : >"$get_count_file"
    printf '0' >"$get_count_file"

    cat >"$fake_gh_dir/gh" <<EOF
#!/usr/bin/env bash
set -euo pipefail

case "\$*" in
  "--version")
    printf 'gh version 2.50.0\n'
    exit 0
    ;;
  "api -X GET repos/jrnb2024/pim/branches/main/protection")
    get_count=\$(cat $count_q)
    if [ "\$get_count" -eq 0 ]; then
      cat $before_q
    else
      cat $after_q
    fi
    printf '%s' "\$((get_count + 1))" >$count_q
    ;;
  "api -X PUT repos/jrnb2024/pim/branches/main/protection"*)
    cat >$capture_q
    exit $exit_q
    ;;
  "api user --jq .login")
    printf 'tester\n'
    ;;
  *)
    printf 'unexpected gh args: %s\n' "\$*" >&2
    exit 1
    ;;
esac
EOF
    chmod +x "$fake_gh_dir/gh"
  }

  restore_case_dir="$TMPDIR/restore-case"
  mkdir -p "$restore_case_dir"

  restore_json="$restore_case_dir/restore-valid.json"
  cat >"$restore_json" <<'EOF'
{
  "repo": "jrnb2024/pim",
  "branch": "main",
  "before": {
    "url": "https://api.github.com/repos/jrnb2024/pim/branches/main/protection",
    "_links": {
      "html": "https://github.com/jrnb2024/pim"
    },
    "required_status_checks": {
      "url": "https://api.github.com/repos/jrnb2024/pim/branches/main/protection/required_status_checks",
      "strict": true,
      "contexts": [
        "policy-check / scp/policy-check"
      ],
      "checks": [
        {
          "context": "policy-check / scp/policy-check",
          "state": "success",
          "url": "https://api.github.com/repos/jrnb2024/pim/check-runs/1"
        }
      ]
    },
    "enforce_admins": {
      "url": "https://api.github.com/repos/jrnb2024/pim/branches/main/protection/enforce_admins",
      "enabled": true
    },
    "required_pull_request_reviews": {
      "url": "https://api.github.com/repos/jrnb2024/pim/branches/main/protection/required_pull_request_reviews",
      "_links": {
        "html": "https://github.com/jrnb2024/pim/pull/1"
      },
      "dismiss_stale_reviews": true,
      "dismissal_restrictions": {
        "url": "https://api.github.com/repos/jrnb2024/pim/branches/main/protection/required_pull_request_reviews/dismissal_restrictions",
        "_links": {
          "html": "https://github.com/jrnb2024/pim/pulls/1"
        },
        "users": [
          {
            "login": "alice",
            "url": "https://api.github.com/users/alice"
          }
        ],
        "teams": [],
        "apps": []
      }
    },
    "restrictions": {
      "url": "https://api.github.com/repos/jrnb2024/pim/branches/main/protection/restrictions",
      "_links": {
        "html": "https://github.com/jrnb2024/pim"
      },
      "users": [
        {
          "login": "alice",
          "url": "https://api.github.com/users/alice"
        }
      ],
      "teams": [],
      "apps": []
    }
  }
}
EOF

  restore_put_capture="$restore_case_dir/restore-put-body.json"
  fake_restore_gh_dir="$TMPDIR/fake-gh-restore-valid"
  make_restore_fake_gh "$fake_restore_gh_dir" "$restore_json" "$restore_json" "$restore_put_capture" 0 "$restore_case_dir/get-count-valid"
  run_restore_case "$restore_json" "$fake_restore_gh_dir" 0 '## Invocation log entry' '[020G] restoring branch protection for jrnb2024/pim@main'
  python3 - "$restore_put_capture" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
expected = {
    "required_status_checks": {
        "strict": True,
        "contexts": ["policy-check / scp/policy-check"],
    },
    "enforce_admins": True,
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": True,
        "dismissal_restrictions": {
            "users": [{"login": "alice"}],
            "teams": [],
            "apps": [],
        },
    },
    "restrictions": {
        "users": [{"login": "alice"}],
        "teams": [],
        "apps": [],
    },
}
if payload != expected:
    raise SystemExit(f"unexpected restore PUT payload: {payload!r}")
PY

  restore_degraded_json="$restore_case_dir/restore-degraded.json"
  cat >"$restore_degraded_json" <<'EOF'
{
  "repo": "jrnb2024/pim",
  "branch": "main",
  "before": {
    "required_status_checks": {
      "strict": true,
      "contexts": []
    },
    "enforce_admins": {
      "enabled": false
    },
    "required_pull_request_reviews": null,
    "restrictions": null
  }
}
EOF

  restore_degraded_capture="$restore_case_dir/restore-degraded-put-body.json"
  fake_restore_gh_dir="$TMPDIR/fake-gh-restore-degraded"
  make_restore_fake_gh "$fake_restore_gh_dir" "$restore_degraded_json" "$restore_degraded_json" "$restore_degraded_capture" 0 "$restore_case_dir/get-count-degraded"
  run_restore_case "$restore_degraded_json" "$fake_restore_gh_dir" 2 '' 'restore pre-state would remove admin enforcement'
  run_restore_case "$restore_degraded_json" "$fake_restore_gh_dir" 0 '## Invocation log entry' '[020G] restoring branch protection for jrnb2024/pim@main' --i-understand-restore-removes-admin-enforcement --i-understand-restore-removes-required-checks
  python3 - "$restore_degraded_capture" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
expected = {
    "required_status_checks": {
        "strict": True,
        "contexts": [],
    },
    "enforce_admins": False,
    "required_pull_request_reviews": None,
    "restrictions": None,
}
if payload != expected:
    raise SystemExit(f"unexpected degraded restore PUT payload: {payload!r}")
PY

  restore_failed_capture="$restore_case_dir/restore-failed-put-body.json"
  fake_restore_gh_dir="$TMPDIR/fake-gh-restore-failed"
  make_restore_fake_gh "$fake_restore_gh_dir" "$restore_json" "$restore_json" "$restore_failed_capture" 1 "$restore_case_dir/get-count-failed"
  run_restore_case "$restore_json" "$fake_restore_gh_dir" 1 '## Invocation log entry' '[020G] restoring branch protection for jrnb2024/pim@main'
  python3 - "$restore_failed_capture" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
expected = {
    "required_status_checks": {
        "strict": True,
        "contexts": ["policy-check / scp/policy-check"],
    },
    "enforce_admins": True,
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": True,
        "dismissal_restrictions": {
            "users": [{"login": "alice"}],
            "teams": [],
            "apps": [],
        },
    },
    "restrictions": {
        "users": [{"login": "alice"}],
        "teams": [],
        "apps": [],
    },
}
if payload != expected:
    raise SystemExit(f"unexpected failed restore PUT payload: {payload!r}")
PY

  local restore_path_traversal_json
  restore_path_traversal_json="$restore_case_dir/restore-path-traversal.json"
  cat >"$restore_path_traversal_json" <<'EOF'
{
  "repo": "jrnb2024/../pim",
  "branch": "main",
  "before": {
    "required_status_checks": {
      "strict": true,
      "contexts": [
        "policy-check / scp/policy-check"
      ]
    },
    "enforce_admins": {
      "enabled": true
    },
    "required_pull_request_reviews": null,
    "restrictions": null
  }
}
EOF
  run_restore_case "$restore_path_traversal_json" "$fake_restore_gh_dir" 2 '' "error: --restore repo 'jrnb2024/../pim' contains path-traversal sequence"
}

main
