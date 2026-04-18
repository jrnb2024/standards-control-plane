# Deployment Runbook

This document is the runtime contract for **Standards Control Plane** (`standards-control-plane`) when used as a shared human-facing app and API.

**Deployment target**: `https://scp.brokapps.ai` (shared) / `https://scp-dev.brokapps.ai` (local dev tunnel)  
**Port**: `3787`  
**Control Tower OAuth audience**: `scp` (shared) / `scp-dev` (dev)

## 1. Overview

Standards Control Plane serves:

- the browser frontend at `/`
- the onboarding guide at `/docs/adoption`
- health and status integration at `/health` and `/status-app/health`
- consult and audit APIs at `/consult` and `/audit`

Browser access should be protected with Control Tower OIDC. Machine callers can keep legacy bearer auth enabled during rollout.

## 2. Control Tower pattern

SCP should follow the same estate pattern as docs-agent and the other Control Tower-integrated apps:

- a single shared Control Tower at `https://control-tower.brokapps.ai`
- app-specific OAuth audiences for environment isolation
- local review via a Cloudflare dev tunnel on a `.brokapps.ai` hostname so CT cookies work

Canonical auth endpoints:

```text
Base:      https://control-tower.brokapps.ai
JWKS:      https://control-tower.brokapps.ai/api/v1/.well-known/jwks.json
Authorize: https://control-tower.brokapps.ai/api/v1/auth/authorize
Token:     https://control-tower.brokapps.ai/api/v1/auth/token
```

## 3. One-time Control Tower registration

Control Tower must register these OAuth clients:

```python
"scp": {"redirect_uris": [
    "https://scp.brokapps.ai/auth/callback",
    "http://localhost:3787/auth/callback",
]},
"scp-dev": {"redirect_uris": [
    "https://scp-dev.brokapps.ai/auth/callback",
    "http://localhost:3787/auth/callback",
]},
```

Control Tower CORS should also allow:

```text
https://scp.brokapps.ai
https://scp-dev.brokapps.ai
```

## 4. Environment variables

Start from [`.env.example`](../.env.example).

| Variable | Dev tunnel | Shared / staging |
| --- | --- | --- |
| `PORT` | `3787` | `3787` |
| `ENV` | `development` | `production` |
| `AUTH_ENABLED` | `true` | `true` |
| `CT_BASE_URL` | `https://control-tower.brokapps.ai` | `https://control-tower.brokapps.ai` |
| `CT_JWKS_URL` | `.../.well-known/jwks.json` | `.../.well-known/jwks.json` |
| `CT_APP_ID` | `scp-dev` | `scp` |
| `PUBLIC_BASE_URL` | `https://scp-dev.brokapps.ai` | `https://scp.brokapps.ai` |

## 5. Local development

Use the dev tunnel rather than plain localhost when testing login:

```bash
cd /Users/amplience/Projects/standards-control-plane
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
AUTH_ENABLED=true CT_APP_ID=scp-dev PUBLIC_BASE_URL=https://scp-dev.brokapps.ai \
  standards-control-plane serve --host 0.0.0.0 --port 3787
```

Then expose it through the shared dev tunnel:

```bash
cloudflared tunnel route dns brokapps-dev scp-dev.brokapps.ai
cat >/tmp/scp-cloudflared-dev.yml <<'EOF'
tunnel: brokapps-dev
credentials-file: /Users/amplience/.cloudflared/34f6b04e-2116-4e3f-9343-cf032781480a.json
ingress:
  - hostname: scp-dev.brokapps.ai
    service: http://127.0.0.1:3787
  - service: http_status:404
EOF
cloudflared tunnel --config /tmp/scp-cloudflared-dev.yml run brokapps-dev
```

Expected local review URL:

```text
https://scp-dev.brokapps.ai
```

Temporary local ingress on the shared named tunnel is enough for smoke testing, but it can be intermittent if other active `brokapps-dev` connectors do not carry the same `scp-dev` hostname rule. For deterministic local review, add the ingress rule to the canonical dev tunnel config on the machine that owns the tunnel session.

## 6. Docker / staging runtime

The repo ships both local and staging compose contracts:

```bash
docker compose up -d --build
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d --build
```

Staging host contract:

- checkout path: `/home/webapp/apps/standards-control-plane`
- compose file: `/home/webapp/apps/standards-control-plane/docker-compose.staging.yml`
- backend port: `3787`
- Cloudflare hostname: `scp.brokapps.ai`

Suggested staging steps:

```bash
ssh mapp-staging
cd /home/webapp/apps/standards-control-plane
git pull origin main
cp .env.staging.example .env.staging
# edit .env.staging for shared/staging values:
#   ENV=production
#   CT_APP_ID=scp
#   PUBLIC_BASE_URL=https://scp.brokapps.ai
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d --build
docker compose -f docker-compose.staging.yml --env-file .env.staging logs -f scp
```

## 7. Cloudflare tunnel configuration

Dev tunnel ingress:

```yaml
- hostname: scp-dev.brokapps.ai
  service: http://127.0.0.1:3787
```

Shared tunnel ingress on staging:

```yaml
- hostname: scp.brokapps.ai
  service: http://127.0.0.1:3787
```

DNS routes:

```bash
cloudflared tunnel route dns brokapps-dev scp-dev.brokapps.ai
cloudflared tunnel route dns brokapps scp.brokapps.ai
```

## 8. Smoke tests

Once deployed:

```bash
curl -fsS http://127.0.0.1:3787/health
curl -fsS http://127.0.0.1:3787/status-app/health | jq '.auth'
curl -I https://scp-dev.brokapps.ai
curl -I https://scp.brokapps.ai
```

Expected behaviour:

- `/health` returns the SVC-002 shape: `{"status":"healthy","version":"<package-version>","checks":{}}`
- `/status-app/health` reports `auth.mode` as `oidc` or `oidc+bearer`
- `/` redirects to `/auth/login` when browser auth is enabled and no session exists

## 9. Notes

- The service uses the vendored `ct-auth` Python SDK for JWT validation and the BFF helper routes under `/api/auth/*`.
- The browser callback remains service-owned at `/auth/callback` so the built-in UI can complete the redirect flow cleanly.
