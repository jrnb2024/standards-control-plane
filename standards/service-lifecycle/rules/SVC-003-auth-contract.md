# SVC-003 — Service Must Declare Auth Contract

**Domain:** service-lifecycle
**Version:** 1.0.0
**Status:** active
**Severity default:** high

Every service registered in `services.yml` must include an `auth_contract`
block under its `runtime_contract`. The contract declares which auth modes
the service accepts and carries the metadata required by each declared mode.

The approved mode set is **closed**. Services may declare any combination of
the four modes below. Custom modes are not permitted; a new mode requires a
standards change.

Presence of the `auth_contract` block is enforced by the service-lifecycle
evaluator, not by the runtime-contract schema's `required` list. This matches
SVC-001's pattern (the evaluator enforces block presence; the schema describes
block shape when the block is present).

## Approved modes

| Mode ID | Shape | Use |
|---------|-------|-----|
| `mode.user_oidc` | Control Tower OIDC + JWKS verification + `aud=<app-id>` claim + httpOnly cookie session | Browser flows |
| `mode.service_rs256` | S2S RS256 + required `aud` claim matching target app-id from `services.yml` + JWKS verification | Service-to-service (target state; replaces HS256) |
| `mode.api_key` | CT-issued agent/machine key, revocable via Control Tower | Agents, CLIs, machine callers |
| `mode.bearer_legacy` | Raw bearer token | **Deprecated.** Requires a per-service migration waiver with an explicit close date. |

The shape of `mode.user_oidc` is the estate pattern for browser-facing
services. Per the CT 2026-04-18 estate bearer-token audit
(`control-tower/governance/docs/notifications/SCP-FOLLOWUP-2026-04-18-bearer-token-audit.md`),
the pure-CT-SSO cohort is returns-intelligence, size-allocation,
visual-shopping, living-canvas, agentic-commerce-pac, doc-agent, and
estate-dashboard. A further cohort (fashion-labelling, brand-dna, acc,
market-feed) runs CT-SSO alongside legacy S2S-bearer — the CT-SSO half
matches the same pattern.

The reference implementation in this repo is commit `66ba8a4` —
`src/standards_control_plane/service.py` (vendored `ct_auth` wheel,
`CT_JWKS_URL`, `CT_APP_ID`, httpOnly cookie session via
`ct_auth.bff.create_bff_routes`).

## Required declaration

Each entry in `auth_contract.accepted_modes` must name a mode from the approved
set and include the metadata required by that mode:

- `mode.user_oidc` — `audience`, `jwks_url`
- `mode.service_rs256` — `audience`, `jwks_url`
- `mode.api_key` — `issuer` (e.g. `control-tower`)
- `mode.bearer_legacy` — `deprecation_close_date`, `waiver_ref`

`audience` is a bare literal app-id string matching the service's key in
`services.yml` (e.g. `scp`, `scp-dev`, `pim`). It is not a URI. `jwks_url` is
the full URL of the JWKS endpoint and is the authoritative expected value that
the service's implementation must verify against.

`waiver_ref` is the `waiver_id` of a waiver record in
`output/findings/waivers.json`. The waiver captures the migration plan and the
authorising owner for the `mode.bearer_legacy` exception.

A service may declare more than one mode. Example: Standards Control Plane
itself runs with both CT OIDC (browser flows) and a raw bearer token (machine
callers during the deprecation window), so its declaration is
`accepted_modes: [{mode: mode.user_oidc, …}, {mode: mode.bearer_legacy, …}]`.

See `schemas/auth-contract.schema.json` for the full contract.

## Signals

Static signals (auto-checked from `services.yml` and service source files):

- service entry in `services.yml` has no `auth_contract` under `runtime_contract`
- `auth_contract` value is not a mapping
- `auth_contract.accepted_modes` is empty or not a list
- an `accepted_modes` entry is not a mapping, or its `mode` value is not a
  string
- an accepted-mode entry carries a field the auth-contract schema does not
  allow (catches typos in required-field names such as `audeince` for
  `audience`)
- an accepted-mode entry names a mode outside the approved set
- an accepted-mode entry is missing the metadata required by its mode
- `mode.user_oidc` or `mode.service_rs256` `audience` is not a bare app-id
  matching `^[a-z][a-z0-9-]*$`
- `mode.user_oidc` or `mode.service_rs256` `jwks_url` is not a valid http(s)
  URL
- `mode.bearer_legacy` entry is present without `deprecation_close_date` or
  `waiver_ref`
- `mode.bearer_legacy` `deprecation_close_date` is malformed (not a YYYY-MM-DD
  date)
- `mode.bearer_legacy` `deprecation_close_date` is on or before the evaluator
  run date (date-in-past comparison is evaluator logic, not schema validation)
- `mode.bearer_legacy` `waiver_ref` does not resolve to a known `waiver_id` in
  `output/findings/waivers.json` (skipped when no waivers are registered)
- the same mode is declared twice in `accepted_modes`
- implementation source code accepts a mode that is not declared in
  `auth_contract` (detected by code-pattern scan — e.g. a
  `ControlTowerAuth(...)` instantiation when `mode.user_oidc` is not declared)
- implementation source code contains no handler for a declared mode (detected
  by the absence of the mode's expected code pattern)

Runtime signals (out of scope for the static evaluator; covered by dogfood
and adopter review, matching the SVC-002 pattern):

- implementation actually rejects a request carrying a valid token for a
  declared mode
- implementation actually accepts a request carrying a token for a
  non-declared mode

## Rationale

The estate runs three live token types (CT JWT RS256, service JWT HS256, API
key) and at least one cookie-session browser flow. A single fixed mechanism
breaks machine callers; an open-ended declaration produces drift. A closed
mode set plus an auto-checked declaration gives adopters a bounded choice and
gives the estate a single place to audit conformance.

This rule also anchors the sunset of `mode.bearer_legacy`. Services that still
use raw bearer tokens must declare it explicitly, carry a waiver, and name a
close date. After the close date passes, the auto-check fails.

## Exceptions

- Services with `local.status: planned` are exempt until they reach `ready`,
  consistent with SVC-001.
- OIDC bootstrap paths served by any service declaring `mode.user_oidc` are
  exempt from the declared-mode check: `/health`, `/status-app/health`,
  `/auth/login`, `/auth/callback`, `/auth/logout`, `/auth/me`, `/api/auth/*`,
  `/.well-known/*`. These paths exist to establish or project the auth
  session itself and cannot depend on it.

## Schema

`schemas/auth-contract.schema.json`
