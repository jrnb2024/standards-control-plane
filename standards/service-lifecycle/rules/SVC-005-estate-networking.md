# SVC-005 — Estate Networking Uses the One Canonical Cloudflared Tunnel Recipe

**Domain:** service-lifecycle
**Version:** 1.0.0
**Status:** active
**Severity default:** medium

> **Enforcement posture: ADVISORY-CONSULT.** Tunnel configuration is host-side
> (`~/.cloudflared` on dev, `/etc/cloudflared` on the Hetzner staging box), not
> in any adopter repo tree — there is nothing in an adopter PR to lint. This rule
> authors no Rego; it is the consultable recipe + the canonical-ref pointer.

Every estate app reaches the outside world through the SAME cloudflared tunnel
setup. **SVC-004** covers DEPLOY (Docker container + `scripts/deploy-{dev,staging}.sh`
+ Control Tower SSO); SVC-005 fills the NETWORKING gap SVC-004 left open — how an
app gets its `*.brokapps.ai` hostname. It is the networking member of the
canonical-source standards family (WP-SCP-037).

## The canonical recipe

### Dev — tunnel `brokapps-dev`

Config at `~/.cloudflared/config.yml` (+ `cert.pem` + `<UUID>.json`). Add an
ingress rule **before** the 404 catch-all, then restart the tunnel:

```yaml
ingress:
  # ... existing hostnames ...
  - hostname: <app>-dev.brokapps.ai
    service: http://localhost:<port>
  # 404 catch-all MUST stay last:
  - service: http_status:404
```

The app is then live at `https://<app>-dev.brokapps.ai`.

### Staging — tunnel `mapp-staging-hetzner`

UUID `6d21b62e-ce85-4332-9d59-329e52d1442b`; config on the Hetzner box at
`/etc/cloudflared/config.yml`. Add a DNS CNAME `<app>.brokapps.ai →
<UUID>.cfargotunnel.com` plus the matching ingress rule. The app is then live at
`https://<app>.brokapps.ai`.

## Canonical references (do NOT re-derive)

- `control-tower/docs/runbooks/staging-bring-up.md` — the staging tunnel runbook.
- `control-tower/infra/cloudflare-tunnel/` — the 01–04 setup scripts +
  `scripts/staging-bring-up.sh`.

Consult these before adding a hostname; do not hand-roll a bespoke ingress or a
second tunnel.

## No production tier

Hetzner is staging (GOV-005 — the estate has no production tier). The staging
tunnel is the estate's outermost surface; there is no separate prod tunnel to
document. When a first real customer with an SLA arrives, a managed-DNS/prod
tunnel is a future standards change, not a gap in this rule.

## Adoption triggers

- **T1** — the app is first stood up on a `*.brokapps.ai` hostname ("stand up
  the app" = deploy to the tunnel, not localhost).
- **T2** — the app moves from dev to staging (add the staging CNAME + ingress).

## Signals

The consult signals are enumerated in this rule's `index.json` entry (an app on
localhost instead of a tunnel hostname; a bespoke ingress or a second tunnel; a
dev hostname added after the 404 catch-all; a staging hostname with no CNAME to
the tunnel UUID). Because tunnel config is host-side, not in any adopter tree,
these are consult-only guidance served via `consult_rules` — there is no
enforcing Rego.

## Rationale

"Stand up the app" means deploy to the brokapps.ai tunnel, not localhost — but
without an authored recipe each app hand-rolls a bespoke ingress or spins up a
second tunnel, and the estate's outermost surface fragments. SVC-004 already
names the deploy half (Docker + deploy scripts + CT SSO) but stops at the host;
SVC-005 names the networking half so the `*.brokapps.ai` hostname is added the
one canonical way. It is advisory because the tunnel config lives on the host
(`~/.cloudflared`, Hetzner `/etc/cloudflared`), not in any adopter repo tree —
there is nothing in an adopter PR to gate, only a recipe to consult.

## Cross-references

- **SVC-004** — deploy recipe (Docker + deploy scripts + CT SSO). SVC-004 +
  SVC-005 together are the full dev/staging bring-up.
- **SVC-ADOPT-001** — registration (touchpoint 1 = stood up on a brokapps.ai
  hostname pairs with this rule).
- **GOV-005** — no production tier (Hetzner is staging).
- **`reference_estate_canonical_sources.md`** — the estate canonical map
  (networking → the brokapps cloudflared tunnels).
