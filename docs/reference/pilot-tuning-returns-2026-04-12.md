# Returns Pilot Tuning — 2026-04-12

## Scope

This note records the first bounded trust-tuning pass against the seeded
Returns pilot in `WP-SCP-008`.

## Trust issue addressed

Before this slice, governance review-evidence checks could pass on loose
signals:

- area-like text anywhere in a review file
- finding-like IDs anywhere in the text
- status-like words anywhere in the text

That was fast to bootstrap, but it risked false confidence from unrelated or
partially formatted markdown.

## Calibration applied

This slice replaces that heuristic with a structured fenced JSON block inside
`review_findings.md`:

- one explicit `area_id`
- explicit `reviewed_paths`
- explicit finding entries with statuses
- explicit `reviewed_at` and summary

The same structured metadata now powers:

- governance traceability checks
- consult-time historical review retrieval

## Effect on the Returns pilot

- the seeded Returns pilot review evidence was migrated to the structured block
- governance now proves traceable review evidence through structured metadata
  instead of loose markdown matches
- consult for the Returns pilot can now surface relevant historical reviews
  deterministically

## Remaining residual risk

- review metadata is still authored manually inside markdown files
- only migrated review packs participate in historical retrieval
- this slice does not yet implement the broader false-positive review loop or
  confidence taxonomy

These are acceptable residuals for the first trust-tuning pass and remain
bounded compared with the prior text-only behaviour.
