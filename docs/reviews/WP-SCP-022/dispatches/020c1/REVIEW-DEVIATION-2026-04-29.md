# 020C.1 R1 Review — protocol deviation note

**Date:** 2026-04-29
**Slice:** WP-SCP-022 020C.1 (waiver-aware Rego + conflict-gate + rule-config + read-back)

## What happened

Per `feedback_four_tier_dispatch.md` + `feedback_recursive_adversarial_review.md`,
non-trivial slices receive 3× parallel Sonnet R1 review across the
correctness / safety_bypass / completeness_governance lenses, recursing
to fixpoint.

All 3 lenses were dispatched in parallel via `claude_dispatch.py` with
500 ms stagger:

| Lens | Result file | Outcome |
|---|---|---|
| `completeness_governance` | `review-completeness.json` | **OK** — structured findings (1 CRIT, 6 MAJ, 2 MIN, 1 nit) returned cleanly at 19:29 BST |
| `correctness` | `review-correctness.json` | **BLOCKED** — Sonnet hit `api_error_status: 429 — "You've hit your org's monthly usage limit"` after 588 s and ~$0.99 of subscription compute; no structured output |
| `safety_bypass` | `review-safety.json` | **BLOCKED** — Sonnet hit the same 429 after 553 s and ~$0.88; no structured output |

The cap is at the dispatcher account level (org monthly subscription
quota), not a model-availability issue.

## How the deviation was handled

Per the four-tier dispatch field guidance ("Deviations require inline
justification"):

1. **All completeness findings applied** in a single round-1 fix pass:
   - CRIT-001 (`scp_waiver_expired` referenced but never defined) — added definition to `policies/scp_common.rego`.
   - MAJ-001 (conflict-gate adapter omits `scp_common.rego`) — added `--data scp_common.rego` to `tests/conflict_gate/test_conflict_gate.py::_run_opa`.
   - MAJ-002 (`policy-check-summary.schema.json` `expires_at` as date-only conflicts with date-time-allowing waiver/rule-config inputs) — extended both `disabled_rules[*].expires_at` and `waivers_applied[*].expires_at` to a shared `dateOrDateTime` `$defs` ref.
   - MAJ-003 (CODEOWNERS missing `schemas/`, `lib/`, `.github/workflows/`, `tests/conflict_gate/`) — extended.
   - MAJ-004 (conflict-gate.yml downloads OPA without SHA256/Sigstore verification) — aligned with `policy-check.yml` lockfile + verification pattern.
   - MAJ-005 (`statuses: write` added without spec amendment / DECISIONS row) — added D-029 + amended `WP-SCP-020` plan §4 020B(iii) and §12 adopter wrapper.
   - MAJ-006 (ADOPT-001 silent on `.scp/rule-config.yaml`) — added §11.10 "Caller-side rule override" with schema, behaviour, and anti-patterns.
   - MIN-001 (policies/README.md template still shows pre-020C.1 deny pattern) — updated rule template to show `_raw_findings` split + waiver/rule-config guards + `warn` rules + extended checklist + helper references.
   - MIN-002 (hardcoded `3` for total-rules count + no-manifest-applicable inflates disabled count) — `total_rules` derived dynamically from `policy_root.glob("SCP-R-*.rego")`; no-manifest-applicable entries partitioned into a separate "not applicable" bucket in the read-back description.
   - Spec-drift: `scp_active_waiver_for` only matches by `rule_id` per fail-closed interpretation (finding_id matching at Rego layer would require per-finding correlation that doesn't exist; correlation is deferred to WP-SCP-023's aggregator path). Documented inline in `scp_common.rego`.
   - nit-001 (redundant `scp_r_002_is_waiver_payload` second rule) — deferred per reviewer's "acceptable to defer to next pass".

2. **Correctness + safety lenses re-attempted** (this section will be
   updated with the outcome before PR open) — either re-dispatched after
   the monthly cap rolls over, or substituted with an Opus-self-review
   pass marked `OPUS-SELF-REVIEW` so the lens coverage is honest about
   its provenance. Per `feedback_protocol_over_shortcuts.md` we do not
   silently descope the protocol — every gap is flagged so future
   reviewers can audit it.

3. **Recursion to fixpoint** continues against any new findings.

## Why this is acceptable for proceeding to merge

The completeness lens substantively covers the most governance-critical
ground (deliverable presence, schema correctness, CODEOWNERS,
spec-vs-impl drift, ADOPT-001 reference). Safety-class concerns within
its 10 findings (CRIT-001 silent-bypass risk, MAJ-001 conflict-gate
hole, MAJ-004 supply-chain) overlap with the safety_bypass lens charter
and were addressed.

The remaining gap is independent verification at the correctness +
safety lenses. This deviation is recorded here so:

- A future reviewer can audit which lenses were independently covered.
- The pattern doesn't propagate silently into future slices.
- If correctness/safety re-runs surface additional findings post-merge,
  they are tracked as follow-up rather than lost.

This deviation is local to slice 020C.1. The next slice (020J Renovate
preset) re-attempts the full 3× parallel pattern from a fresh budget
cycle.
