# WP-SCP-003 Implementation Notes

## Scope delivered

- added a live `audit` path that runs extraction, normalisation, governance
  evaluation, and audit-result assembly
- introduced `src/standards_control_plane/audit.py`
- introduced `src/standards_control_plane/evaluators/governance.py`
- extended `project-area` with `review_evidence`
- extended `audit-result` with structured `domain_status`
- tightened `audit-request` so the live path and the schema now agree

## Design choices

1. `scope.area_id` is validated, not trusted:
   the audit path now infers the area from extracted files and only accepts a
   provided `scope.area_id` when it matches that inference.

2. Unsupported domains are explicit:
   the audit result records `not_evaluated` domains in `domain_status` while
   only emitting scores for evaluated domains.

3. `GOV-003` now checks traceable evidence content:
   review files must mention the area and include finding identifiers plus an
   explicit status token, which avoids passing the rule on path presence alone.

4. Scoring stays narrow:
   governance uses the documented severity-deduction model and does not imply
   wider audit completeness for unsupported domains.

## Touched modules

- `schemas/audit-request.schema.json`
- `schemas/audit-result.schema.json`
- `schemas/project-area.schema.json`
- `src/standards_control_plane/audit.py`
- `src/standards_control_plane/cli.py`
- `src/standards_control_plane/evaluators/__init__.py`
- `src/standards_control_plane/evaluators/governance.py`
- `src/standards_control_plane/normaliser.py`
- `examples/audit-result.json`
- `examples/project-area-returns-exceptions.json`
- `fixtures/returns-pilot/docs/reviews/WP-RET-014/review_findings.md`
- `tests/test_extraction_normalisation.py`
- `tests/test_governance_audit.py`

## Deferred follow-on

- `SCP-022` captures the remaining refinement to promote review evidence from a
  path bucket to a richer structured metadata contract.
