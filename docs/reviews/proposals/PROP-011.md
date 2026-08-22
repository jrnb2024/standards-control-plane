---
adjudication_status: accepted
accepted_as: GOV-007
enforcement_policy: SCP-R-015
decision_ref: D-067
accepted_at: 2026-07-12
accepted_note: adjudicated into standards/governance/rules/GOV-007-integrity-green-required-to-leave-red.md + index.json + policies/SCP-R-015.rego (warn-baseline, ships dormant/vacuous-pass). Live enforcement today = the conformance-tcb repo gate (policy/scp_r_triad_001.rego); SCP-plane firing gated on FUP-D067-CONFORMANCE-TCB-MATERIALISER-001.
expected_review_date: null
queued_at: 2026-07-12T10:07:59Z
---
> NOTE: WP-SCP-022-proposal-queue adjudication workflow is not yet live;
> proposals queue until adjudication ships. Status updates via
> GitHub issue on this branch (proposals/PROP-011). See
> docs/plans/WP-SCP-022-implementation-programme-plan.md §12.

<!-- proposal_metadata: {"affected_repos":["kg-demo-framework"],"caller_id":"stdio:99776:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server","mcp_origin":true,"proposal_hash":"1583b719145178f30fc57216d2a5ae732637dd86b5c1c66a8389e8a790b6f608","rule_id":"SCP-R-TRIAD-001","signing_key_id":"428dfee16bc954ad"} -->

# PROP-011: SCP-R-TRIAD-001 — Integrity-green required to leave RED (deny plane, not SVC-*)

## Proposal Envelope
- mcp_origin: true
- caller_id: stdio:99776:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server
- signing_key_id: 428dfee16bc954ad

## Affected Repositories
- kg-demo-framework

## Rule Context
SCP-R-TRIAD-001

## Proposal Body
PROPOSED DENY-PLANE RULE (Rego SCP-R-*, required policy-check gate). Supersedes the earlier mis-plan to author this as an advisory SVC-JOIN-002 — the round-2 red-team (Lane D) caught that the SVC-* advisory plane NEVER gates CI (audit_changed only), so a fake green could merge with CI staying green. It MUST be a deny rule.

Provenance: Phase-0 charter v2 §5 (~/Projects/PHASE-0-CHARTER-conformance-lite-v2-2026-07-12.md). Draft for operator review — do not self-approve.

INTENT: no fake 'done'. A conformance-board cell may transition to a non-RED status only by EARNING it against the frozen oracle — status is computed, never typed.

DENY marking a board cell non-RED unless ALL hold:
 1. COMPUTED STATUS — render_board derives the status from the proof outcome; a typed board.json status disagreeing with the computed one fails the run (implemented, L2, genesis commit 63250ca).
 2. STANDING FAKE-MUTANT — the cell's committed FAKE fixture (the cheap shortcut: hardcode / baked-read / flag) FAILS the JoinTest on this run (anti-Goodhart workhorse; always-on, not one-time).
 3. CHEAP BEHAVIOURAL TRIAD — red-first (a CI-observed, ledger-signed RED, not merely a committed sha) + discriminate-vs-knowledge-off (knowledge layer is a pure additive term the TCB nulls: score = base + Δ, so the fleet can't sabotage the baseline) + lineage-present.
 4. TRANSITION CLASSIFIER — the cumulative diff since the cell's last ledger-signed RED touches ONLY SUT paths and leaves the TCB byte-identical (over an open()-traced read-set), run from a pinned harness copy.

TRUST-FLOOR TAG (separate required annotation, not a merge blocker on the integrity flip): each green is tagged `integrity`, `correctness:external` (externally-verifiable non-fleet ground truth), or `correctness:attested` (dated operator sign-off for authored-judgment cells — distinct board colour). An integrity-verified green with no correctness root shows `ungrounded-authored` and is never counted done. This names the intrinsic residual (a self-authoring system cannot prove its own rules correct) rather than pretending crypto closes it.

PLANE: deny / required check — never SVC-*.
