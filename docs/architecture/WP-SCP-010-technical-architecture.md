# TechnicalArchitecture — WP-SCP-010 UX / IA Scaffolding and Evaluator Shell

**Work Package:** `WP-SCP-010`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Objective

Add a live UX domain without widening into screenshot or model-heavy review.

## 2. Proposed components

### `standards/ux`

- domain index
- three rules
- two patterns

### `evaluators/ux.py`

- primary-action clarity check
- state-coverage check
- navigation or screen-role clarity check

### Audit wiring

- register the UX evaluator in the domain dispatcher

## 3. Output rules

- findings use direct file evidence
- confidence stays medium in this slice because the checks are bounded but still
  heuristic
- consult remains registry-driven; no UX-specific contract change is needed
