# Autonomous SCP Session — WP-SCP-026 026B/C/D/E + FUP sweep + Z-blocker memo

**Drafted:** 2026-05-26
**Session character:** Single long autonomous run. No operator-in-the-loop except where explicitly flagged HOLD-FOR-OPERATOR.
**Expected duration:** 12-18h. May exceed a single context window — if so, checkpoint after each phase merge + re-arm cleanly via memory + STATUS.md re-read.
**Reviewer-approved amendments folded in:** Plan reviewed by 3 parallel agents 2026-05-26; all critical findings folded into this prompt.

---

## Pre-flight (do this FIRST, before any other work)

1. Verify current main HEAD. Run:
   ```bash
   cd /Users/amplience/Projects/standards-control-plane
   git checkout main && git pull --ff-only origin main && git log --oneline -3
   ```
2. Confirm `https://scp.brokapps.ai/health` is responding + `/health.git_sha` matches main HEAD:
   ```bash
   curl -s https://scp.brokapps.ai/health | jq '.git_sha, .release_version'
   ```
   If git_sha doesn't match main HEAD, deploy missed your latest changes — pause + flag to operator.
3. Read in order (DO NOT skip; you'll be ineffective without this state):
   - `STATUS.md` (header + at-a-glance + 2026-05-26 chain rows)
   - `docs/OVERVIEW.md` §1-§3 + §5
   - `docs/plans/WP-SCP-026-mcp-consumer-integration-v1.md` v1.0 (full)
   - `docs/decisions/D-054-wp-scp-026-shape-c-ratification-2026-05-25.md` (full)
   - `docs/plans/WP-SCP-026-Z-r006-workflow-input-materialisation.md` v0.2 (full)
   - `docs/governance/work-packages/wp-scp-026-z-r006-workflow-input.json` v0.2 (full)
4. Survey memory: `ls ~/.claude/projects/-Users-amplience-Projects/memory/feedback_*.md | head -20`
5. List open PRs across SCP: `gh pr list --state open`
   - If PIM #344 (SCP-wrapper bump to v1.3.0) is open + all-green: admin-merge it before any other work.
   - Any other open PRs not in scope of this prompt: leave alone; flag in summary.

### Cardinal disciplines (re-read these; they apply throughout)

- **PR workflow estate-wide.** No direct commits to main. Every change goes through a PR with CI + R1 evidence (`feedback_pr_workflow_never_direct_to_main.md`).
- **3-agent R1 on code/plan reviews.** No focused reviews; no shortcut. Lenses per surface (see per-phase below). (`feedback_never_shortcut_review.md`, `feedback_always_review_plans.md`).
- **No silent descope.** If you can't close something, file it forward. Never silently drop scope. (`feedback_no_silent_descoping.md`).
- **No demo-scope thinking.** Full system, not subsets. (`feedback_no_demo_scope.md`).
- **Cure-worse trigger discipline (per-WP).** Per `feedback_asymptotic_trajectory_split.md`: if R2 surfaces NEW HIGH/CRIT ≥ R1-severity in same WP-class → file SHIP-PROPOSAL + stand down; do NOT iterate R3 without operator authorisation. **Scope: WP-SCP-026 as a unit.** If 026B R2 surfaces cure-worse trigger, 026D + 026E PRs also stand down. Phase 5 (FUP bundles) is a DIFFERENT WP-class and proceeds independently.
- **R1 evidence + lens regex format.** Every PR body must include `## R1 evidence` block with three lenses formatted as `- correctness:`, `- safety_bypass:`, `- completeness_governance:` (no `**bold**` on lens labels — `r1-evidence-check.yml` validator regex `^[ \t]*-[ \t]*(correctness|safety_bypass|completeness_governance):[ \t]*\S` rejects bold). Surfaced twice in 2026-05-25 + 2026-05-26 sessions; do NOT repeat.
- **STATUS.md chain row catch-22 mitigation.** PRs touching only `pyproject.toml` / `src/` / `tests/` will have `check-invocation-log-entry` MISSING (workflow's `paths:` doesn't fire). Add a STATUS chain row to every such PR — it triggers the workflow + short-circuits. (`feedback_docs_only_pr_branch_protection_catch22.md`).
- **Verify branch + staged set before commit.** `git branch --show-current` + `git status --short` before every `git commit`. (`feedback_verify_branch_and_staged_set_before_commit.md`).
- **Grep production before claiming.** Cite file:line + verbatim quote before R1. Don't assert about code or docs you haven't read. (`feedback_grep_production_before_planning.md`).

### Operator-attended gates (READ CAREFULLY — fail of these = lost trust)

Per phase, the merge authority is:

| Phase | Surface | Merge gate |
|---|---|---|
| 0 | Preflight + PIM #344 | **AUTONOMOUS** (CI green sufficient; admin-merge OK) |
| 1 (026B) | scp-cli shim — new CLI surface + pyproject.toml entry-point | **HOLD-FOR-OPERATOR.** Open PR; iterate R1 + fix-cycles to fixpoint; tag PR body with `Status: READY-FOR-OPERATOR-MERGE`. Do NOT merge yourself. |
| 2 (026D) | D-055 ADR (narrative retraction) | **HOLD-FOR-OPERATOR.** ADR-class. DRAFT until operator click-merges. Tag `Status: READY-FOR-OPERATOR-MERGE`. |
| 3 (026E) | ADOPT-001 §13 runbook | **AUTONOMOUS** (doc-only; R1 evidence + CI sufficient). |
| 4 (026C) | ACC RI canary RFC | **AUTONOMOUS** (coordination-only; R1 sufficient). |
| 5 (FUP bundles A/B/C) | scripts + docs | **AUTONOMOUS** (per standard discipline). |
| 6 (Z-blocker memo) | Coordination doc | **AUTONOMOUS** (no code; just memo). |
| 7-8 (bookkeeping) | STATUS + memory + continuation-prompt | **AUTONOMOUS** (no policy mutation). |

---

## Phase 1 — WP-SCP-026 026B (scp-cli shim) [3-5h]

**Goal:** Ship `scp-cli` entry point. Adopters and ACC's per-repo MCP servers will call `subprocess.run(["scp-cli", "consult", "--domain", domain])` and receive `ConsultRulesResponse` JSON.

### Plan-stage 3-agent review (REQUIRED before code)

Per `feedback_orchestrator_auth_surface_plan_review_default.md`: the scp-cli surface is auth-adjacent (called by ACC's per-repo auth-bearing MCP servers; subprocess process-trust is the boundary). Run a lightweight 3-agent plan-stage review on the approach BEFORE writing code:

- **Lens A — architecture:** Is option (i) (subprocess `scp-mcp-server stdio` + JSON-RPC translation) actually the right pattern? Or does the simplicity argument for option (ii) (direct Python import of `consult_rules_impl`) outweigh the MCP-narrative-preservation argument? Note: D-054 ratified option (i) as default + option (ii) as pre-approved fallback. Reviewer should affirm or surface a third option.
- **Lens B — safety:** Subprocess shell injection? Untrusted input to JSON-RPC? Timeout handling? Concurrent invocations safe?
- **Lens C — completeness:** Does the shim's output match `ConsultRulesResponse` shape byte-for-byte? Error pathways covered? Stdout-vs-stderr discipline correct (only JSON on stdout)?

Each lens: post findings as PR body comment block. R-fixpoint MET = all 3 lenses converge on FIRE / FIRE-WITH-FIXES (not REJECT). If REJECT on any lens, file SHIP-PROPOSAL.

### Default approach: option (i) — thin wrapper

```python
# src/standards_control_plane/scp_cli.py (NEW)
import argparse, json, subprocess, sys, uuid
from pathlib import Path

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scp-cli", description="SCP design-time consult CLI")
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    consult = subparsers.add_parser("consult", help="Consult SCP rules")
    consult.add_argument("--domain", required=True)
    consult.add_argument("--subsystem")
    consult.add_argument("--area-id", dest="area_id")
    args = parser.parse_args(argv)

    if args.cmd == "consult":
        return _consult(args)
    return 1

def _consult(args) -> int:
    # Subprocess scp-mcp-server stdio, send JSON-RPC, parse response.
    request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": {
            "name": "consult_rules",
            "arguments": {"domain": args.domain},
        }
    }
    if args.subsystem:
        request["params"]["arguments"]["subsystem"] = args.subsystem
    if args.area_id:
        request["params"]["arguments"]["area_id"] = args.area_id

    proc = subprocess.Popen(
        [sys.executable, "-m", "standards_control_plane.mcp_server.cli", "serve"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = proc.communicate(json.dumps(request) + "\n", timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        print(f"SCP-CLI-E001: scp-mcp-server timeout (10s)", file=sys.stderr)
        return 2

    if proc.returncode != 0:
        print(f"SCP-CLI-E002: scp-mcp-server exit {proc.returncode}: {stderr}", file=sys.stderr)
        return 3

    # Parse JSON-RPC response, extract tool result, emit as JSON on stdout.
    try:
        response = json.loads(stdout)
        result = response["result"]["content"][0]["text"]
        # The MCP tool returns the ConsultRulesResponse as a JSON-stringified text content.
        print(result)
        return 0
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        print(f"SCP-CLI-E003: malformed MCP response: {exc}: {stdout[:200]}", file=sys.stderr)
        return 4
```

**Fallback trigger criteria (option (i) → (ii)):**
- If you spend >2h debugging option (i) JSON-RPC integration → flip to option (ii).
- If `scp-mcp-server` subprocess fails to start 3+ times in test → flip.
- If JSON parse errors on 5+ consecutive tool calls in test → flip.
- Option (ii) is `from standards_control_plane.mcp_server.tools import consult_rules_impl` + call directly. No MCP layer. Faster but less MCP-canonical.

### Subprocess timeout discipline

- Per-tool-call: 10 seconds (set in `subprocess.communicate(..., timeout=10)`)
- 3 retries on timeout before flipping to option (ii)
- All errors emit `SCP-CLI-E00N` to stderr; exit code distinguishes failure type
- No partial output to stdout on error

### `pyproject.toml` change

Add to `[project.scripts]`:
```toml
scp-cli = "standards_control_plane.scp_cli:main"
```

### PATH re-install ceremony (CRITICAL — easy to forget)

After modifying `pyproject.toml`:
```bash
pip install -e .
which scp-cli  # must return a path
scp-cli --help # must succeed
```
If `which scp-cli` doesn't return a path → entry point isn't registered → R1 evidence will fail.

### Verification (run BEFORE opening PR)

```bash
# 1. Bake status check — confirm SCP-self rules are loadable
scripts/operator/check-bake-status.sh --adopter jrnb2024/standards-control-plane --onboard-date 2026-04-30 2>&1 | head -20

# 2. Run consult against current rule set
scp-cli consult --domain auth > /tmp/auth-rules.json
scp-cli consult --domain governance > /tmp/governance-rules.json

# 3. Assert non-empty applicable_rules
python3 -c "
import json
for f in ['/tmp/auth-rules.json', '/tmp/governance-rules.json']:
    data = json.load(open(f))
    n = len(data.get('applicable_rules', []))
    print(f'{f}: {n} applicable rules')
    assert n >= 1, f'Expected ≥1 rule in {f}'
print('OK: scp-cli consult produces non-empty applicable_rules for auth + governance')
"

# 4. Assert ConsultRulesResponse shape
python3 -c "
import json
data = json.load(open('/tmp/auth-rules.json'))
required = ['applicable_rules', 'approved_patterns', 'open_findings', 'historical_reviews', 'guidance', 'risks', 'confidence', 'confidence_class', 'schema_version']
missing = [k for k in required if k not in data]
assert not missing, f'Missing keys: {missing}'
print('OK: response shape matches ConsultRulesResponse')
"
```

### Files touched

1. `pyproject.toml` — add entry_point
2. `src/standards_control_plane/scp_cli.py` (NEW)
3. `tests/test_scp_cli.py` (NEW) — unit tests for argparse + subprocess + JSON-RPC + error paths
4. `README.md` — 1-2 sentence note documenting `scp-cli` as the adopter-facing design-time consult CLI
5. `STATUS.md` — chain row (path-trigger for `check-invocation-log-entry`)

### Code-stage 3-agent R1 review (after code is written)

Per `feedback_never_shortcut_review.md`. Three lenses dispatched in parallel as Explore agents (read-only):
- **correctness:** Does JSON-RPC translation match MCP protocol spec? Does `ConsultRulesResponse` schema preserve? Do tests cover happy path + each error code + timeout?
- **safety_bypass:** Subprocess injection? Shell escape? Stdin/stdout buffering safe? Concurrent calls?
- **completeness_governance:** Pre-existing CLI shape patterns followed? `pyproject.toml` entry registered correctly? Docstrings present? README updated?

**R-fixpoint MET:** all 3 ACCEPT or FIRE-WITH-FIXES with concrete fixable findings. Fold + re-run R2 if any new HIGH/CRIT. Apply cure-worse if R2 surfaces new HIGH/CRIT ≥ R1-severity.

### PR body shape

```markdown
## Summary
WP-SCP-026 slice 026B — `scp-cli` shim shipping the adopter-facing design-time consult CLI...

## R1 evidence
- correctness: [paste R1 lens A verdict + 3-5 lines of evidence]
- safety_bypass: [paste R1 lens B verdict + 3-5 lines of evidence]
- completeness_governance: [paste R1 lens C verdict + 3-5 lines of evidence]

## Test plan
- [ ] policy-check / scp/policy-check
- [ ] check-invocation-log-entry (short-circuit via STATUS.md path-trigger)
- [ ] validate PR body (all three lenses populated)

## Status: READY-FOR-OPERATOR-MERGE
HOLD: do not merge autonomously. Operator merges after reviewing CLI surface.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### Phase 1 stand-down conditions

- Cure-worse R2 trigger → SHIP-PROPOSAL + HALT Phases 1+2+3 (same WP)
- Verification step fails (rules don't load) → HALT + diagnose
- Option (i) → (ii) flip exceeded 4h total → HALT + report to operator

---

## Phase 2 — WP-SCP-026 026D (D-055 narrative retraction) [3-4h, PARALLEL with Phase 1]

**Goal:** Amend `docs/OVERVIEW.md`, `docs/adoption/mcp-adopter-contract.md`, `docs/adoption/ADOPT-001-project-onboarding.md` to retract claims about Ed25519-signed-consult-receipts + HTTP MCP transport + `acc.brokapps.ai` MCP hosting + `SCP_MCP_TOKEN` bearer-token rotation. Move to OVERVIEW.md §6.3 future-scope with WP-SCP-027 forward-link. File D-055 ADR inline.

**Run in parallel with Phase 1** (different files, different PR; no merge conflict risk). But: if Phase 1 hits cure-worse R2 trigger, this Phase 2 PR also stands down (same WP-class).

### Verbatim retraction targets (verified by pre-flight grep 2026-05-26)

**`docs/OVERVIEW.md`** — 8 lines with claims to retract or amend:
- **L47:** `- scp.consult_rules(domain) — agent asks "what rules apply if I'm changing files under X?" before authoring; returns matched rules + Ed25519-signed receipt.` → drop `+ Ed25519-signed receipt` clause; move signed-receipt narrative to §6.3.
- **L50:** Full sentence about receipts signed with private Ed25519 key + PreCommit hook validation + TTL ≤ 2h + replay defence → move entirely to §6.3 future-scope, replace inline with stub note: "Per D-054 (2026-05-25), receipt-signing deferred to WP-SCP-027 pending operator-attended demand signal. Today's consult responses are unsigned JSON; adopters do NOT validate receipts."
- **L82:** `│   • Live Watch UI (acc.brokapps.ai)                             │` → leave as-is (this is ACC's live watch UI, not SCP's MCP server hosting). Verify by reading surrounding context.
- **L105:** Already-correct existing note about stdio-only + retraction. Confirm + leave.
- **L257:** Step `d. signs receipt with private Ed25519 key` in some narrative flow → either delete the step or move full flow to §6.3.
- **L258:** Step `e. returns rules + signed receipt` → same treatment as L257.
- **L277:** `ACC at ~/Projects/acc, deployed at acc.brokapps.ai, is the multi-agent orchestrator` → leave as-is (this is about ACC the orchestrator, not SCP's MCP hosting).
- **L334:** `| WP-SCP-021 (MCP Server) | Ed25519-signed receipts + scoped pre-code consult; stdio + HTTP transports | v0.3 fixpoint 2026-04-29 |` → amend WP-SCP-021 row to reflect what's actually shipped (stdio only; no signed receipts on responses) + note D-054 retraction.
- **L429:** `**Compliance attestation** — for regulated work (data residency, retention, audit), SCP attests via signed receipts that PRs comply with relevant standards` → reword to clarify that compliance attestation is a future-scope item (WP-SCP-027); today, compliance is asserted at PR-merge-time by the federation primitive's required check, not via signed receipts.

**`docs/adoption/mcp-adopter-contract.md`** — 9 lines with substantial sections to retract or amend:
- **L29:** `**Latency budget.** Local stdio transport: <100ms typical; <500ms 99th. HTTP transport: +network RTT. Don't wire consult_rules into hot loops; it's a planning-time call.` → drop HTTP transport reference; keep stdio latency claim.
- **L60-76:** Full `## Receipt verification (Ed25519-signed responses)` section + PyNaCl snippet → DELETE this section. Replace with retraction note pointing to OVERVIEW.md §6.3 + WP-SCP-027.
- **L86-90:** `## Token rotation (HTTP transport)` section → DELETE. Replace with retraction note.
- **L124:** Error-handling row about "Receipt signature verification fail" → DELETE row from error-handling table.

**`docs/adoption/ADOPT-001-project-onboarding.md`** — 1 line:
- **L197:** `scripts/scp-consult` reference → replace with `scp-cli consult` (which is what Phase 1 026B ships).

### D-055 ADR file

**Path:** `docs/decisions/D-055-WP-SCP-026-narrative-reconciliation-2026-05-26.md`

**Template:** Mirror D-054 structure. Status: DRAFT → ACCEPTED on PR merge.

**Decision body (skeleton):**
```markdown
# D-055 — WP-SCP-026 026D narrative reconciliation: retract HTTP MCP transport + Ed25519-signed-consult-receipts + acc.brokapps.ai MCP hosting

**Status:** DRAFT (operator-review surface)
**Date filed:** 2026-05-26
**Closes:** WP-SCP-026 plan-doc §6 D-055 reservation (filed inline with 026D per D-054 §"Decision").
**Predecessor:** D-054 (Shape C ratification).
**Successor:** WP-SCP-027 (HTTP transport + signed receipts; awaits operator-attended demand signal per D-054 + D-056).

## Context
[Document the credibility-risk framing per D-054 §"Context"]

## Decision
Retract from OVERVIEW.md / mcp-adopter-contract.md / ADOPT-001:
1. All Ed25519-signed-consult-receipt narrative (8 lines in OVERVIEW.md + full §"Receipt verification" in mcp-adopter-contract.md)
2. All HTTP MCP transport narrative (3 lines in OVERVIEW.md + full §"Token rotation" in mcp-adopter-contract.md)
3. All claims about `acc.brokapps.ai` MCP hosting (note: acc.brokapps.ai itself exists as ACC's orchestrator UI, not as SCP's MCP server)
4. `SCP_MCP_TOKEN` bearer-token rotation contract

Move to OVERVIEW.md §6.3 future-scope with forward-link to WP-SCP-027.

Replace ADOPT-001 §"scripts/scp-consult" reference with `scp-cli consult` (the binary that 026B ships).

## Rationale
[Mirror D-054 §"Rationale" framing: credibility, reversibility, named-successor discipline]

## Reversal mechanism
≤2 days of doc-only work to swap §6.3 ↔ §1.4/§3.4 if WP-SCP-027 ships later; the WP-SCP-027 build itself is the same scope regardless of when it ships.

## Diff-verification
Per `feedback_verbatim_claim_diff_verification.md`, all retracted text is verified via the actual file diff in this PR — reviewers diff-verify at R1 time via `git show <PR-merge-sha>:docs/OVERVIEW.md`.
```

### DECISIONS.md row

Append a single row after D-054's row in the table. Bump `**Last Updated:**` header.

### R-cycle (3-lens R1, doc-only)

- **correctness:** Does retracted text move cleanly to §6.3? Are all the verbatim lines covered? No stale aspirational claims left standing?
- **safety_bypass:** Does the retraction weaken any security claim? (Note: retracting unimplemented receipt-signing doesn't weaken anything — there was no security being claimed beyond the unimplemented feature.)
- **completeness_governance:** D-055 ADR shape correct? DECISIONS.md row consistent with D-054 pattern? STATUS chain row included? `scripts/scp-consult` → `scp-cli consult` replacement complete in ADOPT-001 (only L197 found in pre-flight grep, but Codex executor should re-grep at run time in case more turn up)?

### Phase 2 stand-down

- Pre-flight grep at run time turns up MORE matches than the 18 lines pre-cited above → file SHIP-PROPOSAL with the new findings + HALT Phase 2 for operator review. Per `feedback_grep_production_before_planning.md`, do NOT silently extend the retraction scope without operator review.

### Files touched

1. `docs/OVERVIEW.md` — 8 line amendments + §6.3 future-scope expansion
2. `docs/adoption/mcp-adopter-contract.md` — 2 full section deletions + 1 line + 1 row in error-handling table
3. `docs/adoption/ADOPT-001-project-onboarding.md` — 1 line replacement
4. `docs/decisions/D-055-WP-SCP-026-narrative-reconciliation-2026-05-26.md` (NEW)
5. `docs/DECISIONS.md` — row + header bump
6. `STATUS.md` — chain row

### PR body shape — IMPORTANT

```markdown
## Summary
WP-SCP-026 slice 026D + D-055 ADR — narrative reconciliation...

## R1 evidence
- correctness: [...]
- safety_bypass: [...]
- completeness_governance: [...]

## Status: READY-FOR-OPERATOR-MERGE
**DO NOT MERGE AUTONOMOUSLY.** D-055 is ADR-class. Stays DRAFT until operator click-merges.
```

---

## Phase 3 — WP-SCP-026 026E (ADOPT-001 §13 MCP integration runbook) [2-3h, PARALLEL with Phase 1+2]

**Goal:** New §13 in ADOPT-001 documenting how adopters wire SCP MCP into their repo. Shape C pattern: stdio MCP, no receipt validation, `scp-cli` wrapper.

**CRITICAL pre-flight:** Per `feedback_verbatim_claim_diff_verification.md` — the canonical example in §13 references RI's `tool_scp_consult_rules`. BEFORE writing §13, read `~/Projects/ri-est-p-ws-2/.acc/mcp_server.py:298-338` (if accessible) to verify the example's accuracy against actual RI code. If the canonical example diverges from real RI code, the §13 documentation will mislead adopters — same class of bug as the PyNaCl snippet that D-054 retracted.

### Section outline

```
## 13. SCP MCP Integration (stdio; no receipt validation today)

### 13.1 Overview
- 8 MCP tools via stdio (`scp-mcp-server serve`)
- Shape C (D-054 / D-055 ratified 2026-05-25 / 2026-05-26): stdio only; receipt-signing + HTTP deferred to WP-SCP-027
- Two paths: (a) direct CLI invocation via `scp-cli`, (b) per-repo MCP server integration

### 13.2 Path (a): Direct CLI invocation (CI / build-time / scripts)
[scp-cli consult --domain example + expected JSON output]

### 13.3 Path (b): Per-repo MCP server integration (agent workflows)
#### 13.3.1 `.mcp.json` registration
[JSON example]
#### 13.3.2 Tool invocation in your per-repo MCP server
[Python example matching RI's actual pattern post-verification]

### 13.4 No receipt validation in v1
[Explicit statement; reference D-054 + D-055; forward-link to WP-SCP-027]

### 13.5 First-consumer pattern (RI canary)
[Reference 026C coordination doc + ACC's PLAN-EST-P §3.3]

### 13.6 Receipt validation as future-scope (WP-SCP-027)
[Forward-link only; how to signal demand]
```

### R-cycle (3-lens R1, doc-only)

- **correctness:** Examples actually work? `.mcp.json` shape valid? `scp-cli consult` invocation correct after Phase 1 ships?
- **safety_bypass:** Does the doc invite unsafe adopter patterns? (e.g., hot-loop calls? Untrusted invocation?)
- **completeness_governance:** All adoption paths covered? Cross-references to D-054 + D-055 + WP-SCP-027 correct? Forward-links not broken?

### Files touched

1. `docs/adoption/ADOPT-001-project-onboarding.md` — new §13 (~200-300 lines)
2. `STATUS.md` — chain row

### Phase 3 stand-down

- RI verification reveals canonical example diverges from real RI code → file SHIP-PROPOSAL; do NOT ship §13 with a wrong example (per `feedback_verbatim_claim_diff_verification.md` + the PyNaCl-snippet precedent).
- Phase 2 hits cure-worse trigger → stand down (same WP-class).

---

## Phase 4 — WP-SCP-026 026C (ACC RI canary coordination RFC) [30 min, AFTER Phase 1 merges]

**Goal:** Publish a coordination RFC on SCP repo documenting the handoff contract. Does NOT touch ACC repo (out of scope for SCP autonomous run).

**Blocker:** Phase 1 must merge first (the RFC references `scp-cli` as a real shipped binary).

### File

`docs/coordination/2026-05-26-WP-SCP-026-026C-ACC-RI-canary-handoff.md` (NEW)

### Content outline

- Contract: `scp-cli consult --domain <domain>` returns ConsultRulesResponse JSON
- Installation: `pip install standards-control-plane==1.4.0+` OR via staging Docker image
- ACC-side action: modify `ri-est-p-ws-2/.acc/mcp_server.py:298-338` `tool_scp_consult_rules` to call `scp-cli`
- Success criterion (026F observation, 4-week window): ≥1 real RI dispatch uses `tool_scp_consult_rules` + agent's output references ≥1 returned rule

### R-cycle (light 2-lens; coordination-only)

- **completeness:** Contract clearly specified? ACC-side action enumerated? Success criterion measurable?
- **governance:** RFC discipline correct (coordination-only doc; no cross-repo merge attempted from SCP-side)?

### Phase 4 stand-down

- Phase 1 didn't merge → defer.
- Operator hasn't merged Phase 1 yet (it's HOLD-FOR-OPERATOR) → defer Phase 4 to next session.

---

## Phase 5 — FUP closure bundles [6-8h, sequential]

### Bundle A — Scripts + validation [2-3h]

**Files (exact targets per pre-flight survey):**

1. **`FUP-WP-SCP-024-SCAFFOLDER-EMIT-PREFLIGHT-001`**
   - File: `scripts/scaffold-downstream.sh`
   - Target: at end of script (after `MANIFEST.json` is written), before the final `OK:` emit line
   - Add: function `_preflight_emitted_wrapper_repo_exists()` that:
     - greps the emitted `policy-check-wrapper.yml` for the `uses:` clause's `owner/name`
     - calls `gh api repos/$OWNER/$NAME` and asserts HTTP 200
     - On 404: emit warning + exit non-zero with clear message ("Generated wrapper references `<owner/name>` which does not exist or is private. Re-check the scaffolder template + your SCP repo rename history.")
   - ~15 lines bash

2. **`FUP-WP-SCP-024-SMOKE-TEST-BEFORE-FLIP-001`**
   - File: `scripts/enable-required-check.sh`
   - Target: in the pre-flight section near `BEFORE_JSON` capture; before any PUT to branch protection
   - Add: flag `--require-recent-green-wrapper-run` (default: ON for `--preserve-existing-contexts` mode; default: OFF for greenfield)
   - When ON: query `gh run list --workflow=policy-check-wrapper.yml --branch=$DEFAULT_BRANCH --limit=5 --json conclusion`; assert at least one conclusion=success
   - On no green runs: emit error + suggest "open a smoke-test PR + verify GREEN before flipping required-check"
   - Override flag `--skip-smoke-test-i-understand-this-blocks-main` for explicit bypass
   - ~25 lines bash
   - Also: extend `scripts/operator/onboard-024e-adopters.sh` to call the smoke-test PR + wait for GREEN before invoking step 4 (`enable-required-check.sh`). Should already do this per current script's design — verify and add an explicit assertion if missing.

3. **`TF-024D-001-ADOPT-001-12.7.16A-SECRETS-CEREMONY-ENUMERATE`**
   - File: `docs/adoption/ADOPT-001-project-onboarding.md` §12.7.16a
   - Target: existing §12.7.16a step listing
   - Amend: enumerate BOTH `SCP_FEDERATION_APP_ID` + `SCP_FEDERATION_APP_PRIVATE_KEY` secrets as a SINGLE ceremony step (currently listed separately; CT 024D ceremony required 2 iterations to get both set because the App-token-exchange error message only surfaces ONE missing secret per fire). ~20 lines markdown.
   - New file: `scripts/scp-verify-adopter-secrets.sh` — wraps `gh api repos/$OWNER/$NAME/actions/secrets` to assert both secrets present + non-empty. ~40 lines bash. Refuses CI.

### Bundle B — Documentation hygiene + BACKLOG sweep [1-2h]

1. **`SCP-073.sec`** — Create `SECURITY.md` at repo root. Template:
   - Reporting a vulnerability section (private disclosure via `security@brokapps.ai` placeholder; OR via GitHub security advisory feature on repo)
   - Embargo period (90 days typical for federation-primitive class)
   - GPG key reference (operator's existing key)
   - Scope: SCP-self + federation primitive only (not adopter repos)
   - ~50 lines markdown.

2. **BACKLOG.md closed-FUP sweep:**
   - Read `docs/BACKLOG.md` Phase 12 + the BACKLOG entries the FUP-inventory agent flagged as "already-closed" (see below)
   - For each FUP that's actually closed (verified via PR merge SHA or BACKLOG row history), update status from `open` to `CLOSED YYYY-MM-DD — <closure-PR/SHA/reason>`
   - Specifically verify + close:
     - `FUP-CLEANUP-2-001-SCP-SELF-WRAPPER-BUMP` — check whether SCP-self wrapper bump PR #160 already shipped this (it did; was the bump-to-d9cf525 → bump-to-80516a6 cycle)
     - Anything else flagged as closed but still showing open

### Bundle C — Defer + memo [<1h]

Move sample-size-1 + post-incident FUPs to a clearly-marked "Held / Defer-to-incident" subsection of BACKLOG.md Phase 12:
- `FUP-CLEANUP-2-002-SELFTEST-MODE-MIS-SET-ERROR-CLARITY`
- `FUP-CLEANUP-2-003-COMPOSITE-SELFTEST-MODE-SIMULATE-CROSS-REPO`
- `FT-PR139-L29-STATIC-VS-DYNAMIC-VERIFICATION-GAP`

Update `FUP-WP-SCP-024-RENOVATE-MARKER-ESTATE-WIDE-001` body with operator-decision-pending options enumerated (Renovate App org-wide / Dependabot per-repo / drop marker).

Add deferral table per Reviewer-1's recommendation:

| FUP ID | Reason | Blocker | Estimated gate date |
|---|---|---|---|
| FUP-024E-RECOMMENDER-DEFER-MANIFEST-STALE-001 | CT manifest refresh required | CT contract pipeline | post-026F observation |
| FUP-WP-SCP-024-SHOPIFY-APP-ONBOARDING-001 | App install ceremony | Operator decision | post-RI canary |
| FUP-WP-CT-GOV-002-PHANTOM-CITATION-PREFLIGHT-001 | CT PR #367 must merge first | CT base preflight ships | operator-paced |

### R-cycle (Bundles A/B/C, doc + script)

- **correctness:** Script changes work as specified? Tests pass? BACKLOG flips accurate?
- **safety_bypass:** Smoke-test-before-flip override flag clearly named + audit-logged? `scp-verify-adopter-secrets.sh` refuses CI?
- **completeness_governance:** All FUPs from inventory addressed (close / defer / advance)? Deferral table machine-readable?

### Files touched (across 3 PRs)

- Bundle A PR: `scripts/scaffold-downstream.sh`, `scripts/enable-required-check.sh`, `scripts/operator/onboard-024e-adopters.sh`, `scripts/scp-verify-adopter-secrets.sh` (NEW), `docs/adoption/ADOPT-001-project-onboarding.md`, `STATUS.md`
- Bundle B PR: `SECURITY.md` (NEW), `docs/BACKLOG.md`, `STATUS.md`
- Bundle C PR: `docs/BACKLOG.md`, `STATUS.md`

---

## Phase 6 — WP-SCP-026-Z CT-side prerequisites memo [1-2h]

**Goal:** Publish a clear, actionable memo documenting exactly what CT must publish before Z.2 (PR #167 dispatch) can fire. The autonomous run does NOT fire Z.2 (Tier 2 kernel-dangerous; operator-attended). It does NOT touch CT repo. It publishes a memo with:
- Concrete file paths CT needs to create
- Schema references (existing in SCP)
- Skeleton example bodies (YAML + JSON)
- Operator decision points
- Recommended sequencing

### File

`docs/coordination/2026-05-26-WP-SCP-026-Z-CT-prerequisites.md` (NEW)

### Content outline

**§1 What needs to exist on CT-side:**

1. **`control-tower/config/estate_repos.yaml`** — schema per `~/Projects/standards-control-plane/schemas/estate-repos.schema.json`. Example skeleton:
   ```yaml
   schema_version: "1.0.0"
   services:
     - service_id: "acc"
       acc_sa_uuid: "<ACC SA UUID — confirm with ACC team>"
       target_repo_app_id: null  # populated post-WS-EST-P-2 when first target is onboarded
   ```

2. **`control-tower/governance/published/cosignal-manifest.json`** — schema per `~/Projects/standards-control-plane/schemas/cosignal-manifest.schema.json`. Skeleton:
   ```json
   {
     "schema_version": "d-036-mcp-manifest-v1",
     "signed_at": "2026-MM-DDTHH:MM:SSZ",
     "key_id": "ct-mcp-manifest-key-1",
     "signature": "<base64-ed25519 over JCS-canonical entries[]>",
     "entries": []
   }
   ```

3. **CT cosignal Ed25519 PUBLIC key** — published to a stable URL that SCP can `gh api`-fetch + vendor at `vendor/ct-cosignal-public-key.pem`. Recommended: same `governance/published/` directory.

**§2 Operator decision points:**

- **D-1: Manifest signing-key custody.** Where does `ct-mcp-manifest-key-1` private key live? Operator's local machine (D-031 bus-factor-1 acknowledged)? File TF-D036-010 SOP for quarterly rotation.
- **D-2: ACC SA UUID value.** Confirmed with ACC team. Source: ACC's own identity store or `.acc/credentials/`.
- **D-3: Sequencing.** CT publishes first (1-2 days), THEN Z.2 fires? OR Z.2 fires first with "pending CT publication" caveat in PR body, with CT catching up immediately after?

**§3 Recommended path:**

CT publishes first (1-2 days operator-attended), THEN Z.2 Codex Tier 2 fire happens on SCP-side. Rationale: cleaner sequencing; Z.2 first-fire validates the rule on real artefacts; no temporal window where SCP-R-006 fires inconsistently.

**§4 Until Z.2 fires:**

SCP-R-006 stays inert (workflow inputs not materialised). Vacuous-pass on all adopters who set `acc-cross-repo-caller-scoped: false` (the default). Safe failure mode preserved.

### Files touched

- `docs/coordination/2026-05-26-WP-SCP-026-Z-CT-prerequisites.md` (NEW)
- `STATUS.md` — chain row

---

## Phase 7 — STATUS + memory + continuation prompt [1h]

- `STATUS.md`:
  - At-a-glance row updates for WP-SCP-026 (slices B/C/D/E shipped; F = 4-week observation begins post-026C)
  - Chain rows for every PR merged in this run
- `docs/OVERVIEW.md`:
  - §1.4 + §3.4 reflect post-026D narrative
  - Reference D-055 at appropriate cross-link
- `~/.claude/projects/-Users-amplience-Projects/memory/project_standards_control_plane.md`:
  - Refresh "Current state" + "Next moves"
  - Note: Z.2 awaiting CT prerequisites per memo
  - Note: 026F observation window begins (4 weeks from 026C merge)
- `docs/continuation-prompts/2026-05-26-evening-WP-SCP-026-shipped.md` (NEW):
  - Handoff for next operator session
  - Recommended next moves (Z.2 fire pending CT, Recommender resume pending CT manifest refresh, shopify-app onboarding queued)
  - Pre-authoring verification: re-read D-054 + D-055 (now ACCEPTED if merged) + WP-SCP-026 plan-doc v1.0 + this prompt's outcomes per `feedback_continuation_prompt_drift_vs_canonical_sources.md`

---

## Phase 8 — Final summary PR [<30 min]

Single bookkeeping PR if any STATUS / memory / continuation-prompt updates didn't go in earlier phases.

---

## Context-budget guidance

If session context budget gets tight (approaching 80% utilisation), checkpoint by:
1. Completing the in-flight PR (open + R1 evidence + push)
2. Writing STATUS.md chain row
3. Updating memory with current state
4. Posting a "session checkpoint" continuation prompt at `docs/continuation-prompts/2026-05-26-checkpoint-N.md` listing the exact next phase + open PRs
5. Stopping cleanly. Operator (or next autonomous run) re-arms via prompt + STATUS.

**Acceptable split points (no work-in-flight):**
- After Phase 1 merge (Phase 2/3/4/5/6/7/8 remain)
- After Phase 2/3 merge (Phase 4/5/6/7/8 remain)
- After Phase 5 Bundle A/B/C merge

**Unacceptable split points (work in flight):**
- Mid-R1 (mid-review cycle)
- Mid-PR-author (incomplete PR body / no R1 evidence)
- During Codex Tier 2 dispatch (not applicable in this run; no Tier 2 fires)

## Final notes

- **Z.2 fire is OUT OF SCOPE.** Do not touch `policies/SCP-R-006.rego` or the dispatch JSON beyond reading them for context. Phase 6 publishes memo only.
- **No cross-repo PRs.** Don't open PRs on `control-tower`, `mapp-pim`, `mf-intent-os`, `mapp-doc-agent`, `acc`, or any other repo. SCP-only.
- **ADR-class operator-attended-merge gates:** D-055 ADR (Phase 2). HOLD; READY-FOR-OPERATOR-MERGE tag.
- **Operator-attended-merge on CLI surface:** 026B (Phase 1). HOLD; READY-FOR-OPERATOR-MERGE tag.
- **All other PRs:** AUTONOMOUS merge per standard discipline (CI green + R1 evidence).
- **Halting conditions:** Cure-worse trigger (Phase 1/2/3 cross-stand-down); any phase pre-flight surfaces unexpected scope changes; context budget exceeds 80%.

## Success criterion for the run

- ✓ scp-cli ships (Phase 1 PR open + READY-FOR-OPERATOR-MERGE)
- ✓ D-055 ADR ships (Phase 2 PR open + READY-FOR-OPERATOR-MERGE)
- ✓ ADOPT-001 §13 shipped (Phase 3 PR merged)
- ✓ ACC RI handoff RFC shipped (Phase 4 PR merged, if Phase 1 has merged; else deferred)
- ✓ 3 FUP bundle PRs shipped (Phase 5)
- ✓ WP-SCP-026-Z prerequisites memo shipped (Phase 6 PR merged)
- ✓ STATUS + memory + continuation prompt updated (Phase 7 / 8)
- ✓ ≥6 FUPs closed via the bundle PRs
- ✓ ≥3 FUPs deferred-with-disposition

If you hit cure-worse trigger or any HALT condition, surface to operator with: open PR list + last phase completed + concrete next-step recommendation. Operator decides whether to resume autonomously or in a follow-up operator-attended session.

🤖 Generated 2026-05-26 by [Claude Code](https://claude.com/claude-code) — autonomous-run continuation prompt for SCP session
