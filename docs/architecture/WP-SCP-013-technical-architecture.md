# TechnicalArchitecture — WP-SCP-013 False-Positive Review Loop and Consult Ordering

**Work Package:** `WP-SCP-013`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Objective

Make calibration inspectable and consult output more implementation-friendly
without changing the core request or finding contracts.

## 2. Proposed components

### `calibration.py`

- build false-positive summary from persisted history
- write summary to `output/findings/false-positive-summary.json`

### CLI

- add a `calibration` read command

### Consult ordering

- detect frontend-oriented requests from domains and paths
- prefer UX/design patterns first
- order response payload as patterns, open findings, history, rules, guidance,
  risks
