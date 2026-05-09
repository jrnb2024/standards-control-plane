#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SCRIPT="${REPO_ROOT}/scripts/scaffold-downstream.sh"
SCP_SHA="$(git -C "${REPO_ROOT}" rev-parse HEAD)"

TMPDIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMPDIR"
}
trap cleanup EXIT

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
  python3 - "$manifest" "$outdir" "$expected_sha" <<'PY'
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
if payload["adopter_repo"] != "jrnb2024/test-adopter":
    raise SystemExit("unexpected adopter_repo")
if payload["default_branch"] != "main":
    raise SystemExit("unexpected default_branch")
if payload["scp_sha"] != sys.argv[3]:
    raise SystemExit("unexpected scp_sha")
if payload["scorecard_emit"] is not False:
    raise SystemExit("unexpected scorecard_emit")
if not isinstance(payload["emitted_at"], str) or not payload["emitted_at"]:
    raise SystemExit("missing emitted_at")
if len(payload["files"]) != 3:
    raise SystemExit("manifest.files should list 3 of 4 emitted files (MANIFEST.json does not hash itself)")

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
  grep -Fq '@<adopter-CODEOWNERS-account>' "$outdir/.github/CODEOWNERS-snippet.txt" || fail "CODEOWNERS snippet placeholder missing"
  grep -Fq 'T-024-09 expects roughly 2-5 minutes on ubuntu-24.04' "$outdir/CASCADE-PR-BODY.md" || fail "PR body missing cost paragraph"
  python3 - "$outdir/.github/workflows/policy-check-wrapper.yml" <<'PY'
import pathlib
import sys

import yaml

yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
PY
  validate_manifest "$outdir/MANIFEST.json" "$outdir" "$SCP_SHA"

  local non_head_sha
  non_head_sha="$(git -C "${REPO_ROOT}" rev-parse HEAD^ 2>/dev/null || git -C "${REPO_ROOT}" rev-list --max-count=2 HEAD | tail -n 1)"
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
  validate_manifest "$outdir_non_head/MANIFEST.json" "$outdir_non_head" "$non_head_sha"

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

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    CI=true \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit false \
    --output-dir "$outdir"

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    GITHUB_ACTIONS=true \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit false \
    --output-dir "$outdir"

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

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo invalid \
    --default-branch main \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit false \
    --output-dir "$outdir"

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch foobar \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit false \
    --output-dir "$outdir"

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha 0123 \
    --scorecard-emit false \
    --output-dir "$outdir"

  run_expect_exit 2 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha 0000000000000000000000000000000000000000 \
    --scorecard-emit false \
    --output-dir "$outdir"

  run_expect_exit 1 env -i PATH="$PATH" HOME="$HOME" \
    "$SCRIPT" \
    --adopter-repo jrnb2024/test-adopter \
    --default-branch main \
    --scp-sha "$SCP_SHA" \
    --scorecard-emit yes \
    --output-dir "$outdir"
}

main
