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

Pending.

## Slice 019D — dogfood

Pending.

## Slice 019E — ADOPT-001 §11 rewrite

Pending.

## Slice 019F — publish

Pending.
