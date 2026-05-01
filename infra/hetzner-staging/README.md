# Standards Control Plane — Hetzner staging

Canonical staging deploy. This replaces the legacy `docker-compose.staging.yml` (which uses `network_mode: host`, the old AWS pattern). The override here layers on the dev compose with bridge networking + 127.0.0.1 port binding for the cloudflared sidecar.

## Files

| File | Purpose |
|---|---|
| `docker-compose.staging-hetzner.yml` | Override layered on the repo-root `docker-compose.yml`. Sets `ENV=staging`, public CT URLs, binds port 3787 to 127.0.0.1. |
| `README.md` | This file. |

## Prerequisites

| Prereq | Where |
|---|---|
| Cloudflare tunnel route `scp.brokapps.ai → http://localhost:3787` | `/etc/cloudflared/config.yml` on hetzner-staging |
| Cloudflare DNS for `scp.brokapps.ai` | Cloudflare side (CNAME to tunnel) |
| Control Tower running on the box | `docker ps \| grep ct-backend` from on-box |

## Deploy procedure

```bash
ssh hetzner-staging

# First time: clone (Hetzner pattern, no /apps/ segment)
cd /home/webapp
git clone https://github.com/jrnb2024/standards-control-plane-.git standards-control-plane
cd standards-control-plane

# Generate .env (one-time)
cat > .env <<'EOF'
PORT=3787
ENV=staging
AUTH_ENABLED=true
CT_BASE_URL=https://control-tower.brokapps.ai
CT_JWKS_URL=https://control-tower.brokapps.ai/api/v1/.well-known/jwks.json
CT_APP_ID=scp
PUBLIC_BASE_URL=https://scp.brokapps.ai
EOF
chmod 600 .env

# Subsequent deploys: pull
git fetch --prune origin && git checkout main && git pull --ff-only

# Bring up with the override
docker compose \
  -f docker-compose.yml \
  -f infra/hetzner-staging/docker-compose.staging-hetzner.yml \
  up -d --build

# Verify
docker compose ps
curl -fsS http://127.0.0.1:3787/health
curl -fsS https://scp.brokapps.ai/health
```

## Why an override (not the existing docker-compose.staging.yml)

The existing `docker-compose.staging.yml` uses `network_mode: host` and `.env.staging`. That was correct for the legacy AWS deploy where the host bound services directly. On Hetzner the cloudflared sidecar forwards from `127.0.0.1:<port>`, which works cleanly with bridge networking + explicit port bindings. Following the estate convention (control-tower, brand-dna, dashboard) keeps deploy mechanics consistent.

The legacy `docker-compose.staging.yml` is left in tree as historical record; new staging deploys use this override.
