# WP-SCP-007 Review Findings

```scp-review-evidence
{
  "review_id": "WP-SCP-007",
  "area_id": "standards-control-plane",
  "reviewed_at": "2026-04-12T00:00:00Z",
  "summary": "Waiver-aware audit assembly and shared scoring landed with explicit review and score-model documentation.",
  "reviewed_paths": [
    "src/standards_control_plane/audit.py",
    "src/standards_control_plane/waivers.py",
    "src/standards_control_plane/scoring.py"
  ],
  "findings": [
    {
      "finding_id": "RV-WP-SCP-007-001",
      "status": "resolved",
      "summary": "Waiver handling needed to preserve visibility while keeping waived issues out of active score penalties.",
      "domain": "governance"
    }
  ]
}
```

**Work Package:** `WP-SCP-007`  
**Date:** 2026-04-12  
**Gate:** A — planning  
**Status:** Findings incorporated; approved for implementation

## Findings

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| architecture / structure | High | The plan did not make the audit-result contract change explicit enough, so implementers could add waiver logic without a stable output boundary. | Accepted and fixed by explicitly stating `waivers_applied` plus waiver-aware summary output in strategy and technical architecture. | Strategy section 4; TechnicalArchitecture section 4 |
| security / quality / governance | Medium | Deterministic ordering for applied waivers was implied but not stated, which risks git churn from human-edited waiver files. | Accepted and fixed by requiring deterministic waiver-aware output ordering. | RequirementSpec FR-SCP-712; Strategy section 4 |
| completeness / acceptance coverage | High | The acceptance set did not prove that expired or removed waivers reopen still-live findings on the next audit. | Accepted and fixed by adding explicit reopening coverage. | AC-WP-SCP-007-007; TechnicalArchitecture section 3 |

## Outcome

Gate A is complete. The planning pack is approved for implementation with an
explicit audit-result contract change, deterministic waiver ordering, and
acceptance coverage for reopening findings after waiver expiry or removal.

## Gate B — Code Review

**Date:** 2026-04-12  
**Status:** Findings addressed; one bounded residual carried to backlog

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| architecture / structure | Medium | Audit results still do not carry a score-model version tag, which will matter once scoring semantics evolve beyond the current phase-1 baseline. | Accepted as a bounded residual because the model is documented and tested in this slice, but payload-level versioning can land separately. | Backlog `SCP-046`; `docs/reference/score-model-2026-04-12.md` |
| security / quality / governance | Low | No blocking findings remained after verification; invalid waiver payloads, overlapping active waivers, and missing waiver files are all covered explicitly. | Closed. | `tests/test_waivers_and_scoring.py`; `schemas/waivers-file.schema.json`; `src/standards_control_plane/waivers.py` |
| completeness / acceptance coverage | Low | No blocking findings remained after verification; the acceptance set covers active waivers, expired waivers, deterministic applied-waiver ordering, and reopened findings after waiver expiry. | Closed. | `tests/test_waivers_and_scoring.py`; `docs/reviews/WP-SCP-007/acceptance_verification.md` |
