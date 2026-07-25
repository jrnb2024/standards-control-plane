<!-- canonical:estate-context-bootstrap v1 -->
# Estate operating context — consult before acting
workspace_id: ws-mapp-fashion   org_id: mapp-labs   observed_at: 2026-07-25

This AGENTS.md carries the canonical marker (so `marker_absent` does NOT fire)
BUT its top-of-file block leaks dynamic Estate state (`workspace_id`, `org_id`,
`observed_at`) — the STATIC-MARKER invariant violation. Instruction files must
carry only the static marker, never live Estate state. SCP-R-031 fires a single
`dynamic_state` finding naming AGENTS.md.
