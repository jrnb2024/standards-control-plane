<!-- not an adopter file; .md is skipped by the conftest per-file pass -->
# fixture-scp-r-013-carveout  ← the authoring-source carve-out

WP-SCP-037 ARCH-006 materialiser selftest fixture — **case 3** of the SPEC §TDD matrix.

Holds an embedded `ontology_complete.yaml` and declares no `ontology_contract` — the
same shape as `fixture-scp-r-013-embedded` — BUT is invoked with
`ontology-repo-id: jrnb2024/fashion-labelling-agent`, an id on the SCP-injected
`ONTOLOGY_AUTHORING_ALLOWLIST` (FOS · FLA · kg-studio).

**Oracle: zero findings, green.** Proves the carve-out: an allowlisted authoring source
is exempt from the embedded-copy signal (3) AND is not treated as a consumer needing a
contract (signal 1) — the materialiser gates `ontology_consumer` off for authoring
sources.

The `ontology-repo-id` override is honoured ONLY in selftest and ONLY when
`GITHUB_REPOSITORY == jrnb2024/standards-control-plane` (the identity-gated seam) — a
real adopter can never reach it, so a non-FLA/FOS/kg repo cannot borrow the exemption.
