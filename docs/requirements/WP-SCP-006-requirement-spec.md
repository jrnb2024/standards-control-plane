# RequirementSpec — WP-SCP-006 Markdown Reports and Area Summaries

**Work Package:** `WP-SCP-006`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-006-reports-and-summaries`

## 1. Purpose

Turn the persisted findings base from `WP-SCP-005` into human-readable markdown
reports and deterministic subsystem-keyed area summaries.

This slice should make the existing `report` command live without inventing a
second source of truth outside the structured audit and findings outputs.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-601 | The system shall generate `output/reports/latest-review.md` from the latest write-backed audit result plus the reconciled findings state produced in the same write flow. |
| FR-SCP-602 | The system shall generate `output/reports/subsystems/<subsystem>-review.md` for the latest audited subsystem when `audit --write-output` runs. |
| FR-SCP-603 | The system shall generate `output/findings/area-summaries/<subsystem>.json` using the existing `area-summary.schema.json` contract. |
| FR-SCP-604 | Markdown reports in this slice shall be derived only from structured audit results and persisted findings, not from independent free-form evaluation logic. |
| FR-SCP-605 | The `report` CLI shall print the generated `output/reports/latest-review.md` file after a live write-backed audit has refreshed it. |
| FR-SCP-606 | `audit --write-output` shall update the findings stores, latest review markdown, subsystem review markdown, and subsystem-keyed area summary in one explicit write flow, reusing the existing per-file atomic replacement and best-effort rollback semantics rather than claiming a crash-safe bundle transaction in this phase. |
| FR-SCP-607 | The latest review markdown shall include: audit timestamp bound to `audit_result.generated_at`, scope, standards version, domain scores, top open high-severity issues with evidence paths, recommended next actions, and explicit regressions/improvements sections even when those sections are empty in this phase. |
| FR-SCP-608 | The subsystem-keyed area summary shall preserve the exact audited `area_id` inside the payload even though the file name is keyed by subsystem in this phase. |
| FR-SCP-609 | The subsystem-keyed area summary `updated_at` field shall equal `audit_result.generated_at`. |
| FR-SCP-610 | The `report` CLI shall fail explicitly when the generated latest review is missing or when its embedded audit timestamp does not match the current persisted open-findings timestamp. |

## 3. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-601 | Re-running report generation with the same audit result and persisted findings state must produce byte-identical markdown and summary outputs. |
| NFR-602 | Report generation must stay downstream of the structured findings lifecycle and must not mutate the findings stores. |
| NFR-603 | Report output ordering must be deterministic and explainable. |
| NFR-604 | The implementation must keep room for later multi-subsystem rollups without redesigning the report generator. |

## 4. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-006-001 | Running `audit --write-output` updates `output/reports/latest-review.md` and `output/reports/subsystems/returns-review.md` from the live audit path. | pytest + CLI/manual run |
| AC-WP-SCP-006-002 | Running `audit --write-output` updates `output/findings/area-summaries/returns.json` with a schema-valid payload. | pytest |
| AC-WP-SCP-006-003 | The `report` CLI prints the generated latest review markdown only when its embedded audit timestamp matches the current persisted open-findings timestamp, and fails explicitly otherwise. | pytest + CLI/manual run |
| AC-WP-SCP-006-004 | The latest review markdown reflects the live audit timestamp, scope, standards version, domain scores, open high-severity issues with evidence paths, recommended actions, and the required regressions/improvements sections in stable order. | pytest |
| AC-WP-SCP-006-005 | Re-running the same write-backed audit twice leaves report and area-summary outputs unchanged. | pytest |
| AC-WP-SCP-006-006 | The subsystem-keyed area summary preserves the exact audited `area_id` while using the subsystem file name, and `updated_at` equals `audit_result.generated_at`. | pytest |
| AC-WP-SCP-006-007 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-006/`. | manual review |

## 5. Scope Boundary

### In scope

- markdown report generation
- subsystem review markdown generation
- subsystem-keyed area summary JSON generation
- report CLI activation against live generated output
- tests and evidence pack

### Out of scope

- waiver-aware report sections
- multi-subsystem rollups
- Control Tower publication
- changed-file or CI-threshold output modes

## 5.1 Backlog mapping

### Consumed in this work package

- remaining `SCP-018` — markdown report generation
- `SCP-034` — area summary foundation

### Explicitly not consumed in this work package

- `SCP-033` — score documentation
- `SCP-050` — changed-file scoped audit
- `SCP-053` / `SCP-054` — Control Tower surfacing

## 6. Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R-601 | Reports drift away from the structured findings source of truth | Generate reports only from the current write-backed audit result and reconciled persisted stores |
| R-602 | File naming implies subsystem rollup while actually covering one audited area | Preserve exact `area_id` inside the summary payload and document the phase-1 naming rule |
| R-603 | Markdown output becomes noisy and unstable in git | Define deterministic section ordering and item ordering |
| R-604 | Findings and report artifacts can still diverge after a process crash mid-write | Reuse the current best-effort write guarantees in this slice and carry a stronger bundled transaction to backlog |

## 7. Rollout / Rollback

This is repo-local work. Rollout is merge to `main`. Rollback is revert of the
work package commit set if the reporting surface proves misleading or unstable.

## 8. Review Protocol

Plan review and code review for this work package must each use three reviewer
roles:

1. architecture / structure
2. security / quality / governance
3. completeness / acceptance coverage

Evidence is stored under `docs/reviews/WP-SCP-006/`.

Required evidence files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

Minimum evidence content:

- `review_findings.md` records reviewer role, severity, disposition, and follow-up path for every plan/code review finding
- `implementation_notes.md` records the chosen report-generation semantics, naming rules, and any backlog carry-forward
- `acceptance_verification.md` maps each acceptance criterion to a concrete verification result
- `test_results.txt` captures the exact local test command output used for closure
