# WP-SCP-019 Implementation Notes

Slice-by-slice implementation notes for WP-SCP-019 as delivered on
`feature/wp-scp-019-svc-003-auth-contract`. Updated alongside each
slice commit; finalised at 019F publish.

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
- Fixture corpus under `fixtures/svc-*/` (seeded at 31 in 019B; grew to 34 after 019B' cross-slice additions and 019D dogfood fixtures; covering every
  signal from every rule, plus positive cases for each approved mode and
  a multi-service yaml).
- Tests at `tests/test_service_lifecycle_audit.py` — 40 tests at publish time (36 in the 019B commit; grew through 019B' cross-slice and 019D fixture additions), all
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

- Added `services.yml` at repo root declaring SCP as a service
  (SVC-001 runtime_contract + SVC-002 healthcheck + SVC-003
  auth_contract with `[mode.user_oidc (audience=scp-dev), mode.bearer_legacy]`).
- Added `examples/audit-request-scp-dogfood.json` scoping to
  `services.yml` + `src/standards_control_plane/service.py`.
- Added `tests/test_scp_dogfood.py` — 10 tests covering clean audit,
  broad-scope audit (proves `EVALUATOR_SELF_EXCLUSIONS` holds),
  close-date canary that parses the date from `services.yml`, positive
  and negative halves of the waiver-ref verification, the D-020
  uninferrable-fallback branch, and the inferred-mismatch guardrail.
- **Three real declaration-vs-reality mismatches** found during the
  dogfood session and fixed in this slice:
  1. `service.py`'s `/health` handler was returning `{"status": "ok"}`
     in violation of SVC-002's mandated `{status, version, checks}`
     shape. Handler rewritten to emit `{status: "healthy", version,
     checks: {}}`; `test_service_api.py` updated to pin the new shape.
  2. First draft `start_command` referenced
     `standards_control_plane.service:app`, a module-level attribute
     that does not exist (SCP uses a `create_app()` factory). Command
     rewritten to `-m standards_control_plane.cli serve ...` which
     matches the console-script and Docker entry points.
  3. First draft `audience: scp` contradicted `.env.example` which
     sets `CT_APP_ID=scp-dev` for local runtime. Declaration updated
     to `audience: scp-dev` (the `local` block describes local
     reality); inline note records staging uses `scp`.
- Extended `src/standards_control_plane/audit.py` `_normalise_scope`
  to fall back to the requested `area_id` when
  `normaliser._infer_area_id` raises the new `AreaIdInferenceError`
  (sentinel exception, replacing an earlier substring match). The
  inferred-mismatch guardrail is preserved; only uninferrable-scope
  + explicit area_id is relaxed. Captured as D-020.
- Added `AreaIdInferenceError(ValueError)` sentinel in
  `src/standards_control_plane/normaliser.py`.
- `service.py` now exports a `_package_version()` helper sourced
  from `importlib.metadata.version("standards-control-plane")` with
  a `0.0.0+unknown` fallback for non-installed test runs.
- Adversarial review (three parallel agents: declaration-accuracy,
  test-durability, audit.py-ripple) surfaced the three declaration
  mismatches above plus the temporal-brittleness and waiver
  positive-path gaps. All fixed in this commit except the documented
  follow-ups (PIM dogfood, multi-environment manifest, runtime
  conformance tooling).
- Full repo suite: 164/164 passing.

## Slice 019E — ADOPT-001 §11 rewrite

- Rewrote §11 of `docs/adoption/ADOPT-001-project-onboarding.md` from
  its pre-SVC-003 "Optional Shared Service Mode" shape (~20 lines
  describing `--auth-token`) into a ~240-line "Service Auth Contract
  (SVC-003)" section with explicit consumer and producer tracks.
- Producer subsections: §11.3 upgrade path (for pre-SVC-003
  services.yml), §11.4 mode.user_oidc, §11.5 mode.api_key, §11.6
  mode.service_rs256, §11.7 mode.bearer_legacy (deprecated, with
  waiver shape), §11.8 mode-selection guide, §11.9 running SCP's HTTP
  service locally.
- §11.1 approved-modes table now includes the exact
  implementation-marker substrings the evaluator scans for
  (`ControlTowerAuth`, `ct_auth.`, `create_bff_routes`, `CT_JWKS_URL`
  for user_oidc; `algorithms=["RS256"]` etc. for service_rs256;
  `X-API-Key`, `x-api-key` for api_key; `secrets.compare_digest`
  for bearer_legacy). Non-Python adopters get explicit guidance that
  the scan is source-pattern-based and language-agnostic.
- §11.2 consumer track covers browser, machine-caller via api_key,
  machine-caller via bearer_legacy (deprecation window), and S2S via
  rs256 — the audience split promised at the top of §11 is now
  maintained through all subsections.
- Adjacent edits:
  - §1 Purpose: added a line naming the service-lifecycle adoption
    obligation for service-hosting repos.
  - §5.3: reworded the shared-consult-service paragraph to point at
    §11.6 (mode selection) and §11.7 (bearer deprecation) rather than
    the whole §11.
  - §6 Pre-Onboarding Decisions: added a "Service auth modes
    (SVC-003)" row.
  - §7.1 Install: added the runtime-dep closure (fastapi, uvicorn,
    httpx, jsonschema, pyyaml>=6.0, pydantic, vendored ct_auth) so
    adopters with locked deps know what's coming. This closes the
    019B review-findings deferral.
  - §9 Agent Workflow: added the instruction to include
    `service-lifecycle` in consult domains when the repo hosts a
    service.
  - §14 Anti-Patterns: four new bullets covering missing auth_contract,
    declared-vs-implemented mismatches (now phrased accurately against
    the `secrets.compare_digest` marker), `--auth-token` as a
    long-term default, and silent waiver lapse.
  - §15 Adoption Acceptance Checklist: separated service-hosting
    checks into a clearly-delimited sub-list so consult-only adopters
    are not blocked by the service-lifecycle bullets.
- Adversarial review (three parallel agents: rule-vs-doc accuracy,
  structural coherence, programme-plan alignment) surfaced ~40
  findings. Three HIGH correctness issues (misnamed code markers in
  §14, a misleading "mode.user_oidc as bearer_legacy migration target"
  suggestion in §11.5, and an undocumented `CT_JWKS_URL` default) and
  one structural gap (consumer-track audience never addressed in the
  first draft) all fixed in this commit. Bearer_legacy marker named;
  skip-when-empty phrasing broadened to cover absent/empty/malformed
  waivers.json; RS256 markers now include the singular `algorithm=`
  forms. Full disposition captured in
  `docs/reviews/WP-SCP-019/review_findings.md`.
- No source code or schema change in 019E. Full repo suite:
  164/164 passing (doc-only change).

## Slice 019F — publish

- Updated `docs/STATUS.md` to reflect WP-SCP-019 as the active
  programme increment on the feature branch (pending PR), list the
  post-closeout commits that landed between WP-SCP-018 and
  WP-SCP-019 (`ecfbce2`, `66ba8a4`, `571d086`, `ba1130e`) per the
  freeze directive, summarise slices 019A–019F, and capture the
  SVC-003 freeze-directive unfreeze-trigger state.
- Updated `README.md` status banner and the "complete through
  WP-SCP-018" paragraph; added cross-links to STATUS and to ADOPT-001
  §11.
- Populated `docs/reviews/WP-SCP-019/acceptance_verification.md` with
  concrete Pass/Deferred rows against each AC-WP-SCP-019-* criterion,
  citing the specific test files and doc sections that verify each.
- Captured the verbose `pytest -v` run in
  `docs/reviews/WP-SCP-019/test_results.txt`.
- Populated this implementation_notes.md §019F section.
- Updated `docs/BACKLOG.md` Phase 7 SCP-071 row from "in progress" to
  "done" with the WP-SCP-019 PR reference; trigger 2 and 3 follow-ups
  captured as notes on that row.
- The WP-SCP-019 PR opens after this commit lands on the feature
  branch. Freeze-directive unfreeze-trigger 1 is satisfied on PR
  merge; triggers 2 (CT SDK vendoring in consuming apps) and 3
  (per-app migration plans) remain external and are tracked under
  SCP-071 follow-ups.
- Full repo suite at publish: 164/164 passing.
