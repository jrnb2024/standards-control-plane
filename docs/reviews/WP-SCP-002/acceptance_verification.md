# WP-SCP-002 Acceptance Verification

**Date:** 2026-04-11

| Acceptance Criterion | Status | Evidence |
|---|---|---|
| AC-WP-SCP-002-001 Extracting the seeded returns pilot scope returns a deterministic set of canonically ordered repo-local file paths. | PASS | `tests/test_extraction_normalisation.py::test_extract_scope_returns_expected_canonical_paths` and manual `PYTHONPATH=src` extraction run. |
| AC-WP-SCP-002-002 Missing or escaped scope paths fail with explicit test coverage. | PASS | `tests/test_extraction_normalisation.py::test_extract_scope_missing_path_fails`, `tests/test_extraction_normalisation.py::test_extract_scope_rejects_boundary_escape`, `tests/test_extraction_normalisation.py::test_extract_scope_rejects_symlink_led_escape`, and `tests/test_extraction_normalisation.py::test_extract_scope_rejects_scope_path_symlink`. |
| AC-WP-SCP-002-003 Normalising the seeded returns pilot scope produces a schema-valid project-area model. | PASS | `tests/test_extraction_normalisation.py::test_normalise_project_area_matches_expected_buckets`. |
| AC-WP-SCP-002-004 The seeded pilot fixture matrix includes at least one concrete file for each declared extraction bucket: docs, code path, enhancement spec, prompt, UI component, service, test, and config. | PASS | Fixture files added under `fixtures/returns-pilot/` and asserted through `tests/test_extraction_normalisation.py::test_normalise_project_area_matches_expected_buckets`. |
| AC-WP-SCP-002-005 The normalised model places docs, code paths, enhancement specs, prompts, UI components, services, tests, and configs into the correct artefact buckets for the seeded pilot. | PASS | `tests/test_extraction_normalisation.py::test_normalise_project_area_matches_expected_buckets`. |
| AC-WP-SCP-002-006 The normalised model infers `returns-exceptions` as the area id for the seeded pilot example. | PASS | `tests/test_extraction_normalisation.py::test_normalise_project_area_matches_expected_buckets`. |
| AC-WP-SCP-002-007 Re-running extraction and normalisation for the same scope returns the same ordered payload. | PASS | `tests/test_extraction_normalisation.py::test_extract_scope_returns_expected_canonical_paths` and `tests/test_extraction_normalisation.py::test_example_project_area_payload_matches_live_output`. |
| AC-WP-SCP-002-008 The example project-area payload validates against the new schema. | PASS | `tests/test_examples_validate.py::test_project_area_example_validates` and `tests/test_extraction_normalisation.py::test_example_project_area_payload_matches_live_output`. |
| AC-WP-SCP-002-009 The project docs, backlog, decision log, and status are updated in the same session as code changes. | PASS | `README.md`, `docs/BACKLOG.md`, `docs/DECISIONS.md`, and `docs/STATUS.md` updated during the same governed work package session. |
