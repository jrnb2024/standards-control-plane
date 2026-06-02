# This repo runs the acc-hook — onboarding notes

This CLAUDE.md is **intentionally missing** the canonical onboarding marker in its
top-of-file lines (the SCP-R-030 `marker_absent` fixture). It still references the
always-allowed `docs/**` paths, a `scripts/operator/scp-pattern3-dispatch.sh`
dispatch ceremony, and the never-disable rule — but because the marker is absent
the rule fires `marker_absent` and the element checks are gated off (they require
`has_marker`), so this is the single expected finding.

Because SCP-R-030 ships warn-baseline, this finding renders as a `::warning::` and
the merge gate stays GREEN.
