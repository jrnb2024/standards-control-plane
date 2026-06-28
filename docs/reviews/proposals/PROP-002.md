---
adjudication_status: accepted
accepted_as: GOV-004
accepted_at: 2026-06-28
accepted_note: adjudicated into standards/<domain>/rules/GOV-004-*.md + index.json; live via consult_rules
expected_review_date: null
queued_at: 2026-06-27T22:31:43Z
---
> NOTE: WP-SCP-022-proposal-queue adjudication workflow is not yet live;
> proposals queue until adjudication ships. Status updates via
> GitHub issue on this branch (proposals/PROP-002). See
> docs/plans/WP-SCP-022-implementation-programme-plan.md §12.

<!-- proposal_metadata: {"affected_repos":["jrnb2024/acc","jrnb2024/kg-studio","jrnb2024/mapp-pim","jrnb2024/control-tower","jrnb2024/mapp-returns-intelligence","jrnb2024/mapp-size-allocation","jrnb2024/standards-control-plane"],"caller_id":"stdio:30251:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server","mcp_origin":true,"proposal_hash":"68c6247b14103df2e922e6c530ceabbe60b7dd5adb7b7abd6191e0b785538193","rule_id":null,"signing_key_id":"428dfee16bc954ad"} -->

# PROP-002: GOV-004 (candidate): Substantial builds use the four-tier orchestrator dispatch (TDD + adversarial reviews) as the standard method

## Proposal Envelope
- mcp_origin: true
- caller_id: stdio:30251:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server
- signing_key_id: 428dfee16bc954ad

## Affected Repositories
- jrnb2024/acc
- jrnb2024/kg-studio
- jrnb2024/mapp-pim
- jrnb2024/control-tower
- jrnb2024/mapp-returns-intelligence
- jrnb2024/mapp-size-allocation
- jrnb2024/standards-control-plane

## Rule Context
null

## Proposal Body
## GOV-004 (candidate) — Four-tier orchestrator dispatch is the standard build method

**Status:** proposed (new rule, `governance` domain). Elevates the estate-standing build method (ACC Phase T, standard estate-wide since 2026-04-22) into a consultable SCP standard so every Claude Code session adopts it by default instead of re-deriving how to build. Complements GOV-002 (planning artefacts) and GOV-003 (review evidence).

**Standard.** Implementation-heavy and review-heavy work is NOT hand-written by the Opus session. It is distributed across tiers, test-first, with mandatory parallel adversarial review:
- **Opus (orchestrator, Tier 1):** plan + AC authoring, spec adjudication, security-bug diagnosis from reviewer output, scope decisions, kernel-dangerous review. Opus orchestrates and adjudicates; it does not bulk-write implementation code.
- **Codex executor (Tier 2 `gpt-5.4 xhigh` for kernel-dangerous/auth/migrations/novel; Tier 3 `gpt-5.4-mini` DEFAULT for routine implementation; Tier 4 for boilerplate/scaffolding):** writes the implementation in an ISOLATED git worktree per dispatch (one worktree per job; never the main tree).
- **TDD:** the operator authors the RED test BEFORE dispatch; the dispatch must make it pass without weakening it.
- **3× Sonnet adversarial review (`claude -p`, parallel):** every substantive change gets a 3-agent R1 adversarial review (correctness / safety_bypass / completeness_governance lenses). Reviewers run in parallel, not sequentially. Findings are verified against the code before action (reviewers over-flag).
- **Cadence per work package:** operator RED test → prove red vs the real datastore → dispatch → OPERATOR verifies the full suite vs a live/throwaway datastore (sandboxes skip integration) → adversarial diff review → apply fixes → PR → CI → squash-merge → fast-forward main. Keep the byte-exact / golden guardrails green throughout.

**Deviation = note-and-justify.** Hand-writing implementation where a Codex dispatch would do, or running review agents sequentially instead of 3× parallel, is an escalation decision: note it inline and justify (per `feedback_four_tier_dispatch.md`).

**Canonical runbooks (do NOT duplicate here — consult them):** ACC repo `docs/guides/four-tier-dispatch-pattern.md` (design), `four-tier-dispatch-portable-adoption.md` (per-repo adoption), `four-tier-dispatch-process-governance.md`, `docs/guides/codex-dispatch-runbook.md`; scripts `scripts/codex_dispatch.py` + `claude_dispatch.py`; schemas `schemas/codex_work_package.schema.json` + `sonnet_review_result.schema.json`. Auth: subscription OAuth only (Claude Max + ChatGPT Max), no API tokens.

**Mandatory security pre-flight before any dispatch (briefing §0):** never `scope_boundary: ["*"]`/`["**"]` (fnmatch `*` crosses `/` and disables the gate); treat `spec_paths` + `verify_commands` as trusted/shell-injectable (literal allowlist); scrub subprocess env to an `env={}` whitelist (estate shells carry tokens/creds); `--sandbox workspace-write` is must-not-relax; validate path traversal; `.gitignore` the dispatch logs. Each adopter repo needs its own acc-kernel install to be a dispatch target (the hook-integrity check is per-`--cwd`).

**Signals (audit).**
- a substantive code change merged with no parallel 3-agent adversarial-review evidence (cf. GOV-003)
- review agents run sequentially rather than 3× parallel on a governance-heavy change
- a behaviour change merged with no operator-authored RED test / TDD trail
- a dispatch with `scope_boundary` of `*` / `**`, or `--sandbox danger-full-access`
- bulk implementation hand-written by the Opus session where a Codex Tier-3 dispatch would do, with no note-and-justify deviation record

**applies_to:** `docs/plans/**/*.md`, `docs/reviews/**/*.md`, `.acc/**`, `scripts/codex_dispatch*.py`   **severity_default:** medium (high for the security-pre-flight invariants)   **scope:** all   **exceptions:** trivial/mechanical single-file edits; conversational turns.
