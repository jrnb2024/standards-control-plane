# Workflow Harness

This harness exercises the reusable `policy-check.yml` workflow with two committed fixture trees:

- `fixture-pass/` is the baseline passing shape.
- `fixture-fail/` already carries a future-deny service shape, but no Rego rules ship in slice 020B.1 so it still evaluates to an empty summary today.

The selftest invokes the reusable workflow twice with `fixture-path` set to the pass and fail subtrees. `policy-check.yml` scopes changed-file discovery to that subtree and, when a policy-only PR does not touch the fixture files, falls back to enumerating the committed fixture tree so both control cases are still exercised.

Both fixtures currently expect an empty `findings` array, no disabled rules, no applied waivers, `bypass_emitted: false`, and an empty `conflict_gate`.

The selftest invokes `policy-check.yml` as a local reusable workflow (`uses: ./.github/workflows/policy-check.yml` without `@<ref>`). GitHub Actions does NOT support `@<ref>` for local reusable-workflow `uses:` lines (only cross-repo refs accept `@ref`); local workflows always run at the calling workflow's HEAD SHA. No pin update is needed on `workflow-selftest.yml` when `policy-check.yml` changes. The `validate-selftest-config` preflight job verifies the invocation count (currently three: fixture-pass, fixture-fail, fixture-simulate-token-exchange-failure) and the per-PR diff-based oracle ratchet instead.

`workflow-selftest` itself runs under `if: always()`, so the comparison step still executes after the fail fixture starts producing deny findings in 020C. The harness also asserts that deny findings force the reusable workflow to conclude with `failure`, which keeps summary generation and threshold enforcement tied together.

Existing fixture pairs are ratcheted: a PR may not change both `services.yml` and `expected-annotations.json` for the same committed fixture in one change. That keeps the oracle from becoming a tautology. The 020C transition is therefore staged by the fixture content already present here: `fixture-fail/services.yml` is pre-positioned to violate the future starter rule set, so 020C only needs to change `fixture-fail/expected-annotations.json` from the current empty summary to the deny summary that the new rules produce.

## TF-PIM-001 Wave E — simulate-token-exchange-failure fixture (mock-based)

TF-PIM-001 Wave E (TF-PIM-001-ARCH-002) adds a third reusable-workflow invocation to this harness: `fixture-simulate-token-exchange-failure-policy-check`. The invocation passes `simulate-app-token-failure: true` to `policy-check.yml`, which engages a stub-mode step that emits an `SCP-E001` workflow-command annotation (with `(selftest)` title suffix) and exits 1 BEFORE the real `actions/create-github-app-token` step runs. The selftest asserts the invocation's result is `failure` or `cancelled` (same by-design-failure shape as the `fixture-fail-policy-check` job; cancelled is acceptable under workflow-run cancellation). The fixture-path input is reused from `tests/workflow/fixture-pass` — no new fixture tree is required because the simulate step exits before fixture evaluation runs.

**Mock-vs-real-API decision (TF-PIM-001 impl WP plan-doc v0.4 §4 Wave E strategic-review decision):** v0.1 ships mock-based coverage only. The mock-mode flag is sufficient to verify the workflow's error-path code is wired correctly — that the simulate step emits SCP-E001 and that the workflow fails when the App token-exchange path is broken. Real-API coverage (exercising a real test App with an intentionally-broken installation, calling the real GitHub App API, verifying the actual failure mode) is tracked-forward as a TF-PIM-001-ARCH-002 follow-up. Real-API coverage is out-of-scope for this WP; it lands as a separate impl slice once TF-PIM-001 closes and Wave H restores PIM `main`'s required-check. The mock-based approach is deterministic in CI (no external GitHub App API dependency), simpler to author + test, and adequate as v0.1 of the selftest fixture.
