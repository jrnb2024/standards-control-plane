#!/usr/bin/env bash
# shellcheck shell=bash
# WP-SCP-024 slice 024B scaffolder contract (D-044).
#
# Generates the adopter-side wrapper, CODEOWNERS snippet, PR body
# template, and manifest from the canonical adopter-wrapper template.
# Bootstrap-only: refuses to run in CI or GitHub Actions.
#
# Reference: docs/DECISIONS.md D-044; docs/plans/WP-SCP-024-estate-cascade.md
# §5.3; docs/adoption/ADOPT-001-project-onboarding.md §12.

set -euo pipefail

SCP_REPO_ROOT="${SCP_REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
TEMPLATE_PATH="${SCP_REPO_ROOT}/templates/adopter-wrapper.yml.tmpl"

usage() {
  cat >&2 <<'EOF'
Usage: scaffold-downstream.sh --adopter-repo OWNER/NAME --default-branch <main|master|develop> --scp-sha <40-char-sha> --scorecard-emit <true|false> --output-dir <local-clone-path>

Required:
  --adopter-repo OWNER/NAME      Target adopter repository.
  --default-branch <branch>      Adopter default branch (main, master, develop).
  --scp-sha <40-char-sha>        SCP wrapper pin SHA.
  --scorecard-emit <true|false>  Wrapper scorecard emit toggle.
  --output-dir <path>            Existing writable output directory.

Flags:
  --help / -h                    Show this help.
EOF
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

warn() {
  printf 'WARNING: %s\n' "$*" >&2
}

sha256_file() {
  python3 -c 'import hashlib, pathlib, sys
path = pathlib.Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest())' "$1"
}

if [ "${CI:-}" = "true" ] || [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  die "bootstrap-only: refuse to run in CI=true or GITHUB_ACTIONS=true"
fi

if [ ! -f "$TEMPLATE_PATH" ]; then
  die "missing template: $TEMPLATE_PATH"
fi

ADOPTER_REPO=""
DEFAULT_BRANCH=""
SCP_SHA=""
SCORECARD_EMIT=""
OUTPUT_DIR=""

while [ $# -gt 0 ]; do
  case "$1" in
    --adopter-repo)
      [ $# -ge 2 ] || die "--adopter-repo requires a value"
      ADOPTER_REPO="$2"
      shift 2
      ;;
    --default-branch)
      [ $# -ge 2 ] || die "--default-branch requires a value"
      DEFAULT_BRANCH="$2"
      shift 2
      ;;
    --scp-sha)
      [ $# -ge 2 ] || die "--scp-sha requires a value"
      SCP_SHA="$2"
      shift 2
      ;;
    --scorecard-emit)
      [ $# -ge 2 ] || die "--scorecard-emit requires a value"
      SCORECARD_EMIT="$2"
      shift 2
      ;;
    --output-dir)
      [ $# -ge 2 ] || die "--output-dir requires a value"
      OUTPUT_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown flag: $1"
      ;;
  esac
done

[ -n "$ADOPTER_REPO" ] || die "--adopter-repo is required"
[ -n "$DEFAULT_BRANCH" ] || die "--default-branch is required"
[ -n "$SCP_SHA" ] || die "--scp-sha is required"
[ -n "$SCORECARD_EMIT" ] || die "--scorecard-emit is required"
[ -n "$OUTPUT_DIR" ] || die "--output-dir is required"

if ! printf '%s' "$ADOPTER_REPO" | grep -qE '^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$'; then
  die "--adopter-repo '$ADOPTER_REPO' must match owner/name"
fi

case "$DEFAULT_BRANCH" in
  main|master|develop) ;;
  *)
    die "--default-branch '$DEFAULT_BRANCH' must be one of main, master, develop"
    ;;
esac

if ! printf '%s' "$SCP_SHA" | grep -qE '^[a-f0-9]{40}$'; then
  die "--scp-sha '$SCP_SHA' must be exactly 40 lowercase hex characters"
fi

case "$SCORECARD_EMIT" in
  true|false) ;;
  *)
    die "--scorecard-emit '$SCORECARD_EMIT' must be true or false"
    ;;
esac

if [ ! -d "$OUTPUT_DIR" ] || [ ! -w "$OUTPUT_DIR" ]; then
  die "--output-dir '$OUTPUT_DIR' must exist and be writable"
fi

