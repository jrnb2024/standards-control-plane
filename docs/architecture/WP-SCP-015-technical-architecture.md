# TechnicalArchitecture — WP-SCP-015 CI Outputs and Warning Thresholds

**Work Package:** `WP-SCP-015`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Objective

Expose CI-ready outputs and warning thresholds without forking the audit model.

## 2. Proposed components

### `ci_outputs.py`

- build a compact CI projection from an audit result
- evaluate deterministic warning thresholds
- render a short markdown summary
- write CI artifacts atomically

### Schemas

- `ci-warning.schema.json`
- `ci-output.schema.json`

### CLI

- extend `audit --write-output` and `audit-changed --write-output` to emit CI outputs
- add a `ci` read command for the latest CI artifact
