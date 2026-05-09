# MCP adopter contract

How an external system (ACC dispatcher, agentic toolchain, CI pipeline) consumes SCP's MCP server. Three integration patterns + per-tool contract + receipt verification + token rotation. Read this before wiring SCP into your dispatch loop.

## Three integration patterns

The estate's first planned consumer is ACC (the LangGraph + Claude-Agent-SDK dispatcher at `acc.brokapps.ai`). ACC's MCP usage maps to three patterns; other consumers (CT planning surface, PIM auth-foundation tooling, Recommender J1 RBAC integration) follow the same shape.

### 1. Pre-code consult — `scp.consult_rules`

Before code generation, the consumer asks SCP "given this scope (changed files + domain + work-package context), which rules apply and what do they require?"

**Use case.** ACC's plan-decompose dispatcher checks SCP at task-spec authoring time — before assigning a Codex executor. If SCP names a rule that the dispatcher's spec violates (e.g. waiver-without-URL per SCP-R-004; missing services.yml entry per SCP-R-001), the dispatcher amends the spec or filters the task before any code is written.

**Tool:** `scp.consult_rules` (registered in `src/standards_control_plane/mcp_server/tools.py:1483`).

**Request shape:**
```json
{
  "domain": "auth | rules | observability | infra | data",
  "subsystem": "<optional sub-scope; falls through to domain default>",
  "context_paths": ["path/to/file.yml", "..."],
  "since": "2026-MM-DDTHH:MM:SSZ"
}
```

**Response shape:** rule list with rule_id + title + applicability evidence + waiver state. Read-only; no side effects.

**Latency budget.** Local stdio transport: <100ms typical; <500ms 99th. HTTP transport: +network RTT. Don't wire `consult_rules` into hot loops; it's a planning-time call.

### 2. Post-code audit — `scp.audit_changed`

After code generation, the consumer asks SCP "did this change introduce findings?"

**Use case.** ACC's verify-cycle dispatcher runs `audit_changed` against the work-package's diff before declaring success. Findings are surfaced to the orchestrator (or back to the executor for fix-cycles).

**Tool:** `scp.audit_changed` (registered `tools.py:1487`).

**Request shape:**
```json
{
  "domain": "<as above>",
  "subsystem": "<optional>",
  "changed_paths": ["path/to/changed/file.py", "..."]
}
```

**Response shape:** findings array (deny + warn + waived counts; rule_id breakdown; per-finding evidence). Includes `verdict: allow | deny | warn` aggregate.

**Latency budget.** Same envelope as `consult_rules`. Don't run on every keystroke; run on logical work-package boundaries.

### 3. Cross-repo audit trail — dispatch-log summary streaming

The consumer streams its dispatch-log summaries to SCP for org-wide compliance visibility. This is the WRITE-side surface; not yet implemented.

**Status.** Forward-planned. Tracked at TF-023D-001 (memory `project_wp_scp_023_state.md` "What's still open"). Likely future tool name: `scp.audit_scorecard_changed`. Adopters interested in streaming may reach out via `~/Projects/control-tower/governance/docs/notifications/` once the write-side surface lands.

**Until then.** Per-PR observability rides on the cross-repo scorecard aggregator (WP-SCP-023 023C / `.github/workflows/scorecard-aggregator.yml`), which is read-only and pull-based — no write coordination needed from adopters.

## Receipt verification (Ed25519-signed responses)

Every `consult_rules` / `audit_changed` / `consult_scorecard` response carries an Ed25519 signature in the receipt envelope. Adopters MUST verify before acting on responses — unsigned responses are not authoritative.

**Public key location:** `docs/security/mcp-signing-keys.pub` in the SCP repo. Pinned by content-hash; rotated on a documented cadence; key history preserved.

**Verification pattern (Python):**
```python
import nacl.signing  # PyNaCl
import json

def verify_receipt(response: dict, key_id: str, public_key_b64: str) -> bool:
    sig_b64 = response["receipt"]["signature"]
    payload = json.dumps(response["receipt"]["payload"], sort_keys=True, separators=(",", ":"))
    verify_key = nacl.signing.VerifyKey(base64.b64decode(public_key_b64))
    try:
        verify_key.verify(payload.encode(), base64.b64decode(sig_b64))
        return True
    except nacl.exceptions.BadSignatureError:
        return False
```

The receipt's `key_id` field disambiguates which public key signed it (multiple active keys during rotation overlap).

