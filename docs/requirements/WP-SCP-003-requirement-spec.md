# RequirementSpec — WP-SCP-003 Governance Evaluator and Audit Wiring

**Work Package:** `WP-SCP-003`  
**Version:** 0.2  
**Status:** Approved for implementation  
**Date:** 2026-04-11  
**Implementation Branch:** `feature/wp-scp-003-governance-evaluator`

## 1. Purpose

Stand up the first real evaluator path by implementing governance evaluation on
top of the extracted project-area model and wiring that through the audit CLI.

This slice does not attempt architecture evaluation yet. It establishes one
real audit path end to end before widening the surface.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-301 | The system shall implement a governance evaluator that consumes a schema-valid project-area payload. |
| FR-SCP-302 | The governance evaluator shall evaluate at least the currently active governance rules in the local registry: `GOV-001`, `GOV-002`, and `GOV-003`. |
| FR-SCP-303 | The governance evaluator shall emit structured findings using the existing finding contract. |
| FR-SCP-304 | The governance evaluator shall emit a deterministic governance score from 0 to 100 based on explicit, documented severity deductions. |
| FR-SCP-305 | The audit CLI shall use the live extraction, normalisation, and governance evaluation path when the requested domains include `governance`. |
| FR-SCP-306 | The governance audit result shall include findings, summary counts, recommended actions, and metadata in the audit-result contract produced by the live evaluator path rather than a scaffolded stub. |
| FR-SCP-307 | The audit-result contract shall include structured per-domain evaluation status so unsupported domains remain explicit rather than silently pretending to have been evaluated. |
| FR-SCP-308 | The project-area contract shall include a first-class `review_evidence` artefact bucket so `GOV-003` can operate on schema-defined input rather than ad hoc path inference. |
| FR-SCP-309 | `GOV-001` shall use a deterministic comparison order: enhancement-spec slug where present, then `area_id`, then subsystem-alignment checks, emitting a finding when those signals conflict. |
| FR-SCP-310 | The work package shall update the audit examples to reflect a real governance evaluation path against the seeded pilot corpus, including structured unsupported-domain status where requested. |

## 3. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-301 | The same audit request and repository state must produce the same governance findings and score ordering. |
| NFR-302 | Scoring must be deterministic and documented in code and evidence. |
| NFR-303 | Governance findings must reference the triggering rule id and concrete evidence paths where available. |
| NFR-304 | The implementation must keep governance evaluation separable from future architecture evaluation. |
| NFR-305 | Governance score in this slice must be presented as a domain-local score, not as a proxy for full audit coverage or confidence across unsupported domains. |

## 4. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-003-001 | Running governance audit on the seeded returns-pilot scope returns a schema-valid audit result from the live evaluator path rather than the previous scaffolded stub. | pytest + CLI/manual run |
| AC-WP-SCP-003-002 | A project-area payload missing an enhancement spec produces a `GOV-002` finding. | pytest |
| AC-WP-SCP-003-003 | A project-area payload missing review evidence produces a `GOV-003` finding. | pytest |
| AC-WP-SCP-003-004 | A project-area payload with a subsystem/area boundary mismatch produces a `GOV-001` finding. | pytest |
| AC-WP-SCP-003-005 | Re-running governance audit for the same request returns the same ordered findings and score. | pytest |
| AC-WP-SCP-003-006 | Unsupported requested domains remain explicit in a structured audit-result field rather than only in prose. | pytest |
| AC-WP-SCP-003-007 | The audit examples are updated to local, schema-valid governance-evaluator outputs and exercise structured unsupported-domain status when applicable. | pytest |
| AC-WP-SCP-003-008 | The project docs, backlog, decision log, and status are updated in the same session as code changes. | manual review |
| AC-WP-SCP-003-009 | The seeded review evidence pack is sufficient to trace plan review, implementation notes, acceptance verification, and raw test output for this work package. | manual review |

## 5. Scope Boundary

### In scope

- governance evaluator module
- deterministic governance scoring
- audit CLI wiring for governance
- governance audit example payloads
- tests and work package evidence

### Out of scope

- architecture evaluator logic
- findings lifecycle transitions
- waiver handling
- markdown report generation
- multi-area audit batching

## 5.1 Backlog mapping

### Consumed in this work package

- `SCP-016` — governance evaluator

### Explicitly not consumed in this work package

- `SCP-017` — architecture evaluator
- `SCP-018` — full findings/report lifecycle

## 6. Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R-301 | Governance checks drift into vague prose | Keep checks explicit, rule-bound, and fixture-backed |
| R-302 | Audit result implies unsupported domains were evaluated | Make unsupported-domain handling explicit in structured domain status |
| R-303 | Scoring becomes arbitrary | Use simple documented deductions by severity |
| R-304 | Review-evidence checks rely on ad hoc repo scanning outside the contract | Add `review_evidence` to the project-area contract before implementation |

## 7. Rollout / Rollback

This is repo-local work. Rollout is merge to `main`. Rollback is revert of the
work package commit set if governance scoring or findings prove wrong.

## 8. Review Protocol

Plan review and code review for this work package must each use three reviewer
roles:

1. architecture / structure
2. security / quality / governance
3. completeness / acceptance coverage

Evidence is stored under `docs/reviews/WP-SCP-003/`.

Required evidence files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

Minimum contents:

- `review_findings.md` must list reviewer role, finding severity, disposition, and patch reference
- `implementation_notes.md` must record key design choices, tradeoffs, and touched modules
- `acceptance_verification.md` must map each acceptance criterion to concrete evidence
- `test_results.txt` must contain raw command lines and pass/fail output captured during local verification
