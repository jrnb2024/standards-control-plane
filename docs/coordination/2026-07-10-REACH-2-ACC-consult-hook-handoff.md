# REACH-2 — ACC consult-hook handoff (2026-07-10)

**From:** SCP (WP-SCP-037 close-out). **To:** ACC (hook authority, D-058). **Type:** concrete handoff
— SCP proposes + supplies `scp-cli consult` + the gating rule; **ACC authors/ratifies the hook** (it
owns the UserPromptSubmit injector canonical; D-058 forbids SCP authoring in ACC's repo).

## Why now (the precondition just cleared)

REACH-2 was blocked on a real chicken-and-egg: a consult-injection hook is only worth its latency if
`consult_rules` returns something load-bearing. As of WP-SCP-037 the estate's cross-cutting standards
are **authored + live + consult-served**:

- **ARCH-006 / SCP-R-013** ontology-canonical-consumption (link to fashion-ontology-service, don't
  embed a divergent copy).
- **SVC-ADOPT-001** estate app-registration (9 touchpoints).
- **SVC-005** estate networking (the brokapps tunnel recipe).
- **ADOPT-001 §12.7.0** the sequential onboarding ceremony.

…on top of the pre-existing ARCH-005 (events), SVC-001..004, GOV-001..005, SCP-R-009/010/011 (auth),
SCP-R-030 (hooked-repo onboarding). A dev touching `services.yml`, an ontology consumer, or a new app
now gets a genuinely useful rule set from `resolve_domain → consult_rules`. That's the content the
hook injects. **REACH-1 is also essentially done: 13 enforced adopters** — so the gated cohort that
would benefit from write-time consult is large.

## R2.1 — the one-line consult instruction (cheap, do first)

Add a consult line to ACC's hooked-repo onboarding canonical (`acc/docs/guides/hooked-repo-onboarding-preamble.md`
or wherever the SCP-R-030-greppable block lives). Proposed text:

> **Before non-trivial work, consult SCP:** run `scp-cli consult --changed <files>` (or MCP
> `resolve_domain({changed_files}) → consult_rules({domain}) → audit_changed({diff})`). Treat returned
> rules as normative; a waiver is the only way around one. This reaches CI/Codex/non-Claude agents
> that read the repo's `CLAUDE.md`/`AGENTS.md` (they do NOT see `~/.claude/CLAUDE.md`).

SCP-R-030 already gates the *presence* of the onboarding block (marker grep); ACC ratifies the added
line since it owns the canonical. This is the line that reaches non-interactive agents — the hook (R2.2)
reaches interactive Claude sessions.

## R2.2 — the consult-injection hook (the mechanism; ACC authors)

**Verify-first:** read the deployed `governance_context_injector.sh` (Recommender / FLA) and decide
extend-vs-new. Build on the **UserPromptSubmit** pattern (scopes to changed files; SessionStart is
once/coarser).

Design SCP supplies:
- **Trigger:** UserPromptSubmit, gated to *first prompt of a session* OR *changed-files present* — do
  NOT run `scp-cli consult` on every prompt (~500ms budget).
- **Command:** `scp-cli consult --changed $(git diff --name-only ...)` → the JSON `applicable_rules` +
  `guidance`. `scp-cli` exists in SCP's `.venv-mcp/bin/scp-cli` and via the MCP server.
- **Injection:** prepend the returned rule IDs + one-line reasons to the session context (the
  governance_context_injector output shape).
- **Pilot:** RI (mapp-returns-intelligence) — one brownfield repo proves the hook before any estate
  fan-out, exactly as R1 piloted the gate.

## R2.3 — measurement (close the "zero consumers" gap honestly)

The acc-hook already HMAC-logs to `.acc/hook-audit-log/`. Add a consult-invocation signal (the
`scp-cli consult` / MCP call leaves a trace) + a per-repo "consulted in last N PRs?" readout so we can
*prove* consultation is happening rather than assert it. Without this, REACH-2's success is unmeasured.

## Division of labour (D-058)

| Who | What |
|---|---|
| **SCP** | This handoff + a `propose()` recording the REACH-2 intent; `scp-cli consult` (exists); the SCP-R-030 gate on the onboarding block (exists). |
| **ACC** | Authors + ratifies the R2.1 canonical line; authors the R2.2 UserPromptSubmit hook; wires R2.3 measurement. Pilots on RI. |

SCP does **not** author anything in ACC's repo (D-058: ACC owns the orchestrator/hook canonical). This
doc + the `propose()` are the SCP-side asks; ACC picks them up.

## Acceptance

- R2.1: the consult line present in ACC's onboarding canonical (SCP-R-030 marker still green).
- R2.2: on a changed-`services.yml` PR in the RI pilot, the session context shows the injected
  SVC-001/002/003 (+ ARCH-006 if ontology files change) rule IDs before the dev writes code.
- R2.3: `.acc/hook-audit-log/` (or an equivalent) shows a consult trace per PR; a per-repo readout exists.

## References

- `docs/reviews/SCP-REACH-PLAN-2026-06-29.md` §REACH-2 (the original scoping).
- `docs/reviews/SCP-REACH-CONTINUATION-2026-06-29.md`.
- D-058 (SCP proposes+gates, domain authorities/ACC author).
- The WP-SCP-030 precedent: `docs/coordination/2026-05-30-WP-SCP-030-ACC-hooked-repo-preamble-handoff.md`
  (the last ACC-authored-canonical / SCP-gates handoff of this exact shape).
