# ProgrammePlan — WP-SCP-006 Markdown Reports and Area Summaries

**Work Package:** `WP-SCP-006`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Branch:** `feature/wp-scp-006-reports-and-summaries`

## 1. Deliverables

1. deterministic latest-review markdown generation
2. deterministic subsystem-review markdown generation
3. deterministic subsystem-keyed area summary generation
4. live `report` command backed by generated output
5. updated output fixtures/examples if needed
6. tests
7. review evidence pack

## 2. Sequence

1. complete Gate A documents
2. run bounded plan review
3. patch planning findings
4. implement report and summary generation
5. update tracked outputs and tests
6. run local verification
7. run bounded code review
8. address blocking findings or backlog non-blocking residuals
9. prepare PR

## 3. Dependencies

- merged `WP-SCP-005` on `main`
- durable findings stores already in place
- placeholder `report` command already present
- existing `area-summary.schema.json`

## 4. Exit criteria

- acceptance criteria met
- tests passing
- review findings dispositioned
- PR opened against `main`

## 5. Review and evidence rules

Plan review and code review both write into `docs/reviews/WP-SCP-006/`.

Required files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

Evidence minimums:

- reviewer role, severity, disposition, and fix/backlog reference for every recorded finding
- exact test command and result captured at closure
- acceptance-criterion-by-criterion verification notes
