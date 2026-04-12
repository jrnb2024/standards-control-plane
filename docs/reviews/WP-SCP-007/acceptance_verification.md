# WP-SCP-007 Acceptance Verification

| Acceptance Criterion | Result | Evidence |
|----------------------|--------|----------|
| AC-WP-SCP-007-001 | Passed | `tests/test_governance_audit.py`; `tests/test_waivers_and_scoring.py::test_build_audit_result_treats_missing_waivers_file_as_empty` |
| AC-WP-SCP-007-002 | Passed | `tests/test_waivers_and_scoring.py::test_build_audit_result_applies_active_waiver_and_updates_score` |
| AC-WP-SCP-007-003 | Passed | `tests/test_waivers_and_scoring.py::test_waived_finding_reopens_after_waiver_expiry` |
| AC-WP-SCP-007-004 | Passed | `tests/test_waivers_and_scoring.py::test_build_audit_result_ignores_expired_waiver`; `tests/test_waivers_and_scoring.py::test_build_audit_result_rejects_overlapping_active_waivers` |
| AC-WP-SCP-007-005 | Passed | `src/standards_control_plane/scoring.py`; `src/standards_control_plane/evaluators/governance.py`; `src/standards_control_plane/evaluators/architecture.py`; `tests/test_waivers_and_scoring.py::test_score_findings_ignores_non_open_statuses_and_clamps_to_zero` |
| AC-WP-SCP-007-006 | Passed | `docs/reference/score-model-2026-04-12.md`; `README.md` |
| AC-WP-SCP-007-007 | Passed | `tests/test_waivers_and_scoring.py::test_waived_finding_reopens_after_waiver_expiry` |
| AC-WP-SCP-007-008 | Passed | `docs/reviews/WP-SCP-007/review_findings.md`; `docs/reviews/WP-SCP-007/implementation_notes.md`; `docs/reviews/WP-SCP-007/test_results.txt` |
