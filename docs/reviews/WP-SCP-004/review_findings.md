# WP-SCP-004 Review Findings

```scp-review-evidence
{
  "review_id": "WP-SCP-004",
  "area_id": "standards-control-plane",
  "reviewed_at": "2026-04-12T00:00:00Z",
  "summary": "Architecture evaluator signals and seeded pilot coverage were tightened.",
  "reviewed_paths": [
    "src/standards_control_plane/evaluators/architecture.py",
    "src/standards_control_plane/audit.py",
    "fixtures/returns-pilot/frontend/app/exceptions/page.tsx"
  ],
  "findings": [
    {
      "finding_id": "RV-WP-SCP-004-001",
      "status": "resolved",
      "summary": "Architecture checks needed repo-backed signal corpora and deterministic ordering.",
      "domain": "architecture"
    }
  ]
}
```

**Work Package:** `WP-SCP-004`  
**Date:** 2026-04-12  
**Gate:** A — planning  
**Status:** Findings incorporated; approved for implementation

## Findings

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| completeness / acceptance coverage | Medium | Unsupported-domain behaviour was not explicitly exercised in acceptance criteria. | Accepted and fixed by adding a mixed-domain unsupported coverage acceptance criterion and strategy note. | RequirementSpec AC-WP-SCP-004-007; Strategy section 5 |
| completeness / acceptance coverage | Medium | Combined audit finding order after merge was not explicitly verified. | Accepted and fixed by adding a combined-order acceptance criterion. | RequirementSpec AC-WP-SCP-004-006; TechnicalArchitecture section 4 |
| completeness / acceptance coverage | Medium | Evidence files were named but minimum contents were not defined. | Accepted and fixed by adding minimum-content requirements to the requirement spec and programme plan. | RequirementSpec section 8; ProgrammePlan section 5 |
| architecture / structure | Medium | `ARCH-003` and `ARCH-004` were still described too loosely and risked drifting back into smell-based inference. | Accepted and fixed by defining concrete marker sets and wrapper exclusions for this slice. | RequirementSpec FR-SCP-409 and FR-SCP-410; Strategy section 3.2; TechnicalArchitecture section 3 |
| architecture / structure | Medium | The plan did not allocate concrete repo-backed fixtures for `ARCH-003` and `ARCH-004`. | Accepted and fixed by requiring a second repo-backed fixture corpus for targeted architecture signal coverage. | Decision D-009; RequirementSpec FR-SCP-411; Strategy section 3.3; ProgrammePlan deliverable 4 |
| security / quality / governance | Medium | `ARCH-004` acceptance was not grounded in a concrete backend-workflow test corpus. | Accepted and fixed by explicitly allocating targeted repo-backed fixture coverage. | RequirementSpec AC-WP-SCP-004-004; Strategy section 3.3 |

## Outcome

Gate A is complete. The planning pack is approved for implementation with
explicit repo-backed signal coverage and stronger proof obligations.

## Gate B — Code Review

**Date:** 2026-04-12  
**Status:** Findings addressed; no backlog carry-forward required for this slice

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| completeness / acceptance coverage | High | The evidence pack was incomplete. | Fixed by adding implementation notes, acceptance verification, and raw test results. | `docs/reviews/WP-SCP-004/implementation_notes.md`, `docs/reviews/WP-SCP-004/acceptance_verification.md`, `docs/reviews/WP-SCP-004/test_results.txt` |
| architecture / structure | Medium | `ARCH-004` was narrower than the approved rule because it only scanned service files and required multiple markers. | Fixed by scanning backend code paths and accepting any explicit async/eventing marker when approved wrappers are absent. | `src/standards_control_plane/evaluators/architecture.py`, `fixtures/architecture-async-drift/backend/services/rebuild_cache.py` |
| architecture / structure | Medium | `ARCH-001` boundary detection was too brittle and missed broader import forms. | Fixed by scanning import lines and broadening frontend/backend boundary markers. | `src/standards_control_plane/evaluators/architecture.py` |
| architecture / structure | Medium | `ARCH-002` missed some multi-step orchestration shapes. | Fixed by broadening the orchestration check to allow either multiple awaits or awaited branching with workflow action markers. | `src/standards_control_plane/evaluators/architecture.py` |
| security / quality / governance | Medium | Raw substring scans could be tripped by comments. | Fixed in-slice by stripping comments before signal scans. | `src/standards_control_plane/evaluators/architecture.py` |
