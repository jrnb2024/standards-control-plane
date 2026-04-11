# TechnicalArchitecture — WP-SCP-006 Markdown Reports and Area Summaries

**Work Package:** `WP-SCP-006`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Objective

Generate deterministic markdown reports and area summaries from the structured
audit and persisted findings outputs already produced by the core runtime.

## 2. Proposed components

### `reports.py`

Responsibilities:

- build latest-review markdown from the latest audit result and open findings
- build subsystem-review markdown with the same structured inputs
- build area-summary JSON payloads from the latest audit result and open
  findings
- write those outputs deterministically

### `findings.py`

Responsibilities:

- keep findings reconciliation and persistence focused on structured findings
- expose the persisted stores needed by the report generator

### CLI

Responsibilities:

- keep `audit --write-output` as the explicit write-backed path
- keep `report` read-only and file-backed

## 3. Data flow in this slice

1. CLI builds the live audit result
2. findings persistence refreshes open and history stores
3. report generator consumes:
   - current audit result
   - reconciled open store
   - reconciled history store
4. report generator writes:
   - `output/reports/latest-review.md`
   - `output/reports/subsystems/<subsystem>-review.md`
   - `output/findings/area-summaries/<subsystem>.json`
5. `report` prints the latest review markdown
6. `report` fails if the latest review is missing or if its embedded audit
   timestamp does not match `open-findings.json.generated_at`

## 4. Output rules

- markdown section ordering is fixed
- open findings listed in markdown are ordered by severity then `finding_id`
- area summary uses the existing schema unchanged
- subsystem-keyed filenames remain phase-1 simple, but the payload and markdown
  must include exact `area_id`
- report and area-summary timestamps are bound to `audit_result.generated_at`
- report generation does not mutate findings stores
- the write flow reuses the current per-file atomic replacement and best-effort
  rollback guarantees; it does not add a crash-safe bundled transaction in
  this phase

## 5. Extension points

- waiver-aware report sections
- multi-subsystem rollups
- historical improvements/regression comparison against more than the latest run
- Control Tower surfacing
