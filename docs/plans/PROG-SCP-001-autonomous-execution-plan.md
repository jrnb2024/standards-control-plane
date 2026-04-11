# Programme Plan — PROG-SCP-001 Autonomous Execution Plan

**Programme ID:** `PROG-SCP-001`  
**Status:** Active  
**Date:** 2026-04-11

## 1. Purpose

Provide the ordered work-package queue from the current repo state to the end
of the currently defined programme, so unattended execution can continue
without waiting for user prioritisation.

## 2. Starting point

Current merged state:

- consult retrieval is live
- extractor and project-area normaliser are live
- governance evaluator and governance audit path are live
- branch / PR / merge discipline has been exercised through `WP-SCP-003`

Next implementation work starts at `WP-SCP-004`.

## 3. Work-package queue

### Phase 1 completion

| Work package | Backlog coverage | Goal | Exit signal |
|--------------|------------------|------|-------------|
| `WP-SCP-004` | `SCP-017` | Add architecture evaluator and extend live audit to governance plus architecture. | Architecture findings and scores are emitted from the live audit path with tests and examples. |
| `WP-SCP-005` | `SCP-018`, `SCP-030`, `SCP-032` | Add finding identity, lifecycle foundation, deduplication, and history persistence. | Open findings, history, and finding updates become durable and deterministic. |
| `WP-SCP-006` | remaining `SCP-018`, `SCP-034` | Generate markdown reports and area summaries from structured findings. | `report` becomes live and area summary outputs are written deterministically. |
| `WP-SCP-007` | `SCP-031`, `SCP-033` | Add waivers and explicit score documentation. | Waivers are honoured by audit and score calculations are documented and tested. |
| `WP-SCP-008` | `SCP-022`, `SCP-035`, `SCP-037` | Harden review-evidence contract, add historical review retrieval, and run the first pilot tuning pass. | Review evidence stops relying on path-only signals and pilot false positives are reduced with documented calibration. |

### Phase 3 expansion

| Work package | Backlog coverage | Goal | Exit signal |
|--------------|------------------|------|-------------|
| `WP-SCP-009` | `SCP-043` | Define confidence taxonomy and evidence classes before broader inference. | Confidence classes exist in contracts/docs and evaluator outputs use them consistently. |
| `WP-SCP-010` | `SCP-040` | Add UX / IA standards scaffolding and evaluator shell. | UX rules and consult/audit scaffolding are live with bounded checks. |
| `WP-SCP-011` | `SCP-041` | Add design-system standards scaffolding and evaluator shell. | Design checks are live with explicit evidence and bounded scope. |
| `WP-SCP-012` | `SCP-042` | Add product-coherence evaluator shell. | Product guidance is structured, confidence-aware, and non-authoritative. |
| `WP-SCP-013` | `SCP-044`, `SCP-045` | Add false-positive review loop and tune consult ordering for front-end use. | Review calibration is documented and consult output ordering improves implementation usefulness. |

### Phase 4 delivery surfacing

| Work package | Backlog coverage | Goal | Exit signal |
|--------------|------------------|------|-------------|
| `WP-SCP-014` | `SCP-050` | Add changed-file scoped audit mode for PR use. | Changed-file audit runs deterministically and stays repo-bounded. |
| `WP-SCP-015` | `SCP-051`, `SCP-052` | Add CI-oriented outputs and warning thresholds. | CI can consume JSON/markdown outputs and warning thresholds are available without hard blocking. |
| `WP-SCP-016` | `SCP-053`, `SCP-054` | Define Control Tower surfacing and estate dashboard outputs. | Control Tower-facing summaries are emitted without coupling evaluator runtime into Control Tower. |

### Phase 5 promotion to shared service

| Work package | Backlog coverage | Goal | Exit signal |
|--------------|------------------|------|-------------|
| `WP-SCP-017` | `SCP-060`, `SCP-061` | Add service API and project overlay mechanism. | CLI and service modes both work against shared standards plus per-project overlays. |
| `WP-SCP-018` | `SCP-062`, `SCP-063`, `SCP-064` | Add auth, multi-repo reporting, and richer evidence adapters. | Shared use is governed, reporting spans repos, and richer evidence ingestion remains optional. |

## 4. Sequence rules

The queue above is the default execution order.

Do not reorder work packages unless:

- a dependency proves wrong in implementation, or
- a backlog item becomes a blocker for the current slice

If reordering is required, record it in `docs/STATUS.md` and explain why in the
next work-package planning pack.

## 5. Unattended continuation rules

For each work package:

- use the autonomous delivery strategy in
  `docs/strategy/STRAT-SCP-002-autonomous-delivery.md`
- keep one branch and one PR per work package
- carry forward non-blocking residuals to backlog
- do not wait for user input unless a hard blocker is hit

## 6. Definition of “end to end” for unattended execution

The programme is considered able to run end to end when:

- the next work package is always unambiguous
- default decisions are documented
- review loops are bounded
- backlog carry-forward is explicit
- the repo can move from one merged work package to the next without user
  clarification
