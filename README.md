# Standards Control Plane

**Status:** Planning  
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
- [`docs/BACKLOG.md`](docs/BACKLOG.md)
  - initial work packages and sequencing
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

## Phase 1 Scaffold

The repository now includes an initial implementation scaffold:

- Python package layout under `src/standards_control_plane/`
- explicit JSON schemas under `schemas/`
- seed governance and architecture standards under `standards/`
- example consult and audit payloads under `examples/`
- output placeholders under `output/`
- basic validation tests under `tests/`

## Quick start

```bash
cd /Users/amplience/Projects/standards-control-plane
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

### CLI scaffold

```bash
standards-control-plane show-registry
standards-control-plane consult --request examples/consult-request.json
standards-control-plane audit --request examples/audit-request.json
standards-control-plane findings
standards-control-plane report
```

The `consult` and `audit` commands are scaffold implementations at this stage:
they validate the request contracts and emit schema-valid placeholder outputs.
