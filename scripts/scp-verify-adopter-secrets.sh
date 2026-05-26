#!/usr/bin/env bash
# shellcheck shell=bash
# scp-verify-adopter-secrets.sh — pre-flight verification that an adopter
# repo has both required SCP federation primitive secrets set before the
# wrapper PR fires.
#
# Closes TF-024D-001 (BACKLOG.md Phase 12). Driver: WP-SCP-024 024D
# control-tower operator ceremony 2026-05-25 required two iterations to
# land both secrets because GitHub Actions surfaces missing-secret errors
# one-at-a-time. This script collapses the two-iteration ceremony into one
# by asserting both secrets are present BEFORE the smoke-test PR opens.
#
# Bootstrap-only: refuses to run in CI or GitHub Actions. Operator-attended.
#
# Reference: docs/adoption/ADOPT-001-project-onboarding.md §12.7.16c;
# docs/decisions/D-050-app-credential-surface-2026-05-21.md.

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scp-verify-adopter-secrets.sh --repo OWNER/NAME [--secret-id NAME] [--secret-key NAME]

Required:
  --repo OWNER/NAME     Adopter repository (e.g. jrnb2024/mapp-pim).

Optional:
  --secret-id NAME      Name of the App-ID secret to verify.
                        Default: SCP_FEDERATION_APP_ID.
  --secret-key NAME     Name of the App-private-key secret to verify.
                        Default: SCP_FEDERATION_APP_PRIVATE_KEY.
  --help / -h           Show this help.

Exits 0 if both required secrets are present on the adopter repo.
Exits non-zero with a clear error if either is missing (or both).

Bootstrap-only — refuses to run in CI or GitHub Actions.
EOF
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

if [ "${CI:-}" = "true" ] || [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  die "bootstrap-only: refuse to run in CI=true or GITHUB_ACTIONS=true"
fi

REPO=""
SECRET_ID="SCP_FEDERATION_APP_ID"
SECRET_KEY="SCP_FEDERATION_APP_PRIVATE_KEY"

while [ $# -gt 0 ]; do
  case "$1" in
    --repo)
      [ $# -lt 2 ] && { echo "error: --repo requires a value" >&2; usage; exit 2; }
      REPO="$2"; shift 2 ;;
    --secret-id)
      [ $# -lt 2 ] && { echo "error: --secret-id requires a value" >&2; usage; exit 2; }
      SECRET_ID="$2"; shift 2 ;;
    --secret-key)
      [ $# -lt 2 ] && { echo "error: --secret-key requires a value" >&2; usage; exit 2; }
      SECRET_KEY="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown flag: $1" >&2; usage; exit 2 ;;
  esac
done

if [ -z "$REPO" ]; then
  echo "error: --repo OWNER/NAME is required" >&2
  usage
  exit 2
fi

# owner/name shape (matches enable-required-check.sh validation).
if ! printf '%s' "$REPO" | grep -Eq '^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$'; then
  die "--repo '$REPO' does not match owner/name shape"
fi
case "$REPO" in
  *..*) die "--repo '$REPO' contains path-traversal sequence (..)" ;;
esac

if ! command -v gh >/dev/null 2>&1; then
  die "gh CLI is required but not installed; install gh (https://cli.github.com/) + re-run"
fi

if ! gh auth status >/dev/null 2>&1; then
  die "gh is not authenticated; run 'gh auth login' + re-run"
fi

# Use the Actions secrets API to list secret NAMES only (the API never returns
# values). This avoids accidentally exposing or echoing any secret content.
# https://docs.github.com/en/rest/actions/secrets#list-repository-secrets
SECRETS_JSON=""
if ! SECRETS_JSON="$(gh api "repos/${REPO}/actions/secrets" --paginate 2>&1)"; then
  echo "error: could not list Actions secrets on $REPO via gh api" >&2
  echo "       (need repo-admin permission OR org-admin on this repo)" >&2
  printf '       gh output: %s\n' "$SECRETS_JSON" >&2
  exit 2
fi

if ! printf '%s' "$SECRETS_JSON" | jq -e '.secrets' >/dev/null 2>&1; then
  die "unexpected response shape from gh api repos/${REPO}/actions/secrets (no .secrets array); cannot verify"
fi

_has_secret() {
  local name="$1"
  printf '%s' "$SECRETS_JSON" \
    | jq -r --arg name "$name" '.secrets[] | select(.name == $name) | .name' \
    | grep -Fxq "$name"
}

missing=()
if _has_secret "$SECRET_ID"; then
  printf 'OK: %s present on %s\n' "$SECRET_ID" "$REPO" >&2
else
  missing+=("$SECRET_ID")
fi
if _has_secret "$SECRET_KEY"; then
  printf 'OK: %s present on %s\n' "$SECRET_KEY" "$REPO" >&2
else
  missing+=("$SECRET_KEY")
fi

if [ ${#missing[@]} -eq 0 ]; then
  printf 'OK: both required secrets present; safe to open the smoke-test wrapper PR.\n' >&2
  exit 0
fi

echo "" >&2
echo "================================================================" >&2
echo "ERROR: missing required adopter-repo secret(s) on $REPO" >&2
for name in "${missing[@]}"; do
  printf '  - %s\n' "$name" >&2
done
echo "" >&2
echo "Both secrets MUST be set BEFORE opening the smoke-test wrapper PR" >&2
echo "per ADOPT-001 §12.7.16c. Set via:" >&2
echo "  https://github.com/${REPO}/settings/secrets/actions/new" >&2
echo "" >&2
echo "Source values:" >&2
echo "  - ${SECRET_ID}: scp-federation-primitive App ID number" >&2
echo "    (Visit https://github.com/settings/apps/scp-federation-primitive)" >&2
echo "  - ${SECRET_KEY}: full .pem private key (BEGIN/END markers included)" >&2
echo "    (Operator's local .pem from App authoring ceremony per" >&2
echo "    docs/plans/TF-PIM-001-impl-path-c-app-credential.md §4 Wave A)" >&2
echo "================================================================" >&2
exit 1
