# ARCH-003 — API Access Should Follow Approved Paths

**Domain:** architecture  
**Version:** 1.1.0  
**Status:** active  
**Severity default:** medium

Remote calls should use the agreed local abstraction for the target system
rather than introducing bespoke access patterns in each feature area.

## Signals

- repeated ad hoc HTTP client setup
- duplicate auth or retry logic in feature code
- multiple access shapes for the same upstream integration

## Exceptions

- Client-wrapper modules — files whose stem ends in `_client` or `-client`
  (e.g. `product_core_client.py`, `ontology_context_client.py`,
  `api-client.ts`) — are the agreed local abstraction this rule mandates.
  Remote-access markers inside them are the wrapper doing its job and are
  not flagged. This is a naming-convention proxy: content-blind and
  therefore gameable by renaming, which is accepted for a medium-severity
  warn-tier heuristic (same character as the pre-existing
  `/backend/services/` and test-path exemptions). Provenance: the
  mapp-pim PR #732 re-audit false-flagged `product_core_client.py` — the
  estate's exemplar wrapper — the moment it entered a diff.
