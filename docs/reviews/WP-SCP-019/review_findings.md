# WP-SCP-019 Review Findings

Stub. Populated as slices 019A–019F land.

## Slice 019A — adversarial review (2026-04-18)

Three parallel reviewer agents (rule/schema correctness, estate reality,
repo wiring) surfaced a combined defect list before the 019A commit.
Findings grouped by disposition:

**Fixed in 019A before commit**

- `interpreter: none` exemption dropped (too loose; SVC-001 permits Go mesh
  services to declare `interpreter: none` for real networked services).
- Contradiction between "must include" rule text and optional schema
  resolved by clarifying that presence is evaluator-enforced, not
  schema-enforced (consistent with SVC-001's pattern).
- Signals split into static (auto-checked) and runtime (out of scope for
  static evaluator) — matches SVC-002's existing shape.
- `accepted_modes` gained `uniqueItems: true`; duplicate-by-mode-id check
  deferred to evaluator semantics and added as an explicit signal.
- `audience` pattern pinned to bare app-id (`^[a-z][a-z0-9-]*$`); rule text
  clarifies it is not a URI.
- `waiver_ref` definition tied to `output/findings/waivers.json`.
- Multi-mode example added (SCP itself declares `[user_oidc, bearer_legacy]`).
- Exempt-path list added covering OIDC bootstrap paths (`/auth/*`,
  `/api/auth/*`, `/.well-known/*`, `/health`, `/status-app/health`).
- `key_id_prefix` added as optional metadata for `mode.api_key` to give the
  evaluator something to cross-reference against.
- Schema `$ref` style aligned to `./<name>.schema.json` convention.
- Programme plan gained explicit Programme Protocol Position, External
  Dependencies (CT agent-key issuer registration, SDK vendoring), and Risks
  sections.
- Freeze directive path reference added to the programme plan.
- Architecture doc clarified that static file scanning includes code-pattern
  scans, not just schema validation.
- BACKLOG.md gained Phase 7 / SCP-071 row.
- Review-pack stub created under `docs/reviews/WP-SCP-019/`.

**Deferred to later slices (by design, not dodge)**

- README.md programme-complete banner updated in 019F alongside STATUS.md,
  per the user's explicit slice plan (019F is the publish slice).
- `key_id_prefix` semantics and `issuer` enum tightening left to 019B/019E
  once the CT agent-key registration conversation lands.
- Cross-repo SDK-vendoring evidence path operationalised in 019F.

**Rejected / OPINION-only**

- Schema `$id` injection: repo convention is loader-injected (`schema_tools._load_schema_file`). Adding `$id` to this schema alone would diverge from 14 sibling schemas. Revisit only if the loader changes.
- Commit-SHA-only rule reference: kept, paired with file-path reference to
  `src/standards_control_plane/service.py`. SHA serves as an archaeological
  marker; file-path ref survives history edits.

## Slice 019B — adversarial review (2026-04-18)

Three parallel reviewer agents (evaluator correctness + edge-cases, fixture
coverage, integration + repo consistency) returned 54 findings. Dispositions:

**Fixed in 019B before commit**

- Bare-map fallback tightened: `_parse_services` now requires a top-level
  `services:` mapping and rejects anything else as malformed. Prevents
  `infrastructure`-type top-level keys from being treated as services.
- SVC-001 gained a `working-dir-missing` check (the signal the rule listed
  but the evaluator never enforced).
- SVC-002 loose match (`healthcheck in content or "/health" in content`)
  replaced with an exact-path-only check. A service declaring `/healthz`
  while code has only `/health` now correctly fires the missing-handler
  finding.
- `standards_version` validation moved into `_validate_standards_version`,
  called from both `_deterministic_timestamp` and the top of
  `evaluate_service_lifecycle`, so non-YYYY-MM-DD input is caught whether
  or not the caller supplies `evaluated_at`.
- `mode.bearer_legacy` code markers tightened: dropped the ambiguous
  `'Bearer "'` / `"Bearer '"` patterns that fired on docstrings and error
  messages. Kept `secrets.compare_digest` — a distinctive, unambiguous
  marker for constant-time bearer comparison.
- Added `audience` pattern check (`^[a-z][a-z0-9-]*$`). Rule text already
  said audience is a bare app-id, not a URI; evaluator now enforces it.
- Added `jwks_url` http(s) URL shape check.
- `auth_contract` that is not a mapping now fires
  `auth-contract-wrong-type`.
- `accepted_modes` that is not a list (e.g. a dict) now fires
  `accepted-modes-wrong-type`.
- Malformed `accepted_modes[i]` (entry not a mapping; `mode` not a string)
  now fires `malformed-entry-<i>` / `malformed-mode-<i>` rather than being
  silently skipped.
- Malformed `deprecation_close_date` distinguished from missing: a
  present-but-unparseable value now fires
  `bearer-legacy-close-date-malformed-<i>`.
- `SEVERITY_ORDER.get(..., 99)` defensive default in `_sorted_findings`.
- `_code_paths_to_scan` output sorted so evidence ordering is stable.
- Fixture corpus extended from 16 to 31 to close coverage gaps:
  - `mode.service_rs256` positive + impl-undeclared + impl-missing
  - `mode.api_key` missing-issuer
  - `mode.bearer_legacy` missing-close-date (distinct from missing-waiver)
  - `mode.bearer_legacy` malformed-close-date
  - audience-pattern invalid
  - jwks_url malformed
  - auth_contract wrong type (string)
  - accepted_modes wrong type (dict)
  - malformed entry (string instead of mapping)
  - working_dir missing
  - multi-service (planned + ready siblings)
  - bare-map (no top-level `services:` key)
  - conformant-all-modes (all four modes declared with correct metadata and
    code markers; proves no false positives at the full conformant path)
- `test_audit_builder_routes_service_lifecycle_domain` tightened to assert
  the signal key, not just `rule_ids == ["SVC-003"]`.
- Architecture doc `docs/architecture/WP-SCP-019-technical-architecture.md`
  fixture-location reference corrected from `fixtures/service-lifecycle/`
  to `fixtures/svc-*/`, and the exempt-paths "constant in the evaluator"
  promise walked back — the exemption is runtime-shaped (URL-level, not
  file-level) and belongs to future runtime conformance tooling.
- `implementation_notes.md` 019B section authored.

**Kept as-is after reasoning**

- Reimplementation of per-field checks instead of a single
  `validate_with_schema(auth_contract, "auth-contract.schema.json")`
  call: hand-rolled checks give per-signal finding IDs with specific
  remediations, which is higher value than a single generic
  schema-violation finding. The hand-roll now covers every shape
  constraint the schema enforces (audience pattern, uri shape,
  additionalProperties via the unknown-mode/malformed-entry path).
- Code-pattern marker breadth: narrow estate-anchored markers
  (`ControlTowerAuth`, `algorithms=["RS256"]`, `X-API-Key`,
  `secrets.compare_digest`) kept over broader aliases. The estate
  converges on `ct_auth`; broadening introduces false positives that
  hurt advisory-first rollout.
- Windows path separators: the extractor already normalises to forward
  slashes via `_canonical_relative`, so the concern doesn't manifest.
- `fixtures/architecture-api-drift` reused as the "no services.yml"
  test scope: it's a stable existing fixture that will fail loudly if
  its contents ever acquire a services.yml. Acceptable coupling.
- Root-level `status` reading: tightened parser means a service entry
  without a `local` block can't be planned anyway, so the concern is
  moot.

**Deferred to later slices by design**

- OIDC bootstrap-path exemption as per-path filter logic: SVC-003's
  exempt-path list is a runtime-shaped concept (which endpoints require
  the declared mode), not a static-scan concept. 019B's static evaluator
  explicitly documents this in the architecture doc; future runtime
  conformance tooling (outside WP-SCP-019 scope) will enforce the
  exemption directly.
- Path-aware code-pattern scanning: deliberately simple substring scan.
  AST-aware or URL-route-aware matching is a separate calibration slice
  (tracked against the 019D dogfood pass).
- Adopter documentation of the pyyaml dependency: 019E rewrites
  `ADOPT-001` §11 and will note runtime deps there.

**Rejected**

- Silent `{services: null}` path: resolved by the tightened parser, which
  now requires `services` to be a mapping.
- Test that pre-existing fixtures don't contain a surprise `services.yml`:
  reviewer verified this directly (none do).
- Adding `$id` to schemas: 14 sibling schemas don't; the repo loader
  synthesises `$id` at load time. Consistency beats isolated hardening.

## Cross-slice adversarial review (2026-04-18, post-019B)

One reviewer audited 019A and 019B together to catch drift invisible to
each per-slice review, plus validate the "on-plan" deferrals from both
slices. Three real defects surfaced, all fixed now (no 019C prerequisite):

**Fixed**

- **Evaluator self-poisoning**: `MODE_CODE_MARKERS` contains marker strings
  as Python literals, which the substring scan then matched when any audit
  scope included the evaluator's own source file (verified empirically:
  all four modes fired on `evaluators/service_lifecycle.py`). Added
  `EVALUATOR_SELF_EXCLUSIONS` with path-suffix match; `_code_paths_to_scan`
  skips any file ending `evaluators/service_lifecycle.py`. Regression test
  at `test_scp_self_audit_does_not_self_poison` using a dedicated
  `fixtures/svc-scp-self-audit/` that mirrors SCP's source layout.
