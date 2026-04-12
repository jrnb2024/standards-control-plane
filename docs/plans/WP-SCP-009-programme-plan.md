# ProgrammePlan — WP-SCP-009 Confidence Taxonomy and Evidence Classes

**Work Package:** `WP-SCP-009`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Branch:** `feature/wp-scp-009-confidence-taxonomy`

## 1. Deliverables

1. shared confidence taxonomy helper
2. finding and consult contract expansion
3. evaluator output updates for governance and architecture
4. refreshed examples and output artefacts
5. confidence taxonomy reference note
6. tests
7. review evidence pack

## 2. Sequence

1. complete Gate A documents
2. run bounded plan review
3. patch planning findings
4. implement shared confidence and evidence-class helpers
5. update schemas, findings store, evaluators, and consult output
6. refresh examples and persisted outputs
7. run local verification
8. run bounded code review
9. address all review findings in-slice
10. prepare PR

## 3. Dependencies

- merged `WP-SCP-008` on `main`
- current consult and audit contracts
- current findings persistence path

## 4. Exit criteria

- acceptance criteria met
- tests passing
- review findings dispositioned
- PR opened against `main`

## 5. Review and evidence rules

Plan review and code review both write into `docs/reviews/WP-SCP-009/`.

Required files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`
