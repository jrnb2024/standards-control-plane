# WP-SCP-018 Review Findings

**Work Package:** `WP-SCP-018`  
**Date:** 2026-04-12  
**Gate:** A — planning  
**Status:** Findings incorporated; approved for implementation

## Findings

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| architecture / structure | Medium | The first concept mixed service auth, portfolio reporting, and richer evidence into one vaguely shared “platform” layer, which risked hiding the actual contracts being extended. | Accepted and fixed by separating service auth, portfolio reporting, and extractor/normaliser contract changes in the plan. | Strategy section 1; TechnicalArchitecture section 2 |
| security / quality / governance | Medium | The service auth requirement did not preserve the unauthenticated default or the existing health-check behaviour. | Accepted and fixed by making bearer auth optional and keeping `GET /health` public. | FR-SCP-1801; FR-SCP-1802 |
| completeness / acceptance coverage | Medium | The first planning pass did not define how trend views would be persisted. | Accepted and fixed by requiring a persisted comparison against prior portfolio snapshots. | FR-SCP-1804 |

## Outcome

Gate A is complete. The planning pack is approved for implementation with
explicit contract extensions rather than a generic platform abstraction.

## Gate B — Code Review

**Date:** 2026-04-12  
**Status:** Findings addressed; approved for PR

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| architecture / structure | Medium | The first richer-evidence pass only matched nested paths such as `/docs/` or `/.storybook/`, which meant repo-root scopes would silently miss Storybook, screenshot, graph, docs, frontend, and backend signals. | Accepted and fixed by widening the normaliser path classifiers to handle repo-root directories as well as nested paths. | `src/standards_control_plane/normaliser.py`; `tests/test_extraction_normalisation.py` |
| security / quality / governance | Low | The new auth coverage was present in the service layer but the test helpers could not send authenticated requests until the request builders accepted custom headers. | Accepted and fixed by extending the HTTP test helpers with explicit header support and exercising protected plus unprotected routes. | `tests/test_service_api.py` |
| completeness / acceptance coverage | Low | The first review pass left the new portfolio reporting slice without an explicit persisted-history contract. | Accepted and fixed by adding separate multi-repo dashboard, portfolio history, and portfolio trend schemas plus write-backed tests. | `schemas/multi-repo-dashboard.schema.json`; `schemas/portfolio-history.schema.json`; `schemas/portfolio-trend.schema.json`; `src/standards_control_plane/estate_reporting.py`; `tests/test_estate_reporting.py` |
