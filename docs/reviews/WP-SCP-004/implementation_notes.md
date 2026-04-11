# WP-SCP-004 Implementation Notes

## Scope delivered

- added `src/standards_control_plane/evaluators/architecture.py`
- extended `audit.py` to dispatch architecture alongside governance and sort
  merged findings deterministically
- updated the seeded returns pilot fixture so live audit produces concrete
  `ARCH-001`, `ARCH-002`, and `ARCH-003` findings
- added two repo-backed architecture signal corpora for targeted `ARCH-003` and
  `ARCH-004` coverage
- updated the example audit result and related tests
- updated README to reflect live governance plus architecture audit support

## Design choices

1. Rule checks are explicit signal heuristics:
   the evaluator reads repo-local file contents and uses bounded markers instead
   of prompt-like inference.

2. Boundary checks use import lines:
   `ARCH-001` now scans import-like lines rather than arbitrary text so boundary
   detection stays tied to code structure.

3. Comment stripping is in-slice:
   the evaluator removes comments before scanning markers to reduce
   comment-driven false positives without widening the slice into heavier
   parsing.

4. Combined audit output is sorted after merge:
   findings from governance and architecture are merged and then sorted by
   severity and finding id so mixed-domain output remains deterministic.

## Touched modules

- `src/standards_control_plane/evaluators/architecture.py`
- `src/standards_control_plane/evaluators/__init__.py`
- `src/standards_control_plane/audit.py`
- `examples/audit-result.json`
- `fixtures/returns-pilot/frontend/app/exceptions/page.tsx`
- `fixtures/returns-pilot/frontend/app/shared/filters.ts`
- `fixtures/returns-pilot/backend/services/returns_exception_service.py`
- `fixtures/architecture-api-drift/`
- `fixtures/architecture-async-drift/`
- `tests/test_architecture_audit.py`
- `tests/test_governance_audit.py`
- `README.md`

## Backlog carry-forward

None for this slice.
