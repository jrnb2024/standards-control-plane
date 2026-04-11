# WP-SCP-001 Acceptance Verification

**Date:** 2026-04-11

| Acceptance Criterion | Status | Evidence |
|---|---|---|
| AC-WP-SCP-001-001 Running `consult` with the example request returns at least one applicable rule and one guidance item derived from real registry content. | PASS | `tests/test_consult_retrieval.py::test_consult_response_is_schema_valid_and_deterministic`, `tests/test_consult_retrieval.py::test_consult_cli_returns_live_registry_data`, and local CLI run with `PYTHONPATH=src python3 -m standards_control_plane.cli consult --request examples/consult-request.json`. |
| AC-WP-SCP-001-002 Running `consult` with the example request returns at least one approved pattern derived from real registry content. | PASS | `tests/test_consult_retrieval.py::test_consult_response_is_schema_valid_and_deterministic` and manual CLI run both returned `dashboard-pattern` and `action-service-pattern`. |
| AC-WP-SCP-001-003 Running `consult` returns a schema-valid consult response. | PASS | `tests/test_consult_retrieval.py::test_consult_response_is_schema_valid_and_deterministic`. |
| AC-WP-SCP-001-004 Broken registry references fail with explicit test coverage. | PASS | `tests/test_consult_retrieval.py::test_broken_registry_reference_fails_explicitly`. |
| AC-WP-SCP-001-005 The minimal findings store is read and matching open findings are surfaced using domain-first matching with area/path refinement. | PASS | `tests/test_consult_retrieval.py::test_findings_store_validates_and_supports_domain_first_matching` plus manual `findings` and `consult` runs. |
| AC-WP-SCP-001-006 Re-running `consult` with the same request and repository state returns the same ordered response content. | PASS | `tests/test_consult_retrieval.py::test_consult_response_is_schema_valid_and_deterministic`. |
| AC-WP-SCP-001-007 The `show-registry` command remains available and reflects the real registry content used by consult. | PASS | `tests/test_consult_retrieval.py::test_show_registry_cli_returns_loaded_registry` and local CLI run with `PYTHONPATH=src python3 -m standards_control_plane.cli show-registry`. |
| AC-WP-SCP-001-008 The project docs, backlog, decision log, and status are updated in the same session as code changes. | PASS | `README.md`, `docs/STATUS.md`, `docs/BACKLOG.md`, and existing decision log updated during the same governed work package session. |
