<!-- not the adopter CLAUDE.md; .md is skipped by the conftest per-file pass -->
# fixture-scp-r-030-pass

WP-SCP-030 companion-activation selftest fixture — **row 1** of the SPEC §6 matrix
(opted-in, full canonical preamble → **PASS**, no SCP-R-030 finding, gate green).

Layout (the `repo/` subtree is the reusable-workflow `fixture-path`; the
`rule-config.yaml` + `expected-annotations.json` live OUTSIDE the subtree so the
conftest per-file pass never enumerates them — the repo-level `opa eval` step
reads `rule-config.yaml` via `rule-config-path` and the orchestrator reads the
oracle directly):

- `rule-config.yaml` — `acc-hook-installed: true` (opts the fixture-repo in to SCP-R-030).
- `repo/CLAUDE.md` — carries the canonical marker on line 1 + all four preamble
  elements (always-allowed list, ceremony pointer, never-disable rule).
- `expected-annotations.json` — `findings: []` (healthy preamble → no finding).
