<!-- canonical:acc-hook-onboarding v1 -->
<!-- canonical:estate-context-bootstrap v1 -->

# ⚠️ This repo runs the acc-hook (PreToolUse enforcement) — read before any write

This repo has the **ACC kernel hook live** (`.claude/settings.json` → `PreToolUse` matcher on `Write|Edit|Bash|NotebookEdit`, binary at `.claude/hooks/dist/<platform>/acc-hook`). It **HARD-BLOCKS** source writes that aren't covered by an active dispatch. This is **not optional guidance** — it will deny your tool calls and you will discover it the hard way if you skip this section.

> This preamble is the canonical hooked-repo onboarding block (D-058 / WP-SCP-030). ACC owns the hook + authors this contract; SCP gates that every hooked repo's CLAUDE.md carries it. The HTML marker on line 1 is what the SCP-R-030 conformance rule greps for. **Do not delete it.**

## Always-allowed — write these freely, no ceremony

`docs/**` · `CLAUDE.md` · `AGENTS.md` · `.acc/work-packages/**` · `.acc/codex-probes/**` · `.acc/claude-probes/**` · `~/.claude/projects/**/memory/*.md`

These are in the hook's `alwaysAllowed()` set. Documentation, memory, and work-package writes never trip the hook.

## Source writes are GATED — satisfy the hook first

Gated paths (denied without an active dispatch): `src/**` · `tests/**` · `policies/**` · `scripts/**` · `schemas/**` · `pyproject.toml` · root `STATUS.md` · `.claude/**`. (Bash redirections are denied **regardless** of dispatch — use the Write tool or rewrite the command.)

**SCP's canonical self-build pattern is Pattern 3** (Claude Code autonomous sessions), governed by a **session-start dispatch** per D-057. Before a session that will write source:

1. The **operator** runs, from a normal terminal (outside the session — the hook only fires on Claude-mediated calls):
   ```bash
   cd ~/Projects/standards-control-plane
   scripts/operator/scp-pattern3-dispatch.sh "<specific-source-path>" ["<another>" ...]
   ```
   This writes `.acc/active-dispatch.json` declaring the session's scope. The script refuses blanket globs, refuses any glob covering `.acc/active-dispatch.json` itself (self-escalation guard), refuses CI, and stamps a fresh 4h TTL.
2. Run the session. Writes inside the declared `scope_boundary` (and in always-allowed paths) pass + are HMAC-logged to `.acc/hook-audit-log/`.
3. At session end, the operator tears down: `scripts/operator/scp-pattern3-dispatch.sh --teardown`.

Full ceremony: `docs/operator-runbooks/scp-pattern3-dispatch.md`. Decision: `docs/decisions/D-057-scp-self-orchestrate-pattern-2026-05-29.md`.

## If you trip the hook

**STOP. Tell the operator the one ceremony step above. Do NOT offer to disable the hook.** Disabling enforcement to get unblocked is **forbidden estate-wide** (D-057): sessions declare scope, they do not disable enforcement. A denial means either (a) the path is outside the declared scope — ask the operator to re-bootstrap with extended scope, or (b) no dispatch was seeded — ask the operator to run the bootstrap. Never `cp`/`mv` the hook aside.

---

# Standards Control Plane (SCP) — what this is

SCP is the estate's **policy federation primitive**: it authors policy as OPA Rego, ships it as a reusable GitHub Actions workflow (`policy-check.yml`), and enforces it at the merge gate as a required status check across cohort adopter repos. Per **D-058** it is evolving from a structural-hygiene linter into a **canonical-architecture conformance oracle**, one domain at a time — SCP gates LINKAGE (does adopter code reference the canonical correctly?), never VALUES; domain authorities author canonicals, SCP gates conformance.

## Cardinal rules (estate-wide)

- **NEVER commit directly to main.** PR workflow, no exceptions including docs/hot-fixes.
- **NEVER silently descope.** Process all items; ask first.
- **NEVER shortcut adversarial review.** 3 parallel lenses minimum for code/plan/strategic reviews (correctness / safety_bypass / completeness_governance).
- **NEVER disable the acc-hook** to get unblocked (see above; D-057).
- **Always create bash scripts** for human-run commands (terminal copy-paste causes line-break errors); put them in `scripts/` + tell the operator to run them.
- **Verify branch + staged set before commit** (`git branch --show-current` + `git status --short`); stage explicitly, never `git add -A` / `git commit -am` over a dirty tree.

## Where things live

| Topic | Source |
|---|---|
| Strategic direction | `docs/decisions/D-058-scp-canonical-conformance-strategy-2026-05-29.md` |
| Decision history | `docs/DECISIONS.md` (single table) + `docs/decisions/D-*.md` (standalone ADRs) |
| Integrated reference | `docs/OVERVIEW.md` |
| Operational state | `STATUS.md` (header + bottom chain entries) |
| Backlog / roadmap | `docs/BACKLOG.md` (Phase 13 = canonical-conformance roadmap) |
| Adoption procedure | `docs/adoption/ADOPT-001-project-onboarding.md` |
| Self-build ceremony | `docs/operator-runbooks/scp-pattern3-dispatch.md` (D-057) |
| Rule library | `policies/SCP-R-*.rego` |
| Adversarial review evidence | `docs/reviews/<WP-or-D>/...` |

## How to run

```bash
opa test policies/ tests/policies/        # rule tests
regal lint policies/                       # Rego lint
opa fmt --diff policies/                   # format check
```

Adopter cohort (LIVE): mapp-pim · control-tower · mapp-doc-agent. SCP self-gates via its own `policy-check-wrapper.yml`.
