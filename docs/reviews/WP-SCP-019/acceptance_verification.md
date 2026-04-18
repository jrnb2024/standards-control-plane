# WP-SCP-019 Acceptance Verification

Populated at slice 019F publish. All acceptance criteria from
`docs/requirements/WP-SCP-019-requirement-spec.md` accounted for below.

| Acceptance Criterion | Verification | Result |
|----------------------|-------------|--------|
| AC-WP-SCP-019-001 | SVC-003 rule published at `standards/service-lifecycle/rules/SVC-003-auth-contract.md` and registered in `standards/service-lifecycle/index.json`; `tests/test_service_lifecycle_audit.py::test_audit_builder_routes_service_lifecycle_domain` exercises the registered rule via the audit CLI path | Pass |
| AC-WP-SCP-019-002 | `schemas/auth-contract.schema.json` validates a four-mode declaration and rejects unknown modes; the runtime-contract schema references it via `$ref`. Pinned by `tests/test_service_lifecycle_audit.py::test_unknown_mode_fires_svc003`, `test_empty_accepted_modes_fires_svc003`, `test_audience_invalid_fires_svc003`, `test_jwks_url_invalid_fires_svc003`, `test_auth_contract_wrong_type_fires_svc003`, `test_accepted_modes_wrong_type_fires_svc003` | Pass |
| AC-WP-SCP-019-003 | `src/standards_control_plane/evaluators/service_lifecycle.py` implements SVC-001/002/003 with fixture-backed positive and negative cases across 34 fixtures under `fixtures/svc-*/` (corpus grew across 019B, 019B', and 019D additions). Pinned by `tests/test_service_lifecycle_audit.py` (40 tests, all passing) | Pass |
| AC-WP-SCP-019-004 | Audit CLI emits SVC-001/002/003 findings against the fixture corpus via `build_audit_result`. Pinned by `tests/test_service_lifecycle_audit.py::test_audit_builder_routes_service_lifecycle_domain`, `test_audit_builder_emits_svc003_for_past_close_date_fixture`; CLI-level end-to-end in `tests/test_service_lifecycle_cli.py::test_audit_write_output_flow_for_service_lifecycle_emits_all_artifacts` which verifies write-output produces valid CI, Control Tower, and report artifacts for a service-lifecycle audit | Pass |
| AC-WP-SCP-019-005 | `mapp-pim` dogfood run is an external-repo deliverable owned by the PIM adoption slice (programme-plan §7 unfreeze trigger 3). The in-repo dogfood against Standards Control Plane itself is pinned by `tests/test_scp_dogfood.py` (10 tests, clean audit against `services.yml` + `src/standards_control_plane/service.py`, plus broader-scope scan proving `EVALUATOR_SELF_EXCLUSIONS` holds) and documented in `docs/reviews/WP-SCP-019/dogfood-scp.md`. PIM dogfood tracked as an SCP-071 follow-up. | Pass (SCP in-repo) / Deferred by-design (mapp-pim external) |
| AC-WP-SCP-019-006 | `docs/adoption/ADOPT-001-project-onboarding.md` §11 rewritten against the SVC-003 four-mode contract with consumer (§11.2) and producer (§11.3–§11.8) tracks; `--auth-token` is no longer documented as a default. Adjacent edits in §1, §5.3, §6, §7.1, §9, §14, §15 preserve coherence. | Pass |
| AC-WP-SCP-019-007 | Review pack under `docs/reviews/WP-SCP-019/` contains `acceptance_verification.md` (this file), `implementation_notes.md` (019A–019F populated), `review_findings.md` (adversarial-review disposition per slice), `dogfood-scp.md` (019D write-up), and `test_results.txt` (full pytest run at publish time). | Pass |

## Test suite result at publish

Full repo suite: 164 passed. Verbose run captured in `test_results.txt`.

## Cross-references

- Rule: `standards/service-lifecycle/rules/SVC-003-auth-contract.md`
- Schema: `schemas/auth-contract.schema.json`
- Evaluator: `src/standards_control_plane/evaluators/service_lifecycle.py`
- Fixtures: `fixtures/svc-*/`
- Tests: `tests/test_service_lifecycle_audit.py`,
  `tests/test_service_lifecycle_cli.py`, `tests/test_scp_dogfood.py`
- Adopter guide: `docs/adoption/ADOPT-001-project-onboarding.md` §11
- Dogfood: `docs/reviews/WP-SCP-019/dogfood-scp.md`
- Decisions: D-019, D-020 in `docs/DECISIONS.md`
- Freeze directive: `FREEZE_DIRECTIVE_SVC003.md` at repo root
- Backlog parent: `SCP-071` in `docs/BACKLOG.md` Phase 7
