#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SCRIPT="${REPO_ROOT}/scripts/scaffold-downstream.sh"
SCP_SHA="41a529908ef5355b82ca924ef0502fa5ec2fcc11"
SCP_SHA_POST_V1_2_0="$(git -C "${REPO_ROOT}" rev-parse main 2>/dev/null || git -C "${REPO_ROOT}" rev-parse HEAD)"

# Output directories are created under $TMPDIR and explicitly removed
# after each case; the trap below is the final backstop. Keep the temp
# root inside the repo workspace so the script's system-path guard
# does not reject it on macOS.
TMPDIR="$(mktemp -d "${REPO_ROOT}/tmp.scaffold.XXXXXX")"
trap 'rm -rf "$TMPDIR"' EXIT INT TERM

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

run_expect_exit() {
  local expected="$1"
  shift
  local stdout_file stderr_file status
  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  if "$@" >"$stdout_file" 2>"$stderr_file"; then
    status=0
  else
    status=$?
  fi
  if [ "$status" -ne "$expected" ]; then
    printf 'unexpected exit code: expected %s got %s\n' "$expected" "$status" >&2
    printf 'stdout:\n' >&2
    cat "$stdout_file" >&2
    printf 'stderr:\n' >&2
    cat "$stderr_file" >&2
    rm -f "$stdout_file" "$stderr_file"
    exit 1
  fi
  rm -f "$stdout_file" "$stderr_file"
}

