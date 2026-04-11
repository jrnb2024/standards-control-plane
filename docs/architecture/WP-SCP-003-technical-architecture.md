# TechnicalArchitecture — WP-SCP-003 Governance Evaluator and Audit Wiring

**Work Package:** `WP-SCP-003`  
**Version:** 0.2  
**Status:** Approved for implementation  
**Date:** 2026-04-11

## 1. Objective

Introduce the first real evaluator path by wiring governance evaluation through
the audit CLI.

## 2. Contract updates before evaluator wiring

### `project-area.schema.json`

Add `artefacts.review_evidence` as an explicit array of repo-relative paths.
The normaliser should populate this bucket from review artefacts so governance
evaluation can reason over a contract field rather than raw path heuristics.

### `audit-result.schema.json`

Add a structured per-domain evaluation-status map so callers can distinguish:

- domains evaluated in this run
- domains requested but not yet implemented in this phase

This prevents a mixed-domain audit request from looking fully evaluated when
only governance actually ran.

## 3. Proposed components

### `evaluators/governance.py`

Responsibilities:

- accept a schema-valid project-area payload
- load active governance rules from the registry
- generate structured findings with evidence
- compute a deterministic governance score

### `audit.py`

Responsibilities:

- validate the audit request
- invoke extractor and normaliser
- dispatch governance evaluation
- assemble a schema-valid audit result

### `cli.py`

Responsibilities:

- remain thin
- route `audit` to the live audit engine
- preserve existing consult/findings/report behaviour

## 4. Data flow

1. CLI reads and validates the audit request
2. extractor builds an extracted-scope payload
3. normaliser builds a project-area payload
4. governance evaluator emits findings and score
5. audit assembler emits the final audit result

## 5. Governance checks in this slice

- `GOV-001`
  - canonical comparison order:
    1. enhancement-spec slug when present
    2. `area_id`
    3. subsystem-alignment expectation
  - emit a finding when those signals conflict or the resolved area falls
    outside the requested subsystem boundary
- `GOV-002`
  - no enhancement spec artefact present
- `GOV-003`
  - no review evidence artefact present

## 6. Output rules in this slice

- findings sorted by severity then finding id
- recommended actions sorted deterministically
- unsupported requested domains marked explicitly in structured evaluation
  status, with prose only as a secondary summary
- architecture score remains omitted unless architecture is truly evaluated
- governance score is emitted only for the governance domain and must not imply
  wider audit completeness

## 7. Extension points

- governance checks for acceptance criteria and verification intent
- architecture evaluator dispatch
- multi-area audit batching
- report generation
