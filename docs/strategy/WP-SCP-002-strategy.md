# Strategy — WP-SCP-002 Extractor and Area Normaliser

**Work Package:** `WP-SCP-002`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-11

## 1. Strategy

Build the shared evaluator input path before writing evaluator logic.

The extractor should remain filesystem-focused and deterministic. The normaliser
should remain contract-focused and deterministic. This work package should not
attempt semantic interpretation beyond seeded-pilot area inference supported by
explicit rules.

## 2. Why this slice now

`consult` can already retrieve rules and open findings, but `audit` still lacks
the shared input model it needs before any domain evaluator can operate
reliably.

This slice reduces future evaluator complexity by:

- centralising scope-path resolution
- centralising file inventory expansion
- centralising deterministic artefact classification
- making area-model shape explicit before governance and architecture logic
  arrives

## 3. Delivery shape

### 3.1 Extract first

Build a repo-bounded extractor that:

- resolves requested scope paths under project root
- canonicalises those paths before recursion
- recursively expands directories into files
- preserves deterministic order
- rejects missing paths, symlink-led boundary escapes, and non-file outputs
- emits an explicit extracted-file record payload rather than ad hoc tuples

### 3.2 Normalise second

Build a normaliser that:

- consumes extracted file records
- classifies artefacts into stable buckets
- infers metadata such as languages and frameworks
- derives a deterministic area identifier for the seeded pilot only when an
  explicit rule matches
- otherwise requires an explicit area hint instead of synthesising a plausible
  area id

### 3.3 Contract third

Lock the intermediate representation behind an explicit schema and example
payload so future evaluator work is constrained by stable contracts at both
seams:

- extracted-file record
- project-area payload

## 4. Seed corpus for this slice

Use `fixtures/returns-pilot/` as the first extraction corpus and extend it only
enough to exercise:

- enhancement spec detection
- prompt detection
- UI component detection
- service detection
- test detection
- config detection

The slice must include at least one concrete fixture file for every bucket
listed above.

## 5. Constraints

- no model-backed inference
- no evaluator scoring
- no findings mutations
- no service runtime changes

## 6. Expected follow-on

If this slice lands cleanly, the next work package can implement governance
evaluation on top of the normalised area model rather than on raw path lists.
