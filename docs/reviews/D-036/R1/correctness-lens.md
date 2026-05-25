# D-036 R1 — correctness lens

**Reviewed:** D-036 v1 (commit `274d801`) + RULE-003 v1 (commit `274d801`).
**Lens scope:** Internal consistency, references to existing artefacts, semantic correctness of the auth flow, Rego shape correctness, cross-document coherence between D-036 + RULE-003.

**Verdict:** CHANGES_REQUESTED.

---

## CRIT

None.

## MAJ

### CORR-MAJ-001 — `iss` claim shape under-specified relative to estate convention

D-036 Element 2 specifies `iss: https://control-tower.brokapps.ai`. Existing estate auth contracts (per `services.yml` `accepted_modes` blocks) declare `jwks_url: https://control-tower.brokapps.ai/api/v1/.well-known/jwks.json`. OAuth/JWT convention treats `iss` as a URI that the JWKS discovery doc is published under, NOT just a bare hostname. CT's actual issuance shape (per `mode.service_rs256`) needs verification — `iss` may be `https://control-tower.brokapps.ai` OR `https://control-tower.brokapps.ai/api/v1` OR full discovery URL. D-036 must match CT's canonical issuance shape or risk verifier mismatch at runtime.

**Disposition:** Fix in v2 — verify against CT's actual `services.yml` issuance side OR mark as "subject to WP-AUTH-007 final shape" and forward-track.

### CORR-MAJ-002 — RULE-003 Inv-C fails-OPEN on missing manifest entry

RULE-003 §3.4 Rego sketch for Inv-C:

```rego
expected := manifest_lookup(input.signed_manifest, input.target_repo_app_id)
expected.mcp_server_sha256 != input.mcp_server_sha256
```

If `manifest_lookup` returns undefined (entry missing for this `target_repo_app_id` — new adopter, manifest publication lag, manifest corruption), the `!=` expression evaluates to undefined and the rule body fails silently. This is **fail-OPEN**: an MCP server present on disk with NO corresponding manifest entry passes the rule. For `acc-cross-repo-caller-scoped: true` adopters with an MCP server in the tree, missing manifest entry MUST fire a finding (fail-CLOSED).

**Disposition:** Fix in v2 — add explicit `scp_r_006_inv_c_missing_entry_finding` partial rule that fires when `mcp_server_path` is non-empty AND `manifest_lookup` returns undefined.

### CORR-MAJ-003 — Rego iteration over `services.yml.services` uses wrong shape

RULE-003 §3.4 Rego: `some service in input.services_yml.services`. The existing `services.yml` shape (per `/Users/amplience/Projects/scp-d-036/services.yml`) is:

```yaml
services:
  scp:
    healthcheck: /health
    local: ...
```

`services` is a YAML mapping (dict), not a list. Rego iteration over a dict yields values when written `some _, service in input.services_yml.services`. The current `some service in input.services_yml.services` works in Rego v1 for both lists and dicts (yields values), but is shape-ambiguous and may break under stricter Rego linting. **More importantly**, the rule's Inv-B logic intends to iterate one-service-per-services_yml-entry; for a multi-service services.yml the current shape iterates correctly but the rule body silently produces N findings per violating entry instead of one.

**Disposition:** Fix in v2 — use explicit dict iteration `some service_name, service in input.services_yml.services` and confirm semantics.

## MIN

### CORR-MIN-001 — `CT_AUTH_TOKEN` env propagation contradicts in-band JWT presentation

D-036 Element 4 lists `CT_AUTH_TOKEN` as MUST-propagate to subprocess. But per the JSON-RPC transport for MCP servers (per EST-P §3.3.1 subprocess transport with stdio JSON-RPC), the JWT is presented as an Authorization header on each RPC call, NOT as a subprocess env var. Propagating the JWT in env is a smell because: (a) env vars persist for subprocess lifetime; (b) subprocess of subprocess inherits; (c) ps/proc/sys inspection on adversary-controlled host reveals the token. The env should carry `CT_JWKS_URL` + `SERVICE_AUTH_SECRET` (for verifier setup), NOT the token itself.

**Disposition:** Fix in v2 — remove `CT_AUTH_TOKEN` from Element 4 allowlist; document JWT presentation is per-call header on JSON-RPC.

### CORR-MIN-002 — pipe-delimited HMAC payload allows future ambiguity

D-036 Element 5 HMAC payload: `"{sender_acc_sa_uuid}|{jwt_jti}|{target_repo_app_id}|{ts_unix_seconds}"`. Each field's current regex precludes `|`, so safe today. But if a future field is added (e.g., `{action_scope}` where action_scope is free-form), pipe collision becomes a vulnerability. Length-prefixed or canonical-JSON-serialised payload is more robust.

**Disposition:** Fix in v2 — switch to canonical JSON serialisation (`{"sa": ..., "jti": ..., "aud": ..., "ts": ...}` with deterministic key ordering). Cite RFC 8785 JCS for canonicalisation.

### CORR-MIN-003 — Rego set-union syntax `|` ambiguity

RULE-003 §3.4: `some finding in (scp_r_006_inv_a_finding | scp_r_006_inv_b_findings | ...)`. Rego v1 supports `|` for set union but interprets it as bitwise-or in some contexts; the safer canonical form is to define a single aggregator rule.

**Disposition:** Fix in v2 — refactor to single `scp_r_006_all_findings` partial rule.

## nit

### CORR-NIT-001 — D-036 v1.4.0 floor matches RULE-003 v1.4.0 target

Consistency check passes; no fix.

### CORR-NIT-002 — Cross-references all verified to exist

Verified files: PLAN-EST-P-cross-repo-orchestration-v3.md exists; D-049 + D-050 exist; ADR-024 is correctly noted as forward-reference.
