# WP-SCP-019 Implementation Notes

Stub. Populated as slices 019A–019F land on
`feature/wp-scp-019-svc-003-auth-contract`.

## Slice 019A — SVC-003 rule + approved-mode enum spec

- Authored `standards/service-lifecycle/rules/SVC-003-auth-contract.md`
  (declare-a-contract, closed mode set, per-mode required metadata).
- Authored `schemas/auth-contract.schema.json` (closed enum, per-mode
  conditional required fields, `audience` pattern, `uniqueItems`).
- Registered SVC-003 in `standards/service-lifecycle/index.json`.
- Extended `schemas/runtime-contract.schema.json` with optional
  `auth_contract` property; presence enforced by the evaluator per SVC-001
  pattern.
- Authored planning quartet under `docs/plans/`, `docs/requirements/`,
  `docs/strategy/`, `docs/architecture/`.
- Added D-019 row to `docs/DECISIONS.md`.
- Added Phase 7 / SCP-071 row to `docs/BACKLOG.md`.
- Adversarial review (three parallel agents) findings addressed in draft 2
  before commit.

## Slice 019B — service-lifecycle evaluator

- Authored `src/standards_control_plane/evaluators/service_lifecycle.py`
  covering SVC-001, SVC-002, and SVC-003. Evaluator validates
  `project_area` against the schema, parses `services.yml` from the
  `artefacts.configs` bucket, and emits one finding per (rule, service,
  signal) combination.
- Added `pyyaml>=6.0` to `pyproject.toml` runtime dependencies.
- Extended `src/standards_control_plane/normaliser.py`
  `CONFIG_FILENAMES` with `services.yml` and `services.yaml` so service
  manifests land in `artefacts.configs`.
- Registered the evaluator in `src/standards_control_plane/evaluators/__init__.py`
  and `src/standards_control_plane/audit.py` `EVALUATORS` so the CLI and
  service surface pick it up automatically.
- Fixture corpus under `fixtures/svc-*/` (31 fixtures covering every
  signal from every rule, plus positive cases for each approved mode and
  a multi-service yaml).
- Tests at `tests/test_service_lifecycle_audit.py` — 36 tests, all
  passing. Full repo suite: 140/140 passing.
- SVC-003 static-vs-runtime signal split honoured: static evaluator does
  schema-style validation plus code-pattern scanning (markers for
  `ControlTowerAuth`, `algorithms=["RS256"]`, `X-API-Key`,
  `secrets.compare_digest`). Runtime request-probing signals remain out
  of scope, consistent with SVC-002's existing pattern.
- Architecture doc updated to reflect the actual fixture location
  (`fixtures/svc-*/`) and the runtime-shaped nature of SVC-003's exempt
  paths (not encoded in the static evaluator).
- Adversarial review (three parallel agents: evaluator correctness,
  fixture coverage, integration + repo consistency) surfaced 54 findings
  across all three lenses; 019B dispositions captured in
  `review_findings.md`.

## Slice 019C — audit CLI integration

- Authored `examples/audit-request-service-lifecycle.json` and
  `examples/consult-request-service-lifecycle.json` so adopters have a
  service-lifecycle-specific starting point matching the style of the
  pre-existing audit/consult examples.
- Added `fixtures/svc-conformant-all-modes/docs/enhancements/
  ENH-923-svc-omni.md` so the audit-builder's area-id inference
  resolves for that fixture (required for the CLI smoke-test against
  the example request).
- Added `tests/test_service_lifecycle_cli.py` with 10 tests exercising:
  example schema validation for both audit and consult requests;
  `audit` CLI against the example conformant fixture;
  `audit --write-output` producing valid CI/report/control-tower/
  findings artifacts and then exercising every read-back subcommand
  (`findings`, `report`, `ci --format json|markdown`, `control-tower`,
  `control-tower --format surface`);
  `show-registry` surfacing SVC-001/002/003; `audit-changed`
  routing service-lifecycle via `changed_paths=[...]`; consult
  surfacing applicable SVC rules; overlay REPLACE semantics raising
  SVC-003 severity while SVC-001/002 survive; mixed-domain audit
  evaluating both governance and service-lifecycle with deterministic
  high-severity finding-id ordering.
- Extended `src/standards_control_plane/consult.py` `_domain_priority`
  to include `service-lifecycle` in both frontend and backend order
  dicts. Backend priority: service-lifecycle sits right after
  architecture; frontend: lowest. Previously fell through to the
  default `99`, which caused fragile tie-breaking in mixed-domain
  consult requests.
- Adversarial review (three parallel agents: test rigor + CLI surface,
  write-output correctness, regression + repo-consistency) surfaced
  ~35 findings. One empirical BLOCKER (area-summary disk leak) fixed;
  overlay, mixed-domain, and consult-priority assertions tightened;
  CLI subcommand read-back coverage added. Disposition captured in
  `review_findings.md` under "Slice 019C — adversarial review".
- Full repo suite: 154/154 passing.

## Slice 019D — dogfood

Pending.

## Slice 019E — ADOPT-001 §11 rewrite

Pending.

## Slice 019F — publish

Pending.
