# WP-SCP-001 Implementation Notes

**Date:** 2026-04-11  
**Branch:** `feature/wp-scp-001-registry-consult`

## Delivered in this slice

- `registry.py` loads the top-level registry and domain indexes, validates rule
  and pattern metadata, and fails clearly on broken file references.
- `findings.py` loads the read-only open findings store, validates schema
  shape, enforces repo-local evidence paths, and applies deterministic
  consult matching with domain scope plus exact area/path escalation.
- `consult.py` assembles schema-valid consult responses from real registry and
  findings data with deterministic ordering, deduplicated request inputs, and
  stable request IDs.
- `cli.py` now routes `consult`, `findings`, and `show-registry` through live
  implementation paths instead of placeholder data.
- governance and architecture indexes now carry explicit structured metadata so
  the slice does not depend on ad hoc markdown parsing.
- seeded returns pilot evidence now lives under `fixtures/returns-pilot/` so
  the sample findings store is inspectable inside this repo.
- open findings and example consult response fixtures now reflect real consult
  behaviour for the seeded returns-exceptions example.

## Intentional limits

- audit remains scaffolded
- no evaluator logic yet
- no lifecycle transitions or waiver handling yet
- no semantic ranking beyond deterministic ordering

## Verification notes

- `pytest` passes locally
- manual `consult`, `show-registry`, and `findings` runs pass with
  `PYTHONPATH=src`
- CLI-level pytest coverage now exercises `consult` and `show-registry`
- `ruff` and `mypy` are declared in `pyproject.toml` but are not installed in
  the current interpreter environment
