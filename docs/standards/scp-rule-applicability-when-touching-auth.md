# SCP rule applicability — when your app touches auth

Quick-reference matrix for adopters wiring auth changes (SDK migrations, BFF refresh, role/permission schema registration, JWT handling). Tells you which SCP rules might fire on your PR + what to expect + valid waiver shapes.

Pairs with CT's matching estate-auth coordination doc (which covers the CT-side decisions: schema registration, wildcard interaction, app_permissions key creation, gate-style convergence). This SCP-side doc covers the rule-applicability axis only.

---

## Rule-applicability matrix

| Rule | Fires on | What it checks | Common adopter touchpoint |
|---|---|---|---|
| **SCP-R-001** | `services.yml` modifications | `auth_contract.accepted_modes` declares one of `{mode.user_oidc, mode.service_rs256, mode.api_key, mode.bearer_legacy}` per entry; `mode.bearer_legacy` carries `deprecation_close_date` ∈ `{2026-06-30, 2026-09-30}` (per D-019 + D-021 forward) | adding a new service to `services.yml`; flipping a service's mode (e.g. bearer_legacy → user_oidc); declaring a deprecation close date |
| **SCP-R-002** | `output/findings/waivers.json` and any other waivers payload modifications | Schema validity per `schemas/waiver.schema.json` — required keys (rule_id, expires_at, reason, approved_by, scope), `expires_at` parseable ISO-8601 | filing a new waiver; renewing an expiring waiver; refactoring waivers structure |
| **SCP-R-003** | Vendoring marker presence | Adopter declares vendored deps via `.vendored` marker file with required structure | first-time vendoring of a new SCP runtime release; updating a pinned dependency |
| **SCP-R-004** | `output/findings/waivers.json` `reason` field | The `reason` string contains at least one HTTP(S) URL pointing to an issue / PR / governance doc explaining why the waiver was filed | filing ANY new waiver; renewing waivers post-v1.1.0 |

**No SCP rule currently targets:**
- CT permission_schemas registration calls (per recommender-shopify-j1-rbac response Q6, 2026-05-09).
- BFF refresh-token rotation patterns (would be candidate for WP-SCP-025 RULE-006 `bff_refresh_hardening`; parked).
- ct-auth-provider memoization patterns (WP-SCP-025 RULE-007 `ct_auth_provider_memoization`; parked).
- JWT shape / claim-set validation (no rule planned; CT's `WP-D035-612` JWT bloat reduction is CT-internal).

WP-SCP-025 (parked plan-doc; kicks off post-WP-SCP-024 Threshold A) may add 2-3 of: `protected_tables_updated_with_migration`, `r1_evidence_linked_in_pr_body`, `waiver_expiry_within_window`, `secrets_not_in_committed_env_files`, `permission_schema_registered_within_wave_window`. None retroactively invalidate prior schema registrations or auth migrations.

---

## What the rules DON'T do

- **Don't drive CT decisions.** SCP rules report on adopter-side state (services.yml, waivers, vendoring). CT's per-app permissions, gate-style convergence, schema registration sequencing, and admin UI ownership are CT decisions, not SCP findings.
- **Don't modify your code.** Findings are advisory until the federation primitive (`policy-check / scp/policy-check` required check) is enabled on your repo via the WP-SCP-024 cascade. Even when enabled, the gate is per-PR; SCP never writes to your repo.
- **Don't aggregate waiver content cross-repo.** Per WP-SCP-023 invariant 2 + plan-doc spec, `reason` / `approved_by` / `waiver_id` strings stay in the source repo's CODEOWNERS scope. Aggregator (`docs/scorecards/`) reports counts only.
- **Don't pre-empt operator review.** SCP-R-004 requires a URL in `reason`; the URL doesn't have to be public, just stable.

---

## Common questions adopters keep asking

These came up in inbound briefings (CT 2026-05-08, Recommender J1 RBAC, PIM auth-foundation, expected VS Phase N). Short answers + pointers.

### "Will SCP block my PR if I don't register a permission_schemas row?"

No. SCP doesn't have a rule for that. CT's per-app permissions schema is CT-internal; SCP doesn't validate registration. If a future SCP rule (WP-SCP-025 candidate `permission_schema_registered_within_wave_window`) materialises, it would be advisory-warn first, then required only after a deprecation ramp per `policies/VERSIONING.md` D-036.

### "Will SCP block my PR if I'm still on `mode.bearer_legacy`?"

Not until the deprecation close date passes. SCP-R-001 currently allows `mode.bearer_legacy` if the entry carries a valid `deprecation_close_date`. As of 2026-05-09, valid values are `{2026-06-30, 2026-09-30}` (the 2026-09-30 anchor lands when D-021 fires per `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`). After the close date, SCP-R-001 starts denying.

### "What's a valid waiver shape?"

Required fields per `schemas/waiver.schema.json`: `rule_id`, `expires_at` (ISO-8601), `reason` (string with ≥1 URL post-v1.1.0 SCP-R-004), `approved_by` (string), `scope` (object). Validation runs via SCP-R-002 (schema) + SCP-R-004 (reason-URL).

### "How do I know which SCP version I'm pinned at?"

Read your `policy-check-wrapper.yml` `uses:` line in your `.github/workflows/`. The SHA after `@` is the pin. Look it up at `https://github.com/jrnb2024/standards-control-plane/commits/<sha>` to identify the version.

### "What's the relationship between SCP rules and CT conformance checks?"

Orthogonal. SCP federation primitive enforces `policy-check / scp/policy-check` against `services.yml` + waivers + vendoring + (future) domain rules. CT's `ct-sdk-conformance` enforces SDK pin + version-bump cadence. Both can run on the same PR; they don't coordinate at runtime.

---

## How to file a waiver

If a SCP rule fires on your PR and the finding is intentional:

1. Open `output/findings/waivers.json` (or your repo's waivers payload location).
2. Add an entry:
   ```json
   {
     "rule_id": "SCP-R-001",
     "expires_at": "2026-12-31T23:59:59Z",
     "reason": "Migration to mode.user_oidc tracked at https://github.com/<your-repo>/issues/123. Bearer-legacy retained until ct-auth-go integration lands.",
     "approved_by": "<your-codeowner>",
     "scope": {"path": "services.yml", "section": "<service-name>"}
   }
   ```
3. Reference the issue/PR URL in `reason`. Both must be stable (don't link to ephemeral comments or chat).
4. Set `expires_at` to a realistic close date — auto-close shouldn't fire silently.

`policy-check / scp/policy-check` re-runs and the waiver suppresses the finding (visible in `scp/policy-check-readback` commit-status description).

---

## Where to ask for help

- Cross-repo notifications: `~/Projects/control-tower/governance/docs/notifications/` (the canonical estate channel per `reference_ct_notifications.md`).
- Issue tracker on `jrnb2024/standards-control-plane` (private; ask for access if you need to file).
- ADOPT-001 §12 (federation-primitive integration appendix) covers the cascade-onboarding contract; §12.7.15 covers scorecard-emit opt-in; §12.8 (lands at WP-SCP-024 024B-extras) covers break-glass.

---

## Cross-link

CT-side estate-auth coordination doc (covers CT decisions, not SCP rule applicability):
[TBD — CT to file at matching path; reference once published]

## Changelog

- **2026-05-09:** initial draft. Rule-applicability matrix; what SCP rules don't do; common questions; waiver-filing procedure.
