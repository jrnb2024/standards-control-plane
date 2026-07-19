# GOV-009 — Proportionate Review Tiering

**Domain:** governance  
**Version:** 1.0.0  
**Status:** active  
**Severity default:** medium

Every code dispatch / work-package is classified into exactly one review tier,
computed from objective, diff-readable signals over its changed-file set, and the
required review depth is matched to that tier. The tier and the signals that produced
it are declared in the work package and recorded in the dispatch audit log. This
refines — it does not relax — the "3-agent adversarial R1 for all code changes"
minimum in GOV-004: the HEAVY tier keeps the full 3-lens panel unchanged, and the
LIGHT/STANDARD tiers are the only relaxations, available only to changes whose diff
is objectively low-risk.

## Tiers

- **LIGHT** — every changed file is test-only (`**/*.spec.ts`, `**/*.test.ts(x)`,
  `**/*_test.go`, `**/test_*.py`, `tests/**`, `e2e/**`, `**/__tests__/**`),
  docs-only (`docs/**`, `**/*.md`, `CLAUDE.md`, `AGENTS.md`), or non-required-CI
  config (informational / `continue-on-error` workflows, lockfiles, formatter/linter
  config); no high-risk glob is hit; the change is small and reversible.
  → **No R1 plan panel.** Evidence of correctness is the relevant CI gates green (the
  tests/build that actually exercise the change) plus one logged orchestrator
  self-review note citing the classifying signals.
- **STANDARD** — production code with bounded blast radius; none of the high-risk
  globs hit. → **1 R1 reviewer** on the most-relevant lens, plus full CI green.
- **HEAVY** — any high-risk glob hit (kernel / enforcement, auth PRODUCTION code,
  contract, DB migration, multi-service, or novel-algorithmic work declared in the
  WP). → **Full 3× parallel R1 panel** (correctness / safety_bypass /
  completeness_governance) plus adversarial fix-to-fixpoint, exactly as GOV-004 and
  the Delivery Governance Protocol mandate today. **UNCHANGED.**

*Production* here means any changed file that is not in the light set (test-only /
docs-only / non-required-CI config) — runtime source such as `services/**`, `pkg/**`,
`pylib/**`, `src/**`, and frontend `apps/**` / `packages/**` `src/**`. LIGHT requires
that EVERY changed file is in the light set; a single production file makes the change
at least STANDARD.

The high-risk globs that force HEAVY include: kernel / enforcement paths
(`.claude/**`, acc-hook binaries, `scripts/codex_dispatch.py`, `.scp/**`); auth
PRODUCTION code — not tests — (`pkg/platform/auth.go`, `**/middleware.{go,ts,tsx}`,
`**/login/**`, `**/auth/callback/**`, ct-auth-wrapper / Control-Tower integration
code); contracts (`api/openapi/**`, `api/schemas/**`, `pkg/platform/**`); DB
migrations (`**/migrations/**/*.up.sql`, `**/*.up.sql`); and any change touching
non-test code in ≥2 services.

## Signals

- a dispatch whose review depth was chosen without a declared `review_tier` and the diff-readable signals that produced it
- a LIGHT or STANDARD tier claimed for a change that hits any high-risk glob (kernel / auth production code / contract / migration / multi-service / novel-algorithmic)
- a test-only or docs-only change forced to a full 3-lens panel purely by topic proximity (e.g. "auth" in a filename) rather than by the risk of the diff
- a computed tier lowered by discretion (discretion may only raise a tier, never lower it), or any review skipped below the computed tier
- a mixed change set (production code alongside test/doc files) classified below STANDARD

## Guardrails

1. **Deterministic + logged.** The tier is a pure function of the signals; the WP
   declares `review_tier` and the signal list; the dispatcher records it. Choosing
   LIGHT is auditable after the fact, never a discretionary vibe.
2. **Highest-risk signal wins.** A one-line change to `pkg/platform/auth.go` is HEAVY
   irrespective of diff size.
3. **Test files are classified by file-type, not by the subsystem they exercise.** A
   change confined to `auth-flow.spec.ts` / `*_test.go` for an auth or kernel flow is
   *test-only*, hence LIGHT-eligible — it does not inherit the HEAVY tier of the code
   it tests.
4. **Mixed sets up-tier.** LIGHT requires EVERY file in the light set; a single
   production file lifts the change to at least STANDARD.
5. **Discretion moves only UP, never down.** An orchestrator may always elect a
   heavier tier than computed; it may never elect a lighter one. Skipping review
   below the computed tier remains forbidden (GOV-004; the estate no-corner-cutting
   standard).

## Rationale

GOV-004 mandates a 3-agent adversarial R1 review for all code changes, with only a
narrow, undefined "trivial or mechanical single-file edits" exception. In practice
that exception is applied by feel, and the auth-surface plan-review trigger
(ADR-0003 / `feedback_orchestrator_auth_surface_plan_review_default`) keys on topic
proximity rather than actual change-risk. The 2026-07-18 motivating incident: a
~10-line, test-only fix to `frontend/tests/uat/auth-flow.spec.ts` — on a
`continue-on-error` CI job that cannot block a merge — drew a full 3-lens R1 panel
plus a fourth fix-forward reviewer (~630k tokens) purely because "auth" appeared in
the filename.

This rule replaces the feel-based exception with a deterministic, auditable
classification: review depth is routed to change-risk read off `git diff
--name-only` plus the WP, so trivially-safe diffs stop drawing panel-grade review
while every genuinely risky change keeps it. It is the review-side complement of
GOV-004's four-tier *executor* dispatch (which tiers the executor model by
implementation complexity): GOV-009 tiers *review depth* by change risk. The
guardrails make the relaxation safe — highest-risk-wins, mixed-sets-up-tier, and
discretion-only-up ensure the tier can only ever be too heavy, never too light, and
the HEAVY tier is preserved byte-for-byte.

Phase-2 automation (a classifier in `scripts/codex_dispatch.py` — ACC repo — that
computes the tier from the diff and writes `review_tier` into the dispatch record) is
deferred and tracked separately (`FUP-D068-REVIEW-TIER-CLASSIFIER-001`); until it
lands, the tier is orchestrator-declared and logged. This rule is advisory
(consult-plane) and carries no Rego enforcement of its own — the same shape as
GOV-001…GOV-005.
