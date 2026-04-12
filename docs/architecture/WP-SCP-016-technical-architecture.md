# TechnicalArchitecture — WP-SCP-016 Control Tower Surfacing and Estate Dashboard Outputs

**Work Package:** `WP-SCP-016`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Objective

Publish Control Tower-facing artifacts without introducing runtime coupling.

## 2. Proposed components

### `control_tower.py`

- build the Control Tower surface contract
- build a subsystem dashboard entry from the current audit result, findings, and CI output
- rebuild the estate dashboard from persisted subsystem dashboard entries
- write artifacts atomically

### Schemas

- `control-tower-surface.schema.json`
- `control-tower-subsystem.schema.json`
- `estate-dashboard.schema.json`

### CLI

- extend `audit --write-output` and `audit-changed --write-output` to refresh Control Tower outputs
- add a `control-tower` read command for the latest dashboard artifacts
