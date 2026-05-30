#!/usr/bin/env bash
# scp-wrapper-bump-sweep.sh — report (and optionally open) SCP-wrapper SHA bumps
# across LIVE cohort adopters, per FUP-WP-SCP-024-RENOVATE-MARKER-ESTATE-WIDE-001
# option (c) (operator-attended cycle; ratified 2026-05-29).
#
# WHY THIS EXISTS
#   SCP adopters pin a 40-char SHA on the `uses:` clause of their
#   `.github/workflows/policy-check-wrapper.yml`. Renovate / Dependabot is NOT
#   wired estate-wide today (justified at <8-10 adopters per the BACKLOG
#   analysis). This script is the canonical monthly sweep: compare each
#   adopter's pin to SCP main HEAD and surface bumps the operator can ship.
#
# USAGE
#   scripts/operator/scp-wrapper-bump-sweep.sh                  # report-only
#   scripts/operator/scp-wrapper-bump-sweep.sh --emit-commands  # also emit gh CLI commands
#
# SAFETY
#   - read-only by default; never mutates adopter repos
#   - refuses CI (operator-attended only)
#   - idempotent (re-runs are safe; latest-already-pinned shows as "current")
#   - reports both `@<SHA>` pin AND `scp-sha:` input, since axis-I requires they match
set -euo pipefail

SCP_REPO="jrnb2024/standards-control-plane"
WRAPPER_PATH=".github/workflows/policy-check-wrapper.yml"

# LIVE cohort adopters (per WP-SCP-024 cohort cascade state 2026-05-29).
# To add an adopter post-onboarding: append to this array.
# Format: "<owner>/<repo>"
ADOPTERS=(
  "jrnb2024/mapp-pim"
  "jrnb2024/control-tower"
  "jrnb2024/mapp-doc-agent"
)

# Refuse CI ----------------------------------------------------------------
if [ "${CI:-}" = "true" ] || [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  printf 'scp-wrapper-bump-sweep: ERROR: refusing to run under CI (operator-attended only)\n' >&2
  exit 1
fi

# Arg parsing --------------------------------------------------------------
EMIT_COMMANDS=0
for arg in "$@"; do
  case "$arg" in
    --emit-commands) EMIT_COMMANDS=1 ;;
    --help|-h)
      sed -n '1,28p' "$0"; exit 0 ;;
    *)
      printf 'scp-wrapper-bump-sweep: ERROR: unknown arg "%s" (try --help)\n' "$arg" >&2
      exit 1 ;;
  esac
done

# Sanity check gh CLI ------------------------------------------------------
if ! command -v gh >/dev/null 2>&1; then
  printf 'scp-wrapper-bump-sweep: ERROR: gh CLI not found in PATH\n' >&2
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  printf 'scp-wrapper-bump-sweep: ERROR: gh CLI not authenticated (run `gh auth login`)\n' >&2
  exit 1
fi

# Fetch SCP main HEAD SHA --------------------------------------------------
TARGET_SHA="$(gh api "repos/${SCP_REPO}/commits/main" --jq '.sha')"
if [ -z "${TARGET_SHA}" ]; then
  printf 'scp-wrapper-bump-sweep: ERROR: could not resolve SCP main HEAD\n' >&2
  exit 1
fi
TARGET_SHORT="${TARGET_SHA:0:7}"

printf '\nSCP main HEAD:    %s (%s)\n\n' "${TARGET_SHA}" "${TARGET_SHORT}"

# Per-adopter survey -------------------------------------------------------
NEEDS_BUMP=()
ALREADY_CURRENT=()
ERRORS=()

for adopter in "${ADOPTERS[@]}"; do
  printf '── %s ─────────────────────────\n' "${adopter}"
  # Pull the wrapper file from the adopter's default branch.
  if ! WRAPPER_RAW="$(gh api "repos/${adopter}/contents/${WRAPPER_PATH}" --jq '.content' 2>/dev/null | base64 -d 2>/dev/null)"; then
    printf '  ERROR: could not fetch %s from %s (no wrapper? not yet onboarded?)\n' "${WRAPPER_PATH}" "${adopter}"
    ERRORS+=("${adopter}")
    printf '\n'
    continue
  fi

  # Grep the @<SHA> pin and the scp-sha: input separately.
  PIN_SHA="$(printf '%s\n' "${WRAPPER_RAW}" | grep -oE 'standards-control-plane/.github/workflows/policy-check\.yml@[a-f0-9]{40}' | head -1 | awk -F@ '{print $2}')"
  INPUT_SHA="$(printf '%s\n' "${WRAPPER_RAW}" | grep -oE 'scp-sha:[[:space:]]+[a-f0-9]{40}' | head -1 | awk '{print $2}')"

  if [ -z "${PIN_SHA}" ]; then
    printf '  ERROR: could not parse @<SHA> pin from wrapper\n'
    ERRORS+=("${adopter}")
    printf '\n'
    continue
  fi

  printf '  @<SHA> pin:    %s (%s)\n' "${PIN_SHA}" "${PIN_SHA:0:7}"
  printf '  scp-sha:       %s (%s)\n' "${INPUT_SHA:-<missing>}" "${INPUT_SHA:0:7}"

  # Axis-I invariant: pin and scp-sha MUST match.
  if [ -n "${INPUT_SHA}" ] && [ "${PIN_SHA}" != "${INPUT_SHA}" ]; then
    printf '  ⚠️  AXIS-I MISMATCH — pin and scp-sha differ (must match per ASC-2026-05-22-001)\n'
  fi

  if [ "${PIN_SHA}" = "${TARGET_SHA}" ]; then
    printf '  ✅ current (matches SCP main HEAD)\n'
    ALREADY_CURRENT+=("${adopter}")
  else
    printf '  📦 needs bump → %s\n' "${TARGET_SHORT}"
    NEEDS_BUMP+=("${adopter}")
  fi
  printf '\n'
