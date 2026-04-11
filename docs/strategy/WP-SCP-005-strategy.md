# Strategy — WP-SCP-005 Findings Lifecycle Foundation and Persistence

**Work Package:** `WP-SCP-005`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Strategy

Make findings durable before widening into waivers or reports.

This slice should take the live audit output that now exists for governance and
architecture and reconcile it into machine-readable stores that can survive
between runs.

## 2. Why this slice now

The project now has:

- live governance and architecture audit output
- deterministic finding IDs from the current evaluators
- a read-only findings-store model already used by consult

What it still lacks is durable update behaviour. Without that, every audit is a
fresh printout rather than a maintained record.

## 3. Delivery shape

### 3.1 Reconcile, do not append blindly

This slice should treat persistence as reconciliation:

- preserve existing findings when they are still present
- add new findings when they appear
- resolve open findings when they disappear from the same audited `scope.area_id`
  and a domain whose `domain_status` is `evaluated`
- leave unrelated findings alone
- fail explicitly if persisted records or incoming audit findings reuse the same
  `finding_id` for a different `(domain, area_id)` pair
- collapse exact duplicate finding payloads inside one audit refresh before
  persistence

### 3.2 Keep lifecycle narrow

Only establish the first lifecycle foundation:

- `open`
- `resolved`
- preservation of pre-existing non-open historical statuses

Waiver semantics and richer manual review actions belong to the next slices.

### 3.3 Keep write behaviour explicit

The audit path should write stores only through `audit --request <path>
--write-output`. The read-only path should remain available and unchanged when
the flag is absent.

## 4. Output strategy

This slice should maintain:

- `output/findings/open-findings.json`
- `output/findings/findings-history.json`

Both outputs should remain deterministic and diff-friendly.

Canonical ordering for persisted findings should be:

1. `domain`
2. `area_id`
3. `finding_id`

Writes should stage temp files in the output directory, replace each target
file atomically, and roll back the pair on caught write failures.

True crash-safe pair commits across both files are explicitly deferred to a
later slice rather than hand-waved into phase 1.

## 5. Expected follow-on

If this slice lands cleanly, the next work package can build reporting and then
waiver handling on top of a stable persisted findings base.
