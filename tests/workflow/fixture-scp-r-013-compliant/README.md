<!-- not an adopter file; .md is skipped by the conftest per-file pass -->
# fixture-scp-r-013-compliant  ← the no-finding control

WP-SCP-037 ARCH-006 materialiser selftest fixture — **case 2** of the SPEC §TDD matrix.

A well-behaved ontology consumer: `services.yml` declares a valid `ontology_contract`
that names the canonical `fashion-ontology-service`, pins a `canonical_version`, lists
endpoints, and uses a fail-closed (non-local) fallback. No vendored ontology files, no
local canonicaliser class.

**Oracle: zero findings, green.** This is the control that proves the materialiser does
NOT false-fire on a compliant consumer — none of the five SCP-R-013 signals trip. It
stays green identically before and after the materialiser step lands (both states
vacuous-pass / compliant-pass), so it is not a RED oracle; it guards against
over-firing.
