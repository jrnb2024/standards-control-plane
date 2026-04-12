# Strategy — WP-SCP-016 Control Tower Surfacing and Estate Dashboard Outputs

**Work Package:** `WP-SCP-016`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Strategy

Keep Control Tower surfacing as a downstream export layer:

- build subsystem and estate dashboard artifacts from persisted SCP outputs
- keep subsystem entries scoped to the audited subsystem
- rebuild the estate dashboard from saved subsystem entries

This keeps Control Tower as a consumer of status rather than a host of the
evaluation runtime.
