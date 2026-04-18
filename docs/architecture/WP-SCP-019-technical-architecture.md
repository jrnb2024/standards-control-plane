# TechnicalArchitecture — WP-SCP-019 Service Auth Contract (SVC-003)

**Work Package:** `WP-SCP-019`
**Version:** 0.1
**Status:** Draft
**Date:** 2026-04-18

## 1. Objective

Stand up SVC-003 as a declare-a-contract rule, wire the service-lifecycle
evaluator for SVC-001/002/003, and integrate it into the existing audit path
without forking evaluator runtime.

## 2. Proposed components

### SVC-003 rule

- `standards/service-lifecycle/rules/SVC-003-auth-contract.md`
- Registered in `standards/service-lifecycle/index.json` alongside SVC-001
  and SVC-002.
- Severity default: `high`, scope: `all`.

### Approved-mode schema

- `schemas/auth-contract.schema.json`
- Closed enum of mode IDs: `mode.user_oidc`, `mode.service_rs256`,
  `mode.api_key`, `mode.bearer_legacy`.
- Per-mode required metadata expressed via conditional subschemas.
- Referenced from `schemas/runtime-contract.schema.json` via an
  `auth_contract` property so SVC-001's existing contract block composes
  cleanly with SVC-003.

### `evaluators/service_lifecycle.py` (019B)

- New evaluator module matching the shape of existing evaluators under
  `src/standards_control_plane/evaluators/`.
- Covers SVC-001 (runtime contract presence/shape), SVC-002 (health endpoint
  schema), and SVC-003 (auth contract presence + declared modes conform to
  approved set + required per-mode metadata present + declared-mode vs.
  implementation coherence).
- Input is the normalised project area plus the service manifest. No network
  calls; signal detection is static file scanning, which includes both
  schema validation of declarative blocks (`services.yml`, health endpoint
  response fixtures where available) and code-pattern scans of the
  service's source tree (e.g. detecting `ControlTowerAuth(...)`
  instantiation, raw-bearer comparisons, `X-API-Key` handlers). Runtime
  probes are out of scope for the static evaluator, consistent with how
  SVC-002 is evaluated today.

### Audit CLI integration (019C)

- Extend the existing audit assembly so the service-lifecycle evaluator
  runs alongside governance and architecture when the `service-lifecycle`
  domain is selected.
- No new evaluator runtime path; reuse the existing audit result contract.

### Fixture corpus

Fixtures live at the repo-top-level `fixtures/svc-*/` directory, one fixture
per signal (flat layout to keep extract-scope calls simple). The corpus
covers at least:

- positive cases: single-mode conformant, all-four-modes conformant, `mode.service_rs256` conformant
- missing `auth_contract`
- unknown mode ID
- `mode.bearer_legacy` without `deprecation_close_date` or `waiver_ref`
- `mode.bearer_legacy` with `deprecation_close_date` in the past
- `mode.bearer_legacy` with a malformed `deprecation_close_date`
- `mode.user_oidc` without `audience` (and `audience` that fails the bare-
  app-id pattern)
- `mode.user_oidc` with a malformed `jwks_url`
- `mode.api_key` without `issuer`
- duplicate `mode` entries in `accepted_modes`
- type-shape violations (`auth_contract` not a mapping; `accepted_modes` not
  a list; entry not a mapping; `mode` not a string)
- implementation code pattern mismatching declared modes (declares only
  `mode.user_oidc` but source decodes tokens with RS256; declares
  `mode.service_rs256` but code lacks the marker)
- SVC-001 coverage: missing `runtime_contract`, missing required fields,
  `python-venv` without `venv_path`, `working_dir` pointing at a
  non-existent directory
- SVC-002 coverage: declared healthcheck path with no matching handler in
  the scanned source
- multi-service yaml mixing planned + ready siblings
- malformed YAML
- bare-map (no top-level `services:` key) — rejected as malformed

### Exempt paths

SVC-003's rule text enumerates OIDC bootstrap paths (`/health`,
`/status-app/health`, `/auth/*`, `/api/auth/*`, `/.well-known/*`) as exempt
from the declared-mode check. That exemption is **runtime-shaped** — it
concerns which endpoints require the declared mode at request time, not
which source files exist at static-scan time. The static evaluator
therefore does not encode per-path exemption logic; adopters who see a
genuine false positive from the impl-pattern scan can waiver it against
the rule's documented exempt-path list, and future runtime conformance
tooling can enforce the exemption directly.

### ADOPT-001 §11 rewrite (019E)

- Replace the current `--auth-token` default with guidance pointing at
  `mode.api_key` for machine callers and `mode.user_oidc` for browsers.
- Cite commit `66ba8a4` as the `mode.user_oidc` reference implementation.
- Document the `--auth-token` deprecation close date 2026-06-30 and the
  waiver shape that covers the transition window.

## 3. Composition with SVC-001

SVC-001 requires every service to declare a `runtime_contract` under its
`local` environment. SVC-003 adds an `auth_contract` block inside that same
`runtime_contract` so the declaration stays in one place and so the
service-lifecycle evaluator can read everything it needs from the existing
`services.yml` scope without a parallel manifest.