case "$OUTPUT_DIR" in
  /etc|/etc/*|/var|/var/*|/usr|/usr/*|/sys|/sys/*|/proc|/proc/*|/tmp|/tmp/*)
    die "--output-dir '$OUTPUT_DIR' refuses system path parents (/etc, /var, /var/*, /tmp, /tmp/*, /usr, /sys, /proc)"
    ;;
esac

if ! git -C "$SCP_REPO_ROOT" cat-file -e "${SCP_SHA}^{commit}" 2>/dev/null; then
  printf 'ERROR: --scp-sha %s does not exist in SCP repo\n' "$SCP_SHA" >&2
  exit 2
fi

MAIN_HEAD_SHA="$(git -C "$SCP_REPO_ROOT" rev-parse main 2>/dev/null || true)"
if [ -z "$MAIN_HEAD_SHA" ]; then
  warn "could not resolve SCP main HEAD; continuing without HEAD-lineage warning"
elif [ "$SCP_SHA" != "$MAIN_HEAD_SHA" ]; then
  warn "--scp-sha $SCP_SHA is not current SCP main HEAD $MAIN_HEAD_SHA; emitted wrapper will be behind main"
fi

WORKFLOWS_DIR="${OUTPUT_DIR}/.github/workflows"
mkdir -p "$WORKFLOWS_DIR"

wrapper_path="${WORKFLOWS_DIR}/policy-check-wrapper.yml"
codeowners_snippet_path="${OUTPUT_DIR}/.github/CODEOWNERS-snippet.txt"
pr_body_path="${OUTPUT_DIR}/CASCADE-PR-BODY.md"
manifest_path="${OUTPUT_DIR}/MANIFEST.json"

sed \
  -e "s/{{DEFAULT_BRANCH}}/${DEFAULT_BRANCH}/g" \
  -e "s/{{SCP_SHA}}/${SCP_SHA}/g" \
  -e "s/{{SCORECARD_EMIT}}/${SCORECARD_EMIT}/g" \
  "$TEMPLATE_PATH" >"$wrapper_path"

cat >"$codeowners_snippet_path" <<'EOF'
# CODEOWNERS snippet for policy-check-wrapper.yml — adopter merges this line into existing CODEOWNERS, replacing <adopter-CODEOWNERS-account> with the right account/team.
.github/workflows/policy-check-wrapper.yml @<adopter-CODEOWNERS-account>
EOF

cat >"$pr_body_path" <<'EOF'
<!-- adopter: review/edit -->
This PR adds the SCP wrapper and required-check bootstrap for the adopter repo. Estimated cost impact is intentionally small: T-024-09 expects roughly 2-5 minutes on ubuntu-24.04, under 10% of a typical adopter CI bill.

<!-- adopter: review/edit -->
Bus-factor-1 is disclosed explicitly here: invariant 9 and D-031 both acknowledge the single-operator posture, and the 2026-07-21 quarterly review is the named follow-up for that exposure.

<!-- adopter: review/edit -->
## What this PR does NOT touch

This cascade slice is purely additive — it adds `.github/workflows/policy-check-wrapper.yml` and, if needed, a `.github/CODEOWNERS-snippet.txt` line for that file. It does NOT modify your existing CI workflows, your build config (`package.json` / `pyproject.toml` / equivalent), your README, your service config, branch-protection rules from this PR, or any other pre-existing file. Per WP-SCP-024 plan-doc §2 invariant 3, the cascade does not touch existing adopter content.

<!-- adopter: review/edit -->
Invariant 1 consent surface is explicit here: the adopter owner chooses the wrapper SHA pin and this PR is the audit record for that choice, not an automatic transitive update.

<!-- adopter: review/edit -->
Version-skew tolerance remains the design point: T-024-04 and the D-036 deprecation ramp are what make SHA pin bumps safe enough to operate across adopter cadence differences.

<!-- adopter: review/edit -->
Scorecard emit stays opt-in by default: TF-023E-002 defers the wrapper-shape change unless the adopter is public or org-owned per TF-023E-001.
EOF

emitted_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
wrapper_sha="$(sha256_file "$wrapper_path")"
codeowners_sha="$(sha256_file "$codeowners_snippet_path")"
pr_body_sha="$(sha256_file "$pr_body_path")"

python3 - "$emitted_at" "$ADOPTER_REPO" "$DEFAULT_BRANCH" "$SCP_SHA" "$SCORECARD_EMIT" "$manifest_path" \
  ".github/workflows/policy-check-wrapper.yml" "$wrapper_sha" \
  ".github/CODEOWNERS-snippet.txt" "$codeowners_sha" \
  "CASCADE-PR-BODY.md" "$pr_body_sha" <<'PY'
import json
import sys

emitted_at, adopter_repo, default_branch, scp_sha, scorecard_emit, manifest_path = sys.argv[1:7]
rest = sys.argv[7:]
files = []
for path, sha in zip(rest[0::2], rest[1::2]):
    files.append({"path": path, "sha256": sha})

payload = {
    "emitted_at": emitted_at,
    "adopter_repo": adopter_repo,
    "default_branch": default_branch,
    "scp_sha": scp_sha,
    "scorecard_emit": scorecard_emit == "true",
    "files": files,
}
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
    f.write("\n")
PY

printf 'OK: emitted 4 files under %s; manifest at %s\n' "$OUTPUT_DIR" "$manifest_path" >&2
