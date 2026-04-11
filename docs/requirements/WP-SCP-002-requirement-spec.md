# RequirementSpec — WP-SCP-002 Extractor and Area Normaliser

**Work Package:** `WP-SCP-002`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-11  
**Implementation Branch:** `feature/wp-scp-002-extractor-normaliser`

## 1. Purpose

Turn raw repo scope paths into deterministic, evaluator-ready area models.

This slice does not implement domain evaluator logic yet. Its job is to
establish the shared input contract so later governance and architecture
evaluators can work on a stable representation rather than ad hoc file-system
traversal.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-201 | The system shall resolve requested scope paths relative to the project root and reject paths that escape repo boundaries. |
| FR-SCP-202 | The system shall extract a deterministic inventory of files from requested scope paths, expanding directories recursively. |
| FR-SCP-203 | The extractor shall canonicalise each requested path before recursion, reject boundary escapes introduced through symlinks, and emit only repo-local file records. |
| FR-SCP-204 | The extractor shall expose an explicit extracted-file record contract that the normaliser consumes. |
| FR-SCP-205 | The system shall normalise extracted material into an explicit project-area intermediate representation. |
| FR-SCP-206 | The normaliser shall classify extracted files into at least enhancement specs, prompts, UI components, services, tests, and configs using deterministic path and extension rules. |
| FR-SCP-207 | The normalised project-area model shall include area identifier, subsystem, paths, artefact buckets, and metadata such as languages, frameworks, and tags. |
| FR-SCP-208 | The normaliser shall support deterministic area inference for the seeded returns pilot fixture set and shall fail clearly when no supported deterministic inference rule applies and no explicit area hint is provided. |
| FR-SCP-209 | The work package shall add explicit JSON schemas for both the extracted-file record contract and the project-area intermediate representation. |
| FR-SCP-210 | The system shall include at least one schema-valid example project-area payload derived from the seeded pilot corpus. |

## 3. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-201 | Extraction and normalisation outputs must be deterministic for the same input scope and repository state, using canonical repo-relative path ordering as the primary sort key. |
| NFR-202 | Path handling must fail clearly on missing scope paths and repo-boundary escapes. |
| NFR-203 | The implementation must remain separable from consult retrieval and later evaluator logic. |
| NFR-204 | The seeded pilot fixture set must remain inspectable inside this repo. |

## 4. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-002-001 | Extracting the seeded returns pilot scope returns a deterministic set of canonically ordered repo-local file paths. | pytest |
| AC-WP-SCP-002-002 | Missing or escaped scope paths fail with explicit test coverage. | pytest |
| AC-WP-SCP-002-003 | Normalising the seeded returns pilot scope produces a schema-valid project-area model. | pytest |
| AC-WP-SCP-002-004 | The seeded pilot fixture matrix includes at least one concrete file for each declared extraction bucket: enhancement spec, prompt, UI component, service, test, and config. | pytest |
| AC-WP-SCP-002-005 | The normalised model places enhancement specs, prompts, UI components, services, tests, and configs into the correct artefact buckets for the seeded pilot. | pytest |
| AC-WP-SCP-002-006 | The normalised model infers `returns-exceptions` as the area id for the seeded pilot example. | pytest |
| AC-WP-SCP-002-007 | Re-running extraction and normalisation for the same scope returns the same ordered payload. | pytest |
| AC-WP-SCP-002-008 | The example project-area payload validates against the new schema. | pytest |
| AC-WP-SCP-002-009 | The project docs, backlog, decision log, and status are updated in the same session as code changes. | manual review |

## 5. Scope Boundary

### In scope

- repo-bounded scope-path resolution
- deterministic file extraction
- extracted-file record contract
- deterministic file classification in the normaliser
- project-area schema
- seeded pilot example payload
- seeded pilot fixture matrix for all declared buckets
- tests and work package evidence

### Out of scope

- governance evaluator logic
- architecture evaluator logic
- audit scoring
- findings lifecycle changes
- consult retrieval changes except where integration glue is unavoidable
- multi-area batching or cross-repo extraction

## 5.1 Backlog mapping

### Consumed in this work package

- `SCP-013` — repo extractor for docs, code paths, tests, and configs
- `SCP-014` — area normaliser / intermediate representation

### Explicitly not consumed in this work package

- `SCP-016` — governance evaluator
- `SCP-017` — architecture evaluator
- `SCP-018` — full findings/report lifecycle

## 6. Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R-201 | Path heuristics become too clever and unstable | Keep extraction rules simple, explicit, and fixture-backed |
| R-202 | Area inference becomes product-specific folklore | Only support deterministic seeded-pilot inference in this slice |
| R-203 | Intermediate representation drifts before evaluators exist | Add an explicit schema and example payload now |

## 7. Rollout / Rollback

This is repo-local work. Rollout is merge to `main`. Rollback is revert of the
work package commit set if the intermediate representation proves wrong.

## 8. Review Protocol

Plan review and code review for this work package must each use three reviewer
roles:

1. architecture / structure
2. security / quality / governance
3. completeness / acceptance coverage

Evidence is stored under `docs/reviews/WP-SCP-002/`.

Required evidence files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

Minimum evidence contents:

- `review_findings.md`
  - reviewer role, finding ID, severity, summary, and disposition
- `implementation_notes.md`
  - delivered modules, intentional limits, and verifier-facing notes
- `acceptance_verification.md`
  - every acceptance criterion with status and concrete evidence
- `test_results.txt`
  - exact commands run and their observed outcomes

No Gate A or Gate C closure without an explicit finding disposition for every
review finding.
