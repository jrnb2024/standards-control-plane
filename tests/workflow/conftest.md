# Workflow Harness

This harness exercises the reusable `policy-check.yml` workflow with two committed fixture trees:

- `fixture-pass/` is the baseline passing shape.
- `fixture-fail/` already carries a future-deny service shape, but no Rego rules ship in slice 020B.1 so it still evaluates to an empty summary today.

The selftest invokes the reusable workflow twice with `fixture-path` set to the pass and fail subtrees. `policy-check.yml` scopes changed-file discovery to that subtree and, when a policy-only PR does not touch the fixture files, falls back to enumerating the committed fixture tree so both control cases are still exercised.

Both fixtures currently expect an empty `findings` array, no disabled rules, no applied waivers, `bypass_emitted: false`, and an empty `conflict_gate`.

The selftest pins `policy-check.yml` to a specific commit SHA. Any PR that changes `.github/workflows/policy-check.yml` must update both pinned `uses:` lines in `workflow-selftest.yml` to the PR head SHA before merge; the preflight job enforces this.

Existing fixture pairs are ratcheted: a PR may not change both `services.yml` and `expected-annotations.json` for the same committed fixture in one change. That keeps the oracle from becoming a tautology. The 020C transition is therefore staged by the fixture content already present here: `fixture-fail/services.yml` is pre-positioned to violate the future starter rule set, so 020C only needs to change `fixture-fail/expected-annotations.json` from the current empty summary to the deny summary that the new rules produce.
