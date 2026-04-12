# WP-SCP-007 Review Findings

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
