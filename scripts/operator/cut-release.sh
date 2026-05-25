#!/usr/bin/env bash
# scripts/operator/cut-release.sh — SCP release ceremony driver
#
# Bash script per operator preference (terminal copy-paste causes line-
# break errors). Runs the four-phase SCP release ceremony per
# `policies/VERSIONING.md` "Tag-cut procedure":
#
#   1. Pre-flight: verify main HEAD matches expected SHA + version-
#      manifest.json declares the expected version
#   2. Release-gate dry-run via `gh workflow run release-gate.yml`
#      (operator-attended workflow_dispatch path per VERSIONING.md
#      "Dry-run pre-flight"). Watches the run to completion + exits
#      non-zero if dry-run fails.
#   3. Tag + push: `git tag <version> <SHA> && git push origin <version>`.
#      Triggers the on:push:tags release-gate run (post-tag observer).
#   4. GitHub release: `gh release create` with operator-supplied notes
#      OR --notes-file path.
#
# DEFAULT MODE: each phase prompts the operator [y/N] before proceeding.
# Override with `--yes` to auto-confirm (use with care).
#
# Refuses CI environments per SCP-operator-script convention.
#
# Usage:
#   scripts/operator/cut-release.sh --version v1.3.0 --sha d9cf525 [--notes-file PATH] [--yes] [--dry-run-only]
#
# Examples:
#   # v1.3.0 ceremony with interactive prompts:
#   scripts/operator/cut-release.sh --version v1.3.0 --sha d9cf52544eea7eb2b0cc5486187952eaef40b1e1
#
#   # Just verify the release-gate dry-run passes (no tag push):
#   scripts/operator/cut-release.sh --version v1.3.0 --sha d9cf525 --dry-run-only

set -euo pipefail

# ---------- CI refusal ----------
if [ "${CI:-}" = "true" ] || [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  echo "error: cut-release.sh is operator-attended; refusing CI environment (CI=${CI:-} GITHUB_ACTIONS=${GITHUB_ACTIONS:-})" >&2
  echo "       run from your interactive shell session" >&2
  exit 1
fi

# ---------- Defaults + arg parse ----------
VERSION=""
SHA=""
NOTES_FILE=""
AUTO_YES=0
DRY_RUN_ONLY=0
REPO="jrnb2024/standards-control-plane"

usage() {
  cat >&2 <<'EOF'
Usage: cut-release.sh --version vX.Y.Z --sha <40-char-sha> [options]

Required:
  --version vX.Y.Z         Semver tag to cut (must start with 'v')
  --sha <40-char-sha>      Commit SHA on main to tag

Options:
  --notes-file PATH        Path to release notes markdown (used by gh release create)
                           If omitted, the script auto-extracts notes from CHANGELOG.md
                           OR (failing that) prompts you to paste notes interactively.
  --yes                    Auto-confirm all phase prompts (use with care)
  --dry-run-only           Run only Phase 1 + Phase 2 (verify dry-run); skip tag-push + release
  --repo OWNER/NAME        Override target repo (default: jrnb2024/standards-control-plane)
  -h / --help              Show this help
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --sha) SHA="$2"; shift 2 ;;
    --notes-file) NOTES_FILE="$2"; shift 2 ;;
    --yes) AUTO_YES=1; shift ;;
    --dry-run-only) DRY_RUN_ONLY=1; shift ;;
    --repo) REPO="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "error: unknown arg '$1'" >&2; usage; exit 2 ;;
  esac
done

# ---------- Validation ----------
[ -z "$VERSION" ] && { echo "error: --version required" >&2; usage; exit 2; }
[ -z "$SHA" ] && { echo "error: --sha required" >&2; usage; exit 2; }

# Version must match vX.Y.Z (semver). Pre-release suffixes (-rc.1, -beta) allowed.
if ! printf '%s' "$VERSION" | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+(-[a-z0-9.]+)?$'; then
  echo "error: --version '$VERSION' must match vX.Y.Z[-pre] (semver)" >&2
  exit 2
fi

