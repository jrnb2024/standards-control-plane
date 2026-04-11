# Strategy — WP-SCP-004 Architecture Evaluator and Audit Extension

**Work Package:** `WP-SCP-004`  
**Version:** 0.2  
**Status:** Approved for implementation  
**Date:** 2026-04-12

## 1. Strategy

Make the architecture domain real by reusing the live audit path introduced in
`WP-SCP-003` and adding deterministic rule checks over explicit file-content
signals.

## 2. Why this slice now

The project now has:

- a live audit path
- a stable project-area contract
- governance evaluation wired into audit
- active architecture rules and patterns in the registry

The next useful step is to make the second core domain real before moving into
findings lifecycle and report generation.

## 3. Delivery shape

### 3.1 Seed explicit architecture signals first

The current returns pilot files are too skeletal to support honest
architecture findings. This slice should update the seeded corpus so the live
audit example is backed by concrete code signals for boundary leaks and UI
orchestration drift.

### 3.2 Use bounded heuristics, not broad inference

This slice should implement explicit checks such as:

- cross-boundary imports or backend calls from frontend code
- orchestration markers in UI modules
- ad hoc remote-access setup in feature code using explicit markers like
  `fetch(`, `axios.`, `requests.`, or `httpx.` outside approved service paths
- inconsistent async or eventing markers in backend workflow code using explicit
  markers like `asyncio.create_task(`, `threading.Thread(`, or direct event
  publication when approved wrappers such as `workflow_runner`, `task_queue`,
  or `event_bus` markers are absent

If a rule cannot be defended with explicit signals in this slice, it should
stay narrow rather than pretending to be smarter than it is.

### 3.3 Use repo-backed targeted fixtures for the hard-to-prove rules

The returns pilot should prove `ARCH-001` and `ARCH-002`.

`ARCH-003` and `ARCH-004` should be anchored to a second repo-backed fixture
corpus so the evaluator tests do not pass on synthetic payloads alone.

### 3.4 Keep audit composition simple

The audit dispatcher should:

1. normalise the requested scope once
2. run governance when requested
3. run architecture when requested
4. merge findings and per-domain scores deterministically
5. keep unsupported domains explicit in `domain_status`
6. preserve deterministic finding order after merge

## 4. Scoring approach for this slice

Use the same severity-deduction model already used in governance:

- start at `100`
- subtract `30` per high-severity finding
- subtract `15` per medium-severity finding
- subtract `5` per low-severity finding
- floor at `0`

This score is the architecture-domain score only.

## 5. Example and evidence strategy

This slice should prove:

- seeded returns-pilot audit output with governance and architecture both live
- targeted repo-backed fixture coverage for `ARCH-003` and `ARCH-004`
- deterministic ordering when multiple architecture findings exist
- explicit unsupported-domain coverage in mixed-domain audit requests
- complete work-package evidence under `docs/reviews/WP-SCP-004/`

## 6. Expected follow-on

If this slice lands cleanly, the next work package can shift from evaluator
creation to findings persistence and reporting without needing another audit
path redesign.
