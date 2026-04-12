# TechnicalArchitecture — WP-SCP-009 Confidence Taxonomy and Evidence Classes

**Work Package:** `WP-SCP-009`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Objective

Make confidence and evidence provenance explicit in the structured contracts
that already power consult, audit, and findings persistence.

## 2. Proposed components

### `confidence.py`

Responsibilities:

- define confidence thresholds
- derive `confidence_class` from numeric confidence
- expose allowed evidence classes for validation and reuse

### Findings contracts

Responsibilities:

- add required `confidence_class` to finding payloads
- add required `evidence_class` to each evidence entry
- keep numeric `confidence` as the source metric

### Evaluators

Responsibilities:

- derive `confidence_class` consistently from numeric confidence
- classify each evidence entry using the shared evidence vocabulary

### Consult assembly

Responsibilities:

- expose a top-level consult `confidence_class`
- surface `confidence_class` for open findings returned to implementation
  agents

## 3. Data flow in this slice

1. evaluator or seed payload provides numeric confidence and evidence entries
2. shared helper derives `confidence_class`
3. evidence entries declare `evidence_class`
4. finding schema validates the expanded contract
5. audit, persistence, and consult paths reuse the same shape

## 4. Output rules

- `confidence_class` is always derived from numeric `confidence`
- `evidence_class` describes source type, not severity or certainty
- consult and audit must stay schema-valid with the expanded contract
- seeded example and output artefacts must be regenerated in the same slice

## 5. Extension points

- confidence-aware warning thresholds
- false-positive calibration by rule and confidence class
- domain-specific heuristics that still map back to the shared taxonomy
