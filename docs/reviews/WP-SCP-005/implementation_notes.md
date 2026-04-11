# WP-SCP-005 Implementation Notes

## Scope delivered

- extended `findings.py` from read-only loading into:
  - audit-result reconciliation
  - deterministic history/open store generation
  - duplicate and scope-collision checks
  - persisted store writing with temp-file staging and rollback on caught failures
- extended the `audit` CLI with the explicit `--write-output` path while
  keeping read-only audit as the default
- updated tracked findings outputs and consult example to match the live
  persistence path
- added persistence, repo-backed CLI, and findings-command coverage
- validated both `open-findings.json` and `findings-history.json` against the
  schema in test

## Design choices

1. Reconciliation is area-scoped and evaluated-domain scoped:
   only open findings whose `area_id` matches the current audit scope and whose
   domains are marked `evaluated` are eligible for automatic resolution.

2. Identity is guarded, not guessed:
   `finding_id` remains the lifecycle key, but the implementation fails
   explicitly if the same `finding_id` appears under a different
   `(domain, area_id)` pair.

3. Duplicate refreshes collapse only when identical:
   exact duplicate findings in one audit refresh are collapsed; conflicting
   duplicates raise an error instead of being silently merged.

4. Persistence uses the honest phase-1 safety bound:
   each file is replaced atomically, and the writer rolls back on caught
   failures. A true crash-safe pair commit across both files is carried
   forward as backlog item `SCP-038`.

5. CLI tests now cover the repo-backed write path:
   the test suite temporarily seeds the tracked output files, runs the real
   `audit --write-output` path, asserts the reconciled result, and restores the
   repo outputs in-process.

## Touched modules

- `src/standards_control_plane/findings.py`
- `src/standards_control_plane/cli.py`
- `tests/test_findings_persistence.py`
- `tests/test_consult_retrieval.py`
- `tests/test_examples_validate.py`
- `output/findings/open-findings.json`
- `output/findings/findings-history.json`
- `examples/consult-response.json`
- `README.md`

## Backlog carry-forward

- `SCP-038` — add a stronger crash-safe pair-commit model for persisted
  findings stores once the storage model can support it cleanly.
