# Estate operating context — onboarding notes for non-Claude agents (disabled fixture)

This AGENTS.md also intentionally lacks the canonical Estate-context bootstrap
marker. It too WOULD fire `marker_absent`, but the `rules.SCP-R-031.disable:
true` override in this fixture's `rule-config.yaml` suppresses every SCP-R-031
deny. Expected outcome: no finding, gate green.
