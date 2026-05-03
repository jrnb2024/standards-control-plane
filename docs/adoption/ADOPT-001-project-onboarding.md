# ADOPT-001 — Standards Control Plane Project Onboarding

**Version:** 0.1
**Status:** Active
**Date:** 2026-04-12

## 1. Purpose

This is the single onboarding brief for any repo that wants to adopt the
Standards Control Plane.

If a team asks, "What do we need to change to use SCP in our repo, wire it into
CI, and update our governance docs?", point them here.

The goal is not to redesign the adopter repo. The goal is to plug SCP into the
repo's existing delivery process in a way that is:

- structured
- reviewable
- advisory first
- easy to run locally and in CI
- compatible with stronger existing repo governance

Repos that host an HTTP service audited by SCP also take on the
service-lifecycle adoption obligation: `services.yml` must declare an
`auth_contract` block conforming to SVC-003 (see §11).

## 2. What Adopting Teams Get

After onboarding, a project should be able to:

1. ask for targeted standards guidance before coding
2. run changed-file audit in PR workflows
3. run full or subsystem audit on a schedule
4. keep findings, waivers, and reports in a consistent shape
5. layer repo-specific standards on top of the shared registry
6. publish CI-facing and Control Tower-facing outputs without a second audit path

## 3. Estate Best-Practice Position

Adopt SCP using the same broad discipline already proven across Control Tower,
Documentation Intelligence, and the estate conformance work:

- use a shared standard, not copy-pasted local folklore
- extract and reuse proven patterns rather than inventing a second mechanism
- keep the integration layer thin; do not refactor core business logic just to
  "make SCP fit"
- keep audit local to the repo that owns the code
- keep findings structured and durable; markdown is a projection, not the source
  of truth
- keep the rollout advisory first; do not introduce hard CI blocking at
  adoption time
- keep project overlays explicit instead of weakening the shared standard into
  vague prose
- keep the existing repo governance protocol if it is stronger; SCP supplements
  governance, it does not replace it

## 4. Governance Rules Teams Must Preserve

The minimum expected governance posture for adopters is:

1. do not silently descope
2. do not skip the repo's existing review process
3. every SCP finding is resolved, waived, accepted, marked false positive, or
   explicitly deferred by the repo's normal governance path
4. docs and control records are updated in the same session as code changes
5. git stays clean: branch, PR, merge, and artifact ownership remain explicit

If a repo already follows the stronger Control Tower delivery protocol with
parallel adversarial review, keep using it.

## 5. Recommended Deployment Model

Use this deployment model unless there is a strong repo-specific reason not to:

### 5.1 Package and CLI first

Install SCP as a Python tool dependency in the adopter repo and call it through
CLI commands in local workflows and CI.

This is the default and recommended mode.

### 5.2 Repo-local audit

Run `audit-changed` and `audit` inside the target repo, not in a central shared
service. The repo that owns the code should own extraction, normalisation, and
artifact generation.

### 5.3 Optional shared consult service

If teams want a shared consult endpoint, run `serve` against a Control Tower
OIDC audience and use it for consult and registry access. Do not move the
canonical audit runtime there yet. Raw `--auth-token` bearer auth is
deprecated — machine callers should use Control Tower agent keys
(`mode.api_key`). See §11.6 for the mode-selection guide and §11.7 for
the bearer deprecation window.

### 5.4 Control Tower consumes artifacts

Control Tower should read the emitted artifacts. It should not invoke evaluator
runtime directly.

### 5.5 Docs-agent remains optional

Docs-agent is a future enrichment layer for broader retrieval and historical
evidence. It is not required for base onboarding.

## 6. Pre-Onboarding Decisions

Before implementation begins, each adopting repo must decide the following:

| Decision | Why it matters |
|----------|----------------|
| **Repo owner** | Owns the adoption and follow-up fixes |
| **Governance owner** | Owns waivers, accepted debt, and process wording |
| **Overlay owner** | Owns repo-specific standards and overlay drift |
| **Pilot subsystem** | Gives consult and audit a bounded first target |
| **Primary domains** | Start with `governance,architecture` unless there is a specific reason not to |
| **CI owner** | Wires PR and scheduled audit jobs |
| **Agent instruction file** | Defines where consult-before-coding will be added (`CLAUDE.md`, `AGENTS.md`, or equivalent) |
| **Service mode decision** | Decide whether local CLI is enough or whether the repo wants the optional HTTP service |
| **Service auth modes (SVC-003)** | If the repo hosts an HTTP service audited by SCP, decide which of the four approved `auth_contract` modes it accepts (see §11). `mode.user_oidc` for browsers, `mode.api_key` for machine callers, `mode.service_rs256` for S2S, `mode.bearer_legacy` only with a time-bound migration waiver |

## 7. Required Repo Changes

Every adopter should make the following changes.

### 7.1 Install SCP as a pinned tool dependency

Until SCP is published to an internal package index, the simplest path is to pin
the GitHub repo:

```bash
pip install "git+https://github.com/jrnb2024/standards-control-plane-.git@main"
```

Best practice:

- pin the Git reference or released version explicitly
- do not install from a floating local copy in CI
- keep SCP version changes visible in dependency review

Installing SCP pulls in a small transitive closure at runtime. The
load-bearing runtime dependencies are:

- `fastapi`, `uvicorn`, `httpx` — the HTTP surface
- `jsonschema>=4.25.0` — schema validation
- `pyyaml>=6.0` — `services.yml` parsing (required once SVC-001/002/003
  are in use; see §11)
- `pydantic>=2.12.0`
- the vendored `ct_auth-0.8.0` wheel — Control Tower OIDC + BFF helpers

No action is required beyond `pip install` — but teams with locked
dependency sets should know these are on the list before SCP lands.

### 7.2 Add a repo-local overlay

Create a repo-local overlay directory so project-specific rules and patterns can
sharpen the shared registry without editing SCP core.

Recommended location:

```text
governance/standards-control-plane/
  standards-index.json
  architecture/
    index.json
    rules/
    patterns/
  governance/
    index.json
    rules/
```

Use overlays for:

- repo-specific boundary rules
- stricter severity for already-shared rules
- approved local patterns
- project terminology or subsystem tags

Do not use overlays for:

- broad restatement of the shared registry
- undocumented local preferences with no owner
- hiding or weakening shared standards that should remain estate-wide

### 7.3 Add thin wrapper scripts

Do not scatter raw long CLI invocations across prompts, READMEs, and CI files.
Create repo-local wrapper scripts with the repo's fixed defaults.

Recommended wrappers:

```text
scripts/scp-consult
scripts/scp-audit-pr
scripts/scp-audit-full
```

Those wrappers should own:

- subsystem default
- overlay path
- standards version
- any repo-specific request-file path

### 7.4 Add findings and waiver ownership

The repo must own these artifacts:

- `output/findings/waivers.json`
- `output/findings/open-findings.json`
- `output/findings/findings-history.json`
- `output/findings/area-summaries/*.json`
- `output/reports/latest-review.md`

Best practice:

- commit waivers and long-lived findings/history artifacts through normal PR flow
- treat PR-scoped CI summaries as build artifacts, not as mandatory committed files
- keep waiver approvals explicit and time-bound

### 7.5 Update governance docs

Every adopter should update:

- `CLAUDE.md`, `AGENTS.md`, or equivalent agent instruction file
- repo governance protocol or delivery guide
- PR template or delivery checklist if one exists

## 8. Governance Doc Wording to Add

At minimum, the adopting repo should add a section equivalent to this:

```text
## Standards Control Plane Usage

Before implementation:
1. Identify impacted subsystem, area, and files.
2. Run SCP consult for the relevant domains.
3. Read applicable rules, approved patterns, and open findings.
4. Summarise the implementation plan against those constraints before coding.

Before PR or handoff:
1. Run SCP changed-file audit.
2. Review findings and fix them where required.
3. Record waivers or accepted debt explicitly; do not silently bypass findings.
4. Keep generated findings and report artifacts aligned with the code change.
```

If the repo already has stronger governance language, integrate SCP into that
language rather than replacing it.

## 9. Agent Workflow Teams Should Adopt

This is the expected operating loop for implementation agents:

1. identify impacted subsystem, area, and likely changed files
2. run `consult` (include `service-lifecycle` in `domains` when the repo
   hosts an HTTP service or when the change touches `services.yml`)
3. read:
   - applicable rules
   - approved patterns
   - open findings
   - relevant historical review references
4. summarise the plan against those constraints
5. implement
6. run `audit-changed`
7. fix findings or explicitly record exceptions through the repo's governance path
8. only then open or update the PR

SCP should become part of the normal pre-coding and pre-PR loop. It should not
be a late afterthought.

## 10. CI Integration

### 10.1 PR workflow

Each adopting repo should add a non-blocking PR job that runs changed-file audit.

Recommended command shape:

```bash
standards-control-plane audit-changed \
  --base-ref origin/main \
  --head-ref HEAD \
  --domains governance,architecture \
  --subsystem <subsystem> \
  --standards-version <registry-version> \
  --overlay governance/standards-control-plane \
  --write-output
```

Then publish:

- `output/ci/latest-ci.json`
- `output/ci/latest-ci.md`
- `output/reports/latest-review.md`

Do not fail the build on day one. Warnings should be visible first.

### 10.2 Scheduled workflow

Each adopting repo should also add a scheduled job for broader refresh:

```bash
standards-control-plane audit \
  --request governance/scp/audit-request.json \
  --overlay governance/standards-control-plane \
  --write-output
```

Recommended cadence:

- nightly for fast-moving repos
- weekly for slower repos

