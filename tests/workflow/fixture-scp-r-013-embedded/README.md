<!-- not an adopter file; .md is skipped by the conftest per-file pass -->
# fixture-scp-r-013-embedded  ← RED oracle

WP-SCP-037 ARCH-006 materialiser selftest fixture — **case 1** of the SPEC §TDD matrix.

A repo that vendors a divergent copy of the canonical ontology (`value_mappings.json`)
and declares **no** `ontology_contract` in `services.yml`. Its `repo_id` (the SCP repo
itself in selftest — no `ontology-repo-id` override) is **not** on the SCP-injected
authoring allowlist, so:

- **signal (3)** fires — embedded canonical ontology file in a non-authoring repo, and
- **signal (1)** fires — the embedded copy marks it an ontology consumer, but it declares
  no `ontology_contract` linking to `fashion-ontology-service`.

Both render as `::warning::` (SCP-R-013 is warn-baseline in both `WARN_BASELINE_RULES`
sites) so the reusable-workflow invocation runs `threshold: deny` yet stays **green**.

**RED→GREEN oracle:** with the fixture wired but the materialiser step ABSENT,
`input` lacks the ontology keys → the rule vacuously passes → the summary carries
**zero** SCP-R-013 findings → this two-finding oracle does not match → the compare step
fails **RED**. Adding the materialiser step makes the two findings appear → **GREEN**.
