# WP-SCP-019 Slice 019D — Dogfood against Standards Control Plane

**Date:** 2026-04-18
**Scope:** Standards Control Plane itself (in-repo service)
**Target audit request:** `examples/audit-request-scp-dogfood.json`

## 1. Purpose

Prove SVC-001, SVC-002, and SVC-003 auto-checks work against a real
service declaration — not just synthetic fixtures. SCP is the natural
first dogfood target because:

- it has a real FastAPI service at
  `src/standards_control_plane/service.py`
- its auth implementation is the named reference for `mode.user_oidc`
  (commit `66ba8a4` — vendored `ct_auth`, CT JWKS, audience =
  `CT_APP_ID`)
- it also carries a `--auth-token` code path, which is exactly the
  `mode.bearer_legacy` shape captured by D-019

Dogfooding here closes the loop: SCP practises what it publishes
before ADOPT-001 §11 is rewritten in slice 019E.

## 2. What dogfood surfaced — and what was fixed

The first dogfood pass revealed three real declaration-vs-reality
mismatches that the static evaluator couldn't catch. All three were
fixed in this slice before the clean-audit result could be claimed.

### 2.1 `/health` response shape violated SVC-002

SCP's `/health` returned `{"status": "ok"}`. SVC-002 mandates
`{status ∈ {healthy, degraded, error}, version, checks}`. The static
evaluator only substring-matches the declared path in source, so it
passed a genuinely non-compliant endpoint. **Fix:** `service.py` now
returns `{"status": "healthy", "version": <package version>, "checks":
{}}`. `test_service_api.py` updated to pin the new shape.

### 2.2 `start_command` described a module path that doesn't exist

The first declaration was
`-m uvicorn standards_control_plane.service:app ...`, but `service:app`
is not a module-level attribute — SCP uses a `create_app(...)` factory,
backed by the `standards-control-plane` console script (pyproject.toml
`[project.scripts]`) which calls `cli.main()` → `serve()` →
`create_app()`. **Fix:** `services.yml` now declares
`-m standards_control_plane.cli serve --host 127.0.0.1 --port 3787`.

### 2.3 `audience: scp` contradicted the local .env defaults

The declaration claimed the local runtime enforces `aud=scp`, but
`.env.example` sets `CT_APP_ID=scp-dev` (so local enforces `aud=scp-dev`).
The `services.yml` `local` block must describe the local runtime.
**Fix:** `audience` is now `scp-dev` with an inline note that staging
uses `scp` per `.env.staging.example`.

## 3. Artefacts in the dogfood

- `services.yml` at repo root declaring SCP as a service
- `examples/audit-request-scp-dogfood.json` — audit request scoped to
  `services.yml` plus `src/standards_control_plane/service.py`
- `tests/test_scp_dogfood.py` — 10 tests including the clean-audit
  canary, the close-date migration canary (reads the date from
  `services.yml` rather than hardcoding), both halves of the waiver-ref
  verification, and direct coverage of the D-020 audit.py contract

## 4. Dogfood run — 2026-04-18

```text
$ PYTHONPATH=src python3 -m standards_control_plane.cli audit \
    --request examples/audit-request-scp-dogfood.json
```

Result: `service-lifecycle` evaluated clean.

- `domain_status.service-lifecycle = evaluated`
- `scores.service-lifecycle = 100`
- `findings = []`
- `summary.{high,medium,low}_severity_count = 0`

The broader-scope variant (including the full
`src/standards_control_plane/` tree) also produces zero findings: the
evaluator's `EVALUATOR_SELF_EXCLUSIONS` skip keeps the evaluator's
own marker constants from self-poisoning the code-pattern scan.

## 5. Signal-level account

What the evaluator actually **ran and passed** against SCP's declaration:

SVC-001:
- runtime_contract block present
- all required fields declared
- `interpreter: python-venv` → `venv_path: .venv` present
- `working_dir: .` resolves (exists)

SVC-002:
- healthcheck path `/health` substring-present in scanned source.
  Response-shape compliance with SVC-002 is proven at runtime by
  `tests/test_service_api.py` pinning `status=healthy`, `version`,
  `checks`.

