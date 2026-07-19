---
adjudication_status: accepted
rule_id: GOV-009
decision_ref: D-068
accepted_at: 2026-07-19
expected_review_date: null
queued_at: 2026-07-18T21:18:29Z
---
> ADJUDICATED 2026-07-19: ACCEPTED as GOV-009 (decision D-068), via the interim
> manual runbook docs/operator-runbooks/adjudicate-proposal.md (the automated
> WP-SCP-022 queue was not live at intake). Live rule prose:
> standards/governance/rules/GOV-009-proportionate-review-tiering.md;
> consult_rules({domain:"governance"}) serves it after merge.

<!-- proposal_metadata: {"affected_repos":["mapp-pim","acc","control-tower","standards-control-plane","Recommender","agentic_commerce_pac","mapp-returns-intelligence","mapp-size-allocation"],"caller_id":"stdio:77607:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server","mcp_origin":true,"proposal_hash":"9360a8f785560e44387772b57ab74ce2f99e0c101cce3edd6859ff685ae1ac20","rule_id":null,"signing_key_id":"428dfee16bc954ad"} -->

# PROP-015: Proportionate Review Tiering — route R1 review depth by change-risk tier (estate-wide)

## Proposal Envelope
- mcp_origin: true
- caller_id: stdio:77607:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server
- signing_key_id: 428dfee16bc954ad

## Affected Repositories
- mapp-pim
- acc
- control-tower
- standards-control-plane
- Recommender
- agentic_commerce_pac
- mapp-returns-intelligence
- mapp-size-allocation

## Rule Context
null

## Proposal Body
# Proportionate Review Tiering

## Status
PROPOSED 2026-07-18. Operator (jimbrooke) authorized immediate working-heuristic application in mapp-pim pending ratification. Submitted estate-wide, rule-only (automation deferred to phase 2).

## Problem
The Delivery Governance Protocol (§2) mandates a 3-agent adversarial R1 review minimum for ALL code changes, with no classification by risk. This over-provisions review for trivial changes, and the current auth-surface plan-review trigger (feedback_orchestrator_auth_surface_plan_review_default / ADR-0003) keys on topic proximity rather than actual risk.

**Incident (2026-07-18):** a ~10-line, test-only fix to `frontend/tests/uat/auth-flow.spec.ts` — on a CI job that is `continue-on-error` (informational, cannot block merge) — drew a full 3-lens R1 plan-review panel plus a 4th fix-forward reviewer (~630k tokens, 3×~15 min wall-clock), because "auth" appeared in the filename. Roughly one working day was spent reviewing five chip-sized changes.

## Rule
Every dispatch / work-package is classified into exactly one review tier, computed from objective, diff-readable signals over its changed-file set. The tier determines the required review depth. The classification and the signals that produced it are declared in the work package and recorded in the dispatch audit log.

### Signals (read off `git diff --name-only` + the WP; no subjective judgment)
- **Path class of each changed file:**
  - *test-only*: `**/*.spec.ts`, `**/*.test.ts(x)`, `**/*_test.go`, `**/test_*.py`, `tests/**`, `e2e/**`, `**/__tests__/**`
  - *docs-only*: `docs/**`, `**/*.md`, `CLAUDE.md`, `AGENTS.md`
  - *non-required-CI/config*: workflow files whose jobs are `continue-on-error`/informational, lockfiles, formatter/linter config
  - *production*: any other source under `services/**`, `pkg/**`, `pylib/**`, frontend `apps/**|packages/**` `src/**`
