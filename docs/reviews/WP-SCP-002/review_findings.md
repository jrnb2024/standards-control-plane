# WP-SCP-002 — Review Findings

**Date:** 2026-04-11  
**Stage:** Gate A plan review  
**Branch:** `feature/wp-scp-002-extractor-normaliser`

## Reviewer roles

1. Architecture / structure
2. Security / quality / governance
3. Completeness / acceptance coverage

## Findings and dispositions

### F-WP-SCP-002-001

**Severity:** HIGH  
**Summary:** The extractor and normaliser seam was ambiguous, with
classification responsibilities split inconsistently across the docs.

**Disposition:** FIXED IN PLAN  

Changes made:

- moved file classification responsibility explicitly into the normaliser
- defined the extractor as a canonical file-record emitter
- aligned RequirementSpec, Strategy, and TechnicalArchitecture

### F-WP-SCP-002-002

**Severity:** HIGH  
**Summary:** The extractor-to-normaliser interface lacked an explicit contract.

**Disposition:** FIXED IN PLAN  

Changes made:

- added extracted-file-record contract requirement
- added `extracted-file-record.schema.json` to the technical design

### F-WP-SCP-002-003

**Severity:** HIGH  
**Summary:** Boundary handling did not explicitly cover canonicalisation and
symlink-led escapes.

**Disposition:** FIXED IN PLAN  

Changes made:

- added canonicalisation requirement before recursion
- added explicit rejection of boundary escapes introduced through symlinks

### F-WP-SCP-002-004

**Severity:** HIGH  
**Summary:** Fixture coverage was under-specified, so the slice could pass
without exercising all declared extraction buckets.

**Disposition:** FIXED IN PLAN  

Changes made:

- added AC requiring one concrete fixture for each declared bucket
- added fixture-matrix language to the strategy

### F-WP-SCP-002-005

**Severity:** MEDIUM  
**Summary:** Determinism requirements did not specify a canonical ordering rule.

**Disposition:** FIXED IN PLAN  

Changes made:

- added canonical repo-relative path ordering to NFRs
- added explicit determinism rules to the technical design

### F-WP-SCP-002-006

**Severity:** MEDIUM  
**Summary:** Area inference was too open-ended and risked synthesising plausible
but untrustworthy area identifiers.

**Disposition:** FIXED IN PLAN  

Changes made:

- removed open-ended fallback inference
- now require a supported deterministic rule or an explicit area hint

### F-WP-SCP-002-007

**Severity:** MEDIUM  
**Summary:** Evidence-file requirements were named but not content-defined.

**Disposition:** FIXED IN PLAN  

Changes made:

- added minimum contents for every required evidence file
- aligned RequirementSpec and ProgrammePlan

## Gate A outcome

Plan review findings were converged and addressed in the planning artefacts.

`WP-SCP-002` is cleared to enter implementation.

## Gate B code review

**Date:** 2026-04-11  
**Stage:** Gate B code review

### F-WP-SCP-002-008

**Severity:** HIGH  
**Summary:** The extractor allowed requested-scope semantics to drift through
symlink handling.

**Disposition:** FIXED IN CODE  

Changes made:

- reject symlinked scope paths
- reject symlinked files and directories encountered during extraction
- added explicit test coverage for repo-boundary and subtree-boundary symlink
  cases

### F-WP-SCP-002-009

**Severity:** HIGH  
**Summary:** The project-area contract under-represented `SCP-013` by lacking
first-class `docs` and `code_paths` outputs.

**Disposition:** FIXED IN CODE  

Changes made:

- added `docs` and `code_paths` artefact buckets to the project-area contract
- updated fixtures, examples, tests, and evidence to cover those buckets

### F-WP-SCP-002-010

**Severity:** MEDIUM  
**Summary:** The previous `standards_references` bucket widened the contract in
the wrong direction before evaluator semantics existed.

**Disposition:** FIXED IN CODE  

Changes made:

- removed `standards_references`
- replaced it with broader, backlog-aligned `docs`

### F-WP-SCP-002-011

**Severity:** MEDIUM  
**Summary:** `ui_components` was too broad and incorrectly absorbed shared
frontend utilities.

**Disposition:** FIXED IN CODE  

Changes made:

- narrowed UI-component detection to actual component-like `.tsx/.jsx` files
- kept `frontend/app/shared/filters.ts` in `code_paths` instead of
  `ui_components`

### F-WP-SCP-002-012

**Severity:** MEDIUM  
**Summary:** Area inference remained too open-ended and could synthesise a
plausible but untrustworthy area identifier.

**Disposition:** FIXED IN CODE  

Changes made:

- limited route-based inference to explicit page files
- require `area_hint` when no supported deterministic rule applies

### F-WP-SCP-002-013

**Severity:** MEDIUM  
**Summary:** The code-review evidence record itself was incomplete during the
first review pass.

**Disposition:** FIXED IN REVIEW PACK  

Changes made:

- added implementation evidence files
- recorded code-review findings and dispositions in this file
- refreshed acceptance and test-result evidence

## Gate B outcome

Code review findings were dispositioned and the updated implementation was
re-reviewed with no remaining findings.
