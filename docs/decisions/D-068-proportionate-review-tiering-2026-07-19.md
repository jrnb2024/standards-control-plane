# D-068 — Accept PROP-015 as GOV-009 (Proportionate Review Tiering)

**Date:** 2026-07-19 · **Status:** ACCEPTED · **Refines:** GOV-004 (four-tier build method) · **Reserves nothing; consumes nothing.**

> **Numbering note.** Filed as **D-068** — the next free number. D-067 is consumed
> (register the conformance-tcb anti-gaming rules, 2026-07-12); D-059 (WP-SCP-028
> deny-promote) and D-060 (WP-SCP-030 observation) remain reserved and are NOT
> touched here. Renumber on merge only if a reservation changed meanwhile.

## Context

GOV-004 mandates a 3-agent adversarial R1 review for *all* code changes, with only a
narrow, undefined "trivial or mechanical single-file edits" exception. The exception
is applied by feel, and the auth-surface plan-review trigger (ADR-0003 /
`feedback_orchestrator_auth_surface_plan_review_default`) keys on topic proximity,
not on the actual risk of the diff.

**Motivating incident (2026-07-18).** A ~10-line, test-only fix to
`frontend/tests/uat/auth-flow.spec.ts` — on a `continue-on-error` CI job that cannot
block a merge — drew a full 3-lens R1 plan-review panel plus a 4th fix-forward
reviewer (~630k tokens, 3×~15 min wall-clock) purely because "auth" appeared in the
filename. Roughly a working day was spent reviewing five chip-sized changes.

Surfaced to SCP via `scp-standards.propose` as **PROP-015** (authored from a mapp-pim
session, 2026-07-18, `adjudication_status: queued_no_adjudicator`). Rule-only;
phase-2 automation explicitly deferred. Operator (jimbrooke) reviewed and approved
the rule content and authorised ratification.

## Decision

**Accept PROP-015 and register it as `GOV-009` (Proportionate Review Tiering) in the
`governance` domain — advisory (consult-plane), `severity_default: medium`,
`status: active`, no Rego enforcement of its own** (the same shape as GOV-001…GOV-005,
and the shape GOV-004 already has as a process rule).

Every code dispatch is classified into exactly one review tier from objective,
diff-readable signals:

- **LIGHT** — all changed files test-only / docs-only / non-required-CI config; no
  high-risk glob; small + reversible → **no R1 panel**; correctness evidence = the CI
  gates that exercise the change green + one logged orchestrator self-review note.
- **STANDARD** — production code (any file not in the light set), bounded blast
  radius, no high-risk glob → **1 R1 reviewer** + full CI green.
- **HEAVY** — any high-risk glob hit (kernel / auth PRODUCTION code / contract /
  migration / multi-service / novel-algorithmic) → **full 3× parallel R1 panel** +
  adversarial fix-to-fixpoint. **UNCHANGED from GOV-004 / today.**

Guardrails (verbatim intent from the proposal): deterministic + logged; highest-risk
signal wins; test files classed by file-type not the subsystem they exercise; mixed
sets up-tier; discretion moves only UP, never down.

This **refines** GOV-004's blanket "3-agent R1 for all code changes" — it does not
weaken HEAVY. The only relaxations are LIGHT (CI + logged self-review) and STANDARD
(1 reviewer), and only for changes whose diff is objectively low-risk.

## Scope of this change

- New rule prose: `standards/governance/rules/GOV-009-proportionate-review-tiering.md`.
- Registry entry added to `standards/governance/index.json`; domain version
  bumped 1.2.0 → 1.3.0. No `applies_to` in the entry (schema is
  `additionalProperties:false`, WP-SCP-037 correction); GOV-009 inherits the
  `governance` domain firing-glob fallback defined in
  `src/standards_control_plane/applies_to.py`
  (`docs/**/*.md`, `docs/DECISIONS.md`, `docs/STATUS.md`), the same as GOV-001…008.
  The rule markdown and the index entry land in the **same commit** — a registry
  entry whose `path` file is absent makes `registry.load_registry()` raise and breaks
  `consult_rules` for *every* domain, not just governance.
