# ProgrammePlan — WP-SCP-001 Registry and Consult Retrieval

**Work Package:** `WP-SCP-001`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-11  
**Branch:** `feature/wp-scp-001-registry-consult`

## 1. Deliverables

1. registry loader module
2. minimal findings loader module
3. consult retrieval module
4. updated standards index shape if required
5. CLI consult wiring
6. CLI registry inspection verification
7. tests
8. review evidence pack

## 2. Sequence

1. complete Gate A documents
2. run 3-reviewer plan review
3. patch planning docs from review findings
4. implement loader and consult retrieval
5. add tests
6. run local verification
7. run 3-reviewer code review
8. address findings
9. prepare PR

## 3. Dependencies

- existing scaffold on `main`
- approved planning docs in this repo

## 4. Exit criteria

- acceptance criteria met
- tests passing
- review findings dispositioned
- PR opened against `main`

## 5. Review and evidence rules

Plan review and code review both write into `docs/reviews/WP-SCP-001/`.

Required files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

Review roles:

1. architecture
2. security / quality / governance
3. completeness
