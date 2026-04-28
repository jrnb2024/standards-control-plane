# WILL-FAIL-AFTER-020C

This fixture is deliberately non-divergent in slice 020B.1 because the reusable
workflow ships before any Rego rules exist.

When slice 020C lands SCP-R-001, SCP-R-002, and SCP-R-003, this fixture's
`services.yml` and `expected-annotations.json` should change together so the
workflow selftest asserts the expected deny summary instead of today's empty
findings payload.
