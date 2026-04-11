# TechnicalArchitecture — WP-SCP-001 Registry and Consult Retrieval

**Work Package:** `WP-SCP-001`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-11

## 1. Objective

Introduce a real retrieval path for consult mode while preserving separation
between:

- registry loading
- findings loading
- consult response assembly
- CLI command execution

## 2. Proposed components

### `registry.py`

Responsibilities:

- load top-level standards index
- load domain indexes
- validate file references
- return structured rules and patterns

### `findings.py`

Responsibilities:

- load open findings store
- validate findings store shape before use
- return findings filtered by domain first, then refined by area and matching
  path hints when available

### `consult.py`

Responsibilities:

- accept a validated consult request
- select relevant rules and patterns for requested domains
- surface matching open findings
- produce schema-valid consult response

### `cli.py`

Responsibilities:

- remain thin
- validate request payload
- invoke consult service
- print JSON

## 3. Data flow

1. CLI reads request JSON
2. request validated against schema
3. consult service loads registry and findings
4. consult service matches:
   - requested domains
   - area id
   - path hints
5. response assembled
6. response validated against schema
7. response printed

## 4. Matching strategy for this slice

Use simple deterministic matching only:

- include all active rules for requested domains
- include all patterns for requested domains
- include findings when domain matches requested domain
- refine priority upward when:
  - `area_id` matches exactly, or
  - a finding evidence path appears in the request paths

No semantic ranking in this slice.

## 4.1 Findings store contract in this slice

This slice depends on the existing `findings-store.schema.json` and the current
open findings file at `output/findings/open-findings.json`.

Only read access is in scope here. Lifecycle transitions, waivers, and history
management remain out of scope.

## 5. Extension points

- richer area/subsystem retrieval
- docs-agent enrichment
- evaluator-produced findings
- confidence scoring beyond fixed retrieval confidence
