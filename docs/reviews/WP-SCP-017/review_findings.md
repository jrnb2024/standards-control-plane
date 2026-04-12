# WP-SCP-017 Review Findings

**Work Package:** `WP-SCP-017`  
**Date:** 2026-04-12  
**Gate:** A — planning  
**Status:** Findings incorporated; approved for implementation

## Findings

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| architecture / structure | Medium | The first idea risked creating a service-only consult/audit path, which would drift from the CLI and make overlays inconsistent across entry points. | Accepted and fixed by requiring the service layer to call the existing consult and audit builders directly. | FR-SCP-1703; FR-SCP-1705; Strategy section 1 |
| security / quality / governance | Medium | Overlay behaviour was not explicit about replacement order, which would make project-specific overrides hard to reason about. | Accepted and fixed by requiring deterministic overlay ordering and identifier-based replacement. | FR-SCP-1701; FR-SCP-1702 |
| completeness / acceptance coverage | Medium | The first planning pass did not pin the minimum service endpoint set. | Accepted and fixed by defining the health, registry, consult, and audit endpoint surface up front. | FR-SCP-1704 |

## Outcome

Gate A is complete. The planning pack is approved for implementation with a
single shared consult/audit core and overlay-aware registry loading.

## Gate B — Code Review

**Date:** 2026-04-12  
**Status:** Findings addressed; approved for PR

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| architecture / structure | Medium | The first overlay pass would only have affected consult and registry reads unless the merged registry snapshot was threaded into evaluator rule lookup as well. | Accepted and fixed by passing `registry_snapshot` through audit dispatch and each evaluator rule loader. | `src/standards_control_plane/audit.py`; `src/standards_control_plane/evaluators/*.py` |
| security / quality / governance | Low | The service and overlay slice initially left touched files with line-length and import-order debt that would make the changed scope fail targeted lint hygiene. | Accepted and fixed with a targeted lint cleanup across the touched file set. | `src/standards_control_plane/registry.py`; `src/standards_control_plane/consult.py`; `src/standards_control_plane/audit.py`; `src/standards_control_plane/evaluators/*.py`; `tests/test_registry_overlays.py`; `tests/test_service_api.py` |
| completeness / acceptance coverage | Low | No blocking coverage gaps remained after verification; overlay merge semantics, overlay-aware consult and audit, and the HTTP service endpoints are all covered. | Closed. | `tests/test_registry_overlays.py`; `tests/test_service_api.py` |
