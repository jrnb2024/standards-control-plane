# RequirementSpec — WP-SCP-010 UX / IA Scaffolding and Evaluator Shell

**Work Package:** `WP-SCP-010`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-010-ux-evaluator`

## 1. Purpose

Add the first bounded UX / IA domain slice so consult and audit can surface
basic screen-structure advice without pretending to perform rich design review.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-1001 | The standards registry shall include an active `ux` domain with rule and pattern scaffolding. |
| FR-SCP-1002 | Audit shall support an evaluated `ux` domain rather than reporting it as not implemented. |
| FR-SCP-1003 | The initial UX evaluator shall check for bounded, explicit signals only: primary action clarity, basic state coverage, and navigation or screen-role clarity. |
| FR-SCP-1004 | UX findings shall remain advisory and confidence-aware in this slice. |
| FR-SCP-1005 | Consult responses for UX requests shall surface active UX rules and patterns from the live registry. |
| FR-SCP-1006 | The repo shall include one stable UX fixture that exercises the evaluator with zero findings. |

## 3. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1001 | The UX evaluator must remain deterministic and repo-bounded. |
| NFR-1002 | The evaluator shell must not attempt screenshot, browser, or Figma analysis in this slice. |
| NFR-1003 | The heuristics must stay narrow enough to be explainable from file evidence. |

## 4. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-010-001 | The registry loads the UX domain rules and patterns successfully. | pytest |
| AC-WP-SCP-010-002 | Audit requests that include `ux` now report the domain as evaluated. | pytest |
| AC-WP-SCP-010-003 | The seeded Returns pilot produces bounded UX findings for missing primary-action, state-coverage, and navigation signals. | pytest |
| AC-WP-SCP-010-004 | The stable UX fixture produces zero UX findings and a clean score. | pytest |
| AC-WP-SCP-010-005 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-010/`. | manual review |

## 5. Scope Boundary

### In scope

- UX standards scaffolding
- bounded UX evaluator shell
- one stable UX fixture
- registry and audit wiring
- tests and evidence pack

### Out of scope

- screenshot analysis
- advanced journey modelling
- accessibility auditing beyond obvious structural signals
- design-system or product-coherence checks

## 5.1 Backlog mapping

### Consumed in this work package

- `SCP-040` — UX / IA standards scaffolding and evaluator shell

### Explicitly not consumed in this work package

- `SCP-041` — design-system evaluator shell
- `SCP-042` — product coherence evaluator shell
- `SCP-045` — consult ordering tune-up

## 6. Review Protocol

Plan review and code review for this work package must each use three reviewer
roles:

1. architecture / structure
2. security / quality / governance
3. completeness / acceptance coverage

Evidence is stored under `docs/reviews/WP-SCP-010/`.