- **`additionalProperties: false` not enforced**: schema rejects unknown
  entry fields (typos like `audeince` for `audience`), evaluator did not.
  Added `ALLOWED_BASE_ENTRY_FIELDS` + `ADDITIONAL_ENTRY_FIELDS_BY_MODE`
  and an `unknown-field-<mode>-<i>` finding per entry with stray keys.
  New fixture `svc-entry-unknown-field` and matching test.
- **`waiver_ref` existence unchecked**: rule promised `waiver_ref` resolves
  to a `waiver_id` in `output/findings/waivers.json`; evaluator never
  looked. Added `_known_waiver_ids()` that loads waivers.json when it
  exists **and is non-empty**; fires
  `bearer-legacy-waiver-not-found-<i>` when the declared ref is absent.
  Skip-when-empty keeps existing conformant fixtures green while the
  check activates automatically once an adopter populates the registry.
  Two new tests exercise both states via `monkeypatch` of
  `service_lifecycle.output_dir`, leaving schema resolution pointed at
  the real SCP repo root.

**Doc fix-ups**

- `SVC-002-health-endpoint.md` split into static / runtime signal
  sections (matching SVC-003's shape). The static evaluator auto-checks
  one signal (path-vs-handler); five runtime signals remain explicitly
  out of scope.
- `SVC-003-auth-contract.md` signal list extended to name the type-shape
  and pattern signals the evaluator already emits
  (`auth_contract` not a mapping; `accepted_modes` not a list; unknown
  field; `audience` pattern; `jwks_url` shape; close-date malformed;
  `waiver_ref` not registered).
- `standards/service-lifecycle/index.json` signals list mirrors the
  extended rule body.

**"On-plan" deferrals validated as genuinely slice-boundary**

- README/STATUS update → 019F: on the user's explicit slice plan.
- Cross-repo SDK vendoring evidence path → 019F: same.
- `pyyaml` adopter documentation → 019E: ADOPT-001 §11 is the rewrite
  slice; external deps get captured there.
- OIDC bootstrap-path exemption as per-path filter: runtime-shaped
  concept (URL-level, not file-level). Architecture doc correctly walks
  back the evaluator-side promise; enforcement belongs to future runtime
  conformance tooling.
- Path-aware code-pattern scanning → 019D calibration: correct placement.

**Cross-slice gaps flagged as OPINION (not fixed in 019B')**

- No fixture pinned to 2026-06-30 close date: the estate-wide bearer
  deprecation date from D-019 isn't directly exercised by a fixture
  whose close-date comparison triggers at that boundary. Existing fixtures
  cover past (2025-12-31) and future (2099-12-31). OPINION — can be
  added during 019D dogfood if useful.
- No breadcrumb in `MODE_METADATA_REQUIRED["mode.api_key"]` referencing
  the CT-side agent-key issuer registration dependency from
  programme-plan §5. OPINION — a one-line comment could close the loop,
  but the dependency is captured in the plan doc itself.

**Verdict**

019A + 019B now mutually consistent. Schema, rule text, `index.json`
signal list, and evaluator implementation agree on every signal. Cross-
slice drift closed. Safe to open 019C.

## Slice 019C — adversarial review (2026-04-18)

Three parallel reviewer agents (test rigor + CLI surface coverage,
write-output flow correctness, regression + repo-consistency) returned
~35 findings. One BLOCKER was empirical: the write-output test left
`output/findings/area-summaries/service-lifecycle.json` on disk after
every run because the cleanup glob filtered on `"svc-custom"` but the
writer keys on `subsystem` (verified on-disk via `git status`).

**Fixed in 019C before commit**

- **Area-summary leak**: cleanup predicate corrected to use explicit
  paths for the three writers that key on subsystem (`area-summaries/
  service-lifecycle.json`, `control-tower/subsystems/
  service-lifecycle.json`, `reports/subsystems/service-lifecycle-
  review.md`). Leaked file deleted from the repo.
- **Mixed-domain test assertion tightened**: now pins both `GOV-003`
  and `SVC-003` are present, asserts high-severity findings appear in
  ascending finding_id order (catching a dict-iteration merge
  regression), and confirms determinism across runs.
- **Overlay test tightened**: `test_overlay_can_replace_svc003_and_raise_severity`
  now also asserts SVC-001 and SVC-002 survive the overlay (catches a
  would-be bug where overlay drops unmentioned rules) and pins their
  base severity.
- **`consult._domain_priority`** missed `service-lifecycle` entirely;
  entries added to both frontend and backend order dicts. Backend
  priority: service-lifecycle is right after architecture; frontend:
  lowest. No tie-breaking ambiguity for mixed-domain consult requests.
- **show-registry coverage**: new test
  (`test_show_registry_cli_surfaces_service_lifecycle_rules`) invokes
  `show-registry` via subprocess and asserts service-lifecycle domain
  with all three SVC rules is present.
- **Read-back CLI subcommand coverage**: the write-output test now
  also invokes `findings`, `report`, `ci --format json`, `ci`,
  `control-tower`, `control-tower --format surface` within the same
  snapshot window and asserts each renders service-lifecycle content.
  Exercises the full read-side CLI surface after a service-lifecycle
  audit.
- **Consult example file**: added
  `examples/consult-request-service-lifecycle.json` matching the style
  of the existing audit-request example. Accompanying schema-validation
  test.

**Kept as-is after reasoning**

- Subprocess-based write-output test (vs. monkeypatched in-process):
  matches the established repo pattern (`test_ci_outputs.py`,
  `test_findings_persistence.py`, `test_control_tower_outputs.py`,
  `test_reports.py`, `test_architecture_audit.py` all do the same
  preserve/restore dance). Reviewer HIGH concerns about interrupt
  corruption and xdist collisions apply equally to all five; fixing
  them properly (CLI `--output-dir` flag or serial pytest marker) is
  cross-test scope and belongs to a dedicated test-hygiene slice, not
  019C.
- Changed-audit git-diff path untested via CLI subprocess: the
  `changed_paths=[...]` bypass exercises the domain-routing contract,
  which is what 019C is actually about. The git-resolution path is
  already covered by `tests/test_changed_audit.py` in a domain-
  agnostic way.
- Serve HTTP surface for service-lifecycle: the FastAPI service routes
  through `build_audit_result` / `build_consult_response` which are
  fully tested for the domain. Adding a parallel HTTP test is redundant
  coverage, not a gap.
- Overlay ADD-a-new-rule semantics: the repo's overlay system allows
  this; the evaluator is hardcoded to SVC-001/002/003 so a new SVC-004
  overlay rule would be loaded in the registry but not auto-checked.
  This is by design (new rules require evaluator code). Documenting it
  would be useful, but the overlay REPLACE semantics (proven) are the
  higher-value coverage.

**Cross-slice gaps noted but not fixed in 019C**

- Area-summary subsystem-area filename collision (pre-existing):
  `reports.py` keys area summaries by `{subsystem}.json`, so two
  distinct areas within the same subsystem overwrite each other. Real
  latent bug that 019C's multi-area fixture suite exposes but does not
  cause. Belongs to a reports-namespacing slice, not service-lifecycle.
- Findings-history corruption on interrupt: shared with five other
  subprocess-preserve-and-restore tests in the repo; belongs to a
  test-hygiene slice.

**Verdict**

019C CLI integration is structurally complete after the cross-slice
defect closure. Ten tests (up from the initial eight) cover the full
CLI surface: audit, audit-changed (via `changed_paths`), consult,
show-registry, findings, report, ci, control-tower, overlay extension,
and mixed-domain audit with deterministic sort order. The empirical
disk leak is closed. Safe to commit.
