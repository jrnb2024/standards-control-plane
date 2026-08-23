#!/usr/bin/env bash
# Canonical docker-host deploy — standards-control-plane (scp).
# Idempotent, hostname-guarded, health-gated by OBSERVED EFFECT:
#   /health must return HTTP 200 AND a body with status=="healthy".
#
# Bring-up captured from the docker-host running config (2026-08-22):
#   base compose + the tailnet-bind overlay.
# The overlay is MANDATORY: without docker-compose.docker-host.yml, scp binds
# 0.0.0.0:3787 (LAN-exposed on a firewall-less box). With it, scp binds
# 100.84.218.122:3787 only — so 127.0.0.1 binds NOTHING and must not be polled.
set -Eeuo pipefail
cd "$(dirname "$0")/.."

[[ "$(hostname)" == "docker-host" ]] || {
  echo "refusing: this deploy targets docker-host (got $(hostname))" >&2; exit 1; }
[[ -f .env ]] || echo "warn: .env missing — scp env (AUTH_ENABLED/CT_APP_ID/CT_* ) falls back to image defaults" >&2

COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.docker-host.yml)
HEALTH_URL="${SCP_HEALTH_URL:-http://100.84.218.122:3787/health}"

echo "[deploy-dev] docker compose up -d --build (base + docker-host overlay)…"
docker compose "${COMPOSE_FILES[@]}" up -d --build

echo "[deploy-dev] gating on ${HEALTH_URL} (HTTP 200 + status=healthy)…"
deadline=$((SECONDS + 240))
code="" body=""
while (( SECONDS < deadline )); do
  resp="$(curl -s -w $'\n%{http_code}' --max-time 5 "$HEALTH_URL" 2>/dev/null || true)"
  code="${resp##*$'\n'}"
  body="${resp%$'\n'*}"
  if [[ "$code" == "200" ]] && grep -Eq '"status"[[:space:]]*:[[:space:]]*"healthy"' <<<"$body"; then
    echo "[deploy-dev] OK: HTTP ${code}, body=${body}"
    exit 0
  fi
  sleep 5
done

echo "[deploy-dev] FAILED to reach healthy within deadline (last: HTTP ${code:-?}, body=${body:-<none>})" >&2
docker compose "${COMPOSE_FILES[@]}" logs --tail=60 scp || true
exit 1