SVC-003:
- auth_contract block is a mapping; accepted_modes is a non-empty list
- each entry is a mapping with a string mode value
- each entry carries only fields the schema allows (no `unknown-field`)
- both declared modes are in the approved set
- each entry carries the per-mode required metadata
- `audience: scp-dev` matches the bare app-id pattern
- `jwks_url` is a well-formed https URL
- `deprecation_close_date` is valid ISO and still in the future on
  `2026-04-18`
- no mode declared twice
- `impl-missing` does not fire: `ControlTowerAuth`, `ct_auth.`, and
  `CT_JWKS_URL` markers present for user_oidc;
  `secrets.compare_digest` present for bearer_legacy
- `impl-undeclared` does not fire: no `algorithms=["RS256"]`,
  `X-API-Key`, or `x-api-key` markers in scanned paths once
  `EVALUATOR_SELF_EXCLUSIONS` skips the evaluator's own module

What the evaluator **skipped** (not the same as passed):

- `bearer-legacy-waiver-not-found` — skipped because
  `output/findings/waivers.json` is `[]`. Both halves of the
  activation contract are covered by dedicated tests:
  `test_scp_waiver_ref_fires_when_an_unrelated_waiver_is_registered`
  and `test_scp_waiver_ref_clears_when_the_scp_migration_waiver_is_registered`.
  Once `scp-bearer-legacy-migration` lands in waivers.json, the check
  becomes an active positive verification.

What the evaluator **cannot** check statically:

- SVC-002's response-shape contract. Proven at runtime via
  `test_service_api.py`. Future runtime conformance tooling is tracked
  separately from WP-SCP-019.

## 6. Observations

1. **Declaration integrity beats evaluator coverage.** The `/health`
   shape mismatch, the phantom `service:app` module path, and the
   `audience: scp` vs `scp-dev` divergence were all things the static
   evaluator would never catch. Fixing them required reading the
   runtime alongside the declaration. Dogfood's real value is exactly
   this — forcing alignment.
2. **Self-exclusion is load-bearing.** Without
   `EVALUATOR_SELF_EXCLUSIONS`, SCP would fire
   `impl-undeclared-service_rs256` and `impl-undeclared-api_key`
   against its own evaluator source.
3. **Skip-when-empty waivers are right for early adoption.** SCP's
   `waivers.json` is `[]`; the waiver-ref check skips. Once governance
   registers `scp-bearer-legacy-migration`, the check activates
   automatically.
4. **`area_id` passthrough (D-020) earns its keep.** The dogfood scope
   has no ENH-style marker; `_normalise_scope` now falls back to the
   request's `area_id` on `AreaIdInferenceError`. The inferred-mismatch
   guardrail is still pinned by
   `test_audit_still_rejects_mismatch_when_inference_succeeds`.
5. **Close-date canary now tracks the declaration.** The
   bearer-legacy canary reads the date from `services.yml` directly,
   so a governance-approved close-date extension that updates the
   declaration keeps the canary honest without any test edit.

## 7. Pilot target coverage

The freeze directive's 019D brief names `mapp-pim` as the natural
pilot because its `pkg/platform/auth.go` implements a pluggable chain
matching the four-mode set. That repository lives outside this
codebase and cannot be audited directly from here; its dogfood belongs
to the PIM repo's own adoption slice. The SCP dogfood above closes
the in-repo half of the contract; the PIM half is tracked under
SCP-071 but does not gate WP-SCP-019 merging (programme-plan §7
Unfreeze Trigger 3: "Per-app migration plans drafted" — a draft, not
a completed dogfood).

## 8. Follow-ups (not in 019D scope)

- Register `scp-bearer-legacy-migration` in
  `output/findings/waivers.json` with owner + expires_at matching
  D-019's 2026-06-30 close date. Tracked under SCP-071.
- PIM dogfood — owned by the PIM adoption slice.
- Multi-environment manifest shape so local + staging can coexist
  without inline narrative notes. Tracked for a future manifest-schema
  amendment, not 019F.
- Runtime conformance tooling for SVC-002 response-shape checks
  (the part the static evaluator cannot see). Tracked separately.