**On verification failure.** Treat as untrusted; fall back to local rules cache OR refuse to proceed. Do NOT silently ignore — log + alert.

## Token rotation (HTTP transport)

Stdio transport: trust-the-local-process; no token. HTTP transport: bearer token in `Authorization: Bearer <token>` header.

**Token location.** Adopter sets `SCP_MCP_TOKEN` (current) and optionally `SCP_MCP_TOKEN_PREV` (during rotation overlap window).

**Rotation cadence.** 30-day overlap. Operator rotates by:
1. Issuing new token (current = NEW; PREV = OLD).
2. Adopters update env var to NEW.
3. After 30 days, OLD token revoked.

**Cache invalidation.** Long-running dispatch loops should re-read the env var on every MCP call (cheap; avoids stale-cache 401s mid-job). Don't cache the token across restarts beyond the env var.

## Per-tool contract details

### `scp.consult_rules`
- **Domain enum:** `auth | rules | observability | infra | data`. Other values rejected with `INVALID_DOMAIN`.
- **Read-only.** Never mutates state.
- **Idempotent within a single (domain, subsystem, since) tuple.** Caching by (domain, since) is safe.
- **Does NOT cite waiver content.** Per WP-SCP-023 invariant 2 + plan-doc spec, waiver `reason` / `approved_by` / `waiver_id` strings are NEVER returned cross-repo.

### `scp.audit_changed`
- **Read-only.** Computes findings from current state + supplied diff; does not write findings to disk.
- **Diff scope.** Adopter supplies `changed_paths` array. Server reads those paths in the SCP working tree at request time. Adopter must commit changes before requesting (server reads working tree).
- **Verdict aggregate.** `allow` = no deny findings. `deny` = ≥1 deny finding (with optional waivers). `warn` = no deny but ≥1 warn finding.

### `scp.consult_scorecard` (WP-SCP-023 023D)
- Per-repo aggregated scorecard view. Read-only. Filters by `repo_filter` + `since_emitted_at`. NEVER returns waiver content.

### `scp.check_waiver` / `scp.list_open_decisions` / `scp.check_finding` / `scp.resolve_domain` / `scp.propose`
- Supporting surfaces. See `tools.py` registration block at lines 1483-1490 for the full registered set. Each is read-only except `propose` which write-side semantics are documented separately at slice authoring time (currently early-stage).

## Failure modes adopters MUST handle

| Mode | Cause | Adopter action |
|---|---|---|
| `INVALID_DOMAIN` / `INVALID_SUBSYSTEM` | Domain/subsystem not in enum | Log + reject the request locally; do NOT retry |
| `TIMEOUT` (default 30s; configurable per-tool) | SCP server slow under load | Retry with backoff (1s, 4s, 16s); after 3 retries fall back to local rules cache OR error to operator |
| Receipt signature verification fail | Compromised response OR wrong key_id | Refuse to act; alert; do NOT silently ignore |
| `401 UNAUTHORIZED` (HTTP) | Token expired / not rotated | Refresh from env var; if still 401, alert operator |
| `404 NOT_FOUND` on tool name | SCP version-skew (older server doesn't have new tool) | Fall back to next-best tool OR error to operator |

## Versioning + cohort cadence

SCP federation primitive at v1.2.0 (post-WP-SCP-023). MCP tool surface evolves additively; new tools land via `register_tools` at `tools.py:1480` without breaking existing tool contracts. MAJOR-pinned schema additions follow `policies/VERSIONING.md` D-036 (additive = MINOR; breaking = MAJOR + one-release deprecation ramp).

Adopters should tolerate version-skew: if `tools.py` adds a new tool you don't know about, ignore it. If a tool you depend on disappears in a MAJOR bump, the deprecation ramp gives one release of warning.

## Where to ask for help

- Estate notifications log: `~/Projects/control-tower/governance/docs/notifications/` (cross-repo conversation channel per `reference_ct_notifications.md`)
- Issue tracker on `jrnb2024/standards-control-plane-` (private; ask for access if you need to file)
- For consumer-side spike work (~3-day envelope per ACC's 2026-05-09 estimate), pre-coordinate via the notifications log before opening a feature branch — the operator may want to align with a release cycle

## Changelog

- **2026-05-09:** initial draft. Three patterns documented; receipt verification pattern; token rotation cadence; failure modes table.
