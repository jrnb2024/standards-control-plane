# D-036 — ACC-as-cross-repo-caller SCP rule-RFC (EST-P enablement)

**Status:** DRAFT (operator-review surface; not signed)
**Date filed:** 2026-05-24
**Decision date:** TBD (operator signature on merge)
**Operator:** @jrnb2024
**Closes:** ESTATE-CONVERGENCE-CHECKPOINTS §43 "DO NOT add a new auth mode to services.yml without going through D-036 SCP rule-RFC" — the long-pending vehicle for any new auth pattern in `services.yml`. This is the first invocation of that vehicle; named auth pattern: **ACC orchestrator as service-to-service caller to target estate repos via per-repo MCP server subprocesses.**
**Companion rule-RFC:** `docs/reviews/rule-proposals/RULE-003-acc-cross-repo-caller.md` (proposes `SCP-R-006` at `warn` baseline; promotes per-adopter via `threshold-overrides` per RULE-002 §3.2 pattern).

---

## Context

ACC (Agent Control Centre, `/Users/amplience/Projects/acc`) is the estate's deterministic orchestration platform for AI-native software development. Its 16-week EST-P programme (Estate-wide Cross-Repo Orchestration; plan-doc at `acc/docs/plans/PLAN-EST-P-cross-repo-orchestration-v3.md`) introduces a structurally new auth pattern: ACC dispatches WorkPackages to target estate repos (mapp-returns-intelligence, mapp-pim, recommender, control-tower, mapp-size-allocation, mapp-doc-agent, mapp-visual-shopping, fashion-labelling-agent, shopify-app) by spawning per-repo MCP server subprocesses with constrained tool surfaces. Each MCP server invocation requires ACC to present a service-to-service JWT scoped to that target repo's app_id.

Today no estate `services.yml` declares a peer service as an `allowed_caller`. Existing auth contracts (per `schemas/auth-contract.schema.json`) only enumerate the auth *modes* a service accepts (`mode.user_oidc`, `mode.service_rs256`, `mode.api_key`, `mode.bearer_legacy`) — they do not name *which peer services* may present those credentials. The estate's current model is "any holder of a valid token of an accepted mode may call"; ACC's cross-repo dispatch substrate requires "this specific peer service (ACC) is authorised to call, others are not."

Per ESTATE-CONVERGENCE-CHECKPOINTS §43, any new auth mode or auth-pattern extension on `services.yml` must go through the D-036 SCP rule-RFC vehicle. This decision is the first ratification of that vehicle.

The EST-P plan-doc converged at R-fixpoint MET (operator-ratified via ASC-2026-05-24-001 + ASC-2026-05-24-002 + ASC-EST-P-002). Plan-doc §3.5 + §15 SB-R2-003/007/008 + §14 ADR-024 skeleton specify the exact auth-pattern shape this decision ratifies SCP-side.

This decision is the SCP-side counterpart to ACC's `ADR-024-cross-repo-trust-boundary.md` (to be authored by ACC EST-P WS-EST-P-3.0). ACC ratifies the orchestrator-side trust boundary; SCP ratifies the policy-layer enforcement of the same pattern at the federation gate.

## Decision

SCP adopts a **five-element rule-RFC vehicle** for the ACC-as-cross-repo-caller auth pattern, ratifying SCP-R-006 (proposed by companion RULE-003) and the supporting schema + threat-model + custody discipline. Each element below is load-bearing on either the auth invariant or the SCP policy-layer's enforcement of it.

### Element 1 — `services.yml` `allowed_callers` schema extension

A new key `allowed_callers: [<service_id>, ...]` is added to the `runtime_contract` block at the same nesting level as `auth_contract`. The key is OPTIONAL (default = absent = no peer-service restriction beyond auth mode). When present and non-empty, it restricts which peer services may present credentials to this service: only services whose `sub` claim (after token verification per the declared `accepted_modes`) matches an entry in `allowed_callers` are authorised.

Schema extension lands in `schemas/runtime-contract.schema.json` (or sibling). The `<service_id>` value is a bare app-id matching the same pattern as `accepted_modes[].audience` — `^[a-z][a-z0-9-]*$`. Entries reference services that themselves carry a `services.yml` declaration in their own repo; cross-repo service registry lives at `control-tower/config/estate_repos.yaml` (per EST-P plan-doc §15 SB-R1-023). The first registered cross-repo caller is `acc`.

Example (post-EST-P, for mapp-returns-intelligence):

```yaml
services:
  mapp-returns-intelligence:
    healthcheck: /health
    local:
      status: ready
      runtime_contract:
        # ... existing fields ...
        auth_contract:
          accepted_modes:
            - mode: mode.service_rs256
              audience: mapp-returns-intelligence
              jwks_url: https://control-tower.brokapps.ai/api/v1/.well-known/jwks.json
        allowed_callers:
          - acc
```

The shape is **additive**: existing `services.yml` files with no `allowed_callers` key continue to operate unchanged. Adopters opt into peer-service authorisation by adding the key. SCP-R-006 (companion RULE-003) fires when an MCP server invocation is logged whose presented `sub` is not in the target service's `allowed_callers` list, when the rule applies (per RULE-003 §3.1 match conditions).

**Implementation contract on ct-auth (per SB-MAJ-004 R1 fix).** The runtime enforcement of `allowed_callers` is a NEW verification step that does not exist in the current `ct-auth` Python / TS / Go libraries. D-036 commits the estate to extending all three language variants to consume the target service's `allowed_callers` declaration at token-verify time:

1. On token presentation, ct-auth performs the standard `iss`/`aud`/`exp`/`sub`/signature verification per existing `mode.service_rs256` shape.
2. If standard verification passes AND the target service's `services.yml` declares a non-empty `allowed_callers` list, ct-auth additionally verifies the token's `sub` claim (canonicalised — lowercase, trimmed) is in the declared list. Verification failure → reject (HTTP 401 + audit log entry).
3. If `allowed_callers` is absent OR empty, the standard behaviour applies (any valid token of an accepted mode is authorised) — preserves backward-compatibility for non-EST-P services.
4. ct-auth additionally maintains the `jti` cache per the replay-defence subsection above.
5. ct-auth additionally vendors an RFC 8785 JCS (canonical-JSON) library per the canonical-JSON requirement on the `ACC_COSIGNAL_TOKEN` payload (Element 5). Per-language JCS dep is pinned + tracked under TF-D036-014. Reference implementations: Python `jcs` (PyPI) or `canonicaljson`; TS `canonicalize` (npm); Go `gowebpki/jcs`.

