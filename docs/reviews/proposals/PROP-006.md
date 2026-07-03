---
adjudication_status: accepted
accepted_as: SVC-005
decision_ref: D-064
accepted_at: 2026-07-03
accepted_note: adjudicated into standards/service-lifecycle/rules/SVC-005-estate-networking.md + index.json (advisory-consult, no Rego); live via consult_rules. WP-SCP-037 §1c.
expected_review_date: null
queued_at: 2026-07-03T11:11:32Z
---
> NOTE: WP-SCP-022-proposal-queue adjudication workflow is not yet live;
> proposals queue until adjudication ships. Status updates via
> GitHub issue on this branch (proposals/PROP-006). See
> docs/plans/WP-SCP-022-implementation-programme-plan.md §12.

<!-- proposal_metadata: {"affected_repos":["standards-control-plane","control-tower"],"caller_id":"stdio:35116:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server","mcp_origin":true,"proposal_hash":"62ebef21868b3cda97757fb35ed6aa58b5ece70a4d0b359a7b0b7226ad678502","rule_id":"SVC-005","signing_key_id":"428dfee16bc954ad"} -->

# PROP-006: SVC-005 estate-networking — the canonical cloudflared tunnel recipe (dev + staging)

## Proposal Envelope
- mcp_origin: true
- caller_id: stdio:35116:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server
- signing_key_id: 428dfee16bc954ad

## Affected Repositories
- standards-control-plane
- control-tower

## Rule Context
SVC-005

## Proposal Body
## Principle

Every estate app reaches the outside world through the SAME cloudflared tunnel setup. SVC-004 covers DEPLOY (Docker + deploy scripts + CT SSO); SVC-005 fills the NETWORKING gap SVC-004 left open — how the app gets its `*.brokapps.ai` hostname. Advisory-consult (tunnel config isn't lint-able from an adopter PR); the canonical refs live in control-tower. Part of the canonical-source standards family (WP-SCP-037).

## The canonical recipe

**Dev** — tunnel `brokapps-dev` (`~/.cloudflared/config.yml` + `cert.pem` + `<UUID>.json`). Add an ingress `hostname: <app>-dev.brokapps.ai → service: http://localhost:<port>` BEFORE the 404 catch-all rule, then restart the tunnel. The app is then live at `https://<app>-dev.brokapps.ai`.

**Staging** — tunnel `mapp-staging-hetzner` (UUID `6d21b62e-ce85-4332-9d59-329e52d1442b`; Hetzner `/etc/cloudflared/config.yml`). Add a CNAME `<app>.brokapps.ai → <UUID>.cfargotunnel.com` + the matching ingress rule. The app is then live at `https://<app>.brokapps.ai`.

## Canonical references (do NOT re-derive)

- `control-tower/docs/runbooks/staging-bring-up.md` — the staging tunnel runbook.
- `control-tower/infra/cloudflare-tunnel/` — the 01–04 setup scripts + `scripts/staging-bring-up.sh`.

## Enforcement posture

**Advisory-consult** (no Rego). Tunnel config is host-side (`~/.cloudflared`, Hetzner `/etc/cloudflared`), not in any adopter repo tree — there is nothing in the adopter PR to lint. The rule is the consultable recipe + canonical-ref pointer so a new app adds its hostname the one canonical way instead of inventing a bespoke ingress. SVC-004 (deploy) + SVC-005 (networking) together cover the full dev/staging bring-up.

## Relationship to GOV-005 / no-prod

Hetzner is staging (GOV-005 — no production tier). The staging tunnel is the estate's outermost surface; there is no separate prod tunnel to document.
