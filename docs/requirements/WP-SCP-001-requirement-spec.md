# RequirementSpec — WP-SCP-001 Registry and Consult Retrieval

**Work Package:** `WP-SCP-001`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-11  
**Implementation Branch:** `feature/wp-scp-001-registry-consult`

## 1. Purpose

Turn the phase 1 scaffold into a usable local standards registry and consult
retrieval slice.

This work package does **not** attempt full audit evaluation. It focuses on the
minimum real path that lets an implementation agent ask for guidance and
receive a structured answer assembled from actual standards content and the
current open findings store.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-001 | The system shall load the top-level standards registry and referenced domain indexes from local files. |
| FR-SCP-002 | The system shall expose parsed governance and architecture rules and patterns in structured form. |
| FR-SCP-003 | The system shall validate consult requests against the schema before processing. |
| FR-SCP-004 | The system shall assemble a consult response using requested domains, applicable rules, relevant patterns, and matching open findings. |
| FR-SCP-005 | The consult response shall remain machine-readable and validate against the response schema. |
| FR-SCP-006 | The CLI `consult` command shall use the real retrieval path instead of a placeholder stub. |
| FR-SCP-007 | The CLI `show-registry` command shall reflect structured registry content suitable for inspection and debugging. |
| FR-SCP-008 | The slice shall include a minimal, versioned, read-only findings-store loader for consult use. |
| FR-SCP-009 | Findings matching shall support domain-first lookup, with area and path matches used as more specific matches when available. |
| FR-SCP-010 | Registry metadata changes shall remain explicit and reviewable in structured index files. |

## 3. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-001 | Output must be deterministic for the same request and repository state. |
| NFR-002 | Rule loading must fail clearly on malformed registry references. |
| NFR-003 | The implementation must keep the retrieval layer separable from future evaluator logic. |
| NFR-004 | The work package must add tests for registry loading and consult output shape. |

## 4. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-001-001 | Running `consult` with the example request returns at least one applicable rule and one guidance item derived from real registry content. | CLI test + manual run |
| AC-WP-SCP-001-002 | Running `consult` with the example request returns at least one approved pattern derived from real registry content. | pytest |
| AC-WP-SCP-001-003 | Running `consult` returns a schema-valid consult response. | pytest |
| AC-WP-SCP-001-004 | Broken registry references fail with explicit test coverage. | pytest |
| AC-WP-SCP-001-005 | The minimal findings store is read and matching open findings are surfaced using domain-first matching with area/path refinement. | pytest |
| AC-WP-SCP-001-006 | Re-running `consult` with the same request and repository state returns the same ordered response content. | pytest |
| AC-WP-SCP-001-007 | The `show-registry` command remains available and reflects the real registry content used by consult. | CLI test |
| AC-WP-SCP-001-008 | The project docs, backlog, decision log, and status are updated in the same session as code changes. | manual review |

## 5. Scope Boundary

### In scope

- standards registry loading
- domain index loading
- minimal findings-store loading for consult
- structured consult retrieval
- findings-store lookup for consult
- CLI consult wiring
- CLI registry inspection
- tests and work package evidence

### Out of scope

- governance evaluator logic
- architecture evaluator logic
- score calculation
- audit execution beyond current scaffold
- CI integration
- UX, design, and product evaluators
- findings lifecycle transitions and waiver handling

## 5.1 Backlog mapping

### Consumed in this work package

- `SCP-011` — standards registry loader and validator
- `SCP-015` — consult retrieval and response assembly
- `SCP-015A` — minimal findings-store read path for consult

### Explicitly not consumed in this work package

- `SCP-016` — governance evaluator
- `SCP-017` — architecture evaluator
- `SCP-018` — full findings store lifecycle and markdown report generation
- `SCP-030+` — waiver and regression lifecycle work

## 6. Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R-001 | Registry shape drifts into ad hoc markdown parsing | Keep metadata structured in index files for this slice |
| R-002 | Consult response becomes a prose dump | Keep schema first and limit response fields |
| R-003 | Findings matching becomes too clever too early | Use simple area/path/domain matching rules first |

## 7. Rollout / Rollback

This is local-only repo work. Rollout is commit + PR merge. Rollback is revert
of the work package commit set if the retrieval shape proves wrong.

## 8. Review Protocol

Plan review and code review for this work package must each use three reviewer
roles:

1. architecture / structure
2. security / quality / governance
3. completeness / acceptance coverage

Evidence is stored under `docs/reviews/WP-SCP-001/`.

Required evidence files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

No Gate A or Gate C closure without an explicit finding disposition for every
review finding.
