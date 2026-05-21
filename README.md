# Standards Control Plane

**Status (2026-05-16):** Federation primitive shipped + dogfooded; estate cascade at canary-start (0 of 5 cohort adopters live; 024C PIM canary at SCP-side R-fixpoint, awaiting operator-attended Phase 1 + ≥1-week bake).
**Latest release:** v1.2.0 (opt-in cross-repo scorecard emit; 2026-05-03)

📖 **Read first:** [`docs/OVERVIEW.md`](docs/OVERVIEW.md) — the integrated what/how/why doc covering architecture, logical flows, platform-service interactions, current scope, and forward direction. The remainder of this README is historical context.

---

**Original framing (preserved for history):**

`standards-control-plane` is the proposed standalone home for a shared internal
consult-and-audit system for agent-assisted software delivery.

The intent is to keep the core evaluator and findings system independent from:

- `mapp-doc-agent`, which is already the estate's documentation retrieval layer
- `control-tower`, which already owns governance, conformance language, and
  estate operations

That gives this project a clean boundary:

- **source of truth for standards and findings**
- **consult interface for implementation agents**
- **audit interface for local, CI, and scheduled review**
- **integration points into docs-agent and Control Tower later**

The scheduled autonomous delivery queue through `WP-SCP-018` is merged on
`main`. `WP-SCP-019` (Service Auth Contract, SVC-003) is the new programme
increment — slices 019A–019F are complete on
`feature/wp-scp-019-svc-003-auth-contract` and the PR is pending. See
[`docs/STATUS.md`](docs/STATUS.md) for the current slice state and the
SVC-003 freeze-directive unfreeze triggers, and
[`docs/adoption/ADOPT-001-project-onboarding.md`](docs/adoption/ADOPT-001-project-onboarding.md)
§11 for the rewritten service-lifecycle auth-contract adopter guide.

## Why this name

`standards-control-plane` is deliberately plain. It describes a central system
that governs consult and audit behaviour across multiple repos without forcing
either the `mapp-doc-agent` or `control-tower` boundary.

It can still present itself externally as the **Standards Consultant and Audit
Service**.

## Initial document map

- [`docs/adoption/ADOPT-001-project-onboarding.md`](docs/adoption/ADOPT-001-project-onboarding.md)
  - the single onboarding brief for other repos integrating SCP into local governance and CI
- [`docs/deployment.md`](docs/deployment.md)
  - local tunnel, Control Tower SSO, Cloudflare, and staging deployment runbook
- [`docs/strategy/STRAT-SCP-001-phased-adoption.md`](docs/strategy/STRAT-SCP-001-phased-adoption.md)
  - recommended rollout strategy, scope control, architecture direction, and
  phasing
- [`docs/strategy/STRAT-SCP-002-autonomous-delivery.md`](docs/strategy/STRAT-SCP-002-autonomous-delivery.md)
  - unattended delivery protocol, default decision rules, blocker policy, and
    review-loop limits
- [`docs/BACKLOG.md`](docs/BACKLOG.md)
  - initial work packages and sequencing
- [`docs/plans/PROG-SCP-001-autonomous-execution-plan.md`](docs/plans/PROG-SCP-001-autonomous-execution-plan.md)
  - ordered work-package queue for end-to-end autonomous execution
- [`docs/reference/original-user-spec-2026-04-11.md`](docs/reference/original-user-spec-2026-04-11.md)
  - verbatim captured source specification from the planning session
- [`docs/reference/assessment-2026-04-11.md`](docs/reference/assessment-2026-04-11.md)
  - placement recommendation and assessment of viability

## Current recommendation

Build this as a new standalone app.

- Use a **local standards registry** as the phase 1 source of truth.
- Use **docs-agent** later as a retrieval augmentation layer for historical
  reviews and broader estate context.
- Use **Control Tower** later as the place to surface reports, waivers, and
  cross-project visibility.

## Phase 1 Progress

The repository now includes the phase 1 scaffold plus the first two governed
implementation slices:

- Python package layout under `src/standards_control_plane/`
- explicit JSON schemas under `schemas/`
- seed governance and architecture standards under `standards/`
- live standards registry loading and validation
- live read-only findings-store loading for consult
- deterministic consult response assembly
- repo-bounded scope extraction
- explicit extracted-scope and project-area contracts
- deterministic area normalisation for the seeded returns pilot
- live governance evaluator and governance audit path
- live architecture evaluator and architecture audit path
- durable open-findings and findings-history persistence from the live audit path
- live markdown review reports and subsystem-keyed area summaries from the write-backed audit path
- repo-local waiver input handling for audit-time exceptions
- shared deterministic score calculation with explicit documentation
- structured review-evidence parsing and consult-time historical review references
- example consult and audit payloads under `examples/`
- output placeholders under `output/`
- validation and retrieval tests under `tests/`

