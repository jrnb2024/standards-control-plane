# WP-SCP-006 Review Findings

```scp-review-evidence
{
  "review_id": "WP-SCP-006",
  "area_id": "standards-control-plane",
  "reviewed_at": "2026-04-12T00:00:00Z",
  "summary": "Reporting moved from placeholders to deterministic projections over structured findings.",
  "reviewed_paths": [
    "src/standards_control_plane/reports.py",
    "src/standards_control_plane/cli.py",
    "output/reports/latest-review.md"
  ],
  "findings": [
    {
      "finding_id": "RV-WP-SCP-006-001",
      "status": "resolved",
      "summary": "Report freshness needed to be bound to structured findings state rather than loose timestamps.",
      "domain": "governance"
    }
  ]
}
```

**Work Package:** `WP-SCP-006`  
**Date:** 2026-04-12  
**Gate:** A — planning  
**Status:** Findings incorporated; approved for implementation

## Findings

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| architecture / structure | High | The pack allowed non-deterministic wall-clock timestamps, which broke byte-identical rerun requirements. | Accepted and fixed by binding report and area-summary timestamps to `audit_result.generated_at`. | RequirementSpec FR-SCP-607 and FR-SCP-609; Strategy section 4; TechnicalArchitecture section 4; Decision `D-012` |
| security / quality / governance | High | The write flow implied a stronger bundled transaction than the existing persistence layer can honestly provide. | Accepted and fixed by reusing the existing per-file atomic replacement plus rollback semantics and carrying true bundled transactions to backlog. | RequirementSpec FR-SCP-606; Strategy section 4.1; TechnicalArchitecture section 4; Backlog `SCP-039`; Decision `D-013` |
| completeness / acceptance coverage | High | The latest review did not require evidence-path visibility for top findings. | Accepted and fixed by requiring high-severity issues in markdown to include evidence paths and by tightening acceptance coverage. | RequirementSpec FR-SCP-607; AC-WP-SCP-006-004; Strategy section 4 |
| security / quality / governance | Medium | Report freshness was under-specified and stale markdown could still be printed. | Accepted and fixed by requiring `report` to fail when the embedded audit timestamp does not match the persisted open-findings timestamp. | RequirementSpec FR-SCP-610; AC-WP-SCP-006-003; Strategy section 3.3; TechnicalArchitecture section 3 |
| architecture / structure | Medium | The pack referred to a “latest persisted audit context” that was not otherwise defined. | Accepted and fixed by grounding report generation in the current write-backed audit result plus reconciled findings stores. | RequirementSpec FR-SCP-601; Strategy section 3.1 |
| security / quality / governance | Medium | The Gate A evidence pack looked incomplete. | Accepted and fixed for planning visibility by adding placeholder evidence files that will be completed during Gate B. | `docs/reviews/WP-SCP-006/implementation_notes.md`; `docs/reviews/WP-SCP-006/acceptance_verification.md`; `docs/reviews/WP-SCP-006/test_results.txt` |

## Outcome

Gate A is complete. The planning pack is approved for implementation with
deterministic timestamp binding, explicit report freshness rules, evidence-path
visibility in markdown, and an honest write-safety boundary for report
artifacts.

## Gate B — Code Review

**Date:** 2026-04-12  
**Status:** Findings addressed; one residual carried to backlog

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| completeness / acceptance coverage | High | The evidence pack still contained placeholders. | Fixed by replacing the placeholders with implementation notes, acceptance verification, and raw test results. | `docs/reviews/WP-SCP-006/implementation_notes.md`, `docs/reviews/WP-SCP-006/acceptance_verification.md`, `docs/reviews/WP-SCP-006/test_results.txt` |
| completeness / acceptance coverage | Medium | `report` missing-file failure was required but not tested. | Fixed by adding explicit missing-report CLI coverage. | `tests/test_reports.py` |
| security / quality / governance | Medium | `report` could fail through an unhandled missing/corrupt findings-store dependency. | Fixed by adding explicit CLI error handling plus coverage for invalid findings-store input. | `src/standards_control_plane/cli.py`; `tests/test_reports.py` |
| architecture / structure | Medium | Timestamp-only freshness checks were too weak to catch same-day content drift. | Fixed by embedding report-source signatures for the open and history stores and verifying them in `report`. | `src/standards_control_plane/reports.py`; `src/standards_control_plane/cli.py`; `tests/test_reports.py`; Decision `D-014` |
| architecture / structure | Medium | Findings persistence and report generation still do not form a crash-safe bundled transaction across all artifacts. | Accepted as a bounded residual: the slice reuses the existing write guarantees and carries a stronger bundled commit model to backlog. | Backlog `SCP-039`; RequirementSpec FR-SCP-606; Strategy section 4.1 |
