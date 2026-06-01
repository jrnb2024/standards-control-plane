# This repo runs the acc-hook — onboarding notes (disabled fixture)

This CLAUDE.md intentionally lacks the canonical onboarding marker, so SCP-R-030
WOULD fire `marker_absent` — except this fixture's `rule-config.yaml` sets
`rules.SCP-R-030.disable: true`, which suppresses the deny inside `data.main.deny`.
The expected outcome is therefore a vacuous-pass (no finding), gate green.
