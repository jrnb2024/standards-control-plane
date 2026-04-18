# WP-SCP-019 Review Findings

Adversarial-review disposition for each slice of WP-SCP-019 plus the
cross-slice sweep. Each section records which findings were closed
before the corresponding commit and which were kept or deferred (with
reasoning).

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

## Slice 019D — adversarial review (2026-04-18)

Three parallel reviewer agents (dogfood declaration accuracy, test
durability + canary rigor, audit.py ripple) returned ~30 findings.
Three were real declaration-vs-reality mismatches that the static
evaluator couldn't catch (dogfood's actual value). All fixed in 019D.

**Declaration fixed to match runtime**

- **`/health` response shape**: SCP's handler returned `{"status": "ok"}`
  while SVC-002 mandates `{status ∈ {healthy, degraded, error},
  version, checks}`. Rewritten to emit the compliant shape with
  `version` sourced via `importlib.metadata`. `test_service_api.py`
  updated to pin the new shape.
- **`start_command` phantom module path**: the first draft targeted
  `standards_control_plane.service:app`, which does not exist (SCP
  uses `create_app()` factory). Rewritten to
  `-m standards_control_plane.cli serve ...` which matches both the
  console-script entry in `pyproject.toml` and the Docker runtime.
- **`audience: scp` vs `scp-dev`**: `local` block claimed
  `audience=scp` but `.env.example` sets `CT_APP_ID=scp-dev`.
  Declaration updated to `audience: scp-dev`; inline note records
  staging uses `scp` per `.env.staging.example`.

**Test hardening fixed**

- Close-date canary (`test_scp_dogfood_audit_fires_bearer_legacy_after_close_date`)
  now reads the close date from `services.yml` itself via a helper
  (`_scp_declared_close_date`) and adds one day. Governance-approved
  extensions update the declaration and the canary tracks.
- Waiver-ref verification split into positive + negative halves:
  `test_scp_waiver_ref_fires_when_an_unrelated_waiver_is_registered`
  (negative) and
  `test_scp_waiver_ref_clears_when_the_scp_migration_waiver_is_registered`
  (positive). The positive test proves the check silences when the
  correct waiver is registered, not just that some waiver being
  registered triggers it.
- `test_scp_dogfood_audit_is_clean_against_scoped_paths` now pins
  `summary.high_severity_count`, `medium_severity_count`, and
  `low_severity_count` all to 0 (previously only `findings == []`).
- `domain_status` assertion relaxed to subset check so future
  additions to the shape don't break the test.
- Added `test_audit_accepts_requested_area_id_when_scope_is_uninferrable`
  and `test_audit_still_rejects_mismatch_when_inference_succeeds` for
  direct coverage of the D-020 contract change.

**audit.py contract tightened**

- Substring match on `"Unable to infer area_id"` replaced with
  `AreaIdInferenceError(ValueError)` sentinel in `normaliser.py`.
  `audit.py` imports and catches the sentinel; future error-message
  changes cannot silently break the fallback path.
- D-020 decision row added to `docs/DECISIONS.md` documenting the
  uninferrable-scope relaxation and the preserved inferred-mismatch
  guardrail.

**Follow-ups deliberately out of 019D scope**