## Quick start

```bash
cd /Users/amplience/Projects/standards-control-plane
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

### CLI

After editable install:

```bash
standards-control-plane show-registry
standards-control-plane consult --request examples/consult-request.json
standards-control-plane audit --request examples/audit-request.json
standards-control-plane audit --request examples/audit-request.json --write-output
standards-control-plane audit-changed --base-ref origin/main --head-ref HEAD --domains governance,architecture --subsystem returns --standards-version 2026-04-12
standards-control-plane findings
standards-control-plane report
standards-control-plane ci
standards-control-plane control-tower
standards-control-plane estate-report --repo-output output --write-output
standards-control-plane show-registry --overlay path/to/project-standards
standards-control-plane consult --request examples/consult-request.json --overlay path/to/project-standards
standards-control-plane serve --port 3787 --auth-token local-dev-token --overlay path/to/project-standards
```

When the service is running:

- open `http://127.0.0.1:3787/` for the built-in frontend
- open `http://127.0.0.1:3787/docs/adoption` for the onboarding guide
- query `http://127.0.0.1:3787/status-app/health` for machine-readable status

Without installation, the local module path works too:

```bash
PYTHONPATH=src python3 -m standards_control_plane.cli show-registry
PYTHONPATH=src python3 -m standards_control_plane.cli consult --request examples/consult-request.json
```

Current state:

- `consult` is live for governance and architecture registry retrieval
- `consult` includes bounded historical review references when structured review evidence exists
- `show-registry` prints the structured registry content actually used by consult
- `findings` validates and prints the read-only findings store
- `audit` is live for governance and architecture, with unsupported requested domains emitted as `not_evaluated`
- `audit` honours active waivers from `output/findings/waivers.json`
- `audit --write-output` reconciles and persists `open-findings.json` plus `findings-history.json`
- `audit --write-output` and `audit-changed --write-output` also emit CI-facing artifacts under `output/ci/`
- `audit --write-output` and `audit-changed --write-output` also emit Control Tower-facing artifacts under `output/control-tower/`
- `report` prints the freshest generated `latest-review.md` and fails explicitly if the report is stale or missing
- `ci` prints the latest advisory CI summary or JSON artifact
- `control-tower` prints the latest estate dashboard or Control Tower surface artifact
- `estate-report` aggregates one or more repo `output/` directories into a portfolio dashboard, history, and trend view under `output/estate/`
- `--overlay` lets consult, audit, audit-changed, show-registry, and service mode merge project-specific standards over the shared registry
- `serve` exposes `GET /health`, `GET /registry`, `POST /consult`, and `POST /audit` over a FastAPI service surface
- `serve` also exposes a built-in landing page at `/`, the onboarding guide at `/docs/adoption`, and status integration health at `/status-app/health`
- browser access can be protected with Control Tower OIDC and estate SSO by setting `AUTH_ENABLED=true`, `CT_APP_ID`, and `PUBLIC_BASE_URL`
- the service also preserves optional legacy bearer auth for machine callers during transition
- SDK-backed BFF auth routes are mounted at `/api/auth/*` for token exchange, refresh, logout, and `/api/auth/me`
- project-area normalisation now preserves explicit evidence buckets for Storybook metadata, screenshots, and graph artifacts without changing the existing bucket semantics

Score semantics are documented in
[`docs/reference/score-model-2026-04-12.md`](docs/reference/score-model-2026-04-12.md).

The first pilot trust-tuning note lives in
[`docs/reference/pilot-tuning-returns-2026-04-12.md`](docs/reference/pilot-tuning-returns-2026-04-12.md).

## Autonomous delivery

The repo now carries an explicit unattended execution protocol and ordered
programme plan:

- use [`docs/strategy/STRAT-SCP-002-autonomous-delivery.md`](docs/strategy/STRAT-SCP-002-autonomous-delivery.md)
  for default decisions, blocker thresholds, and review-loop limits
- use [`docs/plans/PROG-SCP-001-autonomous-execution-plan.md`](docs/plans/PROG-SCP-001-autonomous-execution-plan.md)
  as the canonical work-package queue from the current repo state to the end of
  the programme