### 10.3 Control Tower projection

If the repo participates in estate-level reporting, publish or expose:

- `output/control-tower/surface.json`
- `output/control-tower/estate-dashboard.json`
- `output/control-tower/subsystems/*.json`

## 11. Service Auth Contract (SVC-003)

SVC-003 defines a closed four-mode auth contract every estate service
must declare in its `services.yml`. This section has two tracks:

- **Consumer track (§11.2)** — adopters who only *call* SCP's HTTP
  service (or any other estate service). Read §11.1 and §11.2 and
  skip the producer subsections.
- **Producer track (§11.3–§11.8)** — adopters who *host* an HTTP
  service audited by SCP. Read everything: the services.yml
  declaration shape, per-mode guidance, the `--auth-token`
  deprecation window, and the upgrade path from pre-SVC-003
  manifests.

SCP's own `services.yml` at repo root and `docs/reviews/WP-SCP-019/
dogfood-scp.md` are the canonical producer example.

> **Operative close date update — 2026-04-20.** Per SCP's Option-B
> signal (`docs/reviews/WP-SCP-019/d019-option-b-signal.md`, filed
> 2026-04-20), the estate-wide `mode.bearer_legacy` deprecation close
> date has **operationally slid from 2026-06-30 to 2026-09-30** for
> consumer-team planning and outbound comms from 2026-04-20 forward.
> The formal amending decision (D-021) records on 2026-05-31 with
> observed adoption-PR evidence substituted. D-019's 2026-06-30
> citation in this section, the `deprecation_close_date` example
> snippet in §11.7, and the SCP-specific close-date statement in
> §11.7 all remain as-ratified until D-021 fires — substitute
> `2026-09-30` when authoring new `services.yml` / `waivers.json`
> entries from this signal forward. Threshold for the 2026-05-31
> check (whether Option B holds or D-019 stands) was CT-confirmed
> verbatim on 2026-04-20; corner cases §2.1–§2.3 in
> `SCP-CONFIRM-D-019-THRESHOLD-2026-04-20.md` apply.

### 11.1 Approved modes (closed set)

Custom modes are not permitted; a new mode requires a standards
change. The static evaluator scans for the implementation-marker
patterns listed below; Node/Go services must produce source patterns
matching the same substrings to satisfy the code-pattern scan.

| Mode ID | Use | Shape | Implementation markers |
|---------|-----|-------|------------------------|
| `mode.user_oidc` | Browser flows | Control Tower OIDC + JWKS verification + `aud=<app-id>` claim + httpOnly cookie session | `ControlTowerAuth`, `ct_auth.`, `create_bff_routes`, `CT_JWKS_URL` |
| `mode.service_rs256` | Service-to-service (target state; replaces HS256) | S2S RS256 + required `aud` claim + JWKS verification | `algorithms=["RS256"]`, `algorithms=['RS256']`, `algorithm="RS256"`, `algorithm='RS256'` |
| `mode.api_key` | Agents, CLIs, machine callers | Control Tower-issued agent key, revocable via CT, `X-API-Key` header | `X-API-Key`, `x-api-key` |
| `mode.bearer_legacy` | Deprecated. Pre-SVC-003 raw bearer token | Requires per-service migration waiver with explicit `deprecation_close_date` | `secrets.compare_digest` |

The reference implementation for `mode.user_oidc` is SCP's own
service at `src/standards_control_plane/service.py` (commit
`66ba8a4`): vendored `ct_auth` wheel, `ControlTowerAuth` with
`jwks_url` + `audience`, `create_bff_routes` for the cookie session
flow.

### 11.2 Consumer track: calling SCP (or any SVC-003 service)

Find the target service's `services.yml` (SCP's lives at the root of
`standards-control-plane`). The `auth_contract.accepted_modes` list
tells you which headers your caller must send.

- **Browser**: perform the Control Tower OIDC login flow at the
  service's `/auth/login`; subsequent requests carry the httpOnly
  cookie session the BFF sets. No explicit header from your code.
- **Machine caller (`mode.api_key`)**: request an agent key from
  Control Tower's agent-key admin surface and send
  `X-API-Key: <key>` on every request. Keys are revocable via CT.
- **Machine caller (`mode.bearer_legacy`, deprecated)**: during the
  deprecation window (close date per D-019 is 2026-06-30), send
  `Authorization: Bearer <token>` using the token the target service
  configured via `--auth-token`. Plan your migration to
  `mode.api_key` before the close date — after it, SVC-003 fires
  `bearer-legacy-close-date-passed` on the target service.
- **S2S caller (`mode.service_rs256`)**: mint an RS256 JWT with
  `aud` set to the target service's `services.yml` key and send it
  in the Authorization header.

The producer subsections below describe the shape a service
publishes; as a consumer, you only need the declaration's mode list
and the issuance endpoint for each mode.

### 11.3 Producer track: upgrading a pre-SVC-003 services.yml

If your repo already has a `services.yml` from WP-SCP-018 or earlier
and it has no `auth_contract` block, SVC-003's auto-check will fire
`missing-auth-contract` against every non-planned service. The
minimum upgrade:

1. Pick the auth mode(s) your service actually accepts today. If it
   still uses `--auth-token`, that is `mode.bearer_legacy` and needs
   the waiver shape in §11.7.
2. Add the `auth_contract` block under each service's
   `runtime_contract` (see §11.4–§11.7 for per-mode shape).
3. Run `standards-control-plane audit --request <your-request>.json
   --domains service-lifecycle` and address any findings.

Upgrading one service at a time is supported — other services fire
their own `missing-auth-contract` until they are declared, but the
rule scope is per-service.

### 11.4 Producer track: mode.user_oidc

Register an OAuth client with Control Tower for each environment
(e.g. `my-app`, `my-app-dev`). Control Tower registration covers the
redirect URIs and CORS origins; SCP's `docs/deployment.md` §3 is a
worked example for reference.

Set runtime env vars on the service process:

```text
AUTH_ENABLED=true
CT_BASE_URL=https://control-tower.brokapps.ai
CT_APP_ID=my-app-dev
PUBLIC_BASE_URL=https://my-app-dev.brokapps.ai
```

`CT_JWKS_URL` is optional — if unset, it defaults to
`<CT_BASE_URL>/api/v1/.well-known/jwks.json`. Override only if your
Control Tower deployment publishes JWKS at a non-standard path.

Declare the mode in `services.yml`. The `audience` value must match
the service's `services.yml` key in the target environment. SCP
solves the "local key vs staging key" mismatch by using distinct
service keys per environment (e.g. `scp-dev` locally, `scp` in
staging); adopters should do the same rather than using a shared
key with divergent audiences.

```yaml
services:
  my-app-dev:
    healthcheck: /health
    local:
      status: ready
      runtime_contract:
        # ... SVC-001 fields ...
        auth_contract:
          accepted_modes:
            - mode: mode.user_oidc
              audience: my-app-dev
              jwks_url: https://control-tower.brokapps.ai/api/v1/.well-known/jwks.json
```

In Python services, reuse the vendored `ct_auth` wheel:

```python
from ct_auth.bff import create_bff_routes
from ct_auth.fastapi import ControlTowerAuth

auth = ControlTowerAuth(jwks_url=CT_JWKS_URL, audience=CT_APP_ID)
create_bff_routes(app, auth=auth, ...)
```

Node/Go services need the equivalent OIDC + JWKS implementation.
The code-pattern scan is substring-based on the markers in the
§11.1 table; non-Python services must emit matching patterns or
accept impl-missing findings as waivers.

### 11.5 Producer track: mode.api_key

**Status (as of 2026-04-18):** ratified and admin-surface-live but
operational-doc pending. Adopters should not plan immediate
production migration to `mode.api_key` yet.

Concretely, per the CT 2026-04-18 audit
(`control-tower/governance/docs/notifications/SCP-FOLLOWUP-2026-04-18-admin-ui-audit.md`):

- CT's service-account + API-key backend (`CT-016`) is shipped.
- The admin UI (create / list / revoke / rotate service-account keys,
  7-day rotation overlap window, audit logging) is live today.
- The **operational doc** (`CT_AGENT_KEY_OPS.md`) covering default
  expiry, rotation cadence, revocation path, scope model, audit-log
  format, and `mode.api_key` vs `mode.service_rs256` discrimination
  is **not yet published** — CT-led authoring, target mid-to-late
  May 2026.
- Until the ops doc publishes, production adoption of `mode.api_key`
  has undefined operational characteristics (key rotation timing,
  expiry defaults, rate limits). Declaring the mode is fine; routing
  real traffic through it is not advised.

For services currently on `mode.bearer_legacy` with a deprecation
waiver, stay on the waiver track until the ops doc publishes. The
2026-05-31 D-019 checkpoint
(`docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`) governs whether
the 2026-06-30 close date stands or is amended to 2026-09-30.

When the ops doc publishes, request that Control Tower register the
service (or SCP, if running a shared SCP instance) as an agent-key
issuer. SCP itself is tracked as an SCP-071 dependency.

Declaration shape:

```yaml
auth_contract:
  accepted_modes:
    - mode: mode.api_key
      issuer: control-tower
```

Machine callers pass `X-API-Key: <key>` on every request. Agent keys
are issued and revoked via Control Tower's agent-key admin surface
(not via services.yml edits).

### 11.6 Producer track: mode.service_rs256

Target state for in-estate S2S calls; replaces the HS256 tokens used
by pre-WP-SCP-019 services. The declaration shape matches
`mode.user_oidc` (audience + jwks_url):

```yaml
auth_contract:
  accepted_modes:
    - mode: mode.service_rs256
      audience: my-app
      jwks_url: https://control-tower.brokapps.ai/api/v1/.well-known/jwks.json
