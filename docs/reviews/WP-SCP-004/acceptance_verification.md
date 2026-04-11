# WP-SCP-004 Acceptance Verification

| Acceptance criterion | Evidence |
|----------------------|----------|
| `AC-WP-SCP-004-001` live governance plus architecture audit | `tests/test_governance_audit.py::test_audit_builder_returns_live_governance_result_with_domain_status`; `tests/test_governance_audit.py::test_audit_cli_returns_live_governance_result`; `docs/reviews/WP-SCP-004/test_results.txt` |
| `AC-WP-SCP-004-002` seeded returns pilot emits `ARCH-001` and `ARCH-002` | `tests/test_architecture_audit.py::test_architecture_evaluator_returns_seeded_returns_findings` |
| `AC-WP-SCP-004-003` repo-backed `ARCH-003` case | `tests/test_architecture_audit.py::test_architecture_evaluator_flags_arch_003_from_repo_backed_fixture` |
| `AC-WP-SCP-004-004` repo-backed `ARCH-004` case | `tests/test_architecture_audit.py::test_architecture_evaluator_flags_arch_004_from_repo_backed_fixture` |
| `AC-WP-SCP-004-005` deterministic architecture ordering and score | `tests/test_architecture_audit.py::test_architecture_evaluator_returns_seeded_returns_findings`; `tests/test_architecture_audit.py::test_architecture_evaluator_preserves_findings_order` |
| `AC-WP-SCP-004-006` deterministic merged audit finding order | `tests/test_architecture_audit.py::test_audit_builder_preserves_merged_findings_order_and_unsupported_domains` |
| `AC-WP-SCP-004-007` unsupported requested domain remains explicit | `tests/test_architecture_audit.py::test_audit_builder_preserves_merged_findings_order_and_unsupported_domains` |
| `AC-WP-SCP-004-008` live example audit output updated | `tests/test_governance_audit.py::test_audit_example_matches_live_builder_output`; `tests/test_examples_validate.py::test_audit_result_example_validates` |
| `AC-WP-SCP-004-009` complete evidence pack present | `docs/reviews/WP-SCP-004/review_findings.md`; `docs/reviews/WP-SCP-004/implementation_notes.md`; `docs/reviews/WP-SCP-004/acceptance_verification.md`; `docs/reviews/WP-SCP-004/test_results.txt` |
