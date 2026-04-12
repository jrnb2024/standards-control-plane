# ProgrammePlan — WP-SCP-007 Waivers and Score Model

**Work Package:** `WP-SCP-007`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Branch:** `feature/wp-scp-007-waivers-and-scoring`

## 1. Deliverables

1. waiver loading and validation
2. waiver-aware audit assembly
3. waiver-aware findings persistence
4. shared scoring module used by governance and architecture
5. explicit score-model documentation
6. updated examples and tracked outputs if needed
7. tests
8. review evidence pack

## 2. Sequence

1. complete Gate A documents
2. run bounded plan review
3. patch planning findings
4. implement waiver overlay and shared scoring
5. update schemas, examples, and tracked outputs
6. run local verification
7. run bounded code review
8. address blocking findings or backlog non-blocking residuals
9. prepare PR

## 3. Dependencies

- merged `WP-SCP-006` on `main`
- live audit assembly already in place
- findings history and open-store persistence already in place
- existing `waiver.schema.json`

## 4. Exit criteria

- acceptance criteria met
- tests passing
- review findings dispositioned
- PR opened against `main`

## 5. Review and evidence rules

Plan review and code review both write into `docs/reviews/WP-SCP-007/`.

Required files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

Evidence minimums:

- reviewer role, severity, disposition, and fix/backlog reference for every recorded finding
- exact test command and result captured at closure
- acceptance-criterion-by-criterion verification notes
