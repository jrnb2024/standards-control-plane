# SVC-004 — Dev/Staging Deploy Must Follow the Canonical Recipe

**Domain:** service-lifecycle  
**Version:** 1.0.0  
**Status:** active  
**Severity default:** high

Every estate service deploys to dev and staging the same way, fronted by Control
Tower SSO, with control-tower `services.yml` as the single source of truth for port,
health path, and auth contract. There is no production tier (Hetzner is staging;
boxes labelled 'production' are staging/demo). This rule elevates the repo-local
no-bare-metal decision (`DEC-PIM-017`) and the de-facto `scripts/deploy-{dev,staging}.sh`
pattern into an estate standard so sessions do not re-derive the deploy method.

Dev: a Docker container (not a host process) started by an idempotent
`scripts/deploy-dev.sh`, published on `127.0.0.1:<port>`, fronted by the local
`brokapps` cloudflared tunnel at `<service>-dev.brokapps.ai`. Staging: an idempotent
`scripts/deploy-staging.sh` (thin wrapper over the Hetzner infra script) that deploys
`origin/main` with the canonical compose stack (`docker-compose.yml` + the
`infra/hetzner-staging` override) at `<service>.brokapps.ai`, behind CT SSO. The
published port and health path must match the service's `services.yml` entry
(SVC-001, SVC-002); auth is CT SSO (SVC-003).

## Signals

- no `scripts/deploy-dev.sh` / `scripts/deploy-staging.sh`, or it is not idempotent
- a deploy doc or script that describes a host / bare-metal runtime (violates DEC-PIM-017)
- published port or health path disagreeing with `services.yml`
- a new public surface not fronted by the `brokapps` cloudflared tunnel, or not behind CT SSO
- a deploy path that stops Colima, the docker daemon, or the VM port-forwarder

## Rationale

The deploy method is decided (`DEC-PIM-017`) and scripted, but it was not consultable
estate-wide, so every session re-derived it. Codifying the canonical recipe keeps dev
and staging uniform, prevents bare-metal runtimes that shadow Docker ports and leak via
the tunnel, and keeps `services.yml` the single source of truth.

> Open reconciliation: the exact `DEC-PIM-017` wording is currently PIM-repo-local
> (not yet federated to SCP decisions), and both `<service>.brokapps.ai` and
> `<service>-staging.brokapps.ai` staging hostname conventions are in use.
