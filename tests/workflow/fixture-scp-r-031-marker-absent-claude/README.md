<!-- not the adopter CLAUDE.md; .md is skipped by the conftest per-file pass -->
# fixture-scp-r-031-marker-absent-claude

WP-ESC-012b selftest fixture — opted-in adopter whose `CLAUDE.md` lacks the
canonical Estate-context bootstrap marker while `AGENTS.md` carries it →
**exactly one** SCP-R-031 `marker_absent` finding naming **CLAUDE.md**, gate
GREEN (warn-baseline).

- `rule-config.yaml` — `estate-context-marker: true`.
- `repo/CLAUDE.md` — present, marker absent from the top 5 lines.
- `repo/AGENTS.md` — present, marker on line 1 (conformant sibling).
- `expected-annotations.json` — one SCP-R-031 `marker_absent` deny finding on CLAUDE.md; gate green.
