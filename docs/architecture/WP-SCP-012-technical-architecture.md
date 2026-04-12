# TechnicalArchitecture — WP-SCP-012 Product-Coherence Evaluator Shell

**Work Package:** `WP-SCP-012`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Objective

Add a live product domain with bounded advisory checks sourced from enhancement
spec text, route content, and screen language.

## 2. Proposed components

### `standards/product`

- rule scaffolding
- pattern scaffolding

### `evaluators/product.py`

- job-to-be-done signal check
- action alignment check
- terminology check

### Audit wiring

- register the product evaluator in the shared audit dispatcher