```

Verifying services validate `aud == "<services.yml key>"` and the
RS256 signature against the JWKS endpoint.

### 11.7 Producer track: mode.bearer_legacy (deprecated)

The `--auth-token <token>` flag that shipped in WP-SCP-018 is now
classified as `mode.bearer_legacy`. Services still using this path
must:

1. Declare the mode in `services.yml` with both
   `deprecation_close_date` (an ISO date) and `waiver_ref` (the
   `waiver_id` of a record in `output/findings/waivers.json`).
2. Register the waiver in `output/findings/waivers.json` with
   `approved_by`, `created_at`, and `expires_at` at or before the
   close date.
3. Draft and track a migration plan to either `mode.api_key`
   (Control Tower-issued agent keys, for most machine callers) or
   `mode.service_rs256` (CT-signed S2S JWT, for high-throughput or
   inter-service callers where a CT round-trip per request is a
   latency-budget problem) by the close date. `mode.bearer_legacy`
   is a machine-caller path; migration target is NOT
   `mode.user_oidc` (which is a browser cookie session flow). Mode
   choice follows the throughput / latency heuristic CT carries in
   `CT_AGENT_KEY_OPS.md` §2.2 — `mode.service_rs256` is not
   operational today (CT authoring + JWKS + consumer helpers are
   scoped in SVC-003 but not shipped), so services picking that
   target declare `mode.bearer_legacy` with a waiver now and
   migrate when CT operationalises. Per-app migrations are tracked
   as separate work packages, not as WP-SCP-019 deliverables.

`services.yml`:

```yaml
auth_contract:
  accepted_modes:
    - mode: mode.bearer_legacy
      deprecation_close_date: "2026-06-30"
      waiver_ref: my-app-bearer-legacy-migration
```

`output/findings/waivers.json`:

```json
[
  {
    "waiver_id": "my-app-bearer-legacy-migration",
    "finding_id": "F-SVC-003-<area>-<service>-<signal>",
    "reason": "Machine callers migrating from raw bearer to mode.api_key",
    "approved_by": "my-app-platform-owner",
    "created_at": "2026-04-18T00:00:00Z",
    "expires_at": "2026-06-30T23:59:59Z"
  }
]
```

The `finding_id` in the waiver record is a placeholder shape —
substitute the real evaluator finding_id from a prior audit output
(format: `F-SVC-003-<area_id>-<service>-<signal_key>`).

On or after the close date the SVC-003 evaluator fires
`bearer-legacy-close-date-passed-*` and the waiver must be renewed
(governance-approved) or the mode entry removed. If no waivers are
registered in `waivers.json` (file absent, empty list, or unparseable)
the `bearer-legacy-waiver-not-found-*` check skips — the evaluator
treats pre-adoption state as "not yet using the waiver system" rather
than a hard fail.

The estate-wide close date for SCP's own `--auth-token` path is
`2026-06-30` per D-019. Per-app close dates can be earlier but not
later without an amending decision row.

### 11.8 Which mode to pick (producer track)

- Browser users → `mode.user_oidc` (cookie session via `ct_auth` BFF)
- Python / Node / CLI client hitting the HTTP API programmatically →
  `mode.api_key`
- Service-to-service within the estate → `mode.service_rs256`
- Only during migration off WP-SCP-018 `--auth-token` →
  `mode.bearer_legacy` with a time-bound waiver

Services may declare more than one mode. SCP itself declares
`[mode.user_oidc, mode.bearer_legacy]` during the migration window;
after the 2026-06-30 close date the latter comes out.

### 11.9 Running SCP's HTTP service locally

If your team runs its own SCP instance (for team-scoped consult /
registry access), use the standard CLI form:

```bash
standards-control-plane serve --host 127.0.0.1 --port 3787
```

With auth:

```bash
AUTH_ENABLED=true CT_APP_ID=my-app-dev \
  PUBLIC_BASE_URL=https://my-app-dev.brokapps.ai \
  standards-control-plane serve --host 127.0.0.1 --port 3787
```

See `docs/deployment.md` for the canonical runtime variable contract
and the Cloudflare dev-tunnel setup. Keep the canonical audit runtime
local to each repo — SCP's HTTP surface is for consult and registry
only.

### 11.10 Caller-side rule override (`.scp/rule-config.yaml`)

The `policy-check.yml` reusable workflow accepts a caller-side override
file at `.scp/rule-config.yaml` (configurable via the
`rule-config-path:` input on `workflow_call`). Use this to disable an
SCP rule that doesn't fit your repo's context — but only with
intentional friction: the schema requires a justification + an
expiry, the disable is observable in every PR, and an expired disable
emits a workflow warning every run for one release as a deprecation
ramp.

Schema: `schemas/rule-config.schema.json` (draft 2020-12,
`additionalProperties: false`).

Minimum example:

```yaml
# .scp/rule-config.yaml
rules:
  SCP-R-002:
    disable: true
    justification: "Repo doesn't ship a waivers.json (no governed exceptions yet); revisit when SCP-R-002 surface broadens."
    expires_at: 2026-09-30
```

Required keys per rule entry:

- `disable` (boolean) — when `true`, the rule's deny is suppressed.
- `justification` (string, non-empty) — recorded in the audit trail
  and surfaced to PR reviewers.
- `expires_at` (date or RFC 3339 date-time) — the disable's planned
  end-of-life. The schema accepts either form; the workflow normalises
  to UTC for the expiry comparison.

Behaviour:

- A `disable: true` entry suppresses the rule's deny *and* emits an
  observability record into `policy-check-summary.json`'s
  `disabled_rules:` list with `{rule_id, reason: "rule-config
  override", expires_at}`.
- Each PR run also posts a sibling commit-status `scp/policy-check-readback`
  with text like `"3 rules enabled, 1 disabled: SCP-R-002 until 2026-09-30
  (rule-config override)"` so reviewers see the bypass posture inline.
- When `expires_at` is in the past, the disable still suppresses the
  deny **for one release** as a deprecation ramp, but every PR run
  emits a `::warning::` annotation:
  `SCP-R-NNN rule-config disable expired YYYY-MM-DD; remove or extend`.
  Treat this as merge-soft-blocking — the team should either renew
  the disable with a fresh `expires_at` or remove the entry.

When **not** to use rule-config:

- Per-finding suppression — use a `waivers.json` waiver instead with a
  `finding_id`. Rule-config is rule-wide; waivers are per-finding.
- "Permanent" disables — they are not. The schema requires
  `expires_at`. If your context structurally never matches a rule,
  open an issue against SCP for the rule definition itself rather
  than long-term-disabling it locally.
- One-off PR exceptions — use `scp_bypass: true` on the workflow
  invocation per the **three-gate** break-glass procedure documented
  in §12.7.4 (CODEOWNERS approval + sibling D-NNN row + matching
  `waivers.json` entry — all three required simultaneously).

**CODEOWNERS requirement (MUST).** CODEOWNERS protection on `.scp/rule-config.yaml` is required, not optional: a `disable: true` entry suppresses a rule's deny WITHOUT triggering the three-gate break-glass check (see §12.7.4), making `.scp/rule-config.yaml` a bypass-surface equivalent to `scp_bypass: true`. Without CODEOWNERS coverage, a single developer can silently disable any SCP rule. Minimum:

```
.scp/rule-config.yaml @your-team-owners
```

## 12. Architecture Principles for Adopters

These are the key architectural principles teams should follow while adopting
SCP.

### 12.1 Extract, do not reinvent

Use the shared registry, shared contracts, and shared outputs. Do not create a
repo-specific second standards engine.

### 12.2 Thin integration only

Add wrapper scripts, CI jobs, overlays, and governance references. Do not
perform broad business-logic refactors just because the repo is onboarding SCP.

### 12.3 One audit model

CI outputs, Control Tower outputs, and reports should all be projections from
the same audit result. Do not invent a separate CI-specific evaluator path.

### 12.4 Structured artifacts first

Findings JSON, waivers JSON, audit results, and summaries are the durable
records. Markdown exists to help humans review those records.

### 12.5 Explicit overlays

If the repo needs local specificity, express it through an explicit overlay with
an owner. Do not bake local assumptions into global SCP core.

### 12.6 Deterministic checks before inference

Start by relying most heavily on governance and architecture signals that are
already deterministic or evidence-backed. Expand advisory use of UX, design, and
product only when the repo is comfortable with the confidence model.

### 12.7 Federation primitive — adopter integration

This appendix is the canonical adopter-integration contract for the SCP
federation primitive at v1.0.0. It tells an adopter exactly what to add to
their repo, what to set on their branch protection, what to expect when
SCP cuts a new release, and how break-glass + rollback work.

#### 12.7.1 Minimal caller wrapper

Add this file at `.github/workflows/policy-check.yml` in your repo. Pin
the `uses:` line by 40-character commit SHA, NOT by tag name. The
`# tag: v1.0.0` comment is the human-readable annotation and the signal
the SCP Renovate preset uses to bump the SHA + comment together on every
SCP release.

```yaml
# .github/workflows/policy-check.yml
name: policy-check

"on":
  pull_request:
    branches: [main]

permissions:
  contents: read
  statuses: write  # required for scp/policy-check-readback per D-029 / 020C.1(vi)

jobs:
  policy-check:
    # Refuse fork PRs — same-repo only for v1.0.0 (mandatory; do not
    # remove this `if:`. Fork PRs run with the fork's read-only
    # GITHUB_TOKEN and cannot post the readback commit-status, plus
    # they can carry malicious workflow-context-injection payloads.
    # Closes WP-SCP-020 020D1 R1 review TF-D1-002.
    if: ${{ github.event.pull_request.head.repo.full_name == github.event.pull_request.base.repo.full_name }}
    # renovate: datasource=github-tags depName=jrnb2024/standards-control-plane-
    uses: jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<commit-SHA>  # tag: v1.0.0
```

The `if:` fork-PR refusal is **mandatory**, not optional. Closes the
20D1 R1 review tracked-forward item TF-D1-002.

**Before deploying:** review §12.7.13 for the v1.0.0 supply-chain posture (OPA + Conftest + Regal SHA256-verified per platform).

**CODEOWNERS for the wrapper.** Multi-maintainer adopters MUST
protect this file with CODEOWNERS so a single PR cannot silently
delete the fork-PR `if:`, weaken `permissions:`, or change the
pinned SHA without an owning reviewer. Symmetric with §11.10's
recommendation for `.scp/rule-config.yaml`. Minimum entry:

```
.github/workflows/policy-check.yml @your-team-owners
```

#### 12.7.2 Renovate preset (`extends:` snippet)

Add this single-line preset extension to your repo's `renovate.json`:

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "github>jrnb2024/standards-control-plane-//renovate/default#renovate/v1.0.0"
  ]
}
```

The preset is published at `renovate/v1.0.0` (independent of the
federation-primitive `v*` tag series; see `docs/security/branch-protection.md`).
The customManager regex matches the canonical wrapper marker and bumps both
the SHA pin and the `# tag:` comment together on every SCP release.

