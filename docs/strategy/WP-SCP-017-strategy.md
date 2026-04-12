# Strategy — WP-SCP-017 Service API and Project Overlays

**Work Package:** `WP-SCP-017`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Strategy

Keep service and overlay support thin over the existing core:

- merge overlays through the existing registry loader
- thread the merged registry into consult and audit builders
- expose HTTP endpoints that call those same builders directly

This avoids a second standards mechanism and keeps service mode aligned with
the CLI contracts already in use.
