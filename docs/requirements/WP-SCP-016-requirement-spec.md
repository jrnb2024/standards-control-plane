# RequirementSpec — WP-SCP-016 Control Tower Surfacing and Estate Dashboard Outputs

**Work Package:** `WP-SCP-016`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-016-control-tower-outputs`

## 1. Purpose

Emit Control Tower-facing artifacts that surface subsystem and estate status
without moving evaluator runtime responsibilities into Control Tower.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-1601 | The system shall emit a schema-valid Control Tower surface artifact describing the exported dashboard contracts and artifact paths. |
| FR-SCP-1602 | The system shall emit a schema-valid per-subsystem dashboard artifact containing status, scores, open-finding counts, warning counts, and artifact links for the audited subsystem. |
| FR-SCP-1603 | The system shall emit a schema-valid estate dashboard artifact that rolls up all persisted subsystem dashboard artifacts in deterministic order. |
| FR-SCP-1604 | `audit --write-output` and `audit-changed --write-output` shall refresh the audited subsystem dashboard artifact and rebuild the estate dashboard. |
| FR-SCP-1605 | The Control Tower surfacing layer shall consume existing audit, findings, report, and CI outputs rather than invoking evaluators directly. |
| FR-SCP-1606 | The CLI shall expose a read path for the latest Control Tower dashboard artifacts. |

## 3. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-016-001 | Control Tower surface and subsystem dashboard artifacts validate against their schemas and include deterministic artifact links. | pytest |
| AC-WP-SCP-016-002 | Estate dashboard generation rolls up subsystem entries deterministically and emits stable estate counts. | pytest |
| AC-WP-SCP-016-003 | The CLI can print the latest estate dashboard artifact and fails clearly when it is missing. | pytest |
| AC-WP-SCP-016-004 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-016/`. | manual review |
