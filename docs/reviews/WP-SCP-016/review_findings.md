# WP-SCP-016 Review Findings

**Work Package:** `WP-SCP-016`  
**Date:** 2026-04-12  
**Gate:** A — planning  
**Status:** Findings incorporated; approved for implementation

## Findings

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| architecture / structure | Medium | The first concept risked deriving estate status straight from live evaluator calls, which would have blurred the Control Tower boundary and duplicated write-time work. | Accepted and fixed by making the surfacing layer consume persisted SCP outputs only. | FR-SCP-1605; Strategy section 1; TechnicalArchitecture section 2 |
| security / quality / governance | Medium | The initial scope did not explicitly require deterministic rollup ordering for estate dashboards, which would make downstream diffs noisy. | Accepted and fixed by adding an explicit estate rollup requirement and acceptance criterion. | FR-SCP-1603; AC-WP-SCP-016-002 |
| completeness / acceptance coverage | Medium | The first planning pass did not guarantee a CLI read path for the surfaced artifacts. | Accepted and fixed by adding a Control Tower CLI read requirement and acceptance criterion. | FR-SCP-1606; AC-WP-SCP-016-003 |

## Outcome

Gate A is complete. The planning pack is approved for implementation with
one-way Control Tower surfacing over persisted Standards Control Plane outputs.

## Gate B — Code Review

**Date:** 2026-04-12  
**Status:** Findings addressed; approved for PR

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| architecture / structure | Medium | The first implementation inferred subsystem membership from `area_id` prefixes when counting open findings, which was broader than the persisted data contract justified. | Accepted and fixed by scoping Control Tower counts to the audited `area_id` instead of prefix-based inference. | `src/standards_control_plane/control_tower.py`; `tests/test_control_tower_outputs.py` |
| security / quality / governance | Low | The first exporter pass left avoidable CLI noise and lint issues in the new Control Tower code path. | Accepted and fixed with targeted lint cleanup across the changed file set. | `src/standards_control_plane/cli.py`; `src/standards_control_plane/control_tower.py`; `tests/test_control_tower_outputs.py`; `tests/test_ci_outputs.py` |
| completeness / acceptance coverage | Low | No blocking coverage gaps remained after verification; schema validation, estate rollup, and CLI read-path behaviour are covered. | Closed. | `tests/test_control_tower_outputs.py` |
