# WILL-FAIL-AFTER-020C

This fixture already carries a deliberate future-rule violation in slice 020B.1,
even though the reusable workflow still evaluates to an empty summary because no
Rego rules ship yet.

`workflow-selftest.yml` now invokes `policy-check.yml` with
`fixture-path: tests/workflow/fixture-fail`, so the fail case is isolated from
the pass fixture and still executes when a PR changes only `policies/**`.

When slice 020C lands SCP-R-001, SCP-R-002, and SCP-R-003, update only
`expected-annotations.json` for this fixture to the deny-shaped summary emitted
by the new rules. The reusable workflow keeps `threshold: deny`, so this job
should then conclude with `failure`; `workflow-selftest` still runs under
`if: always()` and compares the uploaded summary before asserting that the
deny findings and failing job result agree. The selftest ratchet forbids
changing both halves of an existing fixture pair in the same PR.