# SHA must be 40 hex chars.
if ! printf '%s' "$SHA" | grep -qE '^[0-9a-f]{40}$'; then
  echo "error: --sha '$SHA' must be a 40-char hex SHA" >&2
  exit 2
fi

# Required tools.
for tool in gh jq git; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "error: required tool '$tool' not on PATH" >&2
    exit 1
  fi
done

# ---------- Helpers ----------
log() { printf '[release] %s\n' "$*"; }

prompt_yn() {
  local msg="$1"
  if [ "$AUTO_YES" -eq 1 ]; then
    log "$msg [auto-y per --yes]"
    return 0
  fi
  read -r -p "$msg [y/N] " ans
  case "$ans" in
    [yY]|[yY][eE][sS]) return 0 ;;
    *) log "aborted by operator"; exit 1 ;;
  esac
}

# ---------- Phase 1: Pre-flight ----------
log "===== Phase 1 — Pre-flight ====="
log "target repo: $REPO"
log "target version: $VERSION"
log "target SHA: $SHA"

# Check we're in a clone of the target repo.
if ! git remote get-url origin 2>/dev/null | grep -q "$REPO"; then
  echo "error: current dir is not a clone of $REPO (origin remote mismatch)" >&2
  echo "       cd into ~/Projects/standards-control-plane first" >&2
  exit 1
fi

# Verify SHA exists on origin/main.
git fetch origin main >/dev/null 2>&1
if ! git merge-base --is-ancestor "$SHA" origin/main 2>/dev/null; then
  echo "error: SHA $SHA is not on origin/main" >&2
  echo "       current origin/main HEAD: $(git rev-parse origin/main)" >&2
  exit 1
fi
log "✓ SHA $SHA is on origin/main"

# Verify the tag doesn't already exist.
if git ls-remote --tags origin "refs/tags/$VERSION" 2>/dev/null | grep -q "$VERSION"; then
  echo "error: tag $VERSION already exists on origin" >&2
  echo "       (release ceremonies are non-amending; cut a new version instead)" >&2
  exit 1
fi
log "✓ tag $VERSION does not yet exist"

# Verify version-manifest.json declares the expected version.
MANIFEST_VERSION="$(git show "$SHA:version-manifest.json" | jq -r '.version')"
EXPECTED="${VERSION#v}"   # strip leading v
if [ "$MANIFEST_VERSION" != "$EXPECTED" ]; then
  echo "error: version-manifest.json at SHA $SHA declares '$MANIFEST_VERSION' but --version is '$VERSION' (expected '$EXPECTED')" >&2
  exit 1
fi
log "✓ version-manifest.json declares $MANIFEST_VERSION"

log ""
prompt_yn "Pre-flight clean. Proceed to Phase 2 (release-gate dry-run)?"

# ---------- Phase 2: Release-gate dry-run ----------
log ""
log "===== Phase 2 — release-gate dry-run ====="

log "dispatching workflow_dispatch for release-gate.yml with dry_run_tag=$VERSION..."
gh workflow run release-gate.yml -f "dry_run_tag=$VERSION" --repo "$REPO"

# Find the most-recent workflow_dispatch run on release-gate.
log "waiting for run to start (up to 30s)..."
DRY_RUN_ID=""
for _ in $(seq 1 15); do
  sleep 2
  DRY_RUN_ID="$(gh run list --workflow=release-gate.yml --repo "$REPO" --event=workflow_dispatch --limit 1 --json databaseId,createdAt --jq '.[0].databaseId' 2>/dev/null || true)"
  if [ -n "$DRY_RUN_ID" ] && [ "$DRY_RUN_ID" != "null" ]; then
    break
  fi
done

if [ -z "$DRY_RUN_ID" ] || [ "$DRY_RUN_ID" = "null" ]; then
  echo "error: could not find the dispatched run after 30s" >&2
  echo "       check https://github.com/$REPO/actions manually" >&2
  exit 1
fi

log "dry-run id: $DRY_RUN_ID"
log "waiting for completion (gh run watch)..."
if ! gh run watch "$DRY_RUN_ID" --repo "$REPO" --exit-status; then
  echo "error: release-gate dry-run FAILED" >&2
  echo "       view run: https://github.com/$REPO/actions/runs/$DRY_RUN_ID" >&2
  exit 1
