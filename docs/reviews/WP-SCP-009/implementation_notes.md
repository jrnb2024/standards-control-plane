# WP-SCP-009 Implementation Notes

## Implementation summary

- added a shared `confidence.py` helper with deterministic thresholds:
  - `high >= 0.95`
  - `medium >= 0.80`
  - `low < 0.80`
- expanded `finding.schema.json` to require:
  - top-level `confidence_class`
  - per-evidence `evidence_class`
- expanded `consult-response.schema.json` to require:
  - top-level `confidence_class`
  - per-open-finding `confidence_class`
- updated governance and architecture evaluators to emit the expanded payloads
- updated findings-store loading to reject persisted records whose
  `confidence_class` does not match the configured numeric threshold model
- regenerated examples and persisted outputs after the contract change

## Evidence-class usage in this slice

- governance findings use `declared_metadata`
- architecture findings use `direct_file`
- seeded historical governance evidence in persisted history uses
  `structured_review`

## Review outcome

The only real Gate B issue was contract drift between live code and persisted
repo artefacts after the schema expansion. That was fixed in-slice by
regenerating the examples and outputs and rerunning the full suite.
