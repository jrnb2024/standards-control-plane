# ProgrammePlan — WP-SCP-002 Extractor and Area Normaliser

**Work Package:** `WP-SCP-002`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-11  
**Branch:** `feature/wp-scp-002-extractor-normaliser`

## 1. Deliverables

1. repo extractor module
2. area normaliser module
3. project-area schema
4. seeded pilot fixtures extended as needed
5. example project-area payload
6. tests
7. review evidence pack

## 2. Sequence

1. complete Gate A documents
2. run 3-reviewer plan review
3. patch planning docs from review findings
4. implement extractor and normaliser
5. add fixtures and example payload
6. run local verification
7. run 3-reviewer code review
8. address findings
9. prepare PR

## 3. Dependencies

- merged `WP-SCP-001` on `main`
- seeded returns pilot fixture path

## 4. Exit criteria

- acceptance criteria met
- tests passing
- review findings dispositioned
- PR opened against `main`

## 5. Review and evidence rules

Plan review and code review both write into `docs/reviews/WP-SCP-002/`.

Required files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

Minimum contents:

- `review_findings.md`: finding ID, reviewer role, severity, disposition
- `implementation_notes.md`: delivered modules, intentional limits
- `acceptance_verification.md`: every AC with concrete evidence
- `test_results.txt`: commands and outcomes

Review roles:

1. architecture
2. security / quality / governance
3. completeness
