# WP-SCP-013 Implementation Notes

## Implementation summary

- added `false-positive-summary.schema.json`
- added `calibration.py` to:
  - build a history-derived false-positive summary
  - persist `output/findings/false-positive-summary.json`
  - load the current summary for CLI consumption
- updated `audit --write-output` to refresh the calibration artifact
- added a `calibration` CLI command
- tuned consult response assembly to:
  - treat frontend requests specially
  - prefer UX and design patterns first
  - place approved patterns and open findings before the full rule list
  - fold open-finding remediation into guidance ordering

## Review outcome

The only follow-up fix after implementation was relaxing an ordering test so it
asserted the actual intended guarantee rather than a too-specific pattern order.
