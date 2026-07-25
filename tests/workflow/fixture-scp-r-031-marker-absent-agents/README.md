<!-- not the adopter CLAUDE.md; .md is skipped by the conftest per-file pass -->
# fixture-scp-r-031-marker-absent-agents  ← LOAD-BEARING

WP-ESC-012b selftest fixture — the **non-negotiable second-file teeth**: an
opted-in adopter whose `AGENTS.md` lacks the canonical Estate-context bootstrap
marker (while `CLAUDE.md` carries it) must emit **exactly one** SCP-R-031
`marker_absent` finding naming **AGENTS.md**, gate GREEN (warn-baseline).

This is the keystone that distinguishes SCP-R-031 from SCP-R-030: SCP-R-030
gates CLAUDE.md ONLY, so it would pass this repo silently. SCP-R-031 gates BOTH
instruction surfaces, so it catches the un-marked AGENTS.md. Paired with
`fixture-scp-r-031-marker-present-both` (which produces NO finding), this fixture
proves the rule has teeth on the AGENTS.md file specifically.

- `rule-config.yaml` — `estate-context-marker: true`.
- `repo/CLAUDE.md` — present, marker on line 1 (conformant sibling).
- `repo/AGENTS.md` — present, marker absent from the top 5 lines.
- `expected-annotations.json` — one SCP-R-031 `marker_absent` deny finding on AGENTS.md; gate green.
