<!-- not the adopter CLAUDE.md; .md is skipped by the conftest per-file pass -->
# fixture-scp-r-031-dynamic-state-present

WP-ESC-012b selftest fixture — the **STATIC-MARKER invariant** row: both files
carry the canonical marker (so `marker_absent` does NOT fire), but `AGENTS.md`
leaks dynamic Estate tokens (`workspace_id`, `org_id`, `observed_at`) into its
top-of-file block → **exactly one** SCP-R-031 `dynamic_state` finding naming
AGENTS.md, gate GREEN (warn-baseline).

This proves the negative check: an instruction file must carry ONLY the static
marker, never live Estate state (which belongs to the runtime Estate-context
plane, not a committed file — a leak is a drift/stale-context hazard).

- `rule-config.yaml` — `estate-context-marker: true`.
- `repo/CLAUDE.md` — marker on line 1, clean top block (conformant sibling).
- `repo/AGENTS.md` — marker present BUT a forbidden dynamic token in the top block.
- `expected-annotations.json` — one SCP-R-031 `dynamic_state` deny finding on AGENTS.md; gate green.
