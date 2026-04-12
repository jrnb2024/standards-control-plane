# WP-SCP-013 Acceptance Verification

| Acceptance Criterion | Verification | Result |
|----------------------|-------------|--------|
| AC-WP-SCP-013-001 | `tests/test_calibration.py::test_false_positive_summary_builds_and_validates` | Pass |
| AC-WP-SCP-013-002 | `tests/test_calibration.py::test_write_false_positive_summary_persists_summary` and `audit --write-output` refresh | Pass |
| AC-WP-SCP-013-003 | `tests/test_calibration.py::test_calibration_cli_prints_current_summary` | Pass |
| AC-WP-SCP-013-004 | `tests/test_consult_ordering.py::test_frontend_consult_orders_patterns_before_rules_and_prefers_frontend_domains` | Pass |
| AC-WP-SCP-013-005 | Review evidence pack completed under `docs/reviews/WP-SCP-013/` | Pass |
