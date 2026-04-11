# WP-SCP-001 — Review Findings

**Date:** 2026-04-11  
**Stage:** Gate A plan review  
**Branch:** `feature/wp-scp-001-registry-consult`

## Reviewer roles

1. Architecture / structure
2. Security / quality / governance
3. Completeness / acceptance coverage

## Findings and dispositions

### F-WP-SCP-001-001

**Severity:** HIGH  
**Summary:** WP-SCP-001 depended on a findings store that was not explicitly in
scope or represented in backlog sequencing.

**Disposition:** FIXED IN PLAN  

Changes made:

- `D-003` updated to include minimal findings loading
- backlog updated with `SCP-015A`
- requirement, architecture, and programme docs updated to make the read-only
  findings-store dependency explicit

### F-WP-SCP-001-002

**Severity:** HIGH  
**Summary:** The review process and evidence path were not auditable enough in
the work package docs.

**Disposition:** FIXED IN PLAN  

Changes made:

- added review protocol section to the RequirementSpec
- added review/evidence rules to the ProgrammePlan
- aligned evidence location to `docs/reviews/WP-SCP-001/`

### F-WP-SCP-001-003

**Severity:** MEDIUM  
**Summary:** Acceptance criteria did not explicitly prove pattern retrieval,
determinism, or registry inspection behaviour.

**Disposition:** FIXED IN PLAN  

Changes made:

- added ACs for pattern retrieval
- added AC for deterministic repeat-run behaviour
- added AC for `show-registry`

### F-WP-SCP-001-004

**Severity:** MEDIUM  
**Summary:** Findings matching was too narrow and would miss domain-only
findings.

**Disposition:** FIXED IN PLAN  

Changes made:

- updated architecture doc to use domain-first matching with area/path
  refinement
- updated RequirementSpec to make matching semantics explicit

### F-WP-SCP-001-005

**Severity:** MEDIUM  
**Summary:** Scope boundary between this work package and later backlog items
was too loose.

**Disposition:** FIXED IN PLAN  

Changes made:

- added backlog mapping section to the RequirementSpec
- explicitly excluded evaluator and lifecycle work from this slice

## Gate A outcome

Plan review findings were converged and addressed in the planning artefacts.

`WP-SCP-001` is cleared to enter implementation.

