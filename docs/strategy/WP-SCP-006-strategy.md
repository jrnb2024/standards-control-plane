# Strategy — WP-SCP-006 Markdown Reports and Area Summaries

**Work Package:** `WP-SCP-006`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Strategy

Make reporting a downstream view over structured audit data, not a second
evaluation system.

This slice should turn the persisted findings state from `WP-SCP-005` into
human-readable markdown and compact area-summary JSON without widening the
domain logic.

## 2. Why this slice now

The project now has:

- live governance and architecture audit output
- durable open and history findings stores
- a read-only `report` command that still points at placeholder content

What it lacks is the human-readable reporting surface promised by the phase-1
scope and the first machine-readable area summary output.

## 3. Delivery shape

### 3.1 Reports are projections, not new judgement

The report generator should consume:

- the live audit result for the current write-backed run
- the persisted open findings store after reconciliation
- the persisted history store only where needed for explicit “none in this
  phase” or trend placeholders

It should not perform new heuristic checks or invent findings.

### 3.2 Keep filenames simple in phase 1

Use the original subsystem-keyed filenames:

- `output/reports/subsystems/<subsystem>-review.md`
- `output/findings/area-summaries/<subsystem>.json`

The payload and markdown content must still carry the exact audited `area_id`
so the phase-1 naming rule remains honest.

### 3.3 One write flow

When `audit --write-output` runs, the write flow should:

1. build the live audit result
2. reconcile and persist findings stores
3. generate latest-review markdown
4. generate subsystem-review markdown
5. generate subsystem-keyed area summary JSON

The `report` command should stay read-only and print the latest generated
review.

If the latest review markdown is missing, or if its embedded freshness metadata
(audit timestamp plus report-source signatures) no longer matches the persisted
findings state, `report` should fail explicitly and tell the caller to refresh
with `audit --write-output`.

## 4. Output strategy

### Latest review markdown

The latest review should include, in stable order:

1. status line
2. generated timestamp bound to `audit_result.generated_at`
3. scope
4. standards version
5. domain scores
6. top open high-severity issues with evidence paths
7. recommended next actions
8. regressions
9. notable improvements

### Area summary JSON

The area summary should be compact and stable:

- filename keyed by subsystem
- payload carries both `subsystem` and exact `area_id`
- `open_findings_count` reflects the open findings for the audited area
- `scores` comes from the current audit result
- `updated_at` equals `audit_result.generated_at`

### 4.1 Write-flow honesty

This slice reuses the current findings-write guarantees:

- explicit write path only
- per-file atomic replacement
- rollback on caught failures

It does not claim a crash-safe bundled transaction across findings plus report
artifacts. That stronger guarantee is carried to backlog.

## 5. Expected follow-on

If this slice lands cleanly, the next work package can add waivers and score
documentation on top of a live reporting surface rather than placeholders.
