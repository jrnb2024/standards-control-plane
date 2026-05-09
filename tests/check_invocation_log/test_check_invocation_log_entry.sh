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
  local stdout_file stderr_file status
  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  if (cd "$repo_dir" && "$SCRIPT" --diff-base base --dispatch-note DISPATCH-NOTE.md --status-md STATUS.md --branch-protection-log "$branch_protection_log") >"$stdout_file" 2>"$stderr_file"; then
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
  local branch_protection_log="${6:-docs/reviews/WP-SCP-020/branch-protection-log.md}"
  local stdout_file stderr_file status
  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  if (
    cd "$repo_dir" &&
    PATH="$fake_gh_dir:$PATH" \
    "$SCRIPT" --pr 99 --dispatch-note DISPATCH-NOTE.md --status-md STATUS.md --branch-protection-log "$branch_protection_log"
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

run_enable_case() {
  local fake_gh_dir="$1"
  local expected_exit="$2"
  local expected_stdout="$3"
  local expected_stderr="$4"
  shift 4
  local stdout_file stderr_file status
  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  if (
    PATH="$fake_gh_dir:$PATH" \
    "$REPO_ROOT/scripts/enable-required-check.sh" "$@"
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
  run_case "$repo_dir" 1 '' 'FAIL-CLOSED: cascade-status field absent or unrecognised; must be one of {onboarded, onboarded-operator-bump, blocked-on-adopter-conflict, not applicable}'

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
- **Target:** jrnb2024/pim
Worked example: cascade-status: onboarded
Worked example: cascade-status: blocked-on-adopter-conflict
See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.
EOF
  cat >"$repo_dir/STATUS.md" <<'EOF'
- **TF-024X-renovate-jrnb2024-pim** (open): Renovate disabled on PIM; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.
EOF
  commit_case "$repo_dir" "case 15b"
  run_case "$repo_dir" 0 'OK: DISPATCH-NOTE declares cascade-status: not applicable; not a cohort cascade slice — nothing to enforce' ''

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

  repo_dir="$TMPDIR/case19"
  init_case_repo "$repo_dir"
  outsider_log="$(mktemp "${TMPDIR}/outside.XXXXXX")"
  run_case "$repo_dir" 2 '' 'ERROR: --branch-protection-log must resolve inside repository root' "$outsider_log"
}

main
