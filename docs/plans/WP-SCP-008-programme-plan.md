# ProgrammePlan — WP-SCP-008 Review Evidence Hardening and Pilot Tuning

**Work Package:** `WP-SCP-008`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Branch:** `feature/wp-scp-008-review-evidence-and-pilot-tuning`

## 1. Deliverables

1. structured review-evidence schema
2. review-evidence parser and selector
3. governance evaluator migration to structured review metadata
4. historical review retrieval in consult output
5. seeded review-file migration
6. pilot tuning note
7. tests
8. review evidence pack

## 2. Sequence

1. complete Gate A documents
2. run bounded plan review
3. patch planning findings
4. implement structured review-evidence parsing and consult retrieval
5. migrate seeded review sources and add pilot tuning note
6. run local verification
7. run bounded code review
8. address blocking findings or backlog non-blocking residuals
9. prepare PR

## 3. Dependencies

- merged `WP-SCP-007` on `main`
- existing `review_evidence` artefact bucket in `project-area`
- consult and governance paths already live

## 4. Exit criteria

- acceptance criteria met
- tests passing
- review findings dispositioned
- PR opened against `main`

## 5. Review and evidence rules

Plan review and code review both write into `docs/reviews/WP-SCP-008/`.

Required files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

Evidence minimums:

- reviewer role, severity, disposition, and fix/backlog reference for every recorded finding
- exact test command and result captured at closure
- acceptance-criterion-by-criterion verification notes
