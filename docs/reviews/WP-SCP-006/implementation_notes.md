# WP-SCP-006 Implementation Notes

## Scope delivered

- added `src/standards_control_plane/reports.py` to generate:
  - `output/reports/latest-review.md`
  - `output/reports/subsystems/<subsystem>-review.md`
  - `output/findings/area-summaries/<subsystem>.json`
- extended `audit --write-output` so report and area-summary generation runs
  immediately after findings persistence
- hardened `report` so it:
  - prints the latest review when the report is fresh
  - fails explicitly when the report is missing
  - fails explicitly when freshness validation against the persisted findings
    state fails
- updated tracked report and area-summary outputs to live generated content
- added deterministic report-generation tests and repo-backed CLI coverage

## Design choices

1. Reports stay downstream of structured state:
   the generator consumes the live audit result plus the reconciled findings
   stores and does not perform new evaluation logic.

2. Freshness is stronger than timestamp-only:
   the latest review embeds the audit timestamp plus signatures for the open and
   history findings stores, and `report` validates both before printing.

3. Area summaries stay subsystem-keyed in phase 1:
   the output file name uses the subsystem, but the payload preserves the exact
   audited `area_id` and counts only scoped open findings for that area.

4. Notable improvements come from structured history:
   the report generator surfaces findings resolved in the current audit run by
   reading the history store instead of inventing an ad hoc “improvement”
   concept.

5. The write-flow limitation is carried honestly:
   report artifacts reuse the current per-file atomic replacement and rollback
   semantics. A stronger crash-safe bundled commit across findings plus report
   artifacts is carried forward as `SCP-039`.

## Touched modules

- `src/standards_control_plane/reports.py`
- `src/standards_control_plane/cli.py`
- `tests/test_reports.py`
- `tests/test_examples_validate.py`
- `output/reports/latest-review.md`
- `output/reports/subsystems/returns-review.md`
- `output/findings/area-summaries/returns.json`
- `README.md`

## Backlog carry-forward

- `SCP-039` — add a stronger bundled commit model across findings and report
  artifacts once the storage model can support it cleanly.
