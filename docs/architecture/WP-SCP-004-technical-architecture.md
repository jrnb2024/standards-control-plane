# TechnicalArchitecture — WP-SCP-004 Architecture Evaluator and Audit Extension

**Work Package:** `WP-SCP-004`  
**Version:** 0.2  
**Status:** Approved for implementation  
**Date:** 2026-04-12

## 1. Objective

Add an architecture evaluator to the existing live audit path without changing
the core audit contract shape.

## 2. Proposed components

### `evaluators/architecture.py`

Responsibilities:

- accept a schema-valid project-area payload
- inspect repo-local file contents for deterministic architecture signals
- emit structured findings and an architecture-domain score
- keep rule checks separated by explicit helper functions

### `audit.py`

Responsibilities:

- reuse the existing scope extraction and normalisation flow
- dispatch architecture evaluation alongside governance when requested
- merge findings, scores, and recommended actions deterministically

### Seeded fixture corpus

Responsibilities:

- provide explicit boundary and orchestration signals for the live example
- stay small enough to remain inspectable in git

### Targeted architecture fixture corpus

Responsibilities:

- provide explicit repo-backed `ARCH-003` and `ARCH-004` cases
- keep signal markers concrete and narrow enough to stay deterministic

## 3. Rule-check approach in this slice

- `ARCH-001`
  - detect obvious service-boundary leaks such as frontend files importing
    backend service modules or code reaching directly across bounded roots
- `ARCH-002`
  - detect UI modules that coordinate multi-step workflow using multiple awaits,
    backend-service imports, or workflow branching markers
- `ARCH-003`
  - detect ad hoc remote-access setup using explicit markers `fetch(`,
    `axios.`, `requests.`, or `httpx.` in non-test feature code outside the
    approved service path
- `ARCH-004`
  - detect backend workflow code using explicit async/eventing markers such as
    `asyncio.create_task(`, `threading.Thread(`, or direct event publication
    when approved wrapper markers like `workflow_runner`, `task_queue`, or
    `event_bus` are absent

## 4. Output rules

- architecture findings sorted by severity then finding id
- combined audit findings sorted by severity then finding id after merge
- governance and architecture scores emitted independently
- unsupported domains remain explicit in `domain_status`

## 5. Extension points

- richer import graph analysis
- subsystem-specific boundary rules
- confidence taxonomy beyond rule-local confidence values
- findings lifecycle and report generation
