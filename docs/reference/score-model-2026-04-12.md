# Score Model — 2026-04-12

## Purpose

This document records the current deterministic score model used by the
Standards Control Plane in phase 1.

The goal is explainability and stable behaviour, not exhaustive sophistication.

## Formula

Each evaluated domain starts at `100`.

For each current finding in that domain:

- `critical` with `status: open` subtracts `40`
- `high` with `status: open` subtracts `30`
- `medium` with `status: open` subtracts `15`
- `low` with `status: open` subtracts `5`

Statuses that do **not** reduce score in this phase:

- `waived`
- `resolved`
- `accepted`
- `false_positive`
- `superseded`

After all deductions, scores clamp to the `0..100` range.

## Interpretation

- `90–100`: strong compliance
- `75–89`: acceptable with notable issues
- `60–74`: meaningful drift or quality risk
- `<60`: poor compliance and remediation should be prioritised

## Current phase-1 limits

- repeated findings weigh more only by accumulating repeated fixed deductions
- regressions do not yet receive extra weighting
- accepted debt does not yet have a distinct score contribution beyond zero
- score output is deterministic, but not yet version-tagged in the audit result

## Implementation references

- `src/standards_control_plane/scoring.py`
- `src/standards_control_plane/audit.py`
- `src/standards_control_plane/evaluators/governance.py`
- `src/standards_control_plane/evaluators/architecture.py`
