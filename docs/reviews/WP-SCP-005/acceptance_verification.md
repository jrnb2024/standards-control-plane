# WP-SCP-005 Acceptance Verification

| Acceptance criterion | Evidence |
|----------------------|----------|
| `AC-WP-SCP-005-001` repeated persistence is idempotent | `tests/test_findings_persistence.py::test_persist_audit_findings_is_idempotent` |
| `AC-WP-SCP-005-002` new findings are written with deterministic identity | `tests/test_findings_persistence.py::test_persist_audit_findings_reconciles_scope_and_preserves_timestamps` |
| `AC-WP-SCP-005-003` disappeared same-scope findings resolve and leave open store | `tests/test_findings_persistence.py::test_persist_audit_findings_reconciles_scope_and_preserves_timestamps` |
| `AC-WP-SCP-005-004` out-of-scope findings remain untouched | `tests/test_findings_persistence.py::test_persist_audit_findings_reconciles_scope_and_preserves_timestamps` |
| `AC-WP-SCP-005-005` explicit `audit --write-output` path writes findings stores | `tests/test_findings_persistence.py::test_audit_cli_write_output_persists_reconciled_stores` |
| `AC-WP-SCP-005-006` tracked open/history outputs are schema-valid and inspectable in git | `tests/test_examples_validate.py::test_open_findings_store_validates`; `tests/test_examples_validate.py::test_history_findings_store_validates` |
| `AC-WP-SCP-005-007` audit remains read-only when `--write-output` is absent | `tests/test_findings_persistence.py::test_audit_cli_is_read_only_without_write_flag` |
| `AC-WP-SCP-005-008` `created_at` is preserved and `updated_at` refreshes on matching findings | `tests/test_findings_persistence.py::test_persist_audit_findings_reconciles_scope_and_preserves_timestamps` |
| `AC-WP-SCP-005-009` duplicate findings collapse when identical and fail when conflicting | `tests/test_findings_persistence.py::test_reconcile_findings_collapses_identical_duplicates_and_rejects_conflicts` |
| `AC-WP-SCP-005-010` complete evidence pack present | `docs/reviews/WP-SCP-005/review_findings.md`; `docs/reviews/WP-SCP-005/implementation_notes.md`; `docs/reviews/WP-SCP-005/acceptance_verification.md`; `docs/reviews/WP-SCP-005/test_results.txt` |
