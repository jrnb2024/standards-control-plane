# Estate operating context — onboarding notes for non-Claude agents

This AGENTS.md is **intentionally missing** the canonical Estate-context
bootstrap marker in its top-of-file block (the SCP-R-031 `marker_absent`
fixture for the AGENTS.md surface). Because the marker is absent from the
first 5 lines, SCP-R-031 fires a single `marker_absent` finding naming
AGENTS.md. The CLAUDE.md sibling DOES carry the marker, so only AGENTS.md is
named — the proof that SCP-R-031 gates the SECOND file, unlike SCP-R-030.

Because SCP-R-031 ships warn-baseline, this finding renders as a `::warning::`
and the merge gate stays GREEN.
