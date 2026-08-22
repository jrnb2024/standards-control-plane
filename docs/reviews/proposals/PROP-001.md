---
adjudication_status: accepted
accepted_as: SVC-004
accepted_at: 2026-06-28
accepted_note: adjudicated into standards/<domain>/rules/SVC-004-*.md + index.json; live via consult_rules
expected_review_date: null
queued_at: 2026-06-27T22:19:44Z
---
> NOTE: WP-SCP-022-proposal-queue adjudication workflow is not yet live;
> proposals queue until adjudication ships. Status updates via
> GitHub issue on this branch (proposals/PROP-001). See
> docs/plans/WP-SCP-022-implementation-programme-plan.md §12.

<!-- proposal_metadata: {"affected_repos":["jrnb2024/kg-studio","jrnb2024/mapp-estate-dashboard","jrnb2024/control-tower","jrnb2024/linkedin-content-os","jrnb2024/acc"],"caller_id":"stdio:30251:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server","mcp_origin":true,"proposal_hash":"b37ab8679490120ab2e798b4366adf41c11c03fac1db60937918ac226734b5ef","rule_id":null,"signing_key_id":"428dfee16bc954ad"} -->

# PROP-001: SVC-004 (candidate): Dev/staging deploy must follow the canonical Docker + tunnel + CT-SSO recipe

## Proposal Envelope
- mcp_origin: true
- caller_id: stdio:30251:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server
- signing_key_id: 428dfee16bc954ad

## Affected Repositories
- jrnb2024/kg-studio
- jrnb2024/mapp-estate-dashboard
- jrnb2024/control-tower
- jrnb2024/linkedin-content-os
- jrnb2024/acc

## Rule Context
null

## Proposal Body
## SVC-004 (candidate) — Canonical dev/staging deploy recipe

**Status:** proposed (new rule for the `service-lifecycle` domain). Elevates an existing but repo-local decision (`DEC-PIM-017`: no bare-metal) and the de-facto `scripts/deploy-{dev,staging}.sh` pattern into an estate-wide, consultable standard. Today the deploy method is decided in one repo and copied as scripts; it is not consultable estate-wide, so every Claude Code session re-derives it. This rule makes it the single canonical recipe.

**Summary.** Every estate service deploys to dev and staging the same way, fronted by Control Tower SSO, with control-tower `services.yml` as the single source of truth for port, health path, and auth contract. There is no production tier (Hetzner = staging; AWS/`*.brokapps.ai` boxes labelled 'production' are staging/demo).

**Dev (operator's machine).**
- Runtime is a Docker container, NOT a host/bare-metal process (`DEC-PIM-017`).
- Started by an idempotent `scripts/deploy-dev.sh` (safe to re-run; rebuilds the image; preflights Docker + the local `../control-tower` checkout for the `services.yml` mount).
- Published on `127.0.0.1:<port>`, fronted by the local `brokapps` cloudflared tunnel at `<service>-dev.brokapps.ai`.
- The script may stop a stray bare-metal process on the port, but must NEVER touch Colima / the docker daemon / the VM port-forwarder.

**Staging (Hetzner `mapp-staging-1`).**
- `scripts/deploy-staging.sh` is a thin, discoverable wrapper over the canonical idempotent infra script (`infra/hetzner-staging/*-deploy-*.sh`); it deploys the current `origin/main`.
- Brought up with the canonical multi-file compose stack (`docker-compose.yml` + the `infra/hetzner-staging` override).
- Live at `<service>.brokapps.ai` (or `<service>-staging.brokapps.ai`), behind CT SSO; requires the staging SSH key.

**Both tiers.**
- The published port + health path MUST match the service's `services.yml` entry (see SVC-001 runtime_contract, SVC-002 health endpoint).
- Public access is the `brokapps` cloudflared tunnel; auth is CT SSO (see SVC-003 auth_contract). No new public surface may bypass the tunnel or CT SSO.
- Deploy is idempotent and safe to re-run after any code change.

**Signals (audit).**
- no `scripts/deploy-dev.sh` / `scripts/deploy-staging.sh`, or it is not idempotent
- deploy doc/script describes a host/bare-metal runtime (violates `DEC-PIM-017`)
- published port or health path disagrees with `services.yml`
- a new public surface not fronted by the brokapps cloudflared tunnel / not behind CT SSO
- a deploy path that kills Colima / the docker daemon / the VM port-forwarder

**applies_to:** `scripts/deploy-*.sh`, `docker-compose*.yml`, `infra/**/deploy*.sh`, `Dockerfile`, `services.yml`
**severity_default:** high   **scope:** all   **exceptions:** services with `local.status: planned`

**Open reconciliation before acceptance:** confirm the exact `DEC-PIM-017` wording (currently PIM-repo-local, not yet federated to SCP decisions) and the staging hostname convention (bare `<service>.brokapps.ai` vs `<service>-staging.brokapps.ai` — both are in use).
