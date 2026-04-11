# ARCH-003 — API Access Should Follow Approved Paths

**Domain:** architecture  
**Version:** 1.0.0  
**Status:** draft  
**Severity default:** medium

Remote calls should use the agreed local abstraction for the target system
rather than introducing bespoke access patterns in each feature area.

## Signals

- repeated ad hoc HTTP client setup
- duplicate auth or retry logic in feature code
- multiple access shapes for the same upstream integration

