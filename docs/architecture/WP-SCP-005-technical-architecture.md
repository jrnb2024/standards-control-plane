# TechnicalArchitecture — WP-SCP-005 Findings Lifecycle Foundation and Persistence

**Work Package:** `WP-SCP-005`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Objective

Add a deterministic persistence layer for audit findings without redesigning
the existing evaluator outputs.

## 2. Proposed components

### `findings.py`

Responsibilities:

- load existing open and history stores
- reconcile current audit findings into those stores
- preserve finding identity and lifecycle transitions deterministically
- write updated stores back to disk

### `audit.py`

Responsibilities:

- keep building live audit results
- optionally invoke findings persistence when the caller explicitly requests a
  write

### CLI

Responsibilities:

- add an explicit write path for `audit`
- keep read-only operation available

## 3. Reconciliation rules in this slice

- identity key is `finding_id`, guarded by `(domain, area_id)`
- a repeated `finding_id` with a different `(domain, area_id)` pair is a hard
  failure
- exact duplicate incoming findings for the same `finding_id` collapse to one
  record before reconciliation
- open findings present in the current audited area/domain remain open
- resolution scope is exactly:
  - `audit_result["scope"]["area_id"]`
  - domains whose `audit_result["domain_status"][domain]["status"] ==
    "evaluated"`
- open findings absent from that audited area plus evaluated-domain boundary
  become resolved in history
- unrelated findings remain untouched
- non-open historical findings remain in history unchanged unless the same
  finding reappears
- when the same finding reappears with the same scope, `created_at` is
  preserved and `updated_at` becomes the current audit timestamp

## 4. Output rules

- open store contains only `open` findings
- history store contains all known findings with their latest status
- both stores sorted by `(domain, area_id, finding_id)`
- writes are confined to the findings output area
- writes use temp-file staging and atomic replacement for each target file
- the default audit path remains read-only; persistence is only invoked when
  the CLI receives `--write-output`

## 5. Extension points

- waivers and accepted debt
- superseded and false-positive handling
- area summaries and rollups
- report generation