Adopters MUST NOT add packageRules that override the preset's
`automerge: false` for the SCP federation primitive — that's how
malicious supply-chain updates would auto-promote.

**Tag-series protection.** The `renovate/v*` tag series is
protected by Repository Ruleset `scp-tag-protection-renovate-v`
(D-034 — deletion + force-push + non-fast-forward all blocked,
including for admins). Verify before extending:

```bash
gh api repos/jrnb2024/standards-control-plane-/rulesets \
  --jq '.[] | select(.name == "scp-tag-protection-renovate-v") | .enforcement'
# expected: active
```

`docs/security/branch-protection.md` carries the full SCP-side
protection state.

#### 12.7.3 Branch-protection setup

Run the SCP-published helper from your local clone of the SCP repo:

```bash
cd <your-local-clone-of-standards-control-plane>
./scripts/enable-required-check.sh \
  --repo OWNER/NAME \
  --branch main
```

The script (per WP-SCP-020 §4 020G + D-035):

1. Asserts `gh --version >= 2.40` + `jq` + `git` + `python3` + `shasum` on PATH.
2. Refuses to run when `CI=true` or `GITHUB_ACTIONS=true` (bootstrap-only).
3. Validates `--repo` (regex + path-traversal guard) and `--branch` (no slashes / .. / leading dot).
4. Logs a stderr WARNING about required PAT scope (`administration:write` on the single target repo).
5. Captures before-state, applies the unified PUT (status-checks + admins + reviews), then a separate POST to the `required_signatures` sub-resource.
6. Verifies 4 properties (strict, contexts, enforce_admins, signatures) and emits the result.
7. Emits an invocation-log markdown block for paste into `docs/reviews/WP-SCP-020/branch-protection-log.md` on the SCP repo. The log commit is part of the invocation procedure.

Use `--plan` first to see both the current state and the proposed payload before applying.

For multi-maintainer adopters who want review enforcement: the script *preserves* any existing `required_pull_request_reviews` shape rather than nulling it (per 020G fix-round-1 SAF-002 closure). Configure your review-shape via the standard GitHub UI or API; the SCP helper won't touch it. **Multi-maintainer adopters MUST also set `dismiss_stale_reviews: true`** — see §12.7.4 for the security rationale and the helper's stderr WARNING when this is missing.

**PAT scope is broader than it looks.** `administration:write` on a fine-grained PAT covers more than branch-protection settings — it also enables some webhook operations, repository-transfer initiation, and archival. (Repository **environments** — deployment secrets and protection rules — are governed by a separate `environments: write` permission and are NOT included in `administration:write`; mention here only to clarify the boundary.) Issue a single-use fine-grained PAT scoped to the one target repo, run the helper, then immediately revoke or expire the PAT. Do NOT retain an `administration:write` PAT for routine use.

**Required-check context name.** The required status check MUST be configured to the **check-run** context `policy-check / scp/policy-check`, NOT to the **commit-status** context `scp/policy-check-readback`. The check-run is the authoritative gate (driven by GitHub Actions); the readback is an informational commit-status forge-able by any runner with `statuses: write`. The `enable-required-check.sh` helper defaults to the correct check-run context per D-033.

