# Strategy — WP-SCP-015 CI Outputs and Warning Thresholds

**Work Package:** `WP-SCP-015`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Strategy

Keep CI surfacing as a projection layer over the existing audit result:

- build CI JSON and markdown from the validated audit result
- evaluate warnings from explicit deterministic thresholds
- keep warnings advisory and visible without changing process exit behaviour

This preserves one audit pipeline while making the results easier for CI and
review tooling to consume.
