# Strategy — WP-SCP-003 Governance Evaluator and Audit Wiring

**Work Package:** `WP-SCP-003`  
**Version:** 0.2  
**Status:** Approved for implementation  
**Date:** 2026-04-11

## 1. Strategy

Prove one end-to-end audit path before widening to architecture.

The evaluator should be deterministic, rule-bound, and evidence-oriented. It
should consume the project-area model produced by `WP-SCP-002`, not raw scope
paths.

## 2. Why this slice now

The project now has:

- a standards registry
- consult retrieval
- extracted-scope and project-area contracts

What it still lacks is a real evaluator path. Governance is the lowest-risk
domain to stand up first because its current rules are mostly artefact and
process checks, not deeper architectural inference.

## 3. Delivery shape

### 3.1 Tighten the contracts first

Before evaluator code lands, two contracts need to become explicit:

- `project-area` must expose `review_evidence` as a first-class artefact bucket
- `audit-result` must expose structured per-domain evaluation status

That keeps `GOV-003` and unsupported-domain handling inside typed inputs and
outputs instead of burying them in implementation detail or prose.

### 3.2 Keep the evaluator narrow

Start with checks that clearly map to the existing governance rules:

- `GOV-001`: area/subsystem boundary mismatch
- `GOV-002`: required planning artefact missing
- `GOV-003`: review evidence missing

### 3.3 Wire audit for governance first, not governance only

When `audit` is invoked with `governance`, the CLI should:

1. validate the audit request
2. extract the requested scope
3. normalise to project-area
4. run governance evaluation
5. emit a schema-valid audit result

If the request also asks for other domains, the same live audit path should
still run, but only governance should be evaluated in this slice.

### 3.4 Keep unsupported domains explicit

If the request also asks for `architecture`, `ux`, `design`, or `product`, the
result should mark those domains as not evaluated in structured output.

## 4. Scoring approach for this slice

Use a simple severity-deduction model:

- start at `100`
- subtract `30` per high-severity finding
- subtract `15` per medium-severity finding
- subtract `5` per low-severity finding
- floor at `0`

This score is the governance-domain score only. It is not a stand-in for full
audit coverage or evaluator confidence across unsupported domains.

## 5. Example and evidence strategy

This slice should prove both the clean path and the failure path:

- seeded pilot audit request/result from the live governance path
- negative fixtures or tests for `GOV-001`, `GOV-002`, and `GOV-003`
- review evidence pack that shows plan review, implementation notes, acceptance
  verification, and raw test output

## 6. Expected follow-on

If this slice lands cleanly, `WP-SCP-004` can reuse the same audit wiring for
architecture evaluation rather than inventing a second path.