**Verify the gate is live before relying on it.** Empirical verification, per D-033 (don't trust the spec — test the live state):

1. Confirm the required-check context is registered:

   ```bash
   gh api repos/OWNER/NAME/branches/BRANCH/protection/required_status_checks \
     --jq '{strict: .strict, contexts: .contexts}'
   # expected (selectively): {"strict": true, "contexts": ["policy-check / scp/policy-check"]}
   ```

2. Confirm `enforce_admins` and `required_signatures`:

   ```bash
   gh api repos/OWNER/NAME/branches/BRANCH/protection/enforce_admins --jq '.enabled'
   # expected: true
   gh api repos/OWNER/NAME/branches/BRANCH/protection/required_signatures --jq '.enabled'
   # expected: true
   ```

3. Open a draft PR introducing a deliberate `SCP-R-001` violation (e.g., a `services.yml` entry with an invalid `auth.mode` value). Confirm the PR's `policy-check / scp/policy-check` check shows red with an `SCP-E003` annotation AND that the merge button is disabled. Close the draft PR after verification — it is not for merge. Do NOT promote production traffic onto a gate that has not been empirically tested with a real deny.

#### 12.7.4 Break-glass procedure (three-gate model)

The SCP federation gate fails closed by default. To bypass on a single PR (`scp_bypass: true` on the wrapper), the PR must satisfy ALL THREE gates simultaneously:

1. **Approving review** from a member listed in your repo's CODEOWNERS for the paths the bypass affects. (This is the adopter's own CODEOWNERS file, not SCP's.) **Minimum-necessary path: `output/findings/waivers.json`** — every bypass PR adds a waiver entry per Gate 3 below, so CODEOWNERS coverage on this path guarantees Gate 1 fires on every bypass PR. Extend coverage to `services.yml`, `policies/**` (if you mirror policies locally), and any other SCP-governed paths in your repo, but do NOT omit `waivers.json` — without it, a bypass PR that touches only the wrapper or only a non-listed path slips through Gate 1.
2. **Sibling D-NNN row** in the SAME PR adding a new row to your equivalent of `docs/DECISIONS.md` (regex pattern `^\|\s*D-[0-9]{3}\s*\|\s*20[0-9]{2}-[0-9]{2}-[0-9]{2}\s*\|`).
3. **Matching `waivers.json` entry** in the SAME PR with `expires_at > now` and `rule_id` matching the bypass-triggering SCP-R-NNN rule.

`scripts/verify-bypass-pairing.sh` (in the SCP repo, called by the workflow's `bypass-gate` step) checks Gates 2 and 3. Gate 1 (CODEOWNERS approval) is enforced by GitHub branch protection — see the two-mode breakdown immediately below. Any miss → `SCP-E004` → merge-blocked.

**Two operating modes — Gate 1 enforcement varies.** Per D-033, the SCP self-dogfood gate runs in single-operator mode with `required_approving_review_count = 0` because GitHub forbids PR authors from approving their own PRs (count=1 + a single CODEOWNER would lock the operator out entirely). Adopters inherit the same dichotomy:

- **Multi-maintainer adopters.** Configure branch protection with `required_approving_review_count >= 1`, `require_code_owner_reviews: true`, **AND `dismiss_stale_reviews: true`**. (GitHub enforces non-self-approval at the platform level — there is no separate REST API field for that constraint; the WP-SCP-020 plan corpus uses `require_review_from_non_author: true` as shorthand for this platform behaviour, but no API field needs to be set.) Gate 1 is **machine-enforced** — a bypass PR cannot merge without a CODEOWNER review from someone other than the author. The `dismiss_stale_reviews: true` setting is non-optional in this mode: without it, an approving CODEOWNER review on an initial commit persists across subsequent commits in the same PR, so an attacker who obtains a clean review can later push commits that add `.scp/rule-config.yaml disable: true`, change `scp_bypass: true`, or weaken the wrapper's fork-PR `if:` — and merge without re-review. Dismissal fires on ANY push to the PR branch regardless of which files the new commit touches — it is not path-selective. Stale-review dismissal is the enforcement complement to `require_code_owner_reviews`. The `enable-required-check.sh` helper preserves your existing review-shape verbatim and does NOT set `dismiss_stale_reviews: true` for you; configure it explicitly via the GitHub branch-protection UI or API. (As of fix-round-5 of this slice, `enable-required-check.sh` emits a stderr WARNING when the preserved existing review config has `dismiss_stale_reviews: false` — see also the "verify the gate is live" block in §12.7.3.)
- **Single-operator adopters** (personal account, sole maintainer). Configure `required_approving_review_count = 0` per D-033 (count >= 1 makes the repo unmergeable). Gate 1 collapses to **documentation-only** — `scripts/verify-bypass-pairing.sh` does NOT check for an approving review, and the operator can self-author a bypass PR satisfying only Gates 2 and 3. This is the accepted bus-factor-1 cost (WP-SCP-020 §8 risk row); revisit at the 2026-07-21 quarterly review when a second maintainer onboards.

**SCP source — bus-factor-1 disclosure.** As of v1.0.0, the SCP reusable workflow and Renovate preset (the supply-chain source this integration depends on) are themselves operated by a single maintainer (`@jrnb2024`) per D-031 (WP-SCP-020 §8 bus-factor-1 risk row). The SCP-side quarterly bus-factor-1 review is scheduled for 2026-07-21, separate from your repo's own bus-factor review. Adopters with multi-maintainer or regulatory requirements for supply-chain diversity should note this constraint and re-evaluate at that checkpoint. Estate-cascade rollouts (FLA pilot → PIM / recommender / shopify-app / mapp-doc-agent / control-tower per WP-SCP-024) will surface the same constraint until SCP onboards a second maintainer.

**Gate 2 content-check limitation.** `verify-bypass-pairing.sh` checks that a D-NNN row containing the bypassed `rule_id` was added in the same PR, using a fixed-string substring match on the row contents (line 33 of the script). It does NOT validate that the row's Decision column specifically authorizes the bypass — a row that merely mentions the rule_id in the Rationale column will satisfy the content check. Human reviewers MUST verify the D-NNN row content is a genuine bypass authorization, not a tangential reference.

**Alternative bypass surface — `.scp/rule-config.yaml`.** The three-gate model above covers `scp_bypass: true` invocations only. A rule disabled via `.scp/rule-config.yaml` (`disable: true` with an `expires_at`) suppresses the deny WITHOUT triggering `verify-bypass-pairing.sh`; the only signal is the SCP-E006 observability annotation (informational; non-blocking — see §12.7.7). Treat `.scp/rule-config.yaml` as a bypass-surface equivalent to `scp_bypass: true`:

- **Adopters MUST CODEOWNERS-protect `.scp/rule-config.yaml`** (per §11.10) so a single developer cannot silently disable a rule.
- An expired `disable` entry (`expires_at < now`) continues to suppress the deny for **one release** while the workflow emits a per-PR `::warning::` annotation `SCP-R-NNN rule-config disable expired YYYY-MM-DD; remove or extend` (`.github/workflows/policy-check.yml` "Emit expired-rule-config one-release warning" step). The runtime warning IS shipped at v1.0.0; **release-tag-time refusal** of SCP-self expired rule-config entries is shipped at v1.0.0 via `.github/workflows/release-gate.yml` (TF-005 closed in slice 020H.3 — the release-gate workflow refuses a tag-cut when SCP-self `.scp/rule-config.yaml` has any `disable: true` entry with `expires_at < <UTC tag-cut date>`). Adopter-side rule-config expiry is enforced separately at PR time via SCP-E007. Treat the runtime warning as merge-soft-blocking and the CODEOWNERS coverage as the hard control.

#### 12.7.5 Rollback procedure

If a SCP release introduces a regression that breaks your repo's PR flow:

0. **Close any open Renovate-bot PR** that is bumping the wrapper SHA pin. The discriminating label is `scp-bump` (applied by the preset's SCP-primitive packageRule); this is distinct from the root-level `scp-federation` label, which appears on every PR generated by this preset. Filter on `scp-bump` so the rollback closure scopes to exactly the SCP-primitive bump series, not all Renovate PRs in your repo. If left open, a teammate may merge the bump PR during the rollback window and silently re-pin to the bad SHA. Re-open or let Renovate recreate the PR only after the SCP-side regression is confirmed resolved.
1. Revert the wrapper's `@<SHA>` pin to the previous SCP release SHA via PR.
2. Update the `# tag:` comment to match.
3. Renovate will re-run the bump on its next scheduled cycle (default weekly); if you need it to retry sooner, close + reopen the Renovate-bumped PR or run Renovate dispatch manually.
4. Open an issue at https://github.com/jrnb2024/standards-control-plane-/issues using the `rule-regression` template (`.github/ISSUE_TEMPLATE/rule-regression.md` — shipped at 020H.1) so SCP-side detection workflows correlate.

Target: 4 hours from regression report to tag-pin revert (per WP-SCP-020 §4 020H.1 iv-e).

**Full de-adoption** (different from per-release rollback). If your repo is exiting the SCP federation primitive entirely:

1. Open a PR that:
   - Deletes `.github/workflows/policy-check.yml`.
   - Removes the `extends:` entry pointing at `github>jrnb2024/standards-control-plane-//renovate/default` from your `renovate.json`.
   - Adds a D-NNN row in your DECISIONS log naming the de-adoption rationale.
2. After merge, remove the required-check from branch protection. The `enable-required-check.sh` helper does NOT have a removal mode — invoke the GitHub API directly:

   ```bash
   # List current required-check contexts
   gh api repos/OWNER/NAME/branches/BRANCH/protection/required_status_checks --jq '.contexts'
   ```

   Then PATCH the contexts list. **Important:** the PATCH replaces the contexts array entirely, it does not subtract. If `policy-check / scp/policy-check` is your only required check, pass an empty array; if you have other required checks, you MUST include them in the new array or this PATCH removes them too:

   ```bash
   # Case A — SCP federation was your only required check
   gh api -X PATCH repos/OWNER/NAME/branches/BRANCH/protection/required_status_checks \
     --input - <<'EOF'
   {"strict": true, "contexts": []}
   EOF

   # Case B — you have other required checks (substitute their context names)
   gh api -X PATCH repos/OWNER/NAME/branches/BRANCH/protection/required_status_checks \
     --input - <<'EOF'
   {"strict": true, "contexts": ["other-required-check-1", "other-required-check-2"]}
   EOF
   ```

3. Optionally relax `enforce_admins` if it was set ONLY for the SCP gate. Keep `required_signatures` regardless — it is independent of SCP and a baseline supply-chain hygiene control.

This procedure is intentionally explicit so de-adoption is auditable; partial de-adoption (deleting the wrapper without removing the required-check) leaves the branch unmergeable.

#### 12.7.6 Python evaluator vs Rego scope

- **Rego** (this gate) = PR-time fast shape-checks. Three rules in v1.0.0 (SCP-R-001/002/003).
- **Python** evaluator (existing in SCP) = nightly + manual + release-gate deep audit. Different code path.

The conflict-gate (CI job `rego-vs-python-conflict`) ensures both engines agree on every shared fixture. Disagreement → `SCP-E005` → merge-blocked → amending decision row in a separate PR resolves it.

#### 12.7.7 Error codes

| Code | Meaning | Failure mode |
|---|---|---|
| `SCP-E001` | Infrastructure fetch failure (OPA/Conftest binary unreachable, SHA256 mismatch, lockfile pin missing) | Fail-closed (workflow exits non-zero before policy evaluation) |
| `SCP-E002` | Policy-bundle or invocation pre-condition failure — policy directory missing/wrong type, changed-files manifest absent, waivers/rule-config data preparation error, manifest-file checkout missing, or Conftest invocation failure (Rego compilation, missing helper, etc.) | Fail-closed |
| `SCP-E003` | Policy deny — a rule fired and no waiver suppressed it | Merge-blocked; structured finding emitted |
| `SCP-E004` | Break-glass bypass failed three-gate check | Merge-blocked |
| `SCP-E005` | Conflict-gate disagreement (Rego ≠ Python on shared fixture) | Merge-blocked; amending D-NNN required |
| `SCP-E006` | Disabled-rule observability record (informational) | Non-blocking — step exits 0 and merge proceeds. Note: GitHub renders the `::error::` annotation as a red X icon in the PR Files-Changed tab; this is observability noise, not a hard failure. |
| `SCP-E007` | Rule-config schema validation failure (`.scp/rule-config.yaml` does not conform to `schemas/rule-config.schema.json` — missing required field, invalid `expires_at` format, or `additionalProperties` violation) | Fail-closed (workflow exits non-zero before policy evaluation) |
| `SCP-FRESH-001` | Wrapper pin is more than `freshness_warning_threshold_minor` (default 2) minor versions behind SCP `main` HEAD's `version-manifest.json` (post-020H.1). Title is `::warning::`, not `::error::` — adopters bump via Renovate (§12.7.2) or manually. | Non-blocking — informational annotation only. |
| `SCP-EREL-001` | SCP-side release-gate refusal (post-020H.3). Tag-cut blocked because `policies/deprecations.yaml` shows a deprecation whose ramp window has not elapsed (one MINOR release per VERSIONING.md (ii)) OR because `.scp/rule-config.yaml` on the SCP repo has an expired `disable` entry. Two operating modes: dry-run pre-flight via `workflow_dispatch` (operator pre-emptive check before pushing the tag); post-tag observer on `push:tags:['v*']` (last-line-of-defense annotator AND auto-opens a `release-gate-violation` GitHub issue assigned to `@jrnb2024` per 020H.3.1 closure of TF-020H3rg-003 — the bad tag is immutable per D-030, recovery is via cutting a corrected v<X>.<Y+1>.0). A non-blocking `::warning::` variant (title `SCP-EREL-001-warn`) fires when an entry's `announced_release` is more than one major behind the candidate — operator advisory for potential backdating; does not block the tag-cut. Both titles fire on the SCP source repo only; adopter annotation parsers never receive them. **Adopter-side relevance:** none directly. Adopters interact with the same invariants via SCP-E007 (rule-config schema/expiry at PR time) + the per-surface deprecation `::warning::` annotations (SCP-DEP-001) emitted during the one-MINOR ramp window. | Tag-cut blocked at SCP source (dry-run mode) OR annotated + auto-issue post-tag (push:tags mode). |
| `SCP-DEP-001` (announcement class) | Per-PR deprecation `::warning::` annotation emitted while a rule (or other public surface) is in its one-MINOR ramp window before removal at the next MAJOR. Format: `SCP-R-NNN deprecated; will be removed in v<X+1>.0.0; <migration-pointer>` (or analogous text for non-rule surfaces). Emission responsibility belongs to the surface itself (e.g. the rule's Rego implementation) — there is no centralized emitter. **Adopter-side relevance:** read the migration pointer + plan to bump the wrapper SHA past the removal release. The ramp window is auditable in `policies/deprecations.yaml` on the SCP source. | Non-blocking — informational annotation only. |

#### 12.7.8 SECURITY.md pointer

Adopters concerned about a policy-bypass disclosure should follow the SCP repo's `SECURITY.md` policy at https://github.com/jrnb2024/standards-control-plane-/blob/main/SECURITY.md. Use a private GitHub Security Advisory at https://github.com/jrnb2024/standards-control-plane-/security/advisories/new (preferred) or email `jimbrooke@me.com`. Initial response SLA: 3 business days. Closure of WP-SCP-020 §4.1 follow-up `SCP-073.sec` shipped at 020H.1.

#### 12.7.9 Pre-commit hook (optional, recommended)

Run the SCP gate locally on every commit so you catch denies before pushing:

```bash
# In your repo root, install the pre-commit hook
cat > .git/hooks/pre-commit <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec <your-local-clone-of-standards-control-plane>/scripts/scp-policy-check
EOF
chmod +x .git/hooks/pre-commit
```

The local script (`scripts/scp-policy-check`) reproduces the CI invocation against staged files using the same SHA-locked OPA + Conftest binaries. SHA256 verification is performed for these two; offline support if binaries are already downloaded. (Note: the local hook does not invoke Regal — Regal lint runs CI-only against the policy bundle. The CI workflow's Regal binary IS SHA256-verified as of slice 020H.2; see §12.7.13 for the supply-chain posture.)

**The local SCP clone MUST be checked out at the same commit SHA as your wrapper's `# tag:` pin.** A stale clone runs old policy rules and produces hook verdicts that diverge from CI — false-passes that the developer only discovers when CI runs (defeating the hook's stated purpose). A tampered clone can suppress denies entirely. Before relying on the hook:

```bash
git -C <your-local-clone-of-standards-control-plane> fetch
git -C <your-local-clone-of-standards-control-plane> checkout <your-wrapper-pinned-SHA>
```

Or extend the hook to read the SHA from `.github/workflows/policy-check.yml` and verify the clone matches before invoking the script. Divergence from the CI-pinned SHA invalidates the hook's verdicts.

##### 12.7.9.1 Rule-author pre-push verify wrapper (post-TF-020P-005)

**Audience: SCP-repo rule authors only.** This subsection is for contributors working directly inside the `standards-control-plane` repository on `policies/SCP-R-*.rego` rule files. **Adopter repos do not need this wrapper** — your pre-push verification is covered by the SCP reusable workflow you wired in §12.7.1, and the SHA-pinning warnings in the parent §12.7.9 do not apply to invocations from inside the SCP repo itself.

If you are authoring or modifying SCP-R-NNN rule files (`policies/SCP-R-*.rego`), `scripts/scp-pre-push-verify.sh` mirrors the three CI rule-author gates locally so you do not have to round-trip through CI to surface them: Regal lint (with the same disable list as `.github/workflows/policy-check.yml`), `opa fmt --fail` over the entire `policies/` tree, and per-rule `opa test --coverage --threshold 90 --fail-on-empty -v`. Run it from any subdirectory of the SCP clone:

```bash
scripts/scp-pre-push-verify.sh
```

The wrapper assumes `opa` and `regal` are installed locally (it does not bootstrap binaries — that is `scripts/scp-policy-check`'s job for the policy-bundle evaluation half). It emits a non-fatal warning if your local versions diverge from `scripts/.tool-versions`. **CI is still the authoritative gate** — the wrapper is a CI-roundtrip saver, not a federation-conformance gate. Closes WP-SCP-022 TF-020P-003 / 004 / 005.

#### 12.7.10 NEVER use `secrets: inherit`

The SCP reusable workflow **does not declare any `secrets:`**. Adopter wrappers MUST NOT use `secrets: inherit` on the `uses:` invocation. The caller's `GITHUB_TOKEN` is the privilege ceiling; granting any other secret to the workflow expands the blast radius beyond what the federation primitive's threat model assumes.

**Forward-compatibility caveat.** Do not add `secrets: inherit` even if it appears to be a safe no-op at the current SCP version (where the reusable workflow declares no secrets). A future SCP version that introduces any named `secrets:` declaration would retroactively pass every caller secret to the workflow on adopter repos that pre-emptively added `secrets: inherit`. Bypassing this declaration is therefore both unnecessary today AND a forward-compatibility risk.

#### 12.7.11 Freshness warning (post-020H.1)

The SCP reusable workflow annotates `::warning::title=SCP-FRESH-001` on each PR run if your wrapper's pinned SHA is more than 2 minor versions behind the latest SCP release (e.g., your pin is `v1.0.x` but `v1.2.0` is available). The freshness check reads `version-manifest.json` from two sources at workflow-execution time:

1. `${SCP_RUNTIME_ROOT}/version-manifest.json` — the manifest at the SHA your wrapper pins. If absent (wrapper pin predates 020H.1), the check skips silently.
2. `https://raw.githubusercontent.com/jrnb2024/standards-control-plane-/main/version-manifest.json` — the manifest at SCP `main` HEAD. Network errors / 404s skip silently — the check is best-effort and never fails the gate.

Compare the `minor` fields. The minor field is a dotted string `X.Y` (e.g. `1.0`). The check parses both as `(major, minor)` integer pairs and emits the warning when:

- the majors differ (treated as far-behind — always emits), OR
- the majors match AND `(main.minor - pinned.minor) > freshness_warning_threshold_minor` (default `2`).

The `freshness_warning_threshold_minor` value is read from the **PINNED** manifest (the one in `.scp-runtime/`), not from main HEAD's manifest — this prevents an attacker who compromises main HEAD's `version-manifest.json` from silencing the warning by setting the threshold to a large number (closes 020H.1 R1 SAFE-MIN-006).

The annotation is informational; it does not block merge. Adopters who pin via the SCP Renovate preset (§12.7.2) will see automated bump PRs that resolve the warning; adopters whose Renovate is misconfigured can still rely on this CI-time signal.

**Wrapper pins predating 020H.1** silently skip the check (no `version-manifest.json` shipped under the SHA pin). When you next bump to a 020H.1+ release the warning becomes active.

#### 12.7.12 Actions-billing note

Each PR run consumes ~30 seconds of GitHub Actions runner time (warm-start; cold-start adds 10–15s for binary download + SHA verification). GitHub bills Actions in whole minutes per job, rounded up — a ~30–45s job counts as 1 billed minute. Personal-account adopters on the GitHub Free tier with the standard 2,000-minute monthly budget should therefore expect ~2,000 PR runs/month before the budget caps — comfortable headroom for typical adopter PR volumes. Organisation accounts with paid plans have effectively unlimited budget.

#### 12.7.13 Supply-chain posture (post-020H.2)

The reusable workflow downloads three binaries at runtime, all SHA256-verified per platform against `scripts/scp-policy-check.lock`:

- **OPA** (policy evaluator) — pinned by version in `scripts/.tool-versions`; SHA256-verified.
- **Conftest** (Rego harness) — pinned by version + archive SHA256 + binary SHA256 per platform.
- **Regal** (Rego linter) — pinned by version in `scripts/.tool-versions` (`regal 0.40.0`); SHA256-verified per platform via the same `resolve_regal()` helper pattern as `resolve_opa()`. **TF-020H3-001 closed in slice 020H.2** (2026-05-01) ahead of the 2026-05-14 deadline.

**Sigstore attestation status.** OPA `gh attestation verify` is invoked but soft-warns on every run because OPA v1.x has not yet published Sigstore attestations to GitHub's attestation database (HTTP 404). Conftest does not publish attestations either. Regal is published via OPA's pipeline and almost certainly shares the same gap; slice 020H.2 elected NOT to add a parallel `gh attestation verify` for Regal (which would just emit symmetric 404 noise). All three tools' Sigstore re-tightening is tracked as **TF-007** (now extended to cover Regal) — re-tighten to hard-fail when OPA upstream begins publishing attestations.

**Lockfile + version-pin governance.** `scripts/scp-policy-check.lock` and `scripts/.tool-versions` are the cryptographic root-of-trust for every supply-chain check. Both are CODEOWNERS-protected on the SCP repo via `scripts/** @jrnb2024` (and `vendor/** @jrnb2024` for the resolve-fallback path) — so a PR mutating either file must be reviewed (in single-operator count=0 mode the rule is documentary; in multi-maintainer mode it is machine-enforced). Adopters who run their own SCP fork MUST mirror this CODEOWNERS coverage on their fork: add `scripts/** @<owner>` and `vendor/** @<owner>` to the fork's CODEOWNERS, inserted **before** any CODEOWNERS self-protection line (last-match-wins ordering — see the SCP repo's CODEOWNERS comment block for the ORDERING INVARIANT). This is analogous to but distinct from the adopter-side caller-wrapper CODEOWNERS recommendations in §12.7.1 and §12.7.4 — those protect the adopter's own `.github/workflows/policy-check.yml` and `.scp/rule-config.yaml`, not the fork's lockfile.

**RUNNER_TEMP TOCTOU assumption.** `verify_sha256` is called inside each `resolve_<tool>()` function on the path returned to the caller, which then `cp`s into `BIN_DIR`. There is a TOCTOU window between the verify and the cp — closed in practice on GitHub-hosted ubuntu-24.04 by the runner user being the exclusive writer (`RUNNER_TEMP` is owned by the runner user; the ephemeral single-user VM has no other local accounts that could exploit the window between operations). On self-hosted runners, ensure `RUNNER_TEMP` is not group/world-writable and that no other process running as the runner user can substitute the file mid-flight. This is the same design as `resolve_opa` and is not introduced by 020H.2.

**Asset-shape pin.** The lockfile's `regal` block is bare-binary-shaped (single `sha256` field, no `archive_sha256`) because Regal v0.40.0 ships as a bare binary, not a tarball. If Regal upstream moves to tarball shipping in a future release, both the lockfile schema (add `archive_sha256`) and `resolve_regal()` (add a `.gz` extraction branch matching `resolve_conftest()`) need updating in lockstep with the version bump. The current `resolve_regal()` includes `assert_bare_binary_shape()` which reads the first two bytes of the downloaded asset via Python (already a runner dependency for other helpers — no `xxd` reliance) and emits an explicit infra-failure message if the asset begins with the gzip magic bytes (`0x1f 0x8b`). Defends against a silent shape transition.

**Python dependency hash-pinning (post-020M).** As of v1.0.1 the reusable workflow + release-gate workflow install Python dependencies (`pyyaml`, `jsonschema`, and the full transitive closure: `attrs`, `jsonschema-specifications`, `referencing`, `rpds-py`) via `pip install --require-hashes -r requirements/policy-check.txt`. The lockfile `requirements/policy-check.txt` is generated by `pip-compile --generate-hashes` from the input file `requirements/policy-check.in` (which carries the top-level pins `pyyaml==6.0.2` + `jsonschema==4.23.0`). Every wheel hash for every released platform-specific build is recorded; `pip` refuses install if PyPI serves a wheel whose SHA256 is not in the lockfile. Both the lockfile and its `.in` source are CODEOWNERS-protected on the SCP repo via `requirements/** @jrnb2024` (closes 020M R1 SAFE-MAJ-001). The install step is **unconditional** — a presence-only conditional guard (`if ! python3 -c 'import yaml'; then pip install...`) was previously skipping the hash-verified install on hosted ubuntu-24.04 runners which preinstall pyyaml 6.0.1 from apt; the v1.0.1 pattern always runs `pip install --require-hashes` and follows it with a version-pin assertion (`assert yaml.__version__ == '6.0.2'`) to defend against future-PR drift (closes 020M R1 SAFE-MAJ-002). Adopters running their own SCP fork should mirror this CODEOWNERS coverage on their fork: add `requirements/** @<owner>` before the CODEOWNERS self-protection line.

**Lockfile regeneration procedure.** When bumping `pyyaml` or `jsonschema`, edit `requirements/policy-check.in` (the top-level pin source), then run:

```bash
python3 -m venv /tmp/scp-piptools
/tmp/scp-piptools/bin/pip install pip-tools
/tmp/scp-piptools/bin/pip-compile --generate-hashes \
  --output-file requirements/policy-check.txt requirements/policy-check.in
```

Review the diff (transitive deps may also bump), file the version change as a PATCH or MINOR per VERSIONING.md.

> **REGENERATION INVARIANT (closes 020M R2 SAFE-R2-MIN-001 + COMP-R2-MIN-002 — TF-020M-002; extended in 020N R1 SAFE-MIN-001 + COMP-MIN-001 to cover conflict-gate.yml).** When ANY lockfile's top-level pins change, the **version-pin assertion strings hardcoded in the calling workflow files MUST be updated in lockstep**. The SCP repo currently maintains TWO independent lockfiles (each with its own assertion sites):
>
> - **`requirements/policy-check.txt`** (slice 020M, v1.0.1; calling workflows: `policy-check.yml` + `release-gate.yml`). Search `.github/workflows/policy-check.yml` and `.github/workflows/release-gate.yml` for `assert yaml.__version__ ==` and `assert jsonschema.__version__ ==` and update to the new pinned versions.
> - **`requirements/conflict-gate.txt`** (slice 020N; calling workflow: `conflict-gate.yml` only). Search `.github/workflows/conflict-gate.yml` for `assert yaml.__version__ ==`, `assert jsonschema.__version__ ==`, `assert fastapi.__version__ ==`, and `assert pydantic.VERSION ==` and update each to the new pinned versions.
>
> The assertions are intentionally string-literal (not parsed from the lockfile) so a copy/paste regression triggers fail-closed CI on the regeneration PR rather than silently allowing a version skew. Failure mode is loud: SCP-E001 / SCP-E004 annotation listing the actual vs expected versions. **A regeneration PR that bumps `requirements/<lockfile>.in` without bumping the matching assertion strings WILL fail CI** — this is the intended pre-merge enforcement.

#### 12.7.14 Adopter response to SCP-R-004 warn annotations (post-020P / v1.1.0)

SCP-R-004 (added in v1.1.0 per slice 020P / RULE-001) fires at **warn baseline** on each waiver entry whose `reason` field is a non-empty string but does NOT contain at least one HTTP(S) URL. The motivation is auditability: SCP-R-002 already enforces waiver shape (every entry has a non-empty `reason`), but `reason` is free-text — `reason: "approved by Jim"` passes both layers without a machine-checkable link to a reviewable decision artifact (issue, PR, decision log entry).

When you bump your SCP federation primitive SHA pin to v1.1.0, the next PR that touches a waivers payload will surface `::warning::` annotations on every waiver entry whose `reason` lacks a URL. **The warning is non-blocking** — your `policy-check / scp/policy-check` check stays green and merge proceeds. The annotation appears as a yellow triangle in the PR Files-Changed tab on `output/findings/waivers.json` with title `SCP-R-004` and the message format specified in RULE-001 §3.3.

You have three response options. Pick the one that matches your team's posture:

**Option A — Gradual amendment (lowest friction, recommended for most adopters).** On each next-touch PR that modifies a waiver entry (e.g. extending `expires_at`), amend the entry's `reason` to include a URL pointing at the artifact that justified the waiver. For new waivers, include a URL at creation time. The estate's governance pattern (per `MEMORY.md` `project_estate_structure.md`) already routes most waivers through GitHub issues / PRs / `docs/notifications/` files — those have natural URLs. Over a few months your waivers.json migrates organically.

**Option B — `.scp/rule-config.yaml` disable for a transition window.** Add an entry suppressing SCP-R-004 for ~90 days while you do a planned cleanup pass. The shape is:

```yaml
# .scp/rule-config.yaml
rules:
  SCP-R-004:
    disable: true
    expires_at: "2026-08-02"  # ~90 days from v1.1.0 adoption
    justification: "transition window — amending legacy waivers to include URLs per RULE-001"
```

Both `expires_at` and `justification` are required by `schemas/rule-config.schema.json` (per `SCP-E007`). After the transition window expires, the workflow emits a one-release `::warning::` annotation `SCP-R-004 rule-config disable expired YYYY-MM-DD; remove or extend` (per §12.7.7 `SCP-E006`-adjacent behaviour).

**Option C — Bulk-amend cleanup PR (highest friction, most complete).** Open a single PR that walks every waiver in `output/findings/waivers.json` (or wherever your waivers payload lives) and adds a URL to each `reason`. Useful if your repo's waivers count is small (≤20) or if you want to close out the SCP-R-004 surface before any other PRs touch the file.

**Promotion to deny default.** SCP-R-004 stays at warn baseline at v1.1.0. The earliest plausible promotion to deny default is v2.0.0; promotion requires its own RFC-NNN proposal per `docs/reviews/rule-proposals/README.md` §When to file. The proposal would observe the warn-baseline period's actual FP rate against legacy waivers across the estate before justifying the promotion. Adopter waivers already cleaned up under Option A or C are unaffected by promotion; adopters relying on Option B's rule-config disable should remove the disable before the promotion lands (the deny-default rule-config disable still suppresses for one release per `SCP-E006`-adjacent behaviour, but that grace window is your last chance).

**Meta-waiver shape.** If you waive SCP-R-004 itself (e.g. for a single legacy waiver entry that you cannot retrofit a URL onto), the meta-waiver's OWN `reason` field MUST contain a URL — otherwise the meta-waiver is itself a raw finding for SCP-R-004. Per RULE-001 §5: `reason: "waiving SCP-R-004 for legacy waiver W-X per https://github.com/<your-repo>/issues/NNN"`. If you cannot supply a URL in the meta-waiver reason (e.g. governance artifact lives behind VPN with no stable URL), use Option B (rule-config disable) instead.

**Reference.** RULE-001 in `docs/reviews/rule-proposals/RULE-001-waiver-reason-must-cite-issue-or-pr.md` is the canonical specification — it covers the false-positive surface (§4), the implicit-exclusion set (§5), the conflict-gate strategy (§6), the estate-cascade considerations (§7), and the Phase-2 implementation details that produced this v1.1.0 ship. The merged proposal is the durable reference for any adopter question about SCP-R-004 semantics.

#### Reference

- `docs/DECISIONS.md` D-022 (federation-primitive adoption); D-029 (`statuses: write` for readback); D-030 (020J `v*` tag-protection); D-031 (020K CODEOWNERS personal-account); D-032 (020D2 SCP-self required-check); D-033 (rendered context-name `policy-check / scp/policy-check`); D-034 (020F `renovate/v*` tag-protection); D-035 (020G adopter-helper invocation); D-036 (`policies/VERSIONING.md` semver contract + rule-RFC process as estate doctrine; closes 020H.1 (i)+(ii)+(iii) and BS-5); D-040 (slice 020L: 48h is CEILING-not-FLOOR in single-operator mode for the rule-RFC process); D-041 (cross-repo scorecard data shape, opt-in adopter participation); D-042 (aggregator pipeline trust model + mandatory `gh attestation verify --signer-workflow`); D-043 (MCP `scp.consult_scorecard` read-only contract).
- `docs/plans/WP-SCP-020-policy-federation-primitive.md` for the full federation-primitive spec.
- `docs/plans/WP-SCP-023-cross-repo-scorecards.md` for the full cross-repo scorecard plan.
- `docs/reviews/rule-proposals/RULE-001-waiver-reason-must-cite-issue-or-pr.md` (post-v1.1.0) — canonical specification for SCP-R-004.
- `docs/security/branch-protection.md` for the SCP-side protection state.
- §11.10 of this document for the `.scp/rule-config.yaml` CODEOWNERS recommendation referenced from §12.7.4.

#### 12.7.15 Cross-repo scorecard opt-in (post-WP-SCP-023 / v1.2.0)

Adopters MAY opt in to cross-repo scorecard aggregation. This is **optional**; non-participating repos see no behaviour change and are NOT listed as "non-compliant" anywhere — invariant 4 of WP-SCP-023 plan-doc.

**Privacy contract:** the emit aggregator carries **aggregated counts only** — never `reason`, `approved_by`, or `waiver_id` strings from your `output/findings/waivers.json`. Schema (`schemas/scorecard-emit.schema.json`) enforces `additionalProperties: false` at every level. The aggregator NEVER reads your sibling waiver content directly; it consumes only the per-PR `scorecard-emit.json` artifact your wrapper publishes.

**Three steps to opt in:**

1. **Bump your wrapper's SHA pin to v1.2.0 or later.** Renovate will prompt automatically; merge as you would any other SCP version bump.

2. **Set `scorecard-emit: true`** on your wrapper's `with:` block AND grant the two extra permissions the called `attest-scorecard` job needs:
   ```yaml
   permissions:
     contents: read
     statuses: write
     attestations: write   # required by called attest-scorecard job
     id-token: write       # required for OIDC artifact attestation
   jobs:
     policy-check:
       uses: jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<sha>
       with:
         scorecard-emit: true   # opt-in; default false
   ```
   Default-false (no `with:` block at all) means existing wrappers continue to work unchanged with the original two-permission ceiling. **You only add `attestations: write` + `id-token: write` if you opt in** — reusable workflows can never escalate above the caller's permission ceiling, so without these two the workflow fails at startup. The called workflow's `attest-scorecard` job is JOB-SCOPED on these permissions (closes WP-SCP-023 023B R1 MAJ-SAFE-001), so opt-out runs never request an OIDC token even if you grant them at the wrapper level.

   > **Repo visibility / ownership prerequisite (TF-023E-001).** GitHub's `actions/attest-build-provenance` rejects user-owned private repos with HTTP error `Feature not available for user-owned private repositories`. Your repo MUST be either (a) public, or (b) owned by an organisation. If neither applies, the attestation step will fail and your runs will not produce a verifiable emit. The aggregator records repos without a verifiable attestation as `verification_failure` (per D-042 trust model); they are NOT silently accepted.

3. **PR an entry to `docs/scorecards/opt-in-registry.yaml`** in this repo:
   ```yaml
   - repo: "<your-owner>/<your-repo>"
     default_branch: "main"
     expected_scp_workflow_ref: "jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<the-same-sha>"
     opted_in_at: "2026-MM-DDTHH:MM:SSZ"
   ```
   The `expected_scp_workflow_ref` is what the aggregator passes to `gh attestation verify --signer-workflow`. **It MUST match the SHA your wrapper pins.** When you bump the SHA pin, update this entry in the same PR (or a sibling PR before the next aggregator run) — a mismatch records as `verification_failure` in the index, NOT silent acceptance.

**How to read your data:**

- **Markdown report:** `docs/scorecards/<YYYY-MM-DD>.md` is rendered weekly. The aggregator opens a PR for operator review on the SCP repo each Monday; the report lands on `main` once @jrnb2024 reviews and merges.
- **Central index:** `output/scorecards/index.json` carries the canonical machine-readable shape; schema at `schemas/scorecard-index.schema.json`.
- **MCP method:** `scp.consult_scorecard` (per D-043) returns aggregated metrics + verification status. Optional filters: `repo_filter` (single repo) and `since_emitted_at` (ISO-8601). Read-only — no mutation surface.

**Common failure modes you may see in the index:**

| Status | Cause | Remediation |
|---|---|---|
| `verified` | OIDC verification + schema validation succeeded. | None. |
| `verification_failure` | `gh attestation verify --signer-workflow` failed (SHA pin mismatch in `expected_scp_workflow_ref`) OR emit schema validation failed. | Update your registry entry's `expected_scp_workflow_ref` to match your wrapper's pinned SHA. |
| `unreachable` | The aggregator could not reach your repo (rate limit, deletion, transient API error). | If transient, the next weekly run should recover. The aggregator retains the prior verified row's data alongside the unreachable status when available. |
| `no_emit` | No green policy-check run on default branch within last 7 days OR run had no `scorecard-emit` artifact. | Confirm `scorecard-emit: true` is on your wrapper; confirm your default branch's policy-check is green. |

**Verifying a downloaded emit on your side:**

```bash
gh run download <run-id> --repo <your-owner>/<your-repo> --name scorecard-emit
gh attestation verify scorecard-emit/scorecard-emit.json \
  --signer-workflow jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<sha>
```

**Opt-out:** delete your row from `docs/scorecards/opt-in-registry.yaml` via PR. The next aggregator run will not include you. You can also turn off `scorecard-emit: true` in your wrapper independently.

**Reference:** `docs/plans/WP-SCP-023-cross-repo-scorecards.md` (plan-doc); `docs/DECISIONS.md` D-041/D-042/D-043; `schemas/scorecard-emit.schema.json` + `schemas/scorecard-index.schema.json`.

## 13. Recommended Adoption Phases

### Phase 0 — Prep

- choose owners
- choose pilot subsystem
- add overlay directory
- add wrapper scripts
- update governance docs

### Phase 1 — Local advisory use

- run `consult` before implementation work
- run `audit-changed` locally before PRs
- keep domains to `governance,architecture`

### Phase 2 — CI advisory mode

- add PR CI job for changed-file audit
- publish CI artifacts
- do not block merges on warnings yet

### Phase 3 — Scheduled findings refresh

- add scheduled full or subsystem audit
- start maintaining waivers and accepted debt explicitly
- review trend and rollup artifacts regularly

### Phase 4 — Optional service and estate surfacing

- stand up the optional consult service if it helps multiple teams
- plug emitted artifacts into Control Tower or a local dashboard

## 14. Anti-Patterns to Avoid

Do not do these:

- do not make SCP the user's first hard merge gate
- do not onboard all five domains at once unless the repo already trusts the
  weaker advisory domains
- do not put repo-specific assumptions into SCP core when an overlay would do
- do not keep findings in chat, tickets, or screenshots only
- do not create floating TODOs instead of findings, waivers, or backlog items
- do not replace the repo's stronger existing review protocol with a weaker SCP
  process
- do not run a central service and assume that removes the need for repo-local
  CI integration
- do not ship an HTTP service without declaring an `auth_contract` —
  SVC-003 fires `missing-auth-contract`
- do not declare `mode.user_oidc` while implementing the deprecated
  `secrets.compare_digest` bearer path — the code-pattern scan fires
  `impl-missing-user_oidc` (and `impl-undeclared-bearer_legacy` when
  the `secrets.compare_digest` marker is present in source)
- do not treat `--auth-token` (`mode.bearer_legacy`) as a long-term
  default — it is deprecated per D-019 and requires a time-bound
  migration waiver in every interim services.yml
- do not let a `mode.bearer_legacy` waiver lapse silently — renew via
  governance or complete the migration before the close date

## 15. Adoption Acceptance Checklist

A repo is properly onboarded when all of the following are true:

- SCP is installed as a pinned dependency
- a repo-local overlay exists with a named owner
- wrapper scripts exist for consult and audit
- agent instructions explicitly require consult before coding
- CI runs changed-file audit on PRs
- scheduled audit exists for the repo or pilot subsystem
- waivers are stored in repo and time-bound
- findings and reports are inspectable through normal repo workflows
- the team knows who approves waivers and who owns overlay changes

### Additional checks for service-hosting repos

If the repo hosts an HTTP service audited by SCP, also confirm:

- `services.yml` declares an `auth_contract` conforming to SVC-003
  (§11)
- any `mode.bearer_legacy` entry has a registered waiver with an
  owner and close date
- the service's real implementation matches the declared modes (the
  code-pattern scan must not fire `impl-missing-*` or
  `impl-undeclared-*`)

If those are not true, the repo is not actually onboarded.

## 16. Source Practices This Guide Was Derived From

This onboarding guide is aligned to:

- `control-tower/governance/docs/DELIVERY_GOVERNANCE_PROTOCOL.md`
- `control-tower/governance/docs/DOCUMENTATION_STANDARDS.md`
- `control-tower/docs/strategy/platform-conformance-strategy.md`
- `control-tower/docs/handoffs/conformance-prompts.md`
- [STRAT-SCP-001-phased-adoption.md](../strategy/STRAT-SCP-001-phased-adoption.md)
- [README.md](../../README.md)

Those sources collectively define the estate's strongest current practice for:

- governance discipline
- thin conformance integration
- repo-local ownership with shared standards
- advisory-first rollout
- explicit project overlays
