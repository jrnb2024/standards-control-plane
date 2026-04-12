# RequirementSpec — WP-SCP-013 False-Positive Review Loop and Consult Ordering

**Work Package:** `WP-SCP-013`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-013-calibration-and-consult-ordering`

## 1. Purpose

Improve trust in the advisory system by:

1. generating a structured false-positive calibration view from persisted
   findings history
2. tuning consult output ordering so frontend implementation requests receive
   the most actionable material first

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-1301 | The system shall generate a machine-readable false-positive summary from the persisted findings history. |
| FR-SCP-1302 | The false-positive summary shall group false positives by rule and expose recent false-positive findings. |
| FR-SCP-1303 | `audit --write-output` shall refresh the false-positive summary alongside the other persisted artefacts. |
| FR-SCP-1304 | The CLI shall expose a read path for the current false-positive summary. |
| FR-SCP-1305 | Consult responses for frontend-oriented requests shall prioritise approved patterns, open findings, and risks ahead of the full rule list in the response assembly order. |
| FR-SCP-1306 | Pattern ordering for frontend-oriented consult requests shall prefer UX and design patterns ahead of architecture and governance guidance. |

## 3. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-013-001 | A false-positive summary generated from a history store with false-positive findings validates against an explicit schema. | pytest |
| AC-WP-SCP-013-002 | `audit --write-output` writes the false-positive summary artifact. | pytest |
| AC-WP-SCP-013-003 | The CLI can print the current false-positive summary. | pytest |
| AC-WP-SCP-013-004 | Frontend-oriented consult responses order approved patterns ahead of the rule list and prefer UX/design patterns first. | pytest |
| AC-WP-SCP-013-005 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-013/`. | manual review |