validate_manifest() {
  local manifest="$1"
  local outdir="$2"
  local expected_sha="$3"
  local expected_adopter_repo="$4"
  local expected_default_branch="$5"
  local expected_scorecard_emit="$6"
  python3 - "$manifest" "$outdir" "$expected_sha" "$expected_adopter_repo" "$expected_default_branch" "$expected_scorecard_emit" <<'PY'
import hashlib
import json
import pathlib
import sys

manifest_path = pathlib.Path(sys.argv[1])
outdir = pathlib.Path(sys.argv[2])
payload = json.loads(manifest_path.read_text(encoding="utf-8"))

required_keys = {"emitted_at", "adopter_repo", "default_branch", "scp_sha", "scorecard_emit", "files"}
if set(payload) != required_keys:
    raise SystemExit(f"unexpected manifest keys: {sorted(payload)}")
if payload["adopter_repo"] != sys.argv[4]:
    raise SystemExit("unexpected adopter_repo")
if payload["default_branch"] != sys.argv[5]:
    raise SystemExit("unexpected default_branch")
if payload["scp_sha"] != sys.argv[3]:
    raise SystemExit("unexpected scp_sha")
if payload["scorecard_emit"] != (sys.argv[6] == "true"):
    raise SystemExit("unexpected scorecard_emit")
if not isinstance(payload["emitted_at"], str) or not payload["emitted_at"]:
    raise SystemExit("missing emitted_at")
if len(payload["files"]) != 3:
    raise SystemExit("manifest.files should list the 3 non-manifest emitted files; MANIFEST.json intentionally excludes itself from its own sha256 entries to avoid circular dependency")

for entry in payload["files"]:
    path = outdir / entry["path"]
    if not path.exists():
        raise SystemExit(f"missing emitted file: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != entry["sha256"]:
        raise SystemExit(f"sha mismatch for {entry['path']}")
    if len(entry["sha256"]) != 64:
        raise SystemExit(f"bad sha length for {entry['path']}")
PY
}

assert_wrapper_contract() {
  local wrapper="$1"
  grep -Fq 'github.event.pull_request.head.repo.full_name == github.event.pull_request.base.repo.full_name' "$wrapper" \
    || fail "wrapper missing fork-PR refusal if: clause"
  grep -Fq 'contents: read' "$wrapper" \
    || fail "wrapper missing least-privilege contents: read"
  grep -Fq 'statuses: write' "$wrapper" \
    || fail "wrapper missing statuses: write"
  grep -Fq '# renovate: datasource=github-tags depName=jrnb2024/standards-control-plane-' "$wrapper" \
    || fail "wrapper missing Renovate auto-bump marker"
  ! grep -qF 'id-token:' "$wrapper" \
    || fail "wrapper unexpectedly requests id-token at workflow level"
  ! grep -qF 'attestations:' "$wrapper" \
    || fail "wrapper unexpectedly requests attestations at workflow level"
}

make_output_dir() {
  mktemp -d "${TMPDIR}/out.XXXXXX"
}

main() {
  local outdir
  outdir="$(make_output_dir)"
  run_expect_exit 0 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit false \
    --output-dir "$outdir"

  [ -f "$outdir/.github/workflows/policy-check-wrapper.yml" ] || fail "missing emitted wrapper"
  [ -f "$outdir/.github/CODEOWNERS-snippet.txt" ] || fail "missing CODEOWNERS snippet"
  [ -f "$outdir/CASCADE-PR-BODY.md" ] || fail "missing PR body"
  [ -f "$outdir/MANIFEST.json" ] || fail "missing manifest"

  grep -Fq 'branches: [main]' "$outdir/.github/workflows/policy-check-wrapper.yml" || fail "wrapper missing substituted default branch"
  grep -Fq "$SCP_SHA" "$outdir/.github/workflows/policy-check-wrapper.yml" || fail "wrapper missing substituted SHA"
  grep -Fq 'scorecard-emit: false' "$outdir/.github/workflows/policy-check-wrapper.yml" || fail "wrapper missing scorecard-emit false"
  assert_wrapper_contract "$outdir/.github/workflows/policy-check-wrapper.yml"
  grep -Fq '@<adopter-CODEOWNERS-account>' "$outdir/.github/CODEOWNERS-snippet.txt" || fail "CODEOWNERS snippet placeholder missing"
  grep -Fq 'T-024-09 expects roughly 2-5 minutes on ubuntu-24.04' "$outdir/CASCADE-PR-BODY.md" || fail "PR body missing cost paragraph"
  # pyyaml is optional in some environments; skip the lint check cleanly
  # instead of aborting under set -euo pipefail when the import is absent.
  python3 -c 'import yaml' 2>/dev/null || { echo 'SKIP: pyyaml not installed; YAML validation skipped'; return 0; }
  python3 - "$outdir/.github/workflows/policy-check-wrapper.yml" <<'PY'
import pathlib
import sys

import yaml

yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
PY
  validate_manifest "$outdir/MANIFEST.json" "$outdir" "$SCP_SHA" "jrnb2024/test-adopter" "main" "false"
  rm -rf "$outdir"

  local post_v120_outdir post_v120_stdout post_v120_stderr post_v120_status
  post_v120_outdir="$(make_output_dir)"
  post_v120_stdout="$(mktemp "${TMPDIR}/stdout.XXXXXX")"
  post_v120_stderr="$(mktemp "${TMPDIR}/stderr.XXXXXX")"
  if env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha "$SCP_SHA_POST_V1_2_0" \
    --scorecard-emit false \
    --output-dir "$post_v120_outdir" >"$post_v120_stdout" 2>"$post_v120_stderr"; then
    post_v120_status=0
  else
    post_v120_status=$?
  fi
  if [ "$post_v120_status" -ne 0 ]; then
    printf 'unexpected exit code: expected 0 got %s\n' "$post_v120_status" >&2
    printf 'stdout:\n' >&2
    cat "$post_v120_stdout" >&2
    printf 'stderr:\n' >&2
    cat "$post_v120_stderr" >&2
    exit 1
  fi
  if git -C "${REPO_ROOT}" rev-parse v1.2.0 >/dev/null 2>&1; then
    grep -Fq 'post-v1.2.0' "$post_v120_stderr" || fail "post-v1.2.0 SHA did not warn"
    grep -Fq 'TF-023E-002' "$post_v120_stderr" || fail "post-v1.2.0 warning missing TF-023E-002 reference"
    grep -Fq 'RECOMMENDED: use --scp-sha 41a529908ef5355b82ca924ef0502fa5ec2fcc11 (v1.0.0)' "$post_v120_stderr" || fail "post-v1.2.0 warning missing recommendation"
    assert_wrapper_contract "$post_v120_outdir/.github/workflows/policy-check-wrapper.yml"
    validate_manifest "$post_v120_outdir/MANIFEST.json" "$post_v120_outdir" "$SCP_SHA_POST_V1_2_0" "jrnb2024/test-adopter" "main" "false"
  else
    printf 'SKIP: v1.2.0 tag not present in local repo; skipping TF-023E-002 warning test (shallow-clone or fresh clone)\n' >&2
  fi
  rm -f "$post_v120_stdout" "$post_v120_stderr"
  rm -rf "$post_v120_outdir"

  local cutover_repo cutover_sha missing_cutover_outdir missing_cutover_stdout missing_cutover_stderr missing_cutover_status
  cutover_repo="$(mktemp -d "${TMPDIR}/cutover-repo.XXXXXX")"
  git -C "$cutover_repo" init -q -b main
  git -C "$cutover_repo" config user.name "Codex Test"
  git -C "$cutover_repo" config user.email "codex@example.com"
  mkdir -p "$cutover_repo/templates"
  cp "$REPO_ROOT/templates/adopter-wrapper.yml.tmpl" "$cutover_repo/templates/adopter-wrapper.yml.tmpl"
  printf 'bootstrap\n' >"$cutover_repo/README.md"
  git -C "$cutover_repo" add README.md
  git -C "$cutover_repo" commit -qm "bootstrap"
  cutover_sha="$(git -C "$cutover_repo" rev-parse HEAD)"

  missing_cutover_outdir="$(make_output_dir)"
  missing_cutover_stdout="$(mktemp "${TMPDIR}/stdout.XXXXXX")"
  missing_cutover_stderr="$(mktemp "${TMPDIR}/stderr.XXXXXX")"
  if env -i PATH="$PATH" HOME="$HOME" SCP_REPO_ROOT="$cutover_repo" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha "$cutover_sha" \
    --scorecard-emit false \
    --output-dir "$missing_cutover_outdir" >"$missing_cutover_stdout" 2>"$missing_cutover_stderr"; then
    missing_cutover_status=0
  else
    missing_cutover_status=$?
  fi
  if [ "$missing_cutover_status" -ne 0 ]; then
    printf 'unexpected exit code: expected 0 got %s\n' "$missing_cutover_status" >&2
    printf 'stdout:\n' >&2
    cat "$missing_cutover_stdout" >&2
    printf 'stderr:\n' >&2
    cat "$missing_cutover_stderr" >&2
    exit 1
  fi
  if grep -Fq 'fatal:' "$missing_cutover_stderr"; then
    fail "missing-cutover repo triggered fatal stderr"
  fi
  grep -Fq 'v1.2.0 tag not present in local clone' "$missing_cutover_stderr" || fail "missing-cutover repo did not emit the tag-absent warning"
  assert_wrapper_contract "$missing_cutover_outdir/.github/workflows/policy-check-wrapper.yml"
  validate_manifest "$missing_cutover_outdir/MANIFEST.json" "$missing_cutover_outdir" "$cutover_sha" "jrnb2024/test-adopter" "main" "false"
  rm -f "$missing_cutover_stdout" "$missing_cutover_stderr"
  rm -rf "$missing_cutover_outdir" "$cutover_repo"

  local main_head_sha non_head_sha
  main_head_sha="$(git -C "${REPO_ROOT}" rev-parse main 2>/dev/null || true)"
  non_head_sha="$SCP_SHA_POST_V1_2_0"
  if [ -z "$non_head_sha" ] || [ "$non_head_sha" = "$main_head_sha" ]; then
    non_head_sha="$(git -C "${REPO_ROOT}" rev-parse HEAD^ 2>/dev/null || git -C "${REPO_ROOT}" rev-list --max-count=2 HEAD | tail -n 1)"
  fi
  [ -n "$non_head_sha" ] || fail "could not resolve a non-HEAD SHA"

  local outdir_non_head
  outdir_non_head="$(make_output_dir)"
  local non_head_stdout non_head_stderr non_head_status
  non_head_stdout="$(mktemp "${TMPDIR}/stdout.XXXXXX")"
  non_head_stderr="$(mktemp "${TMPDIR}/stderr.XXXXXX")"
  if env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha "$non_head_sha" \
    --scorecard-emit false \
    --output-dir "$outdir_non_head" >"$non_head_stdout" 2>"$non_head_stderr"; then
    non_head_status=0
  else
    non_head_status=$?
  fi
  if [ "$non_head_status" -ne 0 ]; then
    printf 'unexpected exit code: expected 0 got %s\n' "$non_head_status" >&2
    printf 'stdout:\n' >&2
    cat "$non_head_stdout" >&2
    printf 'stderr:\n' >&2
    cat "$non_head_stderr" >&2
    rm -f "$non_head_stdout" "$non_head_stderr"
    exit 1
  fi
  grep -Fq 'is not current SCP main HEAD' "$non_head_stderr" || fail "non-HEAD SHA did not warn"
  rm -f "$non_head_stdout" "$non_head_stderr"
  [ -f "$outdir_non_head/.github/workflows/policy-check-wrapper.yml" ] || fail "missing emitted wrapper for non-HEAD SHA"
  [ -f "$outdir_non_head/.github/CODEOWNERS-snippet.txt" ] || fail "missing CODEOWNERS snippet for non-HEAD SHA"
  [ -f "$outdir_non_head/CASCADE-PR-BODY.md" ] || fail "missing PR body for non-HEAD SHA"
  [ -f "$outdir_non_head/MANIFEST.json" ] || fail "missing manifest for non-HEAD SHA"
  assert_wrapper_contract "$outdir_non_head/.github/workflows/policy-check-wrapper.yml"
  validate_manifest "$outdir_non_head/MANIFEST.json" "$outdir_non_head" "$non_head_sha" "jrnb2024/test-adopter" "main" "false"
  rm -rf "$outdir_non_head"

  local outdir_master
  outdir_master="$(make_output_dir)"
  run_expect_exit 0 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch master \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit true \
    --output-dir "$outdir_master"
  grep -Fq 'branches: [master]' "$outdir_master/.github/workflows/policy-check-wrapper.yml" || fail "master variant missing substituted branch"
  grep -Fq 'scorecard-emit: true' "$outdir_master/.github/workflows/policy-check-wrapper.yml" || fail "true variant missing scorecard-emit"
  assert_wrapper_contract "$outdir_master/.github/workflows/policy-check-wrapper.yml"
  validate_manifest "$outdir_master/MANIFEST.json" "$outdir_master" "$SCP_SHA" "jrnb2024/test-adopter" "master" "true"
  rm -rf "$outdir_master"

  local outdir_develop
  outdir_develop="$(make_output_dir)"
  run_expect_exit 0 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch develop \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit false \
    --output-dir "$outdir_develop"
  grep -Fq 'branches: [develop]' "$outdir_develop/.github/workflows/policy-check-wrapper.yml" || fail "develop variant missing substituted branch"
  assert_wrapper_contract "$outdir_develop/.github/workflows/policy-check-wrapper.yml"
  validate_manifest "$outdir_develop/MANIFEST.json" "$outdir_develop" "$SCP_SHA" "jrnb2024/test-adopter" "develop" "false"
  rm -rf "$outdir_develop"

  local error_outdir
  error_outdir="$(make_output_dir)"

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    CI=true \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit false \
    --output-dir "$error_outdir"

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    GITHUB_ACTIONS=true \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit false \
    --output-dir "$error_outdir"

  tmp_deny_base="$(mktemp -d "${TMPDIR}/tr.XXXXXX")"
  tmp_deny_dir="${tmp_deny_base}/../../etc"
  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit false \
    --output-dir "$tmp_deny_dir"
  rm -rf "$tmp_deny_base"

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit false \
    --output-dir /tmp

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit false \
    --output-dir /var/tmp

  if [[ "$(uname)" == "Darwin" ]]; then
    if tmp_private_var_deny="$(mktemp -d /private/var/tmp/scp-denylist-test.XXXXXX 2>/dev/null)"; then
      local deny_stdout deny_stderr deny_status
      deny_stdout="$(mktemp "${TMPDIR}/stdout.XXXXXX")"
      deny_stderr="$(mktemp "${TMPDIR}/stderr.XXXXXX")"
      if env -i PATH="$PATH" HOME="$HOME" \
        "$SCRIPT" \
        --adopter-repo jrnb2024/test-adopter \
        --default-branch main \
        --scp-sha "$SCP_SHA" \
        --scorecard-emit false \
        --output-dir "$tmp_private_var_deny" >"$deny_stdout" 2>"$deny_stderr"; then
        deny_status=0
      else
        deny_status=$?
      fi
      if [ "$deny_status" -ne 1 ]; then
        printf 'unexpected exit code: expected 1 got %s\n' "$deny_status" >&2
        printf 'stdout:\n' >&2
        cat "$deny_stdout" >&2
        printf 'stderr:\n' >&2
        cat "$deny_stderr" >&2
        exit 1
      fi
      grep -Eq 'system path|denylist' "$deny_stderr" || fail "Darwin denylist case did not mention denylist/system path"
      rm -f "$deny_stdout" "$deny_stderr"
      rm -rf "$tmp_private_var_deny"
    fi
  fi

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo invalid \
    --default-branch main \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit false \
    --output-dir "$error_outdir"

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch foobar \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit false \
    --output-dir "$error_outdir"

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha 0123 \
    --scorecard-emit false \
    --output-dir "$error_outdir"

  run_expect_exit 2 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha 0000000000000000000000000000000000000000 \
    --scorecard-emit false \
    --output-dir "$error_outdir"

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit yes \
    --output-dir "$error_outdir"

  rm -rf "$error_outdir"
}

main
