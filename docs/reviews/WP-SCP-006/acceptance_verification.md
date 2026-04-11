# WP-SCP-006 Acceptance Verification

| Acceptance criterion | Evidence |
|----------------------|----------|
| `AC-WP-SCP-006-001` `audit --write-output` updates latest and subsystem markdown reports | `tests/test_reports.py::test_report_cli_prints_fresh_review_and_rejects_stale_output` |
| `AC-WP-SCP-006-002` `audit --write-output` updates the subsystem-keyed area summary with a valid payload | `tests/test_reports.py::test_write_audit_reports_generates_markdown_and_area_summary`; `tests/test_examples_validate.py::test_returns_area_summary_validates` |
| `AC-WP-SCP-006-003` `report` prints only fresh generated markdown and fails explicitly otherwise | `tests/test_reports.py::test_report_cli_prints_fresh_review_and_rejects_stale_output`; `tests/test_reports.py::test_report_cli_fails_when_latest_review_is_missing`; `tests/test_reports.py::test_report_cli_fails_explicitly_when_findings_store_is_invalid` |
| `AC-WP-SCP-006-004` latest review reflects required sections, evidence paths, and stable ordering | `tests/test_reports.py::test_write_audit_reports_generates_markdown_and_area_summary` |
| `AC-WP-SCP-006-005` repeat write-backed generation is deterministic | `tests/test_reports.py::test_write_audit_reports_is_deterministic` |
| `AC-WP-SCP-006-006` subsystem-keyed area summary preserves exact `area_id` and audit timestamp | `tests/test_reports.py::test_write_audit_reports_generates_markdown_and_area_summary` |
| `AC-WP-SCP-006-007` complete evidence pack present | `docs/reviews/WP-SCP-006/review_findings.md`; `docs/reviews/WP-SCP-006/implementation_notes.md`; `docs/reviews/WP-SCP-006/acceptance_verification.md`; `docs/reviews/WP-SCP-006/test_results.txt` |
