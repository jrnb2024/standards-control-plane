<!-- not an adopter file; .md is skipped by the conftest per-file pass -->
# fixture-scp-r-013-no-self-assert  ← the load-bearing bypass guard

WP-SCP-037 ARCH-006 materialiser selftest fixture — **case 4** of the SPEC §TDD matrix.

Identical shape to `fixture-scp-r-013-embedded` (embedded `ontology_complete.yaml`, no
`ontology_contract`) with two additions: `services.yml` self-asserts
`ontology_role: authoring-source`, and it is invoked with
`ontology-repo-id: jrnb2024/sneaky-app` — **not** on the allowlist.

**Oracle: two findings (embedded-copy + missing-contract), green.** This is the keystone
bypass guard: the adopter-asserted `authoring-source` role is IGNORED (the rego carve-out
reads only the SCP-injected allowlist), so the findings STILL fire. Contrast with
`fixture-scp-r-013-carveout`, whose only difference is a genuinely-allowlisted
`ontology-repo-id` — it produces zero findings. Together the two fixtures prove the
carve-out keys on the SCP allowlist and cannot be spoofed from adopter content.

**RED→GREEN oracle:** with the materialiser ABSENT the rule vacuous-passes → zero
findings → this oracle mismatches → **RED**; adding the step makes both findings appear
→ **GREEN**.
