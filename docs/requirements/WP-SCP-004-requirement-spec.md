# RequirementSpec — WP-SCP-004 Architecture Evaluator and Audit Extension

**Work Package:** `WP-SCP-004`  
**Version:** 0.2  
**Status:** Approved for implementation  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-004-architecture-evaluator`

## 1. Purpose

Extend the live audit path from governance-only to governance plus
architecture by introducing a deterministic architecture evaluator backed by
repo-local file-content signals.

This slice should make the architecture domain real without widening into
findings lifecycle or report generation.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-401 | The system shall implement an architecture evaluator that consumes a schema-valid project-area payload and repo-local file contents. |
| FR-SCP-402 | The architecture evaluator shall evaluate the currently active architecture rules in the local registry: `ARCH-001`, `ARCH-002`, `ARCH-003`, and `ARCH-004`. |
| FR-SCP-403 | The architecture evaluator shall emit structured findings using the existing finding contract. |
| FR-SCP-404 | The architecture evaluator shall emit a deterministic architecture score from 0 to 100 using explicit severity deductions aligned to the governance slice. |
| FR-SCP-405 | The live audit path shall run both governance and architecture evaluators when both domains are requested, and shall emit per-domain scores without implying unsupported domains were evaluated. |
| FR-SCP-406 | The seeded returns pilot corpus shall contain explicit architecture signals so the example audit result is backed by concrete file content rather than placeholder files. |
| FR-SCP-407 | The architecture evaluator shall attach concrete evidence paths and rule IDs for each finding. |
| FR-SCP-408 | The architecture evaluator shall use explicit signal heuristics tied to file contents and file locations rather than prompt-only or low-traceability inference. |
| FR-SCP-409 | `ARCH-003` in this slice shall only use explicit remote-access markers such as `fetch(`, `axios.`, `requests.`, or `httpx.` in non-test feature code outside the approved service path. |
| FR-SCP-410 | `ARCH-004` in this slice shall only use explicit backend async/eventing markers such as `asyncio.create_task(`, `threading.Thread(`, or direct event publication in backend workflow code when approved wrapper markers are absent. |
| FR-SCP-411 | The work package shall add a second repo-backed fixture corpus for targeted `ARCH-003` and `ARCH-004` coverage rather than relying on synthetic in-memory payloads alone. |

## 3. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-401 | The same audit request and repository state must produce the same architecture findings, order, and score. |
| NFR-402 | Rule checks must be explicit and test-backed, with false-positive risk bounded by narrow heuristics. |
| NFR-403 | The implementation must preserve evaluator modularity so later domains can plug into the same audit dispatcher. |
| NFR-404 | Architecture scoring in this slice must remain domain-local and must not be overread as overall audit completeness. |

## 4. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-004-001 | Running live audit on the seeded returns pilot with governance and architecture requested returns a schema-valid result with both domains marked evaluated. | pytest + CLI/manual run |
| AC-WP-SCP-004-002 | The seeded returns pilot emits at least one `ARCH-001` finding and one `ARCH-002` finding from concrete file content. | pytest |
| AC-WP-SCP-004-003 | A targeted repo-backed fixture case emits an `ARCH-003` finding for ad hoc API access outside the approved path. | pytest |
| AC-WP-SCP-004-004 | A targeted repo-backed fixture case emits an `ARCH-004` finding for inconsistent async or eventing style in backend workflow code. | pytest |
| AC-WP-SCP-004-005 | Re-running architecture evaluation for the same project area returns the same ordered findings and score. | pytest |
| AC-WP-SCP-004-006 | The combined audit result preserves deterministic merged finding order after governance and architecture findings are assembled together. | pytest |
| AC-WP-SCP-004-007 | Unsupported requested domains remain explicit in `domain_status` when governance and architecture are evaluated alongside an unsupported domain. | pytest |
| AC-WP-SCP-004-008 | The audit examples are updated to local, schema-valid outputs from the live governance-plus-architecture path. | pytest |
| AC-WP-SCP-004-009 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-004/`. | manual review |

## 5. Scope Boundary

### In scope

- architecture evaluator module
- live audit dispatcher extension for architecture
- seeded fixture updates needed to prove architecture findings
- examples, tests, and evidence pack

### Out of scope

- findings lifecycle and history persistence
- waiver handling
- markdown report generation
- UX, design-system, or product evaluators

## 5.1 Backlog mapping

### Consumed in this work package

- `SCP-017` — architecture evaluator

### Explicitly not consumed in this work package

- `SCP-018` — findings lifecycle and report generation
- `SCP-022` — richer structured review-evidence metadata

## 6. Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R-401 | Architecture checks become vague semantic guesses | Keep signals explicit, narrow, and fixture-backed |
| R-402 | Placeholder fixture code produces misleading “clean” output | Seed explicit architecture drift into the returns pilot corpus before relying on the example audit result |
| R-403 | Architecture scoring is confused with full audit completeness | Keep per-domain status and score boundaries explicit |

## 7. Rollout / Rollback

This is repo-local work. Rollout is merge to `main`. Rollback is revert of the
work package commit set if architecture checks prove unstable or misleading.

## 8. Review Protocol

Plan review and code review for this work package must each use three reviewer
roles:

1. architecture / structure
2. security / quality / governance
3. completeness / acceptance coverage

Evidence is stored under `docs/reviews/WP-SCP-004/`.

Required evidence files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

Minimum contents:

- `review_findings.md` must list reviewer role, severity, disposition, and patch reference
- `implementation_notes.md` must record key design choices, touched modules, and any backlog carry-forward
- `acceptance_verification.md` must map each acceptance criterion to concrete evidence
- `test_results.txt` must contain raw command lines and pass/fail output captured during local verification
