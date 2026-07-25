<!-- not the adopter CLAUDE.md; .md is skipped by the conftest per-file pass -->
# fixture-scp-r-031-disabled

WP-ESC-012b selftest fixture — the **suppression** row: opted-in, BOTH files
lack the marker (so SCP-R-031 would otherwise fire two `marker_absent`
findings), but `rules.SCP-R-031.disable: true` in `rule-config.yaml` suppresses
the deny inside `data.main.deny` → vacuous-pass (no finding), gate green.

Exercises the standard SCP rule-config disable mechanism (the same
`scp_rule_config_disabled` path every SCP-R-NNN rule reuses from
`scp_common.rego`).

- `rule-config.yaml` — `estate-context-marker: true` AND `rules.SCP-R-031.disable: true`.
- `repo/CLAUDE.md` — present, marker absent (would fire, suppressed).
- `repo/AGENTS.md` — present, marker absent (would fire, suppressed).
- `expected-annotations.json` — `findings: []` (disable suppresses both denies); gate green.
