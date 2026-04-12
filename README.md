# Standards Control Plane

**Status:** In Delivery  
**Date:** 2026-04-11  
**Working service name:** Standards Consultant and Audit Service

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

## Why this name

`standards-control-plane` is deliberately plain. It describes a central system
that governs consult and audit behaviour across multiple repos without forcing
either the `mapp-doc-agent` or `control-tower` boundary.

It can still present itself externally as the **Standards Consultant and Audit
Service**.

## Initial document map

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
standards-control-plane findings
standards-control-plane report
```

Without installation, the local module path works too:

```bash
PYTHONPATH=src python3 -m standards_control_plane.cli show-registry
PYTHONPATH=src python3 -m standards_control_plane.cli consult --request examples/consult-request.json
```

Current state:

- `consult` is live for governance and architecture registry retrieval
- `show-registry` prints the structured registry content actually used by consult
- `findings` validates and prints the read-only findings store
- `audit` is live for governance and architecture, with unsupported requested domains emitted as `not_evaluated`
- `audit` honours active waivers from `output/findings/waivers.json`
- `audit --write-output` reconciles and persists `open-findings.json` plus `findings-history.json`
- `report` prints the freshest generated `latest-review.md` and fails explicitly if the report is stale or missing

Score semantics are documented in
[`docs/reference/score-model-2026-04-12.md`](docs/reference/score-model-2026-04-12.md).

## Autonomous delivery

The repo now carries an explicit unattended execution protocol and ordered
programme plan:

- use [`docs/strategy/STRAT-SCP-002-autonomous-delivery.md`](docs/strategy/STRAT-SCP-002-autonomous-delivery.md)
  for default decisions, blocker thresholds, and review-loop limits
- use [`docs/plans/PROG-SCP-001-autonomous-execution-plan.md`](docs/plans/PROG-SCP-001-autonomous-execution-plan.md)
  as the canonical work-package queue from the current repo state to the end of
  the programme
