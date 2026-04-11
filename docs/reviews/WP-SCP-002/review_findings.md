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