- PIM dogfood — external repo; owned by the PIM adoption slice.
- Multi-environment manifest (declare `local` + `staging` side by side
  so the `audience` and bind-host differences don't need inline notes)
  — tracked for a future manifest-schema amendment.
- SCP migration waiver registration in `output/findings/waivers.json`
  — blocked on the governance conversation; captured under SCP-071.
  The skip-when-empty behaviour means adoption is not blocked on this
  register landing first.
- Runtime conformance tooling for SVC-002 response-shape checks
  (the part the static evaluator cannot see) — tracked separately
  from WP-SCP-019.

**Verdict**

019D is no longer theatre. Three real mismatches fixed; the dogfood
clean-audit is earned, not gamed. The canary tests track the
declaration rather than hardcoding dates. The D-020 contract relaxation
is safe, narrow, typed, documented, and directly tested on both sides
of the discriminator. Safe to commit.

## Slice 019E — adversarial review (2026-04-18)

Three parallel reviewer agents (rule-vs-doc accuracy, structural
coherence, programme-plan alignment) returned ~40 findings against the
first draft of the §11 rewrite. Three HIGH correctness issues, one
structural gap, and two evidence-pack omissions — all closed in 019E.

**Fixed: correctness**

- **§14 anti-pattern mis-described the marker set.** The first draft
  claimed declaring `mode.user_oidc` while implementing "raw bearer"
  fires both `impl-missing-user_oidc` and
  `impl-undeclared-bearer_legacy`. In fact the code-pattern scan
  fires `impl-undeclared-bearer_legacy` only when the source contains
  `secrets.compare_digest` specifically. Rewritten to name the marker.
- **§11.5 migration target confused machine and browser callers.**
  First draft suggested migrating `mode.bearer_legacy` to
  `mode.api_key` "or `mode.user_oidc` where applicable".
  `mode.bearer_legacy` is a machine-caller path; browser callers use
  `mode.user_oidc` directly and have never been on bearer_legacy.
  The "or user_oidc" phrasing is removed; the migration target is
  `mode.api_key` exclusively, with a clarifying sentence that
  per-app migrations are tracked as separate work packages.
- **§11.4 env-var block implied `CT_JWKS_URL` is required.** Actually
  `ServiceConfig.from_env` derives it from `CT_BASE_URL` when unset.
  The doc now notes the default and explains when to override.
- **§11.4 `audience` example was self-contradictory.** Showed service
  key `my-app` with `audience: my-app-dev` under a comment about
  "local binding". Since SVC-003 ties audience to the services.yml
  key, the shape was misleading. Updated to use `my-app-dev` as the
  service key in the local environment, with explicit guidance that
  adopters should keep distinct service keys per environment (the
  pattern SCP itself uses).
- **§11.1 bearer_legacy marker now named** (`secrets.compare_digest`).
  §11.6 service_rs256 markers now include the singular `algorithm="RS256"`
  and `algorithm='RS256'` forms the evaluator actually scans for.
- **§11.7 skip-when-empty phrasing broadened** to "no waivers
  registered (file absent, empty list, or unparseable)" — the exact
  `_known_waiver_ids` predicate.
- **§11.7 waiver `finding_id` placeholder** now explicitly marked as
  a placeholder with the real format shape
  (`F-SVC-003-<area>-<service>-<signal>`); first draft used
  `F-SVC-003-BEARER-LEGACY` which reads as a canonical shape.

**Fixed: structural coherence**

- **Consumer track was promised and not delivered.** §11.1 opened
  with "two audiences" but §11.2–§11.8 were all producer-track
  content. A dedicated §11.2 "Consumer track: calling SCP (or any
  SVC-003 service)" now walks callers through the header
  requirements per mode (OIDC cookie, `X-API-Key`,
  `Authorization: Bearer`, RS256 JWT).
- **Upgrade path added** as §11.3 for adopters with pre-SVC-003
  services.yml.
- **Deps section relocated** out of §11 and into §7.1 where
  dependency review is the subject. `pyyaml>=6.0` gets a version
  floor matching `pyproject.toml`; `ct_auth-0.8.0` wheel named
  explicitly.
- **§15 checklist bullet** split into a clearly-delimited "Additional
  checks for service-hosting repos" sub-list so consult-only adopters
  are not confused by service-lifecycle bullets.
- **§1 Purpose** now mentions service-lifecycle as an adoption
  obligation so readers who skim the opening sections understand the
  scope.
- **§9 Agent Workflow** now tells agents to include
  `service-lifecycle` in consult domains for service-hosting repos
  or `services.yml` changes.
- **Python-only story softened**: §11.1 notes the code-pattern scan
  is source-pattern-based and language-agnostic; §11.4 explicitly
  mentions Node/Go services must emit matching patterns or accept
  impl-missing findings as waivers.

**Fixed: evidence pack**

- `implementation_notes.md` Slice 019E section populated with the
  delivery summary (was "Pending" before this commit).
- `review_findings.md` — this section is the 019E adversarial-review
  disposition that was missing in the first draft.

**Kept as-is after reasoning**

- Close date `2026-06-30` cited in multiple places (§5.3, §11.7,
  §14). Only D-019 is authoritative; every other citation points at
  it. Keeping explicit dates makes the doc greppable for future
  amendments.
