#!/usr/bin/env bash
# scp-pre-push-verify — local pre-push parity wrapper for SCP-R rule
# author workflow.
#
# Mirrors the three CI gates from `.github/workflows/policy-check.yml`
# that exercise `policies/SCP-R-*.rego` correctness:
#
#   1. Lint policies with Regal      (CI lines 545-566)
#   2. Check policy formatting       (`opa fmt --fail`; CI lines 569-577)
#   3. Enforce per-rule OPA coverage (`opa test --coverage --threshold 90
#                                     --fail-on-empty -v`; CI lines 579-620)
#
# Closes:
#   - TF-020P-005 (combine pre-push verification into one wrapper)
#   - TF-020P-003 (Regal lint local-dev gap surfaced in slice 020P fr-2)
#   - TF-020P-004 (`opa test --coverage --threshold 90` local-dev gap
#                  surfaced in slice 020P fr-3)
#
# Scope (what this DOES NOT cover):
#   - Workflow-selftest harness (`.github/workflows/workflow-selftest.yml`)
#   - Conflict-gate Python evaluator (`tests/conflict_gate/test_conflict_gate.py`)
#   - Supply-chain SHA verification (`scripts/scp-policy-check`)
#   - Freshness-warning, release-gate dry-run, canary replay
#
# CI is still the authoritative gate. This wrapper is a CI-roundtrip
# saver for rule-author work, not a federation-conformance gate.
#
# Usage:
#   scripts/scp-pre-push-verify.sh
#
# Reference: docs/adoption/ADOPT-001-project-onboarding.md §12.7.9.1;
#            docs/reviews/WP-SCP-022/dispatches/020p-005-pre-push-verify/.

set -uo pipefail

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

emit_info()  { printf '%s\n' "$*" >&2; }
emit_warn()  { printf 'scp-pre-push-verify: WARNING: %s\n' "$*" >&2; }
emit_error() { printf 'scp-pre-push-verify: ERROR: %s\n' "$*" >&2; }

# Resolve repo root (works from any subdirectory).
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "${REPO_ROOT}" ]; then
  emit_error "not inside a git repository (git rev-parse --show-toplevel failed)"
  exit 2
fi

POLICIES_DIR="${REPO_ROOT}/policies"
TOOL_VERSIONS_FILE="${REPO_ROOT}/scripts/.tool-versions"

# ---------------------------------------------------------------------------
# Tool preflight
# ---------------------------------------------------------------------------

require_cmd() {
  local cmd="$1"
  local install_hint="$2"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    emit_error "required command not found: ${cmd}"
    emit_error "install hint: ${install_hint}"
    exit 2
  fi
}

require_cmd opa   "brew install opa  # or download from https://github.com/open-policy-agent/opa/releases"
require_cmd regal "brew install styrainc/packages/regal  # or download from https://github.com/StyraInc/regal/releases"

# ---------------------------------------------------------------------------
# .tool-versions parity warning (non-fatal)
# ---------------------------------------------------------------------------

# Read pinned tool version from scripts/.tool-versions for the named tool.
# Empty string if unpinned or file missing.
read_pinned_version() {
  local tool="$1"
  if [ ! -f "${TOOL_VERSIONS_FILE}" ]; then
    return
  fi
  awk -v tool="${tool}" '$1 == tool { print $2; exit }' "${TOOL_VERSIONS_FILE}"
}

# Read installed tool version. Best-effort: each tool has its own format.
# Both parsers split on the colon ONLY and then strip all whitespace from
# the captured field — robust to single-space, multi-space, or tab padding
# in any future opa/regal `version` output (closes 020P-005 R1 COR-nit-001).
read_installed_opa_version() {
  # `opa version` emits e.g. "Version: 1.15.2" on the first line.
  opa version 2>/dev/null | awk -F':' '/^Version:/ { gsub(/[[:space:]]/, "", $2); print $2; exit }'
}

read_installed_regal_version() {
  # `regal version` emits e.g. "Version:     0.40.0" (whitespace-padded).
  regal version 2>/dev/null | awk -F':' '/^Version:/ { gsub(/[[:space:]]/, "", $2); print $2; exit }'
}

check_version_parity() {
  local tool="$1"
  local pinned="$2"
  local installed="$3"
  if [ -z "${pinned}" ]; then
    return
  fi
  if [ -z "${installed}" ]; then
    emit_warn "${tool}: could not detect installed version; skipping parity check"
    return
  fi
  if [ "${pinned}" != "${installed}" ]; then
    emit_warn "${tool}: local ${installed} differs from CI-pinned ${pinned} (scripts/.tool-versions) — wrapper results may not match CI; install the pinned version or treat wrapper output as advisory only"
  fi
}

