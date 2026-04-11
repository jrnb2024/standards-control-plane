# ARCH-004 — Async and Eventing Patterns Must Be Consistent

**Domain:** architecture  
**Version:** 1.0.0  
**Status:** draft  
**Severity default:** medium

Async workflows and event publication should follow the established pattern for
the subsystem rather than mixing styles without explicit reason.

## Signals

- event publication added without the expected wrapper or config seam
- background tasks introduced in an inconsistent style
- retries and failure handling differ across adjacent workflow code

