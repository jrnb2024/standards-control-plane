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
