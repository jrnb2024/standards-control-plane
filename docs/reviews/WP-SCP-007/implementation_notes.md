# WP-SCP-007 Implementation Notes

## Scope delivered

- added `src/standards_control_plane/waivers.py` to load and validate
  repo-local waivers, select active waivers for the current audit timestamp,
  and reject overlapping active waivers for the same finding
- added `src/standards_control_plane/scoring.py` as the shared severity and
  status-aware score module
- extended `src/standards_control_plane/audit.py` so live audit assembly:
  - overlays active waivers onto current findings
  - emits `waivers_applied`
  - counts waived findings separately in `summary`
  - calculates domain scores from the waiver-aware findings set
  - derives recommended actions only from active unwaived findings
- updated `src/standards_control_plane/findings.py` so persistence:
  - preserves `waived` status in history
  - excludes waived findings from `open-findings.json`
  - reopens previously waived findings when the same finding is emitted again
    without an active waiver
- tightened `schemas/audit-result.schema.json` and added
  `schemas/waivers-file.schema.json`
- added score-model documentation and updated README guidance
- added waiver/scoring tests and waiver-file validation coverage

## Design choices

1. Waivers are an audit-time overlay:
   evaluators still emit deterministic raw findings, and audit assembly owns
   exception handling.

2. Active waivers preserve visibility:
   a waived finding stays in the audit result and history with `status:
   waived`, but it disappears from the active open store and no longer drags
   score down.

3. Score logic is centralised:
   evaluator-local score duplication was removed so raw evaluator scores and
   audit-level effective scores use the same severity and status rules.

4. Missing waiver input is non-fatal:
   the audit path treats a missing `waivers.json` as an empty set, but invalid
   or overlapping active waivers fail explicitly.

## Touched modules

- `src/standards_control_plane/waivers.py`
- `src/standards_control_plane/scoring.py`
- `src/standards_control_plane/audit.py`
- `src/standards_control_plane/findings.py`
- `src/standards_control_plane/evaluators/governance.py`
- `src/standards_control_plane/evaluators/architecture.py`
- `schemas/audit-result.schema.json`
- `schemas/waivers-file.schema.json`
- `tests/test_waivers_and_scoring.py`
- `docs/reference/score-model-2026-04-12.md`
- `README.md`

## Backlog carry-forward

- `SCP-046` — add score-model version tagging to audit output once score
  evolution needs output-level traceability.
