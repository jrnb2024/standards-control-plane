# GOV-004 — Four-Tier Orchestrator Dispatch Is the Standard Build Method

**Domain:** governance  
**Version:** 1.0.0  
**Status:** active  
**Severity default:** medium

Implementation-heavy and review-heavy work is not hand-written by the Opus
session. It is distributed across tiers, written test-first, and put through
mandatory parallel adversarial review. Opus orchestrates and adjudicates; Codex
executes in an isolated git worktree per dispatch; three Sonnet reviewers run an
adversarial review in parallel; the operator verifies against a live datastore.
Deviation from this method is an escalation decision: note it inline and justify.

> **Refined by GOV-009 (Proportionate Review Tiering).** The "3-agent adversarial R1
> for all code changes" minimum is routed to a change-risk tier — LIGHT / STANDARD /
> HEAVY. The HEAVY tier (kernel / auth PRODUCTION code / contract / migration /
> multi-service / novel-algorithmic) keeps the full 3-lens panel unchanged; GOV-009
> relaxes only objectively low-risk diffs. See `rules/GOV-009-proportionate-review-tiering.md`.

This standard codifies the estate-standing four-tier dispatch pattern (standard
estate-wide since 2026-04-22). It complements GOV-002 (planning artefacts) and
GOV-003 (review evidence).

## Signals

- a substantive code change merged with no parallel 3-agent adversarial-review evidence
- review agents run sequentially rather than three in parallel on a governance-heavy change
- a behaviour change merged with no operator-authored RED test / TDD trail
- a Codex dispatch with `scope_boundary` of `*` / `**`, or `--sandbox danger-full-access`
- bulk implementation hand-written by the Opus session where a Codex Tier-3 dispatch would do, with no note-and-justify deviation record

## Rationale

Opus-tier quota is scarce and most implementation and first-pass review work does
not require Opus judgment. Distributing it preserves Opus for irreducible synthesis
and adjudication while the pattern natively enforces the 3-agent adversarial-review
cardinal rule via parallel Sonnet dispatch and the TDD discipline via an
operator-authored RED test. The method strengthens governance compliance rather
than weakening it.

The canonical runbooks, scripts, schemas, and the mandatory pre-dispatch security
caveats are maintained in the ACC repo (`docs/guides/four-tier-dispatch-*.md`,
`scripts/codex_dispatch.py`, `schemas/codex_work_package.schema.json`); consult
them rather than duplicating here. Auth is subscription OAuth only (Claude Max +
ChatGPT Max), no API tokens. Each adopter repo needs its own acc-kernel install to
be a dispatch target (the hook-integrity check is per-`--cwd`).
