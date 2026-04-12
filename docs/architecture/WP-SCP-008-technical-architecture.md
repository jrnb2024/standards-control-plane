# TechnicalArchitecture — WP-SCP-008 Review Evidence Hardening and Pilot Tuning

**Work Package:** `WP-SCP-008`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Objective

Make review evidence machine-readable enough for trustable governance checks
and reusable consult retrieval without adding a new backing store.

## 2. Proposed components

### `review_evidence.py`

Responsibilities:

- parse structured review-evidence blocks from markdown files
- validate them against an explicit schema
- expose typed records for governance checks and historical retrieval

### Governance evaluator

Responsibilities:

- replace raw text heuristics with structured review-evidence parsing
- require area-aligned structured review metadata with explicit finding states

### Consult retrieval

Responsibilities:

- scan structured review-evidence records from repo-local review files
- select relevant historical review references by area/path relevance
- expose bounded historical review references in the consult response
- return an empty historical-review list when no structured match exists rather
  than failing consult assembly

## 3. Data flow in this slice

1. review markdown contains a fenced `scp-review-evidence` JSON block
2. parser reads and validates the block
3. governance evaluator uses parsed review evidence for `GOV-003`
4. consult retrieval scans review-evidence sources and selects relevant records
5. consult response includes bounded historical review references
6. pilot tuning note records the trust change and residual limits

## 4. Output rules

- review-evidence parsing is repo-bounded
- selection order is deterministic:
  1. exact `area_id` match
  2. reviewed-path overlap
  3. newest `reviewed_at`
  4. stable path tie-break
- the consult-response contract grows in this slice with explicit
  `historical_reviews` output
- consult output remains advisory and bounded
- legacy files without structured blocks are skipped in historical retrieval

## 5. Extension points

- authoring helpers for structured review metadata
- docs-agent-backed historical review enrichment
- confidence classes for historical review references
- richer calibration packs for false positives