The ct-auth extension is a HARD-DEP on CT WP-AUTH-007 (or a sibling WP). The dispatch shape: a new minor-version of ct-auth-py / ct-auth-ts / ct-auth-go ships the `allowed_callers` + `jti`-cache features additively; estate adopters pick up via the existing Renovate cascade. ct-auth versions without the feature behave per the backward-compatible default (point 3 above) — they accept any valid token, which means SCP-R-006's runtime enforcement is gated on the ct-auth version cascade. Per-adopter `acc-cross-repo-caller-scoped: true` opt-in (per RULE-003 §3.1) MUST verify the adopter's ct-auth version supports `allowed_callers`; the install ceremony (`install_per_repo_mcp_server.sh`) checks the vendored ct-auth version + refuses install on too-old versions.

### Element 2 — JWT shape spec for the ACC-as-caller pair

The token ACC presents to a target repo's per-repo MCP server is constrained as follows. This is the canonical shape; deviations require either an amendment to D-036 (via new sibling RFC) or an explicit per-target ASC.

| Claim | Value | Rationale |
|---|---|---|
| `alg` | `RS256` | Estate-standard; matches existing `mode.service_rs256` accepted-mode. |
| `iss` | `https://control-tower.brokapps.ai` (subject to WP-AUTH-007 final-issuer-URI shape — per CORR-MAJ-001 R1 fix) | CT is the canonical token issuer per `mode.service_rs256` discovery; matches `auth-contract.schema.json` `jwks_url` host. WP-AUTH-007's eventual canonical issuer URI is what target-repo `ct-auth` verifiers actually check at receipt; D-036 v2 commits to *whatever WP-AUTH-007 ships* as the canonical form. If WP-AUTH-007 lands with a different shape (e.g., `https://control-tower.brokapps.ai/api/v1` or full discovery-doc URI), D-036 inherits without amendment per TF-D036-011 (filed below). |
| `aud` | Target repo's `app_id` (e.g. `mapp-returns-intelligence`, `mapp-pim`, `recommender`) | Audience binding to the specific target repo; prevents token replay across estate repos. Per EST-P plan-doc §3.5 SB-R1-007 fix. |
| `sub` | ACC service account UUID (canonical form, lowercase, no surrounding whitespace) | Identifies the caller for `allowed_callers` matching + audit trail. ACC's SA UUID is registered in CT's identity store; one stable UUID across all dispatches. |
| `exp` | `iat + min(6h, expected_dispatch_duration + 15min)` | Dynamic TTL per EST-P plan-doc §3.5 SB-R1-012 fix. Hard ceiling 6h per `ASC-2026-05-17-002` (Phase 1A GATE-1a R3 max-TTL). Floor of `expected_dispatch + 15min` to give the target enough time to complete the dispatch without re-presenting a token mid-flight. |
| `iat` | UTC seconds at token issuance | Standard. |
| `jti` | UUID v4 per token | Required for forensic correlation; per EST-P plan-doc §3.8 SB-R1-013 the per-repo MCP server records `{ts, sender_acc_sa_uuid, jwt_jti, ...}` BEFORE invoking any tool, so `jti` is the canonical join key. |

