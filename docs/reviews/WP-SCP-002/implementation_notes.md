# WP-SCP-002 Implementation Notes

**Date:** 2026-04-11  
**Branch:** `feature/wp-scp-002-extractor-normaliser`

## Delivered in this slice

- `extractor.py` resolves scope paths under the repo root, canonicalises them,
  rejects boundary escapes, rejects scope-path and in-scope symlinks,
  recursively enumerates
  files, and emits a schema-valid extracted-scope payload.
- `normaliser.py` consumes extracted-scope payloads, classifies files into
  explicit artefact buckets, including first-class `docs` and `code_paths`,
  infers metadata, and produces a schema-valid project-area payload.
- added explicit schemas for:
  - `extracted-file-record`
  - `extracted-scope`
  - `project-area`
- extended `fixtures/returns-pilot/` so every declared extraction bucket has a
  concrete seeded file.
- tightened scope handling so symlinked files cannot pull repo-local targets in
  from outside the requested subtree.
- added example extracted-scope and project-area payloads derived from the
  seeded pilot.
- updated the audit example scope to use the in-repo seeded pilot path.

## Intentional limits

- no evaluator logic yet
- no audit scoring changes
- no multi-area batching
- area inference supports deterministic seeded-pilot rules only; otherwise an
  explicit area hint is required

## Verification notes

- `pytest` passes locally
- manual extracted-scope and project-area runs pass with `PYTHONPATH=src`
- `ruff` and `mypy` remain declared but not installed in the current
  interpreter environment
