# WP-SCP-008 Implementation Notes

## Scope delivered

- added `src/standards_control_plane/review_evidence.py` to parse fenced
  `scp-review-evidence` JSON blocks, validate them, and select historical
  review references deterministically
- added `schemas/review-evidence.schema.json`
- migrated governance `GOV-003` review-evidence checks from raw string matches
  to structured review-evidence records
- extended `consult` and `consult-response.schema.json` with explicit
  `historical_reviews` output
- migrated the seeded Returns pilot review file plus repo-local work-package
  review packs from `WP-SCP-003` onward to the structured review-evidence
  block format
- added focused review-evidence fixtures for legacy and path-overlap coverage
- added the Returns pilot tuning note documenting the trust improvement in this
  slice

## Design choices

1. One small fenced JSON block:
   the metadata stays readable in markdown and avoids adding a separate backing
   store or non-standard parser dependency.

2. One parser, two consumers:
   the same parsed record shape now powers governance review traceability and
   consult-time historical review retrieval.

3. Legacy files are skipped, not fatal, for consult:
   consult remains usable while review-pack migration is partial, but
   governance traceability still requires a valid structured block for the
   audited area.

4. Historical reviews are explicit:
   the consult contract now returns a bounded `historical_reviews` array rather
   than burying review history inside generic guidance text.

## Touched modules

- `src/standards_control_plane/review_evidence.py`
- `src/standards_control_plane/consult.py`
- `src/standards_control_plane/evaluators/governance.py`
- `schemas/review-evidence.schema.json`
- `schemas/consult-response.schema.json`
- `fixtures/returns-pilot/docs/reviews/WP-RET-014/review_findings.md`
- `fixtures/review-evidence-legacy/docs/reviews/WP-LEG-001/review_findings.md`
- `fixtures/review-evidence-overlap/docs/reviews/WP-OVR-001/review_findings.md`
- `docs/reviews/WP-SCP-003/review_findings.md`
- `docs/reviews/WP-SCP-004/review_findings.md`
- `docs/reviews/WP-SCP-005/review_findings.md`
- `docs/reviews/WP-SCP-006/review_findings.md`
- `docs/reviews/WP-SCP-007/review_findings.md`
- `tests/test_review_evidence.py`
- `tests/test_consult_retrieval.py`
- `tests/test_governance_audit.py`
- `docs/reference/pilot-tuning-returns-2026-04-12.md`
- `README.md`

## Backlog carry-forward

- `SCP-047` — cache parsed structured review evidence once consult/audit volume
  justifies avoiding repeated repo scans.
