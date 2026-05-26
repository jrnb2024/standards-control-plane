# WP-SCP-026 026C — ACC ↔ RI canary handoff contract for `scp-cli consult`

**Filed:** 2026-05-26
**WP:** WP-SCP-026 slice 026C
**Shape:** C (D-054 ratified 2026-05-25; D-055 narrative reconciliation ratified 2026-05-26)
**Successor decision reserved:** D-056 (WP-SCP-026 026F Threshold + USER-GATE-G observation; 4-week observation window from this RFC's referenced canary-ship)
**Anti-scope:** this RFC does NOT touch the ACC repo or the RI repo. It is the SCP-side artefact documenting the contract that ACC + RI consume.

---

## 1. Purpose

`scp-cli consult --domain <X>` shipped via SCP PR #176 (`8ffcb41`, 2026-05-26).
RI's `tool_scp_consult_rules` at `~/Projects/ri-est-p-ws-2/.acc/mcp_server.py:298-338`
already subprocess-wraps `scp-cli` with the contract that matches the shipped
binary (regex-validated `--domain`; `isinstance(parsed, list)` check; error
sentinels). The pieces are in place.

This RFC publishes the SCP-side handoff contract so that:

- ACC team can verify the RI canary path end-to-end on the next real RI dispatch.
- Future adopters following ADOPT-001 §13 Path (b) have a single named reference
  for the canonical first-consumer pattern.
- The 026F observation window has a clearly defined success criterion measurable
  against this contract.

## 2. Contract surface

### 2.1 `scp-cli consult` CLI contract (SCP-side; shipped)

| Aspect | Value | Source |
|---|---|---|
| Console-script entry-point | `scp-cli` | `pyproject.toml` (PR #176) |
| Install line | `pipx install standards-control-plane` OR `pip install standards-control-plane` | ADOPT-001 §13.2.1 |
| Subcommand | `consult` | `src/standards_control_plane/scp_cli.py` `main()` |
| Required argument | `--domain <name>` | regex `^[a-zA-Z0-9_\-]{1,64}$` |
| Optional arguments | `--subsystem <name>` (regex `^[a-zA-Z0-9_\-]{1,64}$`), `--area-id <path-shaped>` (regex `^[a-zA-Z0-9_\-./]{1,128}$`) | `scp_cli.py:43-50` |
| stdout (success) | Single-element JSON list wrapping `ConsultRulesResponse` dict (`json.dumps([result])`) | `scp_cli.py:130` |
| stderr (failure) | `SCP-CLI-EnnN: <message>` (control-char-stripped; truncated) | `scp_cli.py:121-201` |
| Exit codes | 0 success; 2 timeout; 3 server nonzero; 4 protocol/parse error; 5 input validation; 6 stdout cap exceeded | `scp_cli.py:21-26` |
| Per-attempt timeout | 12 s | `scp_cli.py:39` |
| Retries on timeout | 2 (so ≤24 s worst case) | `scp_cli.py:40` |
| Stdout cap | 10 MB | `scp_cli.py:41` |
| Cold-start latency | ~500 ms (Python import + MCP `initialize` handshake) | ADOPT-001 §13.2.5 |
| Env passed to subprocess | scrubbed: PATH + HOME + LANG + LC_ALL only | `scp_cli.py:236-242` |

### 2.2 `ConsultRulesResponse` schema (returned inside the single-element list)

Verified at `src/standards_control_plane/mcp_server/tools.py:118-128`:

```json
{
  "schema_version": "1.0.0",
  "request_id": "<uuid>",
  "domains": ["<domain>", ...],
  "approved_patterns": [{"pattern_id": "<id>", "reason": "<text>"}, ...],
  "open_findings": [{"finding_id": "<id>", "severity": "<level>", "summary": "<text>", "confidence_class": "<class>"}, ...],
  "historical_reviews": [{"review_id": "<id>", "path": "<path>", "summary": "<text>"}, ...],
  "applicable_rules": [{"rule_id": "SCP-R-<NNN>", "reason": "<text>"}, ...],
  "guidance": ["<text>", ...],
  "risks": ["<text>", ...],
  "confidence": 0.0,
  "confidence_class": "<class>"
}
```

Wrapped in a single-element JSON list at stdout:

```json
[{ /* ConsultRulesResponse dict above */ }]
```

The single-element list shape is load-bearing for the RI canary path; see §2.3.

### 2.3 RI canary consumer contract (RI-side; already shipped)

Verified at `~/Projects/ri-est-p-ws-2/.acc/mcp_server.py:298-338` (function
`tool_scp_consult_rules`). Reproduced here as the canonical first-consumer
pattern:

```python
def tool_scp_consult_rules(args: dict[str, Any]) -> list[dict[str, Any]]:
    domain = args.get("domain", "")
    if not isinstance(domain, str) or not re.match(r"^[a-zA-Z0-9_\-]{1,64}$", domain):
        return [{"error": "INVALID_DOMAIN", "detail": "domain must match safe regex"}]
    try:
        proc = subprocess.run(
            ["scp-cli", "consult", "--domain", domain],
            shell=False,
            capture_output=True,
            text=True,
            timeout=_SCP_CLI_TIMEOUT_SECONDS,
            cwd=str(_WORKSPACE_PATH),
            env=_scrubbed_subprocess_env(),
            check=False,
        )
    except FileNotFoundError:
        return [{"error": "CLI_NOT_AVAILABLE", "detail": "scp-cli not on PATH"}]
    except subprocess.TimeoutExpired:
        return [{"error": "CLI_TIMEOUT", "detail": f"scp-cli exceeded {_SCP_CLI_TIMEOUT_SECONDS}s"}]
    if proc.returncode != 0:
        return [{"error": "CLI_NONZERO_EXIT",
                 "detail": f"rc={proc.returncode} stderr={proc.stderr[:512]!r}"}]
    try:
        parsed = json.loads(proc.stdout)
        if isinstance(parsed, list):
            return parsed
        return [{"error": "CLI_OUTPUT_NOT_LIST", "detail": f"got {type(parsed).__name__}"}]
    except json.JSONDecodeError:
        return [{"domain": domain, "raw": proc.stdout[:4096]}]
```

The contract matches: RI checks `isinstance(parsed, list)` at line 333 because
`scp-cli` emits a JSON list (single-element wrapper) on every successful call;
on JSON decode failure RI returns a free-text fallback list element rather than
crashing the MCP frame.

## 3. ACC-side action — what needs to happen

**No code change required on ACC or RI.** The RI canary is already wired
correctly per PR #176's R1 lens C completeness fix (commit `8ffcb41`). The ACC
team's action is verification only:

1. **Confirm `scp-cli` is reachable.** On a real RI workspace (or a fresh CI
   image), run `pipx install standards-control-plane` (or whatever install
   mechanism the workspace uses) and verify `which scp-cli` returns a path.
2. **Smoke-test the CLI directly.** Run
   `scp-cli consult --domain auth | python3 -m json.tool` and verify the output
   is a JSON list with one element whose schema matches §2.2.
3. **Smoke-test the per-repo MCP path.** From a Python REPL in a workspace with
   `.acc/mcp_server.py` installed, call
   `tool_scp_consult_rules({"domain": "auth"})` and verify the return value is
   a list whose first element is either a `ConsultRulesResponse` dict (success)
   or an error sentinel (`INVALID_DOMAIN` / `CLI_NOT_AVAILABLE` / `CLI_TIMEOUT`
   / `CLI_NONZERO_EXIT` / `CLI_OUTPUT_NOT_LIST`).
4. **Trigger a real ACC orchestrate dispatch through RI** that exercises
   `tool_scp_consult_rules` as part of its agent flow. The agent's authored
   output (PR body / review comment / code-change rationale) should reference
   at least one rule_id returned by the consult.

Steps 1-3 are verification-only and do not require an active ACC dispatch.
Step 4 is the load-bearing 026F observation criterion (see §4).

## 4. Success criterion — 026F observation (4-week window from this RFC merge)

Per D-054 §"Decision" 026F row + D-055 §"Boundaries" — the 4-week observation
window starts on the merge of this RFC (or the corresponding 026C
sibling-RFC commit on the ACC side if ACC ratifies independently). Within
that window:

- **Primary criterion (load-bearing).** ≥1 real ACC orchestrate dispatch
  through RI invokes `tool_scp_consult_rules` AND the agent's authored output
  references ≥1 returned `rule_id` (or `pattern_id` from `approved_patterns`,
  if domain returns no `applicable_rules` but does return approved-patterns).
- **Secondary criterion (advisory).** Zero `INVALID_DOMAIN` or
  `CLI_NOT_AVAILABLE` sentinels surfacing in the observation window for
  legitimate inputs — sentinels for malformed inputs or missing-install are
  acceptable; consistent recurrence on a known-good workspace would indicate
  contract drift.

D-056 (filed inline at 026F close-out) ratifies one of three outcomes:

- **(a) Advance to WP-SCP-027** — primary criterion met + operator-attended
  demand signal received (an adopter or ACC team explicitly asks for signed
  receipts or HTTP MCP transport). Triggers the deferred multi-week
  receipt-signing + HTTP build per D-054 + D-055 framing.
- **(b) Hold WP-SCP-027 indefinitely** — primary criterion met + no demand
  signal. Indefinite hold is a valid outcome per D-054 §"What Shape C is and
  is not".
- **(c) Re-scope WP-SCP-026** — primary criterion NOT met within 4 weeks. This
  is the anti-criterion per D-054 §"Anti-criterion" item 1; SHIP-PROPOSAL +
  HALT discipline applies; operator decides next move.

## 5. Anti-criteria (treat as failed and re-scope if any hold at 026F close-out)

From D-054 §"Anti-criterion":

1. Zero real `consult_rules` invocations 4 weeks after this RFC merge — the
   canary doesn't get used.
2. The doc-vs-code divergence persists or grows — new aspirational claims land
   in `docs/OVERVIEW.md` without supporting code.
3. Adopter onboarding fails because the documented MCP integration path doesn't
   actually work — readers of ADOPT-001 §13 cannot reproduce the contract end-
   to-end on a fresh workspace.

The §13 runbook (delivered by sibling PR WP-SCP-026 026E) is the canonical
adopter-facing surface; if the runbook diverges from this RFC's contract, the
runbook is wrong (this RFC is the source-of-truth).

## 6. Sequencing relative to WP-SCP-024 cohort cascade

The cohort cascade (PIM 2026-05-24 + CT 2026-05-25 + mapp-doc-agent 2026-05-25
LIVE; Recommender DEFERRED; shopify-app PENDING) is independent of this RFC.
Cohort adopters consume the federation-primitive's required-status-check
surface; the MCP consult surface is additive (not required for federation-
primitive Threshold A). The 026F observation window operates against
`tool_scp_consult_rules` consumption, not federation-primitive consumption.

## 7. References

- D-054 — Shape C ratification: `docs/decisions/D-054-wp-scp-026-shape-c-ratification-2026-05-25.md`
- D-055 — Narrative reconciliation: `docs/decisions/D-055-WP-SCP-026-narrative-reconciliation-2026-05-26.md`
- WP-SCP-026 plan-doc: `docs/plans/WP-SCP-026-mcp-consumer-integration-v1.md` (v1.0; §5 slice plan row 026C)
- ADOPT-001 §13 MCP integration runbook (sibling PR WP-SCP-026 026E): `docs/adoption/ADOPT-001-project-onboarding.md` §13
- `scp-cli` shim source: `src/standards_control_plane/scp_cli.py` (shipped PR #176, 2026-05-26)
- `ConsultRulesResponse` schema: `src/standards_control_plane/mcp_server/tools.py:118-128`
- RI canonical canary: `~/Projects/ri-est-p-ws-2/.acc/mcp_server.py:298-338`
- ACC PLAN-EST-P-v3 §3.3 (per-repo MCP server pattern; ACC-repo-owned)

## 8. Out-of-scope

This RFC does NOT:

- Modify ACC or RI repo files (ACC-team-owned changes).
- Specify the receipt-signing / HTTP MCP transport contract (deferred to
  WP-SCP-027 per D-054 + D-055; awaits operator-attended demand signal).
- Specify the per-repo MCP server adopter ceremony (deferred to
  `WP-SCP-EST-001-PER-REPO-MCP-PROXY` — see BACKLOG Phase 12).
- Specify the 026F close-out PR content (deferred to D-056 + 026F slice
  itself).

## 9. Forward action

- **SCP-side (this RFC merge):** triggers the 4-week 026F observation window.
- **ACC-team-side:** verification per §3 on the next dispatch they run.
- **No operator action required for the RFC itself** — autonomous merge per
  WP-SCP-026 026C discipline (coordination-only doc).