Tokens with `aud` that does not match the target service's `app_id` are rejected by the target's `ct-auth` verifier (Python or TS variant per the target repo's stack). Tokens with `exp` > `iat + 6h` are rejected at issuance time by CT's token endpoint (this is enforced upstream; the per-target verifier additionally enforces it on receipt as defence-in-depth).

The exchange mechanism by which ACC obtains the token is OPTION A per EST-P plan-doc §3.5 R-EST-P-12 (CT WP-AUTH-007 client_credentials grant). Fallback to Option B (out-of-band rotating SA token) requires explicit operator ASC. The exchange mechanism is OUT OF SCOPE for D-036 — D-036 ratifies the *shape* the token must hold, not the *mechanism* by which ACC obtains it.

**Replay defence (per SB-MAJ-001 R1 fix).** The target-repo `ct-auth` verifier maintains an in-memory `jti` cache for the duration of each token's TTL. On token presentation, the verifier checks `jti` against the cache; cache hit → reject as replay (HTTP 401 + audit log). Cache eviction on `exp` reached. Cache size bounded at 100,000 entries per target with LRU eviction (well above expected dispatch volume for any single target over a 6h window). The `jti`-cache requirement is part of the "Implementation contract on ct-auth" called out in Element 1 below.

### Element 3 — Per-repo MCP server signed-manifest requirement

**Signing-key custody (per SB-MAJ-002 R1 fix).** The Ed25519 manifest signing key inherits D-031 single-operator-mode bus-factor-1 custody — held exclusively by `@jrnb2024`, symmetric with the Cosignal HMAC key (Element 5) and the D-050 GitHub App private key. This is the load-bearing acknowledged residual: a single-machine compromise of `@jrnb2024`'s host collapses the entire trust chain (CT manifest signing + ACC cosignal HMAC + per-target ct-auth credentials). The mitigation set mirrors D-050 §4:

- **Rotation SOP** at `control-tower/docs/security/manifest-signing-key-custody.md` (NEW; authored as TF-D036-010 below; operationally analogous to D-050's `app-key-rotation-sop.md`).
- **2026-07-21 quarterly D-031 review** extension — manifest signing-key custody added to the bus-factor-1 review agenda (TF-D036-001 below already tracks the cosignal HMAC key under the same review; this is a sibling addition).
- **Manifest signing keys can be rolled JWKS-style** — the manifest schema's `signing_key_id` field permits multiple live key-ids concurrently; rotation is a `signing_key_id` bump + grace window for in-flight verification.
- **Recovery on compromise** — generate new Ed25519 keypair; resign the manifest; publish; revoke old `signing_key_id` from the workflow's allowlist. Bounded blast radius; <1 hour operator-attended ceremony.



Before ACC spawns a per-repo MCP server subprocess at `<target_repo>/.acc/mcp_server.{py,ts}`, ACC's `CrossRepoDispatcher` (per EST-P plan-doc §4.5 WS-EST-P-4.3) MUST verify the MCP server source SHA against a signed manifest pinned in WP-CT-E-108 (per the EST-P plan-doc cross-reference). This closes the AC-EST-P-MCP-009 acceptance criterion: a tampered MCP server cannot be spawned regardless of file-system permissions on the target repo's checkout.

The signed manifest is structured as:

```json
{
  "schema_version": "d-036-mcp-manifest-v1",
  "manifest_ts_utc": "2026-MM-DDTHH:MM:SSZ",
  "signing_key_id": "ct-mcp-manifest-key-1",
  "signing_alg": "ed25519",
  "entries": [
    {
      "target_repo_app_id": "mapp-returns-intelligence",
      "mcp_server_path": ".acc/mcp_server.py",
      "mcp_server_sha256": "<64-hex>",
      "language": "python",
      "tool_surface_version": "1.0.0"
    }
  ],
  "signature_b64": "<base64-ed25519-signature-over-canonical-json-of-entries>"
}
```

The manifest is published from CT (single source of truth) and consumed by both ACC (verifies before spawn) and SCP (verifies as part of SCP-R-006 evaluation when the target repo's `services.yml` is processed). Manifest rotation cadence: per-MCP-server source change (the manifest is a build artefact of any MCP server change PR; merging an MCP server change merges a new manifest in the same PR or in a tightly-coupled follow-up PR).

TOCTOU defence per EST-P plan-doc §4.4 WS-EST-P-3.4: ACC opens the MCP server file with `O_NOFOLLOW` + fd-bound `read`, computes SHA over the read bytes, and verifies the SHA against the manifest entry. Then ACC spawns the subprocess from the same fd (where the OS supports `fexecve`) or re-opens with `O_NOFOLLOW` + SHA-re-verify (where it does not). On any SHA mismatch, ACC refuses to spawn + emits `CrossRepoDispatchRefused(reason="mcp_manifest_sha_mismatch")`.

**Schema-version evolution discipline (per CG-MAJ-003 R1 fix).** The workflow consumer (SCP federation-primitive's `policy-check.yml` + SCP-R-006 Rego evaluator) accepts the manifest if `schema_version` matches a known version in its compiled-in version-allowlist. The version-allowlist is bumped via standard SCP federation-primitive PR (same SHA-pin cascade discipline as the rest of the federation-primitive surface). New versions are additive (added to the allowlist alongside older versions, JWKS-style rollover); old versions are removed only when the cohort cascade has migrated. The schema-version-allowlist evolution mirrors `policies/VERSIONING.md` semver discipline: PATCH manifest-schema bump = additive field, all consumers accept; MINOR = new required field with default, requires consumer version bump; MAJOR = breaking change, requires version-allowlist coexistence window before old-version removal.

### Element 4 — Env-propagation contract for cosignal preservation

When ACC's `CrossRepoDispatcher` spawns the per-repo MCP server subprocess, the following env vars MUST propagate from the dispatcher's environment to the subprocess (per EST-P plan-doc §3.5 SB-R1-004 fix + AC-EST-P-AUTH-005):

| Env var | Purpose | Strip → fail-closed? |
|---|---|---|
| `CLAUDECODE` | Cosignal Layer 1 marker — distinguishes Claude Code session from arbitrary CI invocation. | YES — stripping defeats the cosignal trap. |
| `CLAUDE_CODE_ENTRYPOINT` | Cosignal Layer 2 marker (per ACC's `feedback_cosignal_layer_2_claudecode_env_propagation.md`). | YES. |
| `ACC_COSIGNAL_TOKEN` | NEW per SB-R2-003 (see Element 5) — HMAC cosignal token; target-repo's acc-hook verifies before allowing any tool call. | YES — stripping causes target-repo acc-hook to deny all tool calls (fail-closed). |
| `CT_JWKS_URL` | JWKS URL for the verifier. | YES — without it, verifier cannot fetch signing keys (fail-closed if cache cold). |
| `SERVICE_AUTH_SECRET` | Per-target HMAC secret for additional verification layers. | YES. |
| `PATH`, `HOME`, `PYTHONPATH`, `LANG`, `SSL_CERT_FILE` | Standard runtime needs. | YES — stripping causes import-bypass / unicode-error / TLS-MITM (per EST-P §3.5 v4 expansion). |

All other env vars are STRIPPED by `CrossRepoDispatcher`'s hardcoded allowlist (per EST-P plan-doc CRIT-SB-002 fix). The allowlist is the closed set above; expansion requires per-WP plan-stage 3-lens R1 review per `feedback_orchestrator_auth_surface_plan_review_default.md`.

**JWT presentation is in-band, NOT via env (per CORR-MIN-001 R1 fix).** The ACC-as-caller JWT (per Element 2) is presented as an `Authorization: Bearer <token>` header on each JSON-RPC call into the per-repo MCP server, NOT via a subprocess env var. Propagating the JWT in env would: (a) persist it for subprocess lifetime; (b) leak it to grandchild subprocesses via env inheritance; (c) expose it via `ps`/`/proc/<pid>/environ` inspection on adversary-controlled hosts. The subprocess env carries `CT_JWKS_URL` + `SERVICE_AUTH_SECRET` (verifier configuration), but the token itself rides per-call.

**Pre-copy sanitisation (per SB-MAJ-005 R1 fix).** ACC's `CrossRepoDispatcher` does NOT trust its own parent process's env values verbatim. For each env var in the allowlist, the dispatcher validates the value against a known-shape regex BEFORE copying into the subprocess environment:

| Env var | Validation shape |
|---|---|
| `PATH` | colon-separated list of existing absolute-path directories |
| `HOME` | single existing absolute-path directory |
| `PYTHONPATH` | colon-separated list of existing absolute-path directories OR empty |
| `SSL_CERT_FILE` | existing absolute-path file in a known CA bundle directory (`/etc/ssl/certs/`, `/etc/pki/`, `<HOMEBREW_PREFIX>/etc/openssl@<v>/cert.pem`) |
| `LANG` | matches `^[a-z]{2,3}(_[A-Z]{2})?(\.UTF-8)?$` |
| `CLAUDECODE` | exactly `"1"` (rejected otherwise — the cosignal marker is binary) |
| `CLAUDE_CODE_ENTRYPOINT` | matches Claude Code's canonical entrypoint enum (`cli`, `vscode`, etc.) |
| `ACC_COSIGNAL_TOKEN` | matches base64-URL-encoded HMAC-SHA256 output (≈43 chars) |
| `CT_JWKS_URL` | matches `^https://control-tower\.brokapps\.ai/.*\.well-known/jwks\.json$` |
| `SERVICE_AUTH_SECRET` | matches base64-encoded 32-byte length |

Validation failure → `CrossRepoDispatcher` refuses spawn + emits `CrossRepoDispatchRefused(reason="env_var_validation_failed", var=<name>)`. This catches: tainted parent shell, env-file injection, attacker-controlled `SSL_CERT_FILE` MITM, malformed cosignal token (defence-in-depth even when ACC mints the token itself in-process).

The contract is **fail-closed** on the target-repo side: if any of the load-bearing env vars are missing from the subprocess environment, the target-repo's `.acc/mcp_server` validates this on startup and exits 4 (per ACC's existing `_hook_integrity_gate` pattern). The target-repo's acc-hook (installed per EST-P plan-doc §4.7 WS-EST-P-6 cohort cascade) additionally validates `ACC_COSIGNAL_TOKEN` on every tool call before allowing it.

### Element 5 — NEW HMAC-key shared-secret scope (`ACC_COSIGNAL_HMAC_KEY`)

Per EST-P plan-doc §15 SB-R2-003 fix, the cross-subprocess cosignal extension requires an HMAC-signed token (`ACC_COSIGNAL_TOKEN` in Element 4) that the target-repo's acc-hook can independently verify without trusting the subprocess env arbitrarily.

The HMAC key (`ACC_COSIGNAL_HMAC_KEY`) is a 32-byte secret with the following storage + rotation discipline:

| Property | Value | Rationale |
|---|---|---|
| Length | 32 bytes (256 bits) | Standard HMAC-SHA256 key length; matches ACC's existing `.acc/credentials/dispatch-key` shape. |
| Algorithm | HMAC-SHA256 | Estate-standard; matches existing dispatch-log HMAC + hook-audit-log HMAC discipline. |
| Storage (ACC side) | `<acc>/.acc/credentials/cosignal-hmac-key` owned `root:wheel 0400` (kernel-protected; equivalent to existing dispatch-key custody) | Bus-factor-1 single-operator posture per D-031; same threat model as existing ACC HMAC keys. |
| Storage (target-repo side) | `<target>/.acc/credentials/cosignal-hmac-key` owned `root:wheel 0400` | Distributed via `install_per_repo_mcp_server.sh` (per EST-P plan-doc §4.3 WS-EST-P-2.3) — operator-attended per-target install ceremony. Identical bytes across all 9 estate repos (it's a SHARED secret). |
| Rotation cadence | Weekly (every Monday 00:00 UTC; calendar-driven, NOT event-driven) | Bounds the compromise window of any single key. Operator-attended ceremony — script lives at `<acc>/scripts/rotate-cosignal-hmac-key.sh` (operator-attended; rebuilds key file on ACC + cascade-distributes to all 9 estate repos in a single operator session). |
| Event-triggered rotation | Suspected compromise; operator account access change; D-031 quarterly review (2026-07-21 + subsequent) | Standard operational discipline; mirrors `docs/security/app-key-rotation-sop.md` SOP from D-050. |
| Key custody | Bus-factor-1 (`@jrnb2024`) per D-031 | Inherits D-031's escalation review; 2026-07-21 quarterly D-031 review will add cosignal-HMAC-key custody to the agenda (TF-D036-001). |
| Recovery on compromise | Generate new 32 bytes; redistribute to all 9 repos in a single ceremony; in-flight dispatches with old key fail verification at the target (visible failure, not silent compromise) | Bounded blast radius; <1 hour operator-attended recovery. |

The `ACC_COSIGNAL_TOKEN` env var carried in the subprocess environment is computed as (per CORR-MIN-002 R1 fix — canonical-JSON-serialised payload, RFC 8785 JCS, avoids pipe-delimiter ambiguity if future fields are added):

```
payload_json = jcs.canonicalize({
    "sa": "<sender_acc_sa_uuid>",   // ACC SA UUID, canonical lowercase
    "jti": "<jwt_jti>",              // UUID v4 from JWT
    "aud": "<target_repo_app_id>",   // target service id
    "ts": <ts_unix_seconds>           // integer unix seconds
})
ACC_COSIGNAL_TOKEN = base64url(HMAC-SHA256(ACC_COSIGNAL_HMAC_KEY, payload_json))
```

The target-repo's acc-hook recomputes the HMAC on receipt (it has the same key bytes), compares constant-time, and only allows the tool call to proceed if the HMAC matches AND `ts_unix_seconds` is within ±15 minutes of the hook's wall clock (replay defence within the NTP-skew tolerance window). The ±15min window is operator-decision (per SB-MIN-001 R1 disposition) — acceptable today given the 6h JWT TTL ceiling dominates the worst-case replay window, and `jti` cache (per Element 2 replay defence subsection) tightens the in-window replay surface to "until first use observed". TF-D036-012 tracks tightening to ±2min once `jti` cache is empirically observed deployed.

If `ACC_COSIGNAL_HMAC_KEY` is missing from the target-repo's `<target>/.acc/credentials/` (e.g., the install ceremony was incomplete OR the key file was deleted), the target-repo's acc-hook exits 4 + writes a JSONL forensic entry to `<target>/.acc/hook-audit-log/integrity-gate-failures-YYYY-MM-DD.jsonl` (same shape as ACC's existing integrity-gate-failure log) BEFORE denying the tool call. This is the load-bearing failure-closed path for Element 5.

**Threat-model acknowledgement: shared-key lateral-movement risk (per SB-CRIT-001 R1 fix).** The HMAC key being SHARED across all 9 estate repos creates a **lateral-movement attack surface**: a single-repo root-compromise (attacker reads `<target>/.acc/credentials/cosignal-hmac-key`) grants the ability to mint valid `ACC_COSIGNAL_TOKEN` values for ANY other estate repo. Combined with the propagated `SERVICE_AUTH_SECRET` (also estate-shared), single-repo compromise = full estate ACC-impersonation capability. The blast radius is:

| Compromise scenario | Blast radius | Recovery cost |
|---|---|---|
| Single-repo root compromise + key read | Estate-wide ACC-impersonation until rotation | Single weekly-rotation ceremony (≤7 days max exposure) + key rotation across 9 repos in <1h |
| `@jrnb2024` host compromise (full operator machine) | Estate-wide ACC impersonation + CT manifest signing + per-target ct-auth — D-031 single-operator-mode bus-factor-1 collapse | Out of scope for D-036; covered by D-031 escalation review |
| Weekly-rotation ceremony failure (rotation skipped) | Extends exposure window beyond 7 days | Operator-attended ceremony catches at next rotation |

This is the **load-bearing acknowledged residual** for D-036 Element 5. Per-target HKDF-derived ephemeral subkeys (master key kernel-protected on ACC side; per-target subkeys derived per-dispatch with HKDF-SHA256 + per-target context) is the strictly-better security posture but requires per-language HKDF implementation in the ct-auth verifiers, which is out-of-scope for v1.4.0 ship. Captured as TF-D036-008 (per-target HKDF-derived subkeys) for v1.5.0+ evaluation. Operator-authorisation acceptance under D-031 single-operator-mode bus-factor-1 is symmetric with D-050's GitHub App private key custody acceptance + Element 5's HMAC key custody acceptance + Element 3's manifest signing-key custody acceptance — the entire trust chain inherits the same bus-factor-1 posture that D-031 establishes as the estate's accepted v1.0.0 default.

### What this decision explicitly does NOT adopt

These items are deliberately OUT OF SCOPE for D-036; each is forward-tracked as a numbered FUP. The FUPs are operator-decision (or per-trigger) future work; they do NOT block D-036 acceptance, do NOT block EST-P WS-EST-P-2 shipping, and do NOT pre-commit SCP to a position on them.

| Out of scope | FUP | Trigger to reopen |
|---|---|---|
| v2 write-tool surface on per-repo MCP servers (current EST-P scope is read tools + 1 side-effecting tool per MCP server) | FUP-EST-P-008 | First write-tool requirement from a cohort adopter post-WS-EST-P-6 |
| Daemonised long-running MCP server (current EST-P scope is spawn-per-request lifecycle per ADR-025) | FUP-EST-P-001 | Performance evidence from WS-EST-P-5 KGRE wiring showing spawn cost is materially blocking |
| Remote-host orchestration (current EST-P scope is local subprocess; spawn-on-Mac-Studio only) | FUP-EST-P-002 | Operator decision to extend beyond local dev fabric |
| Multi-org adopter ACC SA UUID (current EST-P scope is single ACC SA across all 9 repos in `@jrnb2024` namespace) | FUP-D036-002 | First non-`@jrnb2024` adopter joins the estate |
| Mutual-TLS layer on top of HMAC cosignal (current EST-P scope is HMAC-only) | FUP-D036-003 | If subprocess env-strip attack vector materialises in production despite Element 4's enumerated allowlist |

The two hills the orchestrating-skeptic perspective on this decision will not cede: (a) SCP does not become the JWT issuer (CT remains the canonical issuer per `mode.service_rs256`; D-036 ratifies the *shape* the token holds for the new caller-pair, not a new issuance path); (b) SCP does not load the target-repo's MCP server source to verify it itself (the signed manifest in Element 3 is consumed by ACC at spawn-time; SCP's policy-check evaluates the *declared* shape in `services.yml` + the *audit trail* the manifest pin produces, never the live binary). Both invariants preserve the federation primitive's "OPA Rego against checked-out tree" semantic per D-049 §Justification property 1.

## Rationale

The five-element shape adopted here emerged from EST-P plan-doc R3 + R-fixpoint MET (operator-ratified 2026-05-24 via ASC-2026-05-24-001/002 + ASC-EST-P-002). The plan-doc carried 60 ACs across 6 workstreams; AC-EST-P-AUTH-006 explicitly names "D-036 SCP rule-RFC filed BEFORE WS-EST-P-2 ships" as a hard precondition (per EST-P §3.5 SB-R1-008 fix). This decision satisfies AC-EST-P-AUTH-006.

Four perspectives shaped each element of the decision; each perspective held a load-bearing concern that the final shape addresses:

- **Auth-surface skeptic.** Argued that ACC-as-caller is a *new auth pattern* not just a new auth *audience*, and that the existing `services.yml` `accepted_modes` shape does not adequately constrain *which peer services* may call. Element 1's `allowed_callers` schema extension closes this concern: the new shape names the caller explicitly + restricts to that caller. The skeptic also argued for fail-closed env-strip defence; Element 4's hardcoded allowlist + fail-closed target-repo validation answers this.

- **Cosignal-trap architect.** Argued that the existing 3-layer cosignal trap (Layers 1+2 deployed; Layer 3 WP-1 shipped 2026-05-23 PR #269) does NOT extend across subprocess boundaries — env vars propagate, but the parent-process inspection (Layer 3) walks the subprocess's ancestor PID chain which terminates at ACC's `CrossRepoDispatcher`, NOT at the original Claude Code harness. Element 5 introduces the HMAC-signed `ACC_COSIGNAL_TOKEN` as a cross-subprocess cosignal extension: ACC mints (using a key only the parent Claude Code session has access to), target-repo verifies. This is the architectural answer the EST-P plan-doc §15 SB-R2-003 fix bakes in.

- **Estate-cascade pragmatist.** Argued that any new estate-wide auth pattern lands first at SCP-side WARN baseline, ramps per-adopter, and never opens a SCP-side deny gate before TF-PIM-001 (cross-repo `actions/checkout` auth) closes. Companion RULE-003 §3.2 honours this: SCP-R-006 ships at warn baseline at v1.4.0 (the first SCP release after RULE-002/SCP-R-005's v1.3.0 cut); per-adopter promotion to deny via `threshold-overrides` per the RULE-002 §3.2 pattern. No estate-wide deny ramp; per-adopter ramp only.

- **TF-PIM-001 risk-asymmetry continuator.** Argued that any new ACC↔target-repo auth pattern must preserve the bounded-reversal posture D-050 established for cross-repo `actions/checkout`. Element 3's signed-manifest requirement + Element 5's HMAC-key rotation SOP both have bounded reversal cost: any compromise scenario is recoverable within <1 hour operator-attended ceremony, the same bound D-050 ratified for the GitHub App credential surface.

The decision deliberately defers the harder operational questions — when (if ever) SCP-R-006 promotes from per-adopter to estate-wide deny; whether the HMAC-key custody distribution evolves beyond bus-factor-1 single-operator; whether v2 write-tool surface materialises — to the FUPs enumerated above. The decision commits to the *shape* of the SCP policy-layer's role in the ACC-as-cross-repo-caller auth pattern; the operational ramps are deferred to the WS-EST-P-6 cohort cascade clock + the post-WS-EST-P-6 operational evidence.

## Justification

Five load-bearing properties hold under this decision:

1. **The federation primitive's static-Rego invariant is preserved.** SCP-R-006 (companion RULE-003) evaluates the *declared shape* in `services.yml` (does `allowed_callers` name `acc`?) + the *audit trail* of MCP server spawns (does the `jwt_jti` in the audit log correspond to an `aud` matching this service's `app_id`?). It does not load the live MCP server binary, does not parse the live subprocess environment, does not invoke ACC's `CrossRepoDispatcher` in-flight. Every check is static against a checked-out tree + pre-existing audit log. This preserves the same invariant D-049 Element 1 protects.

2. **The JWT shape is constrained at the issuance layer, not just the consumer layer.** CT's token endpoint (per Element 2) enforces the max-TTL ceiling at issuance time; the target-repo verifier additionally enforces it at receipt as defence-in-depth. This double-enforcement matches the `ASC-2026-05-17-002` enforced-fail-closed pattern and prevents drift if a future CT change forgets the consumer-side check.

3. **The HMAC cosignal layer is composable with the existing 3-layer cosignal trap.** Layer 5 (HMAC) does not replace Layers 1-3; it extends them across subprocess boundaries. The target-repo's acc-hook validates Layers 1+2+3 (existing) on every tool call AND Layer 5 (NEW) when the call originates from an ACC-mediated subprocess (detected via `ACC_COSIGNAL_TOKEN` being present). Layer 5 absent → behave as today (Layers 1+2+3 only — same as a Claude Code session running locally without ACC mediation). Layer 5 present → ALSO validate Layer 5. Additive defence, not replacement.

4. **The reversal mechanism is bounded for every element.** Element 1 (schema extension) — adopters can revert by removing the `allowed_callers` key (additive feature; absence = pre-D-036 behaviour). Element 2 (JWT shape) — TTL ceiling is forward-only-tightening; can always be loosened back to the existing `mode.service_rs256` shape. Element 3 (signed manifest) — manifest deletion + manifest-verify code-path bypass via env var is operator-recoverable in <1 hour. Element 4 (env-propagation contract) — allowlist is hardcoded in `CrossRepoDispatcher`; revert is single-PR. Element 5 (HMAC key) — key compromise recoverable via rotation ceremony (Element 5 row "Recovery on compromise") in <1 hour.

5. **The cohort-onboarding ceremony is documented + replicable.** Each of the 9 target repos receives the same install ceremony: (a) `install_per_repo_mcp_server.sh` provisions `<target>/.acc/credentials/cosignal-hmac-key` + `<target>/.acc/mcp_server.{py,ts}` + verifies the MCP server source SHA against the signed manifest; (b) target repo's `services.yml` is amended to add `allowed_callers: [acc]`; (c) policy-check at the target repo verifies SCP-R-006 evaluates as expected post-cascade. The ceremony is identical across all 9 repos; per-repo divergence (e.g., language-specific MCP server source) is captured in the signed manifest's per-entry fields. No per-repo bespoke ceremony required.

## Cross-references

- `/Users/amplience/Projects/acc-est-p/docs/plans/PLAN-EST-P-cross-repo-orchestration-v3.md` §3.5 + §4 + §15 SB-R2-003/007/008 + §14 ADR-024 skeleton + §3.6 kernel ceremony schedule — the ACC-side parent plan-doc that D-036 ratifies the SCP-side counterpart to.
- `/Users/amplience/Projects/acc-est-p/docs/decisions/ADR-024-cross-repo-trust-boundary.md` — ACC-side companion ADR (to be authored by ACC EST-P WS-EST-P-3.0; D-036 is the SCP-side counterpart).
- `docs/reviews/rule-proposals/RULE-003-acc-cross-repo-caller.md` — the companion rule-RFC proposing SCP-R-006 at warn baseline (filed alongside this ADR for combined operator review).
- `docs/decisions/D-049-design-system-policy-layer-adoption-2026-05-19.md` — precedent ADR shape (DPBM Phase-0 artefact-presence gating); D-036 follows the same five-element pattern + Justification + cross-references + Tracked-forward items + Sequencing + Status flip ceremony structure.
- `docs/decisions/D-050-tf-pim-001-app-credential-surface-2026-05-21.md` — precedent for bounded-reversal posture under D-031 single-operator-mode; D-036 inherits the same reversal-bounded discipline (each element's reversal cost ≤1 hour operator-attended).
- `docs/decisions/D-SCP-024B-SCOPE-SPLIT-2026-05-09.md` — precedent for incremental delivery, NOT descope; D-036's FUP enumeration preserves all original EST-P §15 v2/v3 scope items not ratified in this decision as numbered FUPs (FUP-EST-P-008, FUP-EST-P-001, FUP-EST-P-002, FUP-D036-002, FUP-D036-003).
- `docs/DECISIONS.md` — appended row for D-036 (single-table record).
- `docs/ESTATE-CONVERGENCE.md` §43 — original "DO NOT add a new auth mode to services.yml without going through D-036 SCP rule-RFC" entry this decision closes.
- `docs/home/HOME.md` §8.2 "Policy expansion" — names cross-repo orchestration as one of seven real candidates for the federation primitive to carry; D-036 ratifies it as the second such candidate filed (after D-049 / DPBM).
- `schemas/auth-contract.schema.json` — existing accepted-modes shape; D-036 Element 1 sits at the sibling level (`allowed_callers` is a peer key to `auth_contract`, not a nested field within it).
- `schemas/runtime-contract.schema.json` (or sibling) — target for the Element 1 schema extension.
- `control-tower/config/estate_repos.yaml` — cross-repo service registry per EST-P plan-doc §15 SB-R1-023; the canonical list of `<service_id>` values that may appear in `allowed_callers`. D-036 commits SCP to consume (read-only) this registry as part of SCP-R-006 evaluation but does not commit SCP to own its authoring.
- `docs/security/app-key-rotation-sop.md` — D-050 SOP precedent for Element 5's HMAC-key rotation discipline; D-036 commits to author a sibling `docs/security/cosignal-hmac-key-rotation-sop.md` at the EST-P WS-EST-P-6 cohort cascade clock (the first cohort install ceremony is the load-bearing trigger; tracked as TF-D036-004 below).
- `docs/plans/WP-SCP-024-estate-cascade.md` — canary-first sequencing precedent; D-036 + SCP-R-006 honour the same precedent (SCP self-dogfood first; PIM canary second only after TF-PIM-001 closes; cohort cascade third).

## Tracked-forward items (not blocking this decision)

These items are surfaced for follow-up but do not block D-036 acceptance. They will fold into either WP-SCP-024 cascade slices, future RULE-NNN filings, or operator-decision sweeps as their triggers fire:

- **TF-D036-001 — Cosignal-HMAC-key custody added to 2026-07-21 D-031 quarterly review agenda.** Operator-calendar gate; mirrors D-050's TF-PIM-001-SEC-005.
- **TF-D036-002 — Multi-org adopter ACC SA UUID coordination** (= FUP-D036-002). First non-`@jrnb2024` adopter triggers; mirrors D-050's TF-PIM-001-ARCH-004 shape.
- **TF-D036-003 — Mutual-TLS layer evaluation** (= FUP-D036-003). Trigger: subprocess env-strip attack vector materialises in production despite Element 4's enumerated allowlist.
- **TF-D036-004 — `docs/security/cosignal-hmac-key-rotation-sop.md` SOP authoring.** Operationalises Element 5's rotation cadence row. Authored at the WS-EST-P-6 cohort cascade clock (first cohort install ceremony is the load-bearing trigger).
- **TF-D036-005 — SCP-R-006 estate-wide deny promotion evaluation.** Trigger: 6 months of per-adopter deny operation with zero false-positives on at least 3 adopters. Per-adopter promotion via `threshold-overrides` is the ramp; estate-wide promotion is a separate rule-RFC.
- **TF-D036-006 — Element 3 signed-manifest schema versioning evolution.** Trigger: second `schema_version` value needed (v2 write-tool surface OR multi-org adopter). Manifest schema evolution discipline mirrors `policies/VERSIONING.md`.
- **TF-D036-007 — `verify_at_impl_stage: true` flag** for Element 5 HMAC-key file-permission verification. Per ASC-EST-P-003, the verify_command for `ls -la <target>/.acc/credentials/cosignal-hmac-key` returning `-r-------- root wheel` is structurally only verifiable post-install at impl stage, not at decision-doc filing time. Flag-gated.
- **TF-D036-008 — Per-target HKDF-derived ephemeral cosignal subkeys** (per SB-CRIT-001 R1 disposition Option (a)). Master key kernel-protected on ACC side only; per-target subkeys derived per-dispatch via HKDF-SHA256 + per-target context. Strictly-better security posture vs Element 5's shared-key shape; requires per-language HKDF implementation in ct-auth verifiers. v1.5.0+ evaluation; trigger = first production lateral-movement attack OR estate growth past 9 repos.
- **TF-D036-009 — ACC ADR-024 (cross-repo trust boundary) shape verification** (per CG-MAJ-001 R1 fix). D-036 has hard forward-coupling to ACC's ADR-024 which is to be authored by ACC EST-P WS-EST-P-3.0. If ADR-024 lands with materially different shape than D-036 anticipates, D-036 amendment is required. Trigger = ADR-024 merge; review = compare § shape against D-036 Elements 1-5.
- **TF-D036-010 — `control-tower/docs/security/manifest-signing-key-custody.md` SOP authoring** (per SB-MAJ-002 R1 fix). Operationalises Element 3's CT manifest signing-key custody discipline. Authored at the WS-EST-P-1 ship clock (the first signed manifest is the load-bearing trigger; rotation SOP gates the first ACC-side manifest-verify code path).
- **TF-D036-011 — WP-AUTH-007 final-issuer-URI verification** (per CORR-MAJ-001 R1 fix). D-036 v2 commits to whatever WP-AUTH-007 ships as the canonical `iss` shape. If WP-AUTH-007 lands with materially different shape than D-036 anticipates (`https://control-tower.brokapps.ai` hostname-form), D-036 inherits; this TF tracks the verification.
- **TF-D036-012 — Element 5 ts-window tightening from ±15min to ±2min** (per SB-MIN-001 R1 disposition). Once `jti` cache (Element 2 replay defence) is empirically observed deployed in production for ≥30 days with zero replay-detection events, tighten the cosignal ts window to ±2min for additional defence-in-depth.
- **TF-D036-013 — Symmetric `outbound_callees` field on caller side** (per §"Open questions" item 2; renamed from TF-D036-008 collision per R2 obs 1). Triggered if symmetric-cross-validation of caller-claims vs target-allowed sets becomes load-bearing for operator audit; default acceptance is single-direction declaration per §"Open questions" item 2 implicit acceptance.
- **TF-D036-014 — Canonical-JSON library dependency** (per R2 obs 5). Element 5's HMAC payload requires RFC 8785 JCS serialisation on both ACC mint side + target-repo verify side. Per-language JCS libraries (Python, TS, Go) MUST be available + pinned in the ct-auth versions extended per Element 1's implementation contract. Authored as part of the WP-AUTH-007 sibling work; trigger = ct-auth extension PR landing.

## Sequencing

D-036 is the rule-RFC vehicle ratification. SCP-R-006 (companion RULE-003) ships at v1.4.0 at warn baseline as **self-dogfood-only**. The rule is defined, packaged, and exercised against SCP's own `main` via the existing self-dogfood wrapper. No external adopter is gated by this rule at v1.4.0 — adopter cascade consumption is held pending two upstream events:

1. **TF-PIM-001 closes** (cross-repo `actions/checkout` authentication for SCP federation adopters; per D-050 §Sequencing — already CLOSED-WITH-RATIFIED-PATH 2026-05-21 at PR #133 merge; impl WP merged at PR #134 `89e645c`; awaiting full cohort cascade through Wave H per impl WP plan-doc §4).
2. **ACC EST-P WS-EST-P-2 ships** (per-repo MCP server canary in mapp-returns-intelligence + this ratification of D-036) — at which point the first external adopter (RI) is structurally ready to be evaluated by SCP-R-006.

This is an **artefact-gate, not a time-bake** per `feedback_artefact_gates_not_time_bakes.md` — the unblock signal is "TF-PIM-001 Wave H closes + ACC WS-EST-P-2 ships at least one successful RI dispatch end-to-end," not "X weeks have passed since v1.4.0." Calendar dates in this ADR ("v1.4.0") are orientation aids; the canonical sequence is:

1. **D-036 + RULE-003 merge** (this PR; expected 2026-05-24+).
2. **v1.4.0 ships** with SCP-R-006 at warn, self-dogfood only. (Zero-cost release; no external adopter has `allowed_callers: [acc]` declared yet.)
3. **ACC WS-EST-P-1 ships** (schema extension + `WorkPackage.target_repo` + ADR-026 — per EST-P plan-doc §4.2).
4. **ACC WS-EST-P-2 ships** (per-repo MCP server canary in RI + D-036 ratification cross-link).
5. **RI declares `allowed_callers: [acc]`** in `mapp-returns-intelligence/services.yml`. SCP-R-006 begins evaluating RI's manifest at warn.
6. **Warn-to-deny promotion on RI** via `threshold-overrides: { SCP-R-006: deny }` in RI's `.scp/rule-config.yaml`. Per-adopter promotion; not global RFC. Triggered by RI's own readiness signal (typically: 30 days of warn with zero false-positives).
7. **Subsequent adopters (PIM, recommender, CT, SA, doc-agent, VS, FLA, shopify-app) repeat steps 5-6** on their own clocks per WS-EST-P-6 cohort cascade.

D-036 ratification gates ACC WS-EST-P-2 (per AC-EST-P-AUTH-006). v1.4.0 release of SCP-R-006 is on a parallel clock — design-team-paced per the RULE-002 precedent (decoupled from EST-P WS clocks). v1.4.0 cuts when the rule + schema extension authoring is ready; the per-adopter ramp begins per-adopter post-EST-P-WS-EST-P-2 ship.

## Decision points (operator-resolved in-line)

This ADR is filed 2026-05-24 with the following design decisions pre-resolved in-line. Each is captured at the relevant Element section above; this paragraph names the resolutions explicitly so a reader scanning the doc does not have to cross-reference:

1. **`allowed_callers` placement at `runtime_contract` level, not nested in `auth_contract`.** (Element 1.) Rationale: `auth_contract` declares *modes* (closed enum); `allowed_callers` declares *peer-service identities* (open list, registry-driven). Different shape, different lifecycle. Sibling fields, not nested.

2. **Dynamic TTL with hard 6h ceiling, NOT operator-tunable per-dispatch.** (Element 2.) Rationale: per ASC-2026-05-17-002, 6h is the enforced-fail-closed ceiling. Per-dispatch tunability would create a per-call override surface that is hard to audit; dynamic-floor-with-hard-ceiling is the right compromise.

3. **Signed manifest is published from CT, NOT from SCP.** (Element 3.) Rationale: CT is the canonical estate identity issuer + already has signing-key custody infrastructure (per WP-AUTH-007). SCP consumes the manifest (verifies signatures, fails-closed on mismatch) but does not own its authoring. Reduces SCP's load-bearing custody surface.

4. **Env-propagation allowlist is HARDCODED in `CrossRepoDispatcher`, NOT data-driven from estate_repos.yaml.** (Element 4.) Rationale: per EST-P plan-doc CRIT-SB-002 fix + v4 CRIT-R3-SB-03 close-out. Data-driven allowlist creates a config-file injection surface; hardcoded allowlist requires a code PR (covered by 3-lens R1 review default per `feedback_orchestrator_auth_surface_plan_review_default.md`) for every allowlist change.

5. **HMAC key is a SHARED secret across the estate, NOT per-target.** (Element 5.) Rationale: per-target HMAC keys would create N×N coordination + N rotation ceremonies. Shared key with weekly rotation + recoverable-compromise discipline is operationally tractable for the 9-repo estate at bus-factor-1. Per-target keys is captured as a hypothetical future enhancement (not even a numbered FUP — would require operator decision to file).

6. **`ACC_COSIGNAL_HMAC_KEY` rotation cadence: weekly (Monday 00:00 UTC), calendar-driven NOT event-driven.** (Element 5.) Rationale: calendar-driven cadence is predictable + auditable + avoids "we'll rotate next time something concerning happens" drift. Event-triggered rotation (compromise, account change, D-031 review) is ADDITIVE to the weekly cadence, not in place of it.

## Open questions for operator review

This proposal is filed in DRAFT status. The following points are open for operator amendment before flipping to ACCEPTED:

1. **Should the weekly rotation cadence ceremony script (`<acc>/scripts/rotate-cosignal-hmac-key.sh`) be authored as part of this PR, or deferred to the EST-P WS-EST-P-2 ship?** Filed under operator review because authoring it here pre-commits ACC to the cadence before WS-EST-P-2's evidence base exists; deferring it risks the EST-P WS-EST-P-2 ship lacking the rotation mechanism. **If unresolved at merge, the implicit acceptance is: defer to WS-EST-P-2 (the EST-P plan-doc §4.3 WS-EST-P-2.3 already enumerates `install_per_repo_mcp_server.sh` authoring; the rotation script is a sibling).**

2. **Does `allowed_callers` need a corresponding `outbound_callees` field on the caller side (e.g., ACC's own `services.yml` would declare `outbound_callees: [mapp-returns-intelligence, mapp-pim, ...]`)?** Filed because symmetric declaration would let SCP-R-006 cross-validate caller-claims vs target-allowed sets, but it doubles the maintenance surface for adopters. **If unresolved at merge, the implicit acceptance is: NO — single-direction declaration on the target side (this ADR's Element 1) is sufficient for the policy gate; caller-side declaration is captured as TF-D036-013 (NEW; renamed from TF-D036-008 collision per R2 obs 1) if symmetric-cross-validation becomes load-bearing later.**

3. **Should the signed manifest's `signing_key_id` rotation be coordinated with the SCP-side cohort cascade clock, or run on CT's own clock?** Filed because manifest signing-key rotation is a CT-side custody concern that adopters do not see directly; coordinating with cohort cascade adds operator-attended ceremonies. **If unresolved at merge, the implicit acceptance is: CT's own clock — manifest verification on the SCP side is JWKS-style key-rollover-tolerant (multiple `signing_key_id` values can be live concurrently for a rollover window); SCP-R-006 evaluates against whichever key is named in the manifest's header; no SCP-side cascade coordination required.**

---

## Status flip ceremony

Per established estate pattern (D-047, D-048, D-049, D-050): file lands as DRAFT; flips to ACCEPTED at the next status-bookkeeping commit AFTER operator-attended merge. Operator-attended merge means explicit `gh pr merge` by operator OR explicit paste-back authorisation to orchestrator. Mechanical auto-merge NOT authorised for this PR per the auth-surface plan-stage review default applying to all auth-surface ADRs.
