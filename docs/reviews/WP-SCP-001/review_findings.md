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

## Gate B code review

**Date:** 2026-04-11  
**Stage:** Gate B code review

### F-WP-SCP-001-006

**Severity:** HIGH  
**Summary:** Exact-area or exact-path findings outside the requested domains
could be dropped from consult output, hiding relevant open issues.

**Disposition:** FIXED IN CODE  

Changes made:

- `select_consult_findings()` now includes open findings that match requested
  domains or that match the exact area/path
- added test coverage for area-specific findings surfacing outside requested
  domains

### F-WP-SCP-001-007

**Severity:** HIGH  
**Summary:** Draft standards were treated as usable consult output.

**Disposition:** FIXED IN CODE  

Changes made:

- restricted consult retrieval to `active` standards only
- retained status in the structured registry inspection output

### F-WP-SCP-001-008

**Severity:** MEDIUM  
**Summary:** Seeded findings evidence was not inspectable inside the repo.

**Disposition:** FIXED IN CODE  

Changes made:

- moved seeded pilot evidence into `fixtures/returns-pilot/`
- findings loader now enforces repo-local evidence paths for this slice
- removed placeholder `snippet_ref` usage from seeded evidence

### F-WP-SCP-001-009

**Severity:** MEDIUM  
**Summary:** Registry file references could escape the intended standards
boundary.

**Disposition:** FIXED IN CODE  

Changes made:

- registry path resolution now enforces boundary roots
- added explicit escape test coverage

### F-WP-SCP-001-010

**Severity:** LOW  
**Summary:** Duplicate request domains or paths could duplicate consult output.

**Disposition:** FIXED IN CODE  

Changes made:

- consult request domains and paths are now deduplicated while preserving order

### F-WP-SCP-001-011

**Severity:** MEDIUM  
**Summary:** CLI-level acceptance coverage for `consult` and `show-registry`
was incomplete.

**Disposition:** FIXED IN CODE  

Changes made:

- added CLI subprocess tests for `consult` and `show-registry`
- added explicit guidance assertion in consult response tests

### F-WP-SCP-001-012

**Severity:** HIGH  
**Summary:** Evidence-pack files were reported missing during early code review.

**Disposition:** SUPERSEDED DURING REVIEW  

Changes made:

- added `implementation_notes.md`
- added `acceptance_verification.md`
- added `test_results.txt`

## Gate B outcome

Code review findings were dispositioned and re-verified locally.
