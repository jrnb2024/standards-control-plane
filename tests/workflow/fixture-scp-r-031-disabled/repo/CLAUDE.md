# Estate operating context — onboarding notes (disabled fixture)

This CLAUDE.md intentionally lacks the canonical Estate-context bootstrap
marker, so SCP-R-031 WOULD fire `marker_absent` — except this fixture's
`rule-config.yaml` sets `rules.SCP-R-031.disable: true`, which suppresses the
deny inside `data.main.deny`. The expected outcome is a vacuous-pass (no
finding), gate green.
