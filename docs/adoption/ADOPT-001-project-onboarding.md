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
3. Draft and track a migration plan to `mode.api_key` by the close
   date. `mode.bearer_legacy` is a machine-caller path; migration
   target is `mode.api_key` (Control Tower-issued agent keys),
   not `mode.user_oidc` (which is a browser cookie session flow).
   Per-app migrations are tracked as separate work packages, not
   as WP-SCP-019 deliverables.

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
