# WP-ESC-007 — Authenticated Estate read-only SCP facade

**Programme:** PLAN-CT-ESTATE-CONTEXT-001
**Repository:** standards-control-plane
**Status:** READY FOR TDD IMPLEMENTATION
**Mode:** shadow/read-only; disabled by default
**Base SHA:** `500ec52caa02ebec24f9befcc0c7a313a3cb6fd5`
**Branch:** `feat/estate-context-phase0`
**Worktree:** `/Users/amplience/Projects/standards-control-plane-wt-estate-phase0`
**Writer:** `codex:/root/r8_quality_review`
**Depends on:** WP-ESC-004 identity contract; implementation remains disabled until CT can issue the frozen principal

## 1. Objective and authority limit

Add an opt-in Estate profile to SCP's existing REST and MCP surfaces. The profile exposes
standards evidence only. It cannot propose, mutate files, create branches, admit execution,
merge, deploy, or administer anything. Existing REST behavior and the full legacy MCP profile
remain available when the Estate feature flag/profile is not selected.

The feature flag is `SCP_ESTATE_READ_ONLY_ENABLED`; its default is `false`.

## 2. Frozen REST authentication contract

Selecting the Estate profile requires startup configuration to satisfy all of these conditions:

- `AUTH_ENABLED=true`;
- no legacy static bearer token is configured;
- `CT_APP_ID=scp`;
- `CT_ISSUER` is present and non-empty, providing the environment-pinned exact issuer.

Every protected REST request is first signature/expiry/audience validated by the CT auth SDK,
then must match this exact principal contract:

| Claim | Required value |
|---|---|
| `iss` | exact `CT_ISSUER` value |
| `aud` | exactly `scp` (a string or singleton list only) |
| `sub` | `sa:acc-estate-context` |
| `azp` | `acc` |
| `actor_type` | `service` |
| `scopes` | exactly `['estate:standards:read']` |
| `active_org_id` | non-empty bounded identifier |

No wildcard scope, multi-audience token, user token, cookie-only browser identity, or legacy
bearer credential satisfies this contract.

Each `/registry`, `/consult`, and `/audit` request must also carry the non-empty headers
`X-Estate-Org-ID`, `X-Estate-Workspace-ID`, `X-Estate-Project-ID`, and
`X-Estate-Repository-ID`. The request org must equal `active_org_id`. SCP returns an additive
Estate response envelope containing the exact verified request binding and the read-only result.
The envelope explicitly records `action_authority: false`.

## 3. MCP profile

`ScpMcpServer(profile='legacy')` remains the default and registers the existing full surface.
The new `estate-read-only` profile is selectable only when
`SCP_ESTATE_READ_ONLY_ENABLED=true`. It registers these tools:

- `consult_rules`
- `check_waiver`
- `list_open_decisions`
- `check_finding`
- `resolve_domain`
- `consult_scorecard`

It does not register `propose` or `audit_changed`; therefore it accepts neither proposal writes
nor caller-selected/external repository roots. Committed-state resources remain read-only and are
retained. Stdio is a trusted-outer transport: this profile does not claim that stdio itself is an
authentication boundary.

## 4. Truthful health

`/health` and `/status-app/health` derive their status from the required committed artifacts and
Estate-profile configuration. Missing artifacts report degraded status. The Estate profile
reports its enabled/authenticated state and never reports healthy after an invalid configuration,
because invalid configuration fails application startup.

## 5. TDD acceptance matrix

1. Startup rejects Estate mode with auth disabled, a legacy bearer, non-`scp` app ID, or missing
   `CT_ISSUER`.
2. A valid CT-signed token matching every frozen claim and every binding header reaches each
   read endpoint and receives the exact binding echo plus `action_authority: false`.
3. Wrong issuer, multi/wrong audience, subject, `azp`, actor type, scopes, missing
   `active_org_id`, missing binding header, or org mismatch is rejected fail-closed.
4. Legacy mode tests remain green.
5. Legacy MCP listing is unchanged.
6. Estate MCP listing is the six-tool allowlist and excludes `propose` and `audit_changed`.
7. CLI refuses the Estate MCP profile while the feature flag is off.
8. Missing required artifacts produce degraded health in both health surfaces.

## 6. Exact implementation scope

- `src/standards_control_plane/service.py`
- `src/standards_control_plane/mcp_server/server.py`
- `src/standards_control_plane/mcp_server/tools.py`
- `src/standards_control_plane/mcp_server/cli.py`
- `schemas/status-app-health.schema.json`
- `tests/test_service_api.py`
- `tests/scp_mcp/test_stdio_handshake.py`
- `tests/scp_mcp/test_cli_help.py`
- this brief and `CHANGESET-ESC-007.json`

No policy rule, adopter instruction file, WP-ESC-012 marker, deployment configuration, or
external repository is in scope.

## 7. Compatibility, rollback, and handoff

Compatibility order is CT WP-ESC-004 issuance first, then SCP profile enablement, then ACC
consumption. Until that order is satisfied the SCP flag remains off. Rollback is to set
`SCP_ESTATE_READ_ONLY_ENABLED=false` and select the legacy MCP profile; no stored state or data
migration is introduced. The primary SCP checkout and its dirty/untracked user files remain
read-only and are never staging sources for this work package.
