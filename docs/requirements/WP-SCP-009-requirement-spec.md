# RequirementSpec — WP-SCP-009 Confidence Taxonomy and Evidence Classes

**Work Package:** `WP-SCP-009`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-009-confidence-taxonomy`

## 1. Purpose

Define a repo-local confidence taxonomy and evidence classification model before
the inference-heavier UX, design, and product domains land.

This slice should make confidence visible and consistent across schemas,
evaluator outputs, persisted findings, and consult responses without changing
the scoring model yet.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-901 | The system shall define an explicit confidence taxonomy with deterministic thresholds for `low`, `medium`, and `high`. |
| FR-SCP-902 | Finding contracts shall carry both a numeric `confidence` value and a derived `confidence_class`. |
| FR-SCP-903 | Finding evidence entries shall carry an explicit `evidence_class` so downstream consumers can distinguish direct repo evidence from declared metadata or historical material. |
| FR-SCP-904 | Governance and architecture evaluator outputs shall emit `confidence_class` and `evidence_class` consistently in this slice. |
| FR-SCP-905 | Persisted findings stores, audit results, and consult responses shall remain schema-valid after the contract expansion. |
| FR-SCP-906 | Consult responses shall expose a top-level `confidence_class` for the overall response confidence and shall include `confidence_class` on surfaced open findings. |
| FR-SCP-907 | The repo shall include a reference note that documents the confidence thresholds, intended interpretation, and allowed evidence classes. |
| FR-SCP-908 | This slice shall update seeded examples, fixtures, and output artefacts so the repo remains self-consistent after the contract change. |

## 3. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-901 | Confidence classification must be deterministic and must not depend on model output. |
| NFR-902 | Evidence classes must stay narrow and readable in git; this slice must not introduce a large ontology. |
| NFR-903 | Existing evaluator logic should not gain materially wider detection scope in this slice; the change is contract hardening, not evaluator expansion. |
| NFR-904 | The new contract must leave room for later inference-heavy domains without forcing another breaking schema redesign. |

## 4. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-009-001 | Findings emitted by the live governance and architecture evaluators include valid `confidence_class` and `evidence_class` values. | pytest |
| AC-WP-SCP-009-002 | Persisted open and history findings stores validate after the contract expansion. | pytest |
| AC-WP-SCP-009-003 | Consult responses validate after the contract expansion and expose a top-level `confidence_class` plus per-finding `confidence_class` on surfaced open findings. | pytest |
| AC-WP-SCP-009-004 | Numeric confidence thresholds classify findings deterministically and are covered by direct unit tests. | pytest |
| AC-WP-SCP-009-005 | The confidence taxonomy reference note exists and matches the implementation thresholds and evidence classes. | manual review |
| AC-WP-SCP-009-006 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-009/`. | manual review |

## 5. Scope Boundary

### In scope

- confidence taxonomy helper module
- finding schema and consult schema expansion
- evidence classification in finding evidence entries
- governance and architecture evaluator output updates
- seeded examples, outputs, and tests
- reference documentation and evidence pack

### Out of scope

- score weighting changes based on confidence class
- new evaluator domains
- consult ordering redesign
- false-positive lifecycle workflow
- CI threshold enforcement

## 5.1 Backlog mapping

### Consumed in this work package

- `SCP-043` — confidence taxonomy and evidence classes

### Explicitly not consumed in this work package

- `SCP-044` — false-positive review loop
- `SCP-045` — consult ordering tune-up

## 6. Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R-901 | Confidence classes become arbitrary labels with no implementation discipline | Put thresholds in code and document them in a reference note used by tests and reviewers |
| R-902 | Contract changes break persisted fixtures and examples silently | Update examples, output files, and validation tests in the same slice |
| R-903 | Evidence classes become too abstract to be useful | Keep the class list small and source-oriented |
| R-904 | Later domains need a different confidence model | Use a numeric score plus class derivation rather than a class-only contract |

## 7. Rollout / Rollback

This is repo-local work. Rollout is merge to `main`. Rollback is revert of the
work package commit set if the contract expansion proves too noisy or breaks
downstream artefact handling.

## 8. Review Protocol

Plan review and code review for this work package must each use three reviewer
roles:

1. architecture / structure
2. security / quality / governance
3. completeness / acceptance coverage

Evidence is stored under `docs/reviews/WP-SCP-009/`.

Required evidence files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`