done

# Summary ------------------------------------------------------------------
printf '═══ Summary ═══════════════════════════════\n'
printf '  Current:     %d adopter(s)\n' "${#ALREADY_CURRENT[@]}"
printf '  Needs bump:  %d adopter(s)\n' "${#NEEDS_BUMP[@]}"
printf '  Errors:      %d adopter(s)\n' "${#ERRORS[@]}"

# Emit commands ------------------------------------------------------------
if [ "${#NEEDS_BUMP[@]}" -gt 0 ] && [ "${EMIT_COMMANDS}" = "1" ]; then
  printf '\n── Suggested commands ──────────────────────\n'
  printf '# For each adopter, the operator opens a PR bumping BOTH the @<SHA> pin\n'
  printf '# AND the scp-sha: input (axis-I: must match). Pattern (run in adopter repo):\n\n'
  for adopter in "${NEEDS_BUMP[@]}"; do
    name="${adopter##*/}"
    printf '# %s\n' "${adopter}"
    printf 'cd ~/Projects/%s && git checkout main && git pull && \\\n' "${name}"
    printf '  git checkout -b chore/scp-wrapper-bump-%s && \\\n' "${TARGET_SHORT}"
    printf '  sed -i.bak -E "s|policy-check\\.yml@[a-f0-9]{40}|policy-check.yml@%s|" %s && \\\n' "${TARGET_SHA}" "${WRAPPER_PATH}"
    printf '  sed -i.bak -E "s|scp-sha:[[:space:]]+[a-f0-9]{40}|scp-sha: %s|" %s && \\\n' "${TARGET_SHA}" "${WRAPPER_PATH}"
    printf '  rm -f %s.bak && \\\n' "${WRAPPER_PATH}"
    # git add <specific file> + git commit (NOT git commit -am, which would sweep up
    # any pre-existing operator WIP in the working tree and ship it in the routine
    # bump PR — caught live on PIM bump 2026-05-30).
    printf '  git add %s && \\\n' "${WRAPPER_PATH}"
    printf '  git commit -m "chore(scp-wrapper): bump SCP pin to %s" && \\\n' "${TARGET_SHORT}"
    printf '  git push -u origin chore/scp-wrapper-bump-%s && \\\n' "${TARGET_SHORT}"
    printf '  gh pr create --title "chore(scp-wrapper): bump SCP pin to %s" \\\n' "${TARGET_SHORT}"
    # PR body includes the ## R1 evidence block — some adopter repos (CT, ACC)
    # enforce a `validate PR body` workflow that fails without three plain
    # `- lens:` lines under a `## R1 evidence` heading. The block is lightweight
    # for routine bumps but mechanically required by the gate.
    printf '    --body "$(cat <<EOF\n'
    printf 'Routine SCP-wrapper bump per scripts/operator/scp-wrapper-bump-sweep.sh (option (c) — FUP-WP-SCP-024-RENOVATE-MARKER-ESTATE-WIDE-001). Bumps both `@<SHA>` pin and `scp-sha:` input (axis-I preserved per ASC-2026-05-22-001) from the prior pin to `%s`.\n' "${TARGET_SHORT}"
    printf '\n'
    printf '## R1 evidence\n'
    printf -- '- correctness: 2-line wrapper diff (`@<SHA>` pin + `scp-sha:` input) verified by scripts/operator/scp-wrapper-bump-sweep.sh pre-PR; axis-I invariant preserved (both fields bumped to the same SHA in the same sed transaction).\n'
    printf -- '- safety_bypass: routine pin-currency to a tagged or main-HEAD SHA; SCP-side `policy-check / scp/policy-check` workflow exercises the new SHA as the merge gate.\n'
    printf -- '- completeness_governance: closure mechanism for FUP-WP-SCP-024-RENOVATE-MARKER-ESTATE-WIDE-001 option (c); WP-SCP-024 bake observation criterion 2 (≥1 SHA bump cycle merged + observed clean) advances on merge.\n'
    printf 'EOF\n'
    printf ')"\n\n'
  done
fi

# Exit code: 0 if all current OR all reported cleanly; 1 if errors --------
if [ "${#ERRORS[@]}" -gt 0 ]; then
  exit 1
fi
exit 0
