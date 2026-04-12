# RequirementSpec — WP-SCP-011 Design-System Scaffolding and Evaluator Shell

**Work Package:** `WP-SCP-011`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-011-design-evaluator`

## 1. Purpose

Add the first bounded design-system domain slice so consult and audit can spot
obvious off-pattern frontend implementation without widening into full visual QA.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-1101 | The standards registry shall include an active `design` domain with rules and patterns. |
| FR-SCP-1102 | Audit shall support an evaluated `design` domain rather than reporting it as not implemented. |
| FR-SCP-1103 | The initial design evaluator shall check for bounded, code-backed signals only: off-pattern raw primitives, missing token usage when visual styles are present, and missing interactive-state markers. |
| FR-SCP-1104 | Design findings shall remain advisory and confidence-aware in this slice. |
| FR-SCP-1105 | The repo shall include one failing design-drift fixture and one stable design fixture. |

## 3. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1101 | The design evaluator must remain deterministic and repo-bounded. |
| NFR-1102 | The evaluator must not require Storybook, screenshots, or browser rendering in this slice. |
| NFR-1103 | The checks must stay narrow enough to explain directly from file evidence. |

## 4. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-011-001 | The registry loads the design domain rules and patterns successfully. | pytest |
| AC-WP-SCP-011-002 | Audit requests that include `design` now report the domain as evaluated. | pytest |
| AC-WP-SCP-011-003 | The failing design fixture produces bounded findings for off-pattern primitives, token drift, and missing interactive states. | pytest |
| AC-WP-SCP-011-004 | The stable design fixture produces zero design findings and a clean score. | pytest |
| AC-WP-SCP-011-005 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-011/`. | manual review |
