# Estate operating context — onboarding notes

This CLAUDE.md is **intentionally missing** the canonical Estate-context
bootstrap marker in its top-of-file block (the SCP-R-031 `marker_absent`
fixture for the CLAUDE.md surface). Because the marker is absent from the
first 5 lines, SCP-R-031 fires a single `marker_absent` finding naming
CLAUDE.md. The AGENTS.md sibling in this fixture DOES carry the marker, so
only CLAUDE.md is named.

Because SCP-R-031 ships warn-baseline, this finding renders as a `::warning::`
and the merge gate stays GREEN.
