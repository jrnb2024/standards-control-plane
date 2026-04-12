# RequirementSpec — WP-SCP-012 Product-Coherence Evaluator Shell

**Work Package:** `WP-SCP-012`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-012-product-evaluator`

## 1. Purpose

Add the first bounded product-coherence domain so the control plane can surface
obvious intent drift without pretending to replace product judgement.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-1201 | The standards registry shall include an active `product` domain with rules and patterns. |
| FR-SCP-1202 | Audit shall support an evaluated `product` domain rather than reporting it as not implemented. |
| FR-SCP-1203 | The initial product evaluator shall check bounded, advisory signals only: explicit job-to-be-done language, action alignment to user outcome, and user-facing terminology. |
| FR-SCP-1204 | Product findings shall remain advisory and confidence-aware, with low or medium confidence only in this slice. |
| FR-SCP-1205 | The repo shall include one product-drift fixture and one stable product fixture. |

## 3. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-012-001 | The registry loads the product domain rules and patterns successfully. | pytest |
| AC-WP-SCP-012-002 | Audit requests that include `product` now report the domain as evaluated. | pytest |
| AC-WP-SCP-012-003 | The product-drift fixture produces bounded advisory findings for intent drift and language drift. | pytest |
| AC-WP-SCP-012-004 | The stable product fixture produces zero product findings and a clean score. | pytest |
| AC-WP-SCP-012-005 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-012/`. | manual review |
