# Strategy — WP-SCP-013 False-Positive Review Loop and Consult Ordering

**Work Package:** `WP-SCP-013`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Strategy

Use persisted history as the system of record for false-positive calibration.
Do not invent a second review database in this slice.

At the same time, make consult outputs friendlier for frontend implementation by
ordering the existing fields more intentionally rather than redesigning the
contract.

## 2. Delivery shape

- add a false-positive summary artifact derived from `findings-history.json`
- expose that artifact through the CLI
- keep consult contract stable while reordering patterns, findings, and rules
  for frontend requests
