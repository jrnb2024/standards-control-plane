# WP-SCP-003 Acceptance Verification

| Acceptance criterion | Evidence |
|----------------------|----------|
| `AC-WP-SCP-003-001` live governance audit path | `tests/test_governance_audit.py::test_audit_builder_returns_live_governance_result_with_domain_status`; `tests/test_governance_audit.py::test_audit_cli_returns_live_governance_result`; `docs/reviews/WP-SCP-003/test_results.txt` |
| `AC-WP-SCP-003-002` missing enhancement spec -> `GOV-002` | `tests/test_governance_audit.py::test_governance_evaluator_flags_missing_enhancement_spec` |
| `AC-WP-SCP-003-003` missing review evidence -> `GOV-003` | `tests/test_governance_audit.py::test_governance_evaluator_flags_missing_review_evidence` |
| `AC-WP-SCP-003-004` boundary mismatch -> `GOV-001` | `tests/test_governance_audit.py::test_governance_evaluator_flags_boundary_mismatch`; `tests/test_governance_audit.py::test_audit_rejects_mismatched_scope_area_id` |
| `AC-WP-SCP-003-005` deterministic score and ordered findings | `tests/test_governance_audit.py::test_governance_evaluator_returns_clean_score_for_seeded_area`; `tests/test_governance_audit.py::test_governance_evaluator_orders_multiple_findings_by_severity_then_rule` |
| `AC-WP-SCP-003-006` unsupported domains explicit in structured output | `tests/test_governance_audit.py::test_audit_builder_returns_live_governance_result_with_domain_status`; `examples/audit-result.json` |
| `AC-WP-SCP-003-007` live examples updated | `tests/test_governance_audit.py::test_audit_example_matches_live_builder_output`; `tests/test_extraction_normalisation.py::test_example_project_area_payload_matches_live_output` |
| `AC-WP-SCP-003-008` docs and control records updated | `docs/BACKLOG.md`; `docs/DECISIONS.md`; `docs/STATUS.md`; WP-SCP-003 planning pack |
| `AC-WP-SCP-003-009` seeded review evidence pack present and traceable | `docs/reviews/WP-SCP-003/review_findings.md`; `docs/reviews/WP-SCP-003/implementation_notes.md`; `docs/reviews/WP-SCP-003/acceptance_verification.md`; `docs/reviews/WP-SCP-003/test_results.txt` |