PINNED_OPA="$(read_pinned_version opa)"
PINNED_REGAL="$(read_pinned_version regal)"
INSTALLED_OPA="$(read_installed_opa_version)"
INSTALLED_REGAL="$(read_installed_regal_version)"

check_version_parity opa   "${PINNED_OPA}"   "${INSTALLED_OPA}"
check_version_parity regal "${PINNED_REGAL}" "${INSTALLED_REGAL}"

# ---------------------------------------------------------------------------
# No policies → nothing to verify
# ---------------------------------------------------------------------------

if ! find "${POLICIES_DIR}" -type f -name '*.rego' -print -quit 2>/dev/null | grep -q .; then
  emit_info "scp-pre-push-verify: no .rego files under ${POLICIES_DIR}; nothing to verify"
  exit 0
fi

# ---------------------------------------------------------------------------
# Failure collection
# ---------------------------------------------------------------------------

FAILED_GATES=()

mark_failed() {
  FAILED_GATES+=("$1")
}

# ---------------------------------------------------------------------------
# Gate 1: Regal lint (parity with CI "Lint policies with Regal" step)
# ---------------------------------------------------------------------------

emit_info ""
emit_info "=== [1/3] Regal lint ==="
if ! regal lint \
      --disable directory-package-mismatch \
      --disable no-defined-entrypoint \
      --disable with-outside-test-context \
      --disable unconditional-assignment \
      --disable line-length \
      --disable superfluous-object-get \
      --disable non-loop-expression \
      --disable external-reference \
      --disable unresolved-reference \
      --disable defer-assignment \
      --disable opa-fmt \
      --disable messy-rule \
      "${POLICIES_DIR}"; then
  mark_failed "Regal lint"
fi

# ---------------------------------------------------------------------------
# Gate 2: opa fmt --fail (parity with CI "Check policy formatting" step)
# ---------------------------------------------------------------------------

emit_info ""
emit_info "=== [2/3] opa fmt --fail ==="
fmt_failed=0
while IFS= read -r -d '' rego_file; do
  if ! opa fmt --fail "${rego_file}"; then
    fmt_failed=1
  fi
done < <(find "${POLICIES_DIR}" -type f -name '*.rego' -print0)
if [ "${fmt_failed}" -ne 0 ]; then
  mark_failed "opa fmt --fail"
fi

# ---------------------------------------------------------------------------
# Gate 3: per-rule opa test --coverage --threshold 90 --fail-on-empty -v
#         (parity with CI "Enforce per-rule OPA coverage" step)
# ---------------------------------------------------------------------------

emit_info ""
emit_info "=== [3/3] opa test (per-rule, --coverage --threshold 90) ==="
COMMON_FILE="${POLICIES_DIR}/scp_common.rego"
TEST_ROOT="${POLICIES_DIR}/tests"

test_failed=0
rule_count=0

if [ ! -f "${COMMON_FILE}" ]; then
  emit_error "missing ${COMMON_FILE} — required by every SCP-R-NNN rule (CI gate would fail)"
  mark_failed "opa test (missing scp_common.rego)"
else
  for rule_file in "${POLICIES_DIR}"/SCP-R-*.rego; do
    [ -e "${rule_file}" ] || continue
    rule_count=$((rule_count + 1))

    rule_base="$(basename "${rule_file}" .rego)"
    test_name="$(printf '%s' "${rule_base}" | tr '[:upper:]-' '[:lower:]_')_test.rego"
    test_file="${TEST_ROOT}/${test_name}"

    if [ ! -f "${test_file}" ]; then
      emit_error "missing OPA test file for ${rule_base}: expected ${test_file}"
      test_failed=1
      continue
    fi

    emit_info "--- ${rule_base} ---"
    if ! opa test \
          "${rule_file}" \
          "${COMMON_FILE}" \
          "${test_file}" \
          --coverage \
          --threshold 90 \
          --fail-on-empty \
          -v; then
      test_failed=1
    fi
  done

  if [ "${rule_count}" -eq 0 ]; then
    emit_info "no policies/SCP-R-*.rego rules found; skipping per-rule coverage"
  fi
fi

if [ "${test_failed}" -ne 0 ]; then
  mark_failed "opa test --coverage --threshold 90"
fi

# ---------------------------------------------------------------------------
# Summary banner
# ---------------------------------------------------------------------------

emit_info ""
if [ ${#FAILED_GATES[@]} -eq 0 ]; then
  emit_info "✓ scp-pre-push-verify: all 3 SCP-R gates pass"
  exit 0
else
  emit_info "✗ scp-pre-push-verify: ${#FAILED_GATES[@]} of 3 SCP-R gates failed:"
  for gate in "${FAILED_GATES[@]}"; do
    emit_info "    - ${gate}"
  done
  emit_info ""
  emit_info "CI will reject this branch. Fix the gates above and re-run before pushing."
  exit 1
fi