- Asymmetric domain coverage (service-lifecycle gets a full §11;
  other domains get §12's shared principles). Justified because
  SVC-003 is an adopter-facing declarative contract that requires
  concrete artefacts in the adopter repo; governance/architecture/
  UX/design/product are advisory rules consumed via consult. OPINION
  flag only.
- Anti-pattern style mixing abstract principles with specific finding
  names. Concrete finding IDs help adopters recognise what they'll
  see in audit output; mixing is a feature, not a tone defect.

**Not fixed in 019E by design**

- README.md and STATUS.md updates are 019F scope.
- Linking `dogfood-scp.md` and `README.md` to ADOPT-001 §11 — also
  019F (publish slice) per programme plan §3.
- Per-app migration plans for estate services still on
  `mode.bearer_legacy` — programme plan §4 explicitly lists these
  as separate work packages.

**Verdict**

The §11 rewrite is now accurate against the rule, the schema, the
evaluator, and SCP's own dogfood. Both audiences (consumer and
producer) have their own tracks. The upgrade path for pre-SVC-003
services.yml is explicit. Evidence pack is updated. Safe to commit.

## Slice 019F — adversarial review (2026-04-18)

Two parallel reviewer agents (publish-content accuracy,
PR-readiness) returned a mix of BLOCKER/HIGH/MEDIUM findings against
the first draft of the publish slice. All genuine defects closed in
this commit; the rest are either already-correct or explicit
follow-ups.

**Fixed before commit**

- **Fixture count stale** — acceptance_verification and
  implementation_notes claimed "31 fixtures". Actual count is 34
  (corpus grew through 019B' and 019D). Updated both files with the
  correct count and a note about which slice added which fixtures.
- **019B test count stale** — implementation_notes said "36 tests" in
  `test_service_lifecycle_audit.py`; actual is 40 (019B' added the
  `svc-entry-unknown-field`, `svc-scp-self-audit`, waiver-ref-demo
  cases, and 019D added dogfood-adjacent ones). Updated with the
  019B-seeded vs 019B'/019D-grown framing.
- **`docs/deployment.md` §8 `/health` sample stale** — still
  documented the pre-019D `{"status":"ok"}` shape. Rewritten to the
  SVC-002-compliant `{status,version,checks}` shape. The 019D
  dogfood's whole point was that this endpoint didn't match SVC-002;
  leaving the runbook's sample stale would have contradicted the
  fix.
- **"Opened the PR" past-tense in implementation_notes** — claimed
  the PR was already opened, but the PR opens after this commit
  lands. Rewritten to future-tense.
- **Programme-plan §3 slice-status table stale** — still showed
  "in draft" / "pending" for every row. Updated to "complete" with
  each slice's commit SHA (plus the 019B' row as a formal entry).
- **"Stub" preambles removed** from `implementation_notes.md` and
  `review_findings.md` openings. Both files have been populated for
  slices now; the word "Stub" was false.

**Kept as-is after reasoning**

- **Ruff line-length warnings** in `evaluators/service_lifecycle.py`
  — pre-existing, not a 019-introduced regression, and ruff isn't
  gated in CI. Tech debt; noted for a future style pass.
- **Mypy not installed in the environment** — dev-only optional
  dep; not a regression.
- **`docs/plans/PROG-SCP-001-autonomous-execution-plan.md` still
  says "complete through WP-SCP-018"** — intentional per that plan's
  own §7 framing that any further work is "a new programme
  increment". WP-SCP-019 is that increment; the old plan doesn't
  need amending.
- **README Phase 1 Progress section** — historical; intentionally
  not rewritten. The updated status banner and the forward-reference
  to ADOPT-001 §11 tell current-state readers what they need.
- **Programme-plan §7 evidence capture for external triggers 2 and
  3** — the plan says evidence should be "captured in
  `docs/reviews/WP-SCP-019/` in slice 019F". Acceptance verification
  records these as deferred-by-design (external repos); the
  `dogfood-scp.md` §7 explicitly names the PIM repo's own adoption
  slice as the owner. No additional review-pack file needed —
  the obligation is deferred to per-app slices, which is the
  correct scope boundary.

**Verdict**

Publish slice is accurate. Claims in STATUS.md, README, BACKLOG,
acceptance_verification, and implementation_notes match the actual
state of the branch (commits, counts, cross-references, test
results). Programme plan reflects slice completion. Deployment
runbook's `/health` sample aligns with the 019D handler rewrite.
Safe to commit and open the PR.