- One non-substantive cross-reference blockquote added to
  `standards/governance/rules/GOV-004-four-tier-build-method.md` pointing to GOV-009.
  GOV-004's index summary and signals are UNCHANGED (no change to the consult /
  `scp://rules/registry` summary surface); only the `scp://rule/GOV-004` rule-card
  body gains the additive pointer.
- PROP-015 retired: `adjudication_status: accepted`, `rule_id: GOV-009`,
  `decision_ref: D-068` (the `proposal_metadata` envelope comment — hash +
  signing_key_id — is preserved).

## Honesty (load-bearing)

- **The rule leads; mechanical enforcement follows.** SCP's own `r1-evidence-check.yml`
  CI gate still requires a full 3-lens `## R1 evidence` block on *every* PR to this
  repo — it does not read `review_tier`. Until the phase-2 classifier lands, an interim
  LIGHT/STANDARD SCP PR satisfies that gate via the `## Protocol deviation` escape
  hatch (the gate accepts a documented deviation block with an `FUP-/TF-/D-NNN`
  reference), not by skipping evidence. So GOV-009 (the estate *standard*) permits
  LIGHT-tier self-review while SCP's *own CI gate* still demands one of the two blocks.
  The gap is deliberate and temporary, exactly as GOV-006/007/008 shipped DORMANT
  ahead of their materialiser.
- **Same tension in `CLAUDE.md`.** The estate onboarding contract carries an absolute
  cardinal rule — "NEVER shortcut adversarial review. 3 parallel lenses minimum for
  code/plan/strategic reviews." GOV-009 refines that minimum **for code dispatches
  only**; it does NOT tier *plan* or *strategic* reviews, which stay at 3 lenses.
  This PR does not edit the `CLAUDE.md` kernel block (that is a governed D-058 /
  SCP-R-030 surface, out of scope for a rule-only adjudication); aligning the
  `CLAUDE.md` line and the `r1-evidence-check` gate to read `review_tier` is part of
  the phase-2 follow-up below.
- **Phase-2 automation is deferred and NOT in this change** —
  `FUP-D068-REVIEW-TIER-CLASSIFIER-001`. A classifier that computes the tier from the
  diff and writes `review_tier` into the dispatch record lives in
  `scripts/codex_dispatch.py` **(ACC repo — not this repo; SCP has no copy)**. It must
  coordinate with the in-flight "acc dispatcher false-green on blocked runs" work and
  the open acc dispatcher false-positive FUPs, which touch the same file. Do not build
  it here.
- **Reflexive check.** Adjudicating GOV-009 is itself a governance-rule change → HEAVY
  under GOV-009's own tiering → this PR correctly carries a full 3-lens R1 panel.
- **Proposed by the fleet, adjudicated by the operator.** The content ruling is the
  operator's; this session performed the process (author prose + registry + decision +
  independent 3-lens R1), it did not self-certify the policy.

## Consequences

- After merge, GOV-009 is served on both planes: the `consult_rules` **tool** reads
  the working-tree registry via `registry.load_registry()`; the `scp://rules/registry`
  **resource** builds from committed state via `git show HEAD`
  (`mcp_server/resources.py::_build_registry`). On `main` the working tree equals HEAD,
  so both serve GOV-009 (verify locally after a `git pull`; reconnect the MCP server if
  it has cached an older snapshot).
- `audit_changed` / `resolve_domain` surface GOV-009 as an applicable governance rule
  on `docs/**/*.md` / `docs/DECISIONS.md` / `docs/STATUS.md` changes (domain fallback),
  the same as its GOV siblings.
- No merge-gate behaviour changes: GOV-009 has no Rego, adds nothing to
  `WARN_BASELINE_RULES`, and does not alter `policy-check.yml`.
