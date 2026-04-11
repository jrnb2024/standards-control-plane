# RequirementSpec — WP-SCP-005 Findings Lifecycle Foundation and Persistence

**Work Package:** `WP-SCP-005`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-005-findings-persistence`

## 1. Purpose

Stand up the first durable findings lifecycle path by reconciling live audit
output into persistent open and history stores.

This slice should make findings persistence real before waiver handling and
markdown reporting are added.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-501 | The system shall reconcile audit findings into a durable open-findings store and a durable findings-history store. |
| FR-SCP-502 | Findings reconciliation shall use deterministic identity keyed by `finding_id`, while rejecting any collision where the same `finding_id` maps to a different `(domain, area_id)` pair in the current audit result or persisted stores. |
| FR-SCP-503 | When a fully evaluated audit run no longer emits a previously open finding from the same `scope.area_id` and an evaluated domain, the finding shall transition to `resolved` in history and shall be removed from the open store. |
| FR-SCP-504 | The implementation shall preserve non-open historical findings in the history store rather than dropping them during reconciliation. |
| FR-SCP-505 | The audit CLI shall support writing the reconciled findings stores to disk through the explicit interface `audit --request <path> --write-output`, with read-only audit remaining the default when the flag is absent. |
| FR-SCP-506 | The persisted outputs for this slice shall include `output/findings/open-findings.json` and `output/findings/findings-history.json`. |
| FR-SCP-507 | The findings store contracts for this slice shall remain machine-readable and deterministic enough to inspect in git. |
| FR-SCP-508 | Reconciliation shall deduplicate repeated findings within a single audit refresh by collapsing exact duplicate records and failing explicitly when duplicates disagree on payload or scope. |
| FR-SCP-509 | Writes to the coupled findings stores shall use atomic replacement so `open-findings.json` and `findings-history.json` are not left half-written on failure. |

## 3. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-501 | Re-running persistence for the same audit result and existing store state must produce the same output files. |
| NFR-502 | Reconciliation logic must be area-scoped and domain-scoped so unrelated findings are not spuriously resolved. |
| NFR-503 | The implementation must leave room for later waiver handling without redesigning the persistence model. |
| NFR-504 | The write path must not mutate repository files outside the intended findings output area. |
| NFR-505 | Persisted findings arrays must use a documented canonical ordering so git diffs stay stable across identical runs. |

## 4. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-005-001 | Re-running the same audit persistence flow twice produces identical open and history outputs. | pytest |
| AC-WP-SCP-005-002 | New findings from a live audit are written to the open store and history store with deterministic identity. | pytest |
| AC-WP-SCP-005-003 | Findings that disappear from the same audited area/domain are marked `resolved` in history and removed from the open store. | pytest |
| AC-WP-SCP-005-004 | Findings outside the audited area/domain remain untouched during reconciliation. | pytest |
| AC-WP-SCP-005-005 | The audit CLI can write findings outputs to disk through an explicit write flag or equivalent explicit write path. | pytest + CLI/manual run |
| AC-WP-SCP-005-006 | The persisted example/history outputs are schema-valid and inspectable in git. | pytest |
| AC-WP-SCP-005-007 | Running audit without `--write-output` remains read-only and produces the same audit JSON shape as before this slice. | pytest + CLI/manual run |
| AC-WP-SCP-005-008 | Existing findings preserve `created_at` while refreshed findings update `updated_at` to the current audit timestamp. | pytest |
| AC-WP-SCP-005-009 | Duplicate findings with the same `finding_id` are either collapsed deterministically when identical or rejected explicitly when their payload/scope disagrees. | pytest |
| AC-WP-SCP-005-010 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-005/`. | manual review |

## 5. Scope Boundary

### In scope

- findings reconciliation logic
- findings history persistence
- explicit audit write path
- schema updates needed for persisted history
- tests and evidence pack

### Out of scope

- waiver approval and expiry handling
- markdown report generation
- area summary rollups
- UX, design-system, or product evaluators

## 5.1 Backlog mapping

### Consumed in this work package

- `SCP-018` — findings lifecycle foundation
- `SCP-030` — lifecycle transition foundation
- `SCP-032` — finding identity, dedup, and history tracking

### Explicitly not consumed in this work package

- `SCP-031` — waiver model with expiry handling
- `SCP-034` — area summaries and rollups

## 6. Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R-501 | Findings are spuriously resolved outside the actual audit scope | Reconcile only within the audited area and evaluated domains |
| R-502 | Persistence rewrites file history noisily on every run | Preserve deterministic ordering and timestamps where appropriate |
| R-503 | Lifecycle logic gets entangled with future waiver handling | Keep waiver semantics out of this slice and preserve room for later override rules |
| R-504 | Duplicate or collided finding IDs corrupt persisted lifecycle history | Reject scope-changing collisions and add duplicate-handling tests |
| R-505 | Interrupted writes leave the two findings stores out of sync | Use temp-file staging and atomic replacement for both output files |

## 7. Rollout / Rollback

This is repo-local work. Rollout is merge to `main`. Rollback is revert of the
work package commit set if reconciliation semantics prove unsafe.

## 8. Review Protocol

Plan review and code review for this work package must each use three reviewer
roles:

1. architecture / structure
2. security / quality / governance
3. completeness / acceptance coverage

Evidence is stored under `docs/reviews/WP-SCP-005/`.

Required evidence files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

Minimum evidence content:

- `review_findings.md` records reviewer role, severity, disposition, and follow-up path for every plan/code review finding
- `implementation_notes.md` records the chosen persistence semantics, CLI contract, and any backlog carry-forward
- `acceptance_verification.md` maps each acceptance criterion to a concrete verification result
- `test_results.txt` captures the exact local test command output used for closure
