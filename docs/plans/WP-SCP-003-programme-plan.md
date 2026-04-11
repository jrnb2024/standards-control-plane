# ProgrammePlan — WP-SCP-003 Governance Evaluator and Audit Wiring

**Work Package:** `WP-SCP-003`  
**Version:** 0.2  
**Status:** Approved for implementation  
**Date:** 2026-04-11  
**Branch:** `feature/wp-scp-003-governance-evaluator`

## 1. Deliverables

1. governance evaluator module
2. audit assembler module
3. live audit CLI path for governance
4. contract updates for `project-area` review evidence and audit-result domain status
5. updated audit examples
6. tests
7. review evidence pack

## 2. Sequence

1. complete Gate A documents
2. run 3-reviewer plan review
3. patch planning docs from review findings
4. update contracts needed for governance review evidence and mixed-domain status
5. implement governance evaluation and audit wiring
6. update examples and tests
7. run local verification
8. run 3-reviewer code review
9. address findings
10. prepare PR

## 3. Dependencies

- merged `WP-SCP-002` on `main`
- active governance rules in local standards registry

## 4. Exit criteria

- acceptance criteria met
- tests passing
- review findings dispositioned
- PR opened against `main`

## 5. Review and evidence rules

Plan review and code review both write into `docs/reviews/WP-SCP-003/`.

Required files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

Minimum evidence contents:

- reviewer role, severity, disposition, and patch reference for each review finding
- touched modules and implementation tradeoffs
- acceptance-criteria-to-evidence traceability
- raw command output for verification runs

Review roles:

1. architecture
2. security / quality / governance
3. completeness