- **HIGH-RISK globs (any single hit forces HEAVY):**
  - kernel / enforcement: `.claude/**`, acc-hook binaries, `scripts/codex_dispatch.py`, SCP rule configs (`.scp/**`)
  - auth PRODUCTION code (not tests): `pkg/platform/auth.go`, `**/middleware.{go,ts,tsx}`, `**/login/**`, `**/auth/callback/**` (`.go`/`.ts`/`.tsx`), ct-auth-wrapper / CT integration code
  - contracts: `api/openapi/**`, `api/schemas/**`, `pkg/platform/**`
  - DB migrations: `**/migrations/**/*.up.sql`, `**/*.up.sql`
  - blast radius: touches non-test code in ≥2 services, OR novel algorithmic work declared in the WP
- **CI blast radius:** whether any changed file feeds a REQUIRED status check, or only informational/continue-on-error jobs.
- **Reversibility & size:** additive/test/doc vs destructive/stateful; file count.

### Tier → required review depth
- **LIGHT** — ALL changed files are test-only / docs-only / non-required-CI config; NO high-risk glob hit; change is small and reversible. → No R1 plan panel. Evidence of correctness = the relevant CI gates green (the tests/build that actually exercise the change) + one logged orchestrator self-review note citing the classifying signals.
- **STANDARD** — production code with bounded blast radius; none of the HIGH-RISK globs. → 1 R1 reviewer (most-relevant lens) + full CI green.
- **HEAVY** — any HIGH-RISK glob hit (kernel / auth production code / contract / migration / multi-service / novel-algorithmic). → Full 3× parallel R1 panel (correctness / safety_bypass / completeness_governance) + adversarial fix-to-fixpoint, exactly as the Delivery Governance Protocol and D-026 mandate today. UNCHANGED.

### Guardrails
1. **Deterministic + logged.** The tier is a pure function of the signals; the WP declares `review_tier` and the signal list; the dispatcher records it. Choosing LIGHT is auditable after the fact, never a discretionary vibe.
2. **Highest-risk signal wins.** A one-line change to `pkg/platform/auth.go` is HEAVY irrespective of diff size.
3. **Test files are classified by file-type, not by the subsystem they exercise.** A change confined to `auth-flow.spec.ts` / `*_test.go` for auth or kernel flows is *test-only*, hence LIGHT-eligible — it does not inherit the HEAVY tier of the code it tests. (Specific correction for the 2026-07-18 mis-fire.)
4. **Mixed sets up-tier.** LIGHT requires EVERY file in the light set; a single production file lifts the change to at least STANDARD.
5. **Discretion moves only UP, never down.** An orchestrator may always elect a heavier tier than computed; it may never elect a lighter one. Skipping review below the computed tier remains forbidden (consistent with the estate no-corner-cutting standard).

### Amendment to Delivery Governance Protocol §2
"3-agent adversarial R1 minimum for all code changes" → "3-agent adversarial R1 for all HEAVY-tier changes; ≥1 R1 reviewer for STANDARD-tier; LIGHT-tier changes rely on CI gates + a logged orchestrator self-review, per Proportionate Review Tiering." The "no silent descoping / all CRIT findings addressed before merge" clauses are unchanged and apply at every tier that has a reviewer.

### Prior art
- **acc four-tier-dispatch pattern** tiers the *executor model* by implementation complexity; this rule is its review-side complement — tiering *review depth* by change risk.
- **PAC-v8 phase-9 wave-5 closure** already accepted "behaviour-preserving by construction + CI green is stronger evidence than R1 lens-review" as grounds to skip R1, but as a one-off manual decision. This rule generalizes that precedent into a deterministic, auditable classification.

### Scope
Estate-wide: applies in every repo that runs the four-tier dispatch / R1 adversarial-review delivery process. The `affected_repos` list enumerates the currently-governed repos; the rule binds any repo that adopts the dispatch process.

### Deferred (phase 2, NOT part of this proposal)
A classifier in `scripts/codex_dispatch.py` (or a pre-dispatch helper) that computes the tier from the diff and writes `review_tier` into the dispatch record, making the tier machine-enforced rather than orchestrator-declared. Coordinate with the in-flight "acc dispatcher false-green on blocked runs" work, which touches the same file.
