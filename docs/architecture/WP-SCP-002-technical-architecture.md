# TechnicalArchitecture — WP-SCP-002 Extractor and Area Normaliser

**Work Package:** `WP-SCP-002`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-11

## 1. Objective

Introduce a deterministic extraction and normalisation path that future audit
evaluators can share.

## 2. Proposed components

### `extractor.py`

Responsibilities:

- resolve repo-local scope paths
- canonicalise every requested path before recursion
- reject missing paths, boundary escapes, and symlink-led escapes
- recursively enumerate files
- expose deterministic extracted file records

### `normaliser.py`

Responsibilities:

- classify extracted files into stable artefact buckets
- infer languages and frameworks using explicit rules
- infer a deterministic area identifier for the seeded pilot
- produce a schema-valid project-area payload

### `extracted-file-record.schema.json`

Responsibilities:

- define the explicit extractor-to-normaliser handoff contract
- constrain repo-relative path, extension, and source-scope metadata

### `project-area.schema.json`

Responsibilities:

- define the explicit intermediate representation contract
- constrain required fields and bucket shapes

## 3. Data flow

1. caller provides scope paths and subsystem
2. extractor resolves and expands the scope into file records
3. normaliser classifies files and derives metadata
4. normaliser emits a project-area payload
5. payload validates against schema

## 4. Matching / classification rules for this slice

Use explicit deterministic rules only, applied in the normaliser:

- enhancement specs:
  - paths under `docs/enhancements/`
  - filenames matching `ENH-*.md`
- prompts:
  - paths under `prompts/`
- UI components:
  - `.tsx`, `.jsx`, `.ts`, `.js` under `frontend/` or `components/`
- services:
  - filenames or directories containing `service` or `action`
  - backend modules under `backend/services/`
- tests:
  - paths under `tests/`
  - filenames matching `test_*` or `*.test.*`
- configs:
  - standard config filenames such as `package.json`, `tsconfig.json`,
    `pyproject.toml`, `*.config.*`

## 5. Area inference for this slice

Support only deterministic seeded-pilot inference:

- prefer enhancement spec slug such as `ENH-042-returns-exceptions.md`
- otherwise prefer route folder names such as `frontend/app/exceptions/`
- otherwise require an explicit area hint and fail clearly if one is not
  supplied

## 6. Determinism rules for this slice

- extractor output sorted by canonical repo-relative file path
- normalised bucket contents sorted by canonical repo-relative file path
- metadata lists sorted lexicographically
- tags deduplicated before sorting

## 7. Extension points

- multi-area batching for broader audit scopes
- route graph and component graph extraction
- repo-specific overlay rules for classification
- richer metadata inference
