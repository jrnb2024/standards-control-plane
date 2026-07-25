<!-- not the adopter CLAUDE.md; .md is skipped by the conftest per-file pass -->
# fixture-scp-r-031-marker-present-both

WP-ESC-012b selftest fixture — the **PASS** row: opted-in, and BOTH `CLAUDE.md`
AND `AGENTS.md` carry the canonical Estate-context bootstrap marker in their
top-of-file block → **no SCP-R-031 finding**, gate green.

Layout (the `repo/` subtree is the reusable-workflow `fixture-path`; the
`rule-config.yaml` + `expected-annotations.json` live OUTSIDE the subtree so the
conftest per-file pass never enumerates them — the repo-level `opa eval` step
reads `rule-config.yaml` via `rule-config-path`):

- `rule-config.yaml` — `estate-context-marker: true` (opts the fixture-repo in to SCP-R-031).
- `repo/CLAUDE.md` — carries the canonical marker on line 1.
- `repo/AGENTS.md` — carries the canonical marker on line 1 (the SECOND file SCP-R-031 gates).
- `expected-annotations.json` — `findings: []` (both surfaces linked → no finding).
