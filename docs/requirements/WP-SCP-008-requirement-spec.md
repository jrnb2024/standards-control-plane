# RequirementSpec — WP-SCP-008 Review Evidence Hardening and Pilot Tuning

**Work Package:** `WP-SCP-008`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-008-review-evidence-and-pilot-tuning`

## 1. Purpose

Replace the current path-plus-text review-evidence heuristic with a structured
metadata contract, reuse that contract for historical review retrieval, and
document the first trust-tuning pass against the Returns pilot.

This slice should reduce false positives in governance review-evidence checks
without widening into a full false-positive management workflow yet.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-801 | The system shall define a structured review-evidence metadata contract that can be embedded inside `review_findings.md` files and validated explicitly. |
| FR-SCP-802 | Governance review-evidence checks shall read the structured review-evidence contract rather than relying on raw string matches alone. |
| FR-SCP-803 | A review-evidence file shall count as traceable governance evidence only when its structured metadata matches the audited area and contains at least one finding entry with an explicit status. |
| FR-SCP-804 | The system shall expose a read-only historical review retrieval path that loads structured review-evidence records and selects relevant prior reviews by exact area match first, then reviewed-path overlap. |
| FR-SCP-805 | Consult responses shall expose a bounded list of relevant historical review references when such structured review evidence exists for the requested area or paths. |
| FR-SCP-806 | The seeded Returns pilot review evidence shall be migrated to the structured review-evidence contract in this slice. |
| FR-SCP-807 | The repository’s own governed work-package review packs from `WP-SCP-003` onward that are used as historical review sources in this repo shall also carry structured review-evidence metadata after this slice. |
| FR-SCP-808 | Historical review retrieval shall remain read-only and advisory; it shall not mutate findings, waivers, or reports. |
| FR-SCP-809 | This slice shall record a pilot tuning note that explains the trust issue being reduced, the implemented calibration, and any remaining residual false-positive risk. |
| FR-SCP-810 | The consult-response contract shall be extended explicitly in this slice to include structured `historical_reviews` references when available. |

## 3. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-801 | Review-evidence parsing and selection must be deterministic and repo-bounded. |
| NFR-802 | Review-evidence metadata must not introduce a new dependency on non-standard parsing libraries. |
| NFR-803 | Historical review retrieval must tolerate legacy review files that do not yet carry structured metadata by skipping them rather than failing unrelated consult calls. |
| NFR-804 | The new review-evidence contract must remain inspectable in git and readable inside markdown files. |

## 4. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-008-001 | Governance evaluation still passes for the seeded Returns pilot when the structured review-evidence block is present and valid. | pytest |
| AC-WP-SCP-008-002 | Governance evaluation flags missing review evidence when only legacy unstructured text is present and no valid structured block can be parsed for the area. | pytest |
| AC-WP-SCP-008-003 | Consult responses for the seeded Returns pilot include at least one relevant historical review reference derived from the structured review-evidence retrieval path. | pytest |
| AC-WP-SCP-008-004 | Historical review selection is deterministic and prefers exact area matches over path-only matches. | pytest |
| AC-WP-SCP-008-005 | Structured review-evidence metadata validates against an explicit schema. | pytest |
| AC-WP-SCP-008-006 | Consult retrieval remains schema-valid and deterministic when no structured historical review records match the request. | pytest |
| AC-WP-SCP-008-007 | The pilot tuning note exists and records the false-positive reduction achieved in this slice plus any remaining residual risk. | manual review |
| AC-WP-SCP-008-008 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-008/`. | manual review |

## 5. Scope Boundary

### In scope

- structured review-evidence schema and parser
- governance evaluator migration from raw text matching to structured review metadata
- historical review retrieval adapter
- consult-response historical review references
- structured metadata migration for seeded pilot and repo-local review packs used as history
- pilot tuning note
- tests and evidence pack

### Out of scope

- user-facing tooling to author review metadata automatically
- false-positive lifecycle states beyond the existing finding status model
- consult ordering redesign
- model-heavy trust calibration
- UX/design/product evaluator work

## 5.1 Backlog mapping

### Consumed in this work package

- `SCP-022` — structured review-evidence contract
- `SCP-035` — historical review retrieval adapter
- `SCP-037` — first pilot tuning pass

### Explicitly not consumed in this work package

- `SCP-036` — docs-agent connector for consult enrichment
- `SCP-044` — full false-positive review loop
- `SCP-045` — consult output ordering tune-up

## 6. Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R-801 | The new review-evidence contract is too heavy for teams to maintain | Keep the embedded metadata block small, JSON-based, and review-file-local |
| R-802 | Legacy review files break consult or audit flows | Skip unstructured files in the historical retrieval adapter and migrate the seeded sources used by tests and pilot flows in this slice |
| R-803 | Governance review evidence remains noisy because area matching is under-specified | Require explicit `area_id` in the structured metadata and deterministic selection rules |
| R-804 | Pilot tuning turns into an unbounded heuristic exercise | Limit the slice to the review-evidence trust problem plus documented calibration notes |

## 7. Rollout / Rollback

This is repo-local work. Rollout is merge to `main`. Rollback is revert of the
work package commit set if the metadata contract proves too awkward or consult
retrieval becomes noisy.

## 8. Review Protocol

Plan review and code review for this work package must each use three reviewer
roles:

1. architecture / structure
2. security / quality / governance
3. completeness / acceptance coverage

Evidence is stored under `docs/reviews/WP-SCP-008/`.

Required evidence files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

Minimum evidence content:

- `review_findings.md` records reviewer role, severity, disposition, and follow-up path for every plan/code review finding
- `implementation_notes.md` records the chosen review-evidence block format, retrieval behaviour, tuning changes, and any backlog carry-forward
- `acceptance_verification.md` maps each acceptance criterion to a concrete verification result
- `test_results.txt` captures the exact local test command output used for closure
