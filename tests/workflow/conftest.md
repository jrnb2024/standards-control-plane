# Workflow Harness

This harness exercises the reusable `policy-check.yml` workflow with two committed fixture trees:

- `fixture-pass/` is the baseline passing shape.
- `fixture-fail/` is intentionally identical in slice 020B.1 because no Rego rules ship yet.

Both fixtures currently expect an empty `findings` array, no disabled rules, no applied waivers, `bypass_emitted: false`, and an empty `conflict_gate`.

Slice 020C changes the meaning of `fixture-fail/`: its `services.yml` and `expected-annotations.json` will diverge from `fixture-pass/` once SCP-R-001/002/003 land, and the selftest workflow will then assert a deny-shaped summary for that fixture instead of today's empty result.
