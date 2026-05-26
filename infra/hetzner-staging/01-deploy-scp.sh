#!/usr/bin/env bash
# SCP — Hetzner staging deploy.
# Idempotent: safe to re-run on every code update.
#
# WHAT IT DOES
#   1. Preflight       — SSH key perms + required env vars
#   2. SSH check       — confirm box is reachable
#   3. Repo sync       — git fetch + reset --hard to DEPLOY_BRANCH (or initial clone)
#   4. Render .env     — write staging environment to /home/webapp/standards-control-plane/.env (chmod 600)
#   5. Build + up      — docker compose build with GIT_SHA + RELEASE_VERSION build args, then up -d
#   6. Health check    — local /health + tunnel smoke + verify GIT_SHA appears in /health response
#   7. Summary         — URLs + tail-log commands
#
# USAGE
#   GITHUB_PAT=ghp_xxx ./infra/hetzner-staging/01-deploy-scp.sh                # default deploy from main
#   DEPLOY_BRANCH=feature/X GITHUB_PAT=ghp_xxx ./infra/hetzner-staging/01-deploy-scp.sh
#
# PREREQUISITES
#   - ~/.ssh/hetzner_staging_ed25519 present, chmod 600
#   - GITHUB_PAT env var: fine-grained PAT with Contents:read on jrnb2024/standards-control-plane
#     (generate at https://github.com/settings/personal-access-tokens/new)
#   - CT already deployed at https://control-tower.brokapps.ai (SCP JWKS depends on it)
#   - mapp-staging-1 box has the cloudflared tunnel active for scp.brokapps.ai
#
# CALLED-FROM-CI
#   GitHub Actions workflow .github/workflows/deploy-staging.yml uses appleboy/ssh-action
#   for the on-box pull+build cycle (workflow_dispatch only). This script is for
#   OPERATOR-ATTENDED first-time setup, full-stack rebuilds, or when the workflow
#   isn't available (network blocked, no Actions enabled, etc.). The workflow does
#   a faster subset for routine deploys.
#
# Refuses CI environments per SCP-operator-script convention.

set -euo pipefail