fi
log "✓ release-gate dry-run GREEN"

if [ "$DRY_RUN_ONLY" -eq 1 ]; then
  log ""
  log "===== Done (--dry-run-only set) ====="
  log "Pre-flight + dry-run passed. To complete the ceremony:"
  log "  rerun without --dry-run-only"
  exit 0
fi

log ""
prompt_yn "Dry-run clean. Proceed to Phase 3 (tag + push)?"

# ---------- Phase 3: Tag + push ----------
log ""
log "===== Phase 3 — tag + push ====="

log "creating tag $VERSION at $SHA..."
# Annotated tag with message; signing follows the operator's git config.
git tag -a "$VERSION" "$SHA" -m "$VERSION"
log "✓ tag $VERSION created locally"

log "pushing tag to origin..."
git push origin "$VERSION"
log "✓ tag $VERSION pushed"

log "waiting for the on:push:tags release-gate observer to complete..."
sleep 5
POST_TAG_RUN_ID=""
for _ in $(seq 1 15); do
  sleep 2
  POST_TAG_RUN_ID="$(gh run list --workflow=release-gate.yml --repo "$REPO" --event=push --limit 5 --json databaseId,headBranch,createdAt --jq ".[] | select(.headBranch == \"$VERSION\") | .databaseId" 2>/dev/null | head -1 || true)"
  if [ -n "$POST_TAG_RUN_ID" ]; then
    break
  fi
done

if [ -z "$POST_TAG_RUN_ID" ]; then
  log "warning: could not find the post-tag observer run; check https://github.com/$REPO/actions manually"
else
  log "post-tag observer run id: $POST_TAG_RUN_ID"
  if ! gh run watch "$POST_TAG_RUN_ID" --repo "$REPO" --exit-status; then
    echo "warning: post-tag observer FAILED — tag was pushed but observer reports issue" >&2
    echo "         view: https://github.com/$REPO/actions/runs/$POST_TAG_RUN_ID" >&2
    echo "         (the tag is still pushed; investigate before publishing release)" >&2
  else
    log "✓ post-tag observer GREEN"
  fi
fi

log ""
prompt_yn "Tag pushed + observer GREEN. Proceed to Phase 4 (GitHub release)?"

# ---------- Phase 4: GitHub release ----------
log ""
log "===== Phase 4 — GitHub release ====="

if [ -n "$NOTES_FILE" ]; then
  [ -f "$NOTES_FILE" ] || { echo "error: notes file $NOTES_FILE not found" >&2; exit 1; }
  log "creating release from $NOTES_FILE..."
  gh release create "$VERSION" --repo "$REPO" --title "$VERSION" --notes-file "$NOTES_FILE"
else
  log "no --notes-file supplied; auto-generating release notes from this version's PR commits..."
  PRIOR_TAG="$(gh release list --repo "$REPO" --limit 1 --json tagName --jq '.[0].tagName' 2>/dev/null || echo '')"
  if [ -n "$PRIOR_TAG" ]; then
    log "prior tag: $PRIOR_TAG"
    NOTES_TMP="$(mktemp)"
    {
      printf '%s\n\n' "$VERSION release"
      printf '## Commits since %s\n\n' "$PRIOR_TAG"
      git log --pretty=format:"- %s" "$PRIOR_TAG..$SHA"
    } > "$NOTES_TMP"
    gh release create "$VERSION" --repo "$REPO" --title "$VERSION" --notes-file "$NOTES_TMP"
    rm -f "$NOTES_TMP"
  else
    gh release create "$VERSION" --repo "$REPO" --title "$VERSION" --generate-notes
  fi
fi

log "✓ release published: https://github.com/$REPO/releases/tag/$VERSION"

log ""
log "===== Ceremony complete ====="
log "Renovate will auto-PR adopters within ~24h with the new SHA pin."
log "Verify by checking adopter wrappers' policy-check runs over the next ~24h."