# ---------- CI refusal ----------
if [ "${CI:-}" = "true" ] || [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  echo "error: 01-deploy-scp.sh is operator-attended; refusing CI environment (CI=${CI:-} GITHUB_ACTIONS=${GITHUB_ACTIONS:-})" >&2
  echo "       run from your interactive shell session, or use .github/workflows/deploy-staging.yml for CI deploys" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
HETZNER_HOST="${HETZNER_HOST:-178.104.238.60}"
HETZNER_USER="${HETZNER_USER:-webapp}"
HETZNER_SSH_KEY="${HETZNER_SSH_KEY:-${HOME}/.ssh/hetzner_staging_ed25519}"
GITHUB_PAT="${GITHUB_PAT:-}"
REPO_URL_HTTPS="https://x-access-token:${GITHUB_PAT}@github.com/jrnb2024/standards-control-plane.git"
REPO_DIR="/home/${HETZNER_USER}/standards-control-plane"
PUBLIC_HOSTNAME="https://scp.brokapps.ai"
LOCAL_PORT="3787"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"

TOTAL_STEPS=7
SSH_OPTS=(-i "${HETZNER_SSH_KEY}" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -o BatchMode=yes)
SSH_TARGET="${HETZNER_USER}@${HETZNER_HOST}"

REMOTE_COMPOSE_FILES="-f ${REPO_DIR}/docker-compose.yml -f ${REPO_DIR}/infra/hetzner-staging/docker-compose.staging-hetzner.yml"
REMOTE_COMPOSE="docker compose --env-file ${REPO_DIR}/.env ${REMOTE_COMPOSE_FILES}"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
bold()  { printf '\n\033[1m[%s/%s] %s\033[0m\n' "$1" "${TOTAL_STEPS}" "$2"; }
info()  { printf '  %s\n' "$*"; }
ok()    { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn()  { printf '  \033[33m!\033[0m %s\n' "$*" >&2; }
fail()  { printf '  \033[31m✗\033[0m %s\n' "$*" >&2; exit 1; }

ssh_run() { ssh "${SSH_OPTS[@]}" "${SSH_TARGET}" -- "$@"; }

# ---------------------------------------------------------------------------
bold 1 "Preflight"
# ---------------------------------------------------------------------------
[ -f "${HETZNER_SSH_KEY}" ] || fail "SSH key not found at ${HETZNER_SSH_KEY}"
KEY_PERMS=$(stat -f '%Mp%Lp' "${HETZNER_SSH_KEY}" 2>/dev/null || stat -c '%a' "${HETZNER_SSH_KEY}" 2>/dev/null || echo unknown)
# macOS `stat -f '%Mp%Lp'` zero-pads to 4 digits (e.g. "0600"); Linux
# `stat -c '%a'` returns 3 digits ("600"). Normalise by stripping a
# leading 0 if present.
KEY_PERMS="${KEY_PERMS#0}"
[ "${KEY_PERMS}" = "600" ] || fail "SSH key perms must be 600 (got ${KEY_PERMS}); run: chmod 600 ${HETZNER_SSH_KEY}"
[ -n "${GITHUB_PAT}" ] || fail "GITHUB_PAT env var required (fine-grained PAT, Contents:read on jrnb2024/standards-control-plane)"
for tool in ssh curl git python3; do
  command -v "${tool}" >/dev/null 2>&1 || fail "required tool '${tool}' not on PATH"
done
ok "SSH key, GITHUB_PAT, local tools verified"
ok "Target: ${SSH_TARGET}"
ok "Deploy branch: ${DEPLOY_BRANCH}"

# ---------------------------------------------------------------------------
bold 2 "SSH reachability"
# ---------------------------------------------------------------------------
if ssh_run "echo hetzner-reachable" >/dev/null 2>&1; then
  ok "SSH OK"
else
  fail "Cannot SSH to ${SSH_TARGET} with key ${HETZNER_SSH_KEY}"
fi

# ---------------------------------------------------------------------------
bold 3 "Repo sync (clone OR fetch + reset --hard)"
# ---------------------------------------------------------------------------
if ssh_run "test -d ${REPO_DIR}/.git" >/dev/null 2>&1; then
  info "Repo present; updating to ${DEPLOY_BRANCH}..."
  # Update the remote URL with the current PAT (rotates cleanly).
  ssh_run "cd ${REPO_DIR} && git remote set-url origin '${REPO_URL_HTTPS}' && git fetch --prune origin && git checkout ${DEPLOY_BRANCH} && git reset --hard origin/${DEPLOY_BRANCH}" >/dev/null
  ok "Repo synced to origin/${DEPLOY_BRANCH}"
else
  info "Cloning into ${REPO_DIR}..."
  ssh_run "git clone -b ${DEPLOY_BRANCH} '${REPO_URL_HTTPS}' ${REPO_DIR}" >/dev/null
  ok "Repo cloned"
fi

DEPLOY_SHA=$(ssh_run "cd ${REPO_DIR} && git rev-parse HEAD")
DEPLOY_VERSION=$(ssh_run "cd ${REPO_DIR} && python3 -c \"import json,sys; print(json.load(open('version-manifest.json'))['version'])\"" 2>/dev/null || echo unknown)
ok "HEAD: ${DEPLOY_SHA}"
ok "version-manifest.json: ${DEPLOY_VERSION}"

# ---------------------------------------------------------------------------
bold 4 ".env render"
# ---------------------------------------------------------------------------
# The Hetzner overlay reads the on-box .env file. We render the canonical
# staging env here. .env stays chmod 600 + on-box-only (never copied locally).
info "Writing ${REPO_DIR}/.env (chmod 600)..."
ssh_run "cat > ${REPO_DIR}/.env <<'EOF'
# Generated by infra/hetzner-staging/01-deploy-scp.sh — do not edit by hand.
# Re-run the script to refresh.
ENV=staging
PORT=${LOCAL_PORT}
AUTH_ENABLED=true
CT_BASE_URL=https://control-tower.brokapps.ai
CT_JWKS_URL=https://control-tower.brokapps.ai/api/v1/.well-known/jwks.json
CT_APP_ID=scp
PUBLIC_BASE_URL=${PUBLIC_HOSTNAME}
EOF
chmod 600 ${REPO_DIR}/.env"
ok ".env written + secured"

# ---------------------------------------------------------------------------
bold 5 "Docker compose build + up"
# ---------------------------------------------------------------------------
info "Building image with GIT_SHA=${DEPLOY_SHA} + RELEASE_VERSION=${DEPLOY_VERSION}..."
ssh_run "cd ${REPO_DIR} && ${REMOTE_COMPOSE} build --build-arg GIT_SHA=${DEPLOY_SHA} --build-arg RELEASE_VERSION=${DEPLOY_VERSION}" 2>&1 | tail -10
ok "Image built"

info "Bringing stack up..."
ssh_run "cd ${REPO_DIR} && ${REMOTE_COMPOSE} up -d" 2>&1 | tail -5
ok "Stack up"

# ---------------------------------------------------------------------------
bold 6 "Health checks"
# ---------------------------------------------------------------------------
info "Waiting up to 60s for container health..."
HEALTHY=0
for i in $(seq 1 12); do
  if ssh_run "curl -fsS http://127.0.0.1:${LOCAL_PORT}/health" >/dev/null 2>&1; then
    HEALTHY=1
    break
  fi
  sleep 5
done
[ "${HEALTHY}" = "1" ] || fail "Container failed health check after 60s"
ok "Local /health responding"

# Verify GIT_SHA propagated into /health (closes the "is staging current" gap).
HEALTH_JSON=$(ssh_run "curl -fsS http://127.0.0.1:${LOCAL_PORT}/health")
RUNNING_SHA=$(printf '%s' "${HEALTH_JSON}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('git_sha','unknown'))")
RUNNING_VER=$(printf '%s' "${HEALTH_JSON}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('release_version','unknown'))")
if [ "${RUNNING_SHA}" = "${DEPLOY_SHA}" ]; then
  ok "Running git_sha matches deployed SHA: ${RUNNING_SHA}"
else
  warn "git_sha mismatch — running=${RUNNING_SHA} deployed=${DEPLOY_SHA} (build cache may be stale; consider --no-cache)"
fi
ok "Running release_version: ${RUNNING_VER}"

# Cloudflare tunnel smoke.
TUNNEL_STATUS=$(curl -sk -o /dev/null -w "%{http_code}" "${PUBLIC_HOSTNAME}/" 2>&1)
case "${TUNNEL_STATUS}" in
  200|302|307|401) ok "Tunnel smoke OK (HTTP ${TUNNEL_STATUS})" ;;
  *) warn "Tunnel smoke unexpected (HTTP ${TUNNEL_STATUS})" ;;
esac

# ---------------------------------------------------------------------------
bold 7 "Summary"
# ---------------------------------------------------------------------------
cat <<EOF

  Public:        ${PUBLIC_HOSTNAME}
  Health:        ${PUBLIC_HOSTNAME}/health  (or http://127.0.0.1:${LOCAL_PORT}/health on box)
  Deployed SHA:  ${DEPLOY_SHA}
  Running SHA:   ${RUNNING_SHA}
  Version:       ${RUNNING_VER}

  SSH:           ssh -i ${HETZNER_SSH_KEY} ${SSH_TARGET}
  Logs:          ssh ${SSH_TARGET} 'cd ${REPO_DIR} && ${REMOTE_COMPOSE} logs -f scp'
  Status:        ssh ${SSH_TARGET} 'cd ${REPO_DIR} && ${REMOTE_COMPOSE} ps'
  Restart:       ssh ${SSH_TARGET} 'cd ${REPO_DIR} && ${REMOTE_COMPOSE} restart scp'

  Verification (you):
    curl -sk -o /dev/null -w "%{http_code}\\n" ${PUBLIC_HOSTNAME}/health
    curl -sk ${PUBLIC_HOSTNAME}/health | python3 -m json.tool

EOF
ok "Deploy complete."
