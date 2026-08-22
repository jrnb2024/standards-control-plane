# WP-SCP-037 ARCH-006 materialiser — build-stage 3-lens R1 dispositions

**Change:** activate the dormant `SCP-R-013` (ARCH-006 ontology-canonical-consumption)
via a companion `opa eval` materialiser step in `policy-check.yml` + 4 selftest fixtures.
Branch `feat/wp-scp-037-arch-006-materialiser` (dispatch `pattern3-20260710T232052Z-67597`,
off `c0ec93f`). Plan: `docs/reviews/WP-SCP-037/ARCH-006-materialiser-plan.md` v2.
Closes `FUP-WP-SCP-037-ARCH-006-MATERIALISER-001`.

Three parallel adversarial lenses (GOV-004): correctness / safety_bypass /
completeness_governance. **Outcome: ACCEPT at R-FIXPOINT** — one correctness BLOCKER
found and FIXED; no safety hard-stop; no silent descope.

## Build-time refinements of the plan draft (in-intent; RED-first surfaced)

Both are corrections of the plan's drafted materialiser, recorded here (and inline in the
step + STATUS/BACKLOG) so they are not silent deviations. Both were confirmed correct by
all three lenses.

1. **`is_skippable` measured RELATIVE to `fixture_root` (component-based), not the absolute
   path.** The plan draft skipped any path with `startswith("tests/")` — which would have
   skipped EVERY selftest fixture (they live under `tests/workflow/`), so the rule could
   never fire in the selftest and RED→GREEN was unreachable. Fix: `os.path.relpath(path,
   fixture_root)` then skip on a `tests`/`fixtures`/`__fixtures__` path component (or
   `.example` suffix). In a real adopter (`fixture_root="."`) their own `tests/`/`fixtures/`
   trees are still skipped; the fixture subtree is scanned. Correct on both sides.
2. **`ontology_consumer = raw_consumer and not is_authoring_source`.** The rego
   authoring-source carve-out exempts signals (3)/(4) (embedded-file / local-class) but NOT
   signal (1) (missing-contract). Without gating, the carve-out fixture (an allowlisted
   authoring source holding `ontology_complete.yaml`) would trip signal (1). Gating the
   consumer signal off for allowlisted authoring sources closes the gap so an authoring
   source emits zero findings. Belt-and-braces with the rego carve-out.

## Lens 1 — CORRECTNESS

**Verdict: REJECT → ACCEPT after the one-line fix below.** BLOCKER 1 · MAJOR 0 · MINOR 0.

- **BLOCKER-1 (FIXED).** `fixture-fail-policy-check` still forked off the old chain tail
  (`stash-fixture-scp-r-028-trust-boundary-summary`), so it launched CONCURRENTLY with the
  new `fixture-scp-r-013-embedded-policy-check` (both need that stash). Every
  `policy-check.yml` invocation uploads the artifact hardcoded `name: policy-check-summary`;
  two concurrent producers collide (409 duplicate-name) and the stash delete-guard
  (`len(matches) != 1`) trips → selftest RED. The selftest depends on a single LINEAR
  producer chain (one invocation live at a time). **Fix applied:** re-pointed
  `fixture-fail-policy-check` `needs:` from `stash-fixture-scp-r-028-trust-boundary-summary`
  to `stash-fixture-scp-r-013-no-self-assert-summary` (the new tail). Verified: exactly one
  job now needs the r028 tail (`013-embedded`), and the full 19-producer chain is linear
  (…r028-trust-boundary → 013-embedded → compliant → carveout → no-self-assert → fixture-fail
  → sha-validation error chain). `fixture-fail` remains the terminal surviving producer, so
  the aggregator's bare-name `policy-check-summary` download invariant is preserved.
- Verified CORRECT: all 6 input keys match `SCP-R-013.rego`'s `object.get(input,…)`;
  `to_finding` emits the exact 6-key finding shape; all 4 oracles reproduce byte-for-byte
  (order = sort by `(rule_id, message)`; marker `file` = full checkout-root path;
  missing-contract `file` = rego-hardcoded `"services.yml"`); both build-refinements
  effective; no `--combine` (conftest per-file pass untouched, zero deny-gate regression);
  fail-open merges nothing on opa error; dedup + deterministic sort; uses-count guard = 19.

## Lens 2 — SAFETY_BYPASS (HARD-STOP lens)

**Verdict: ACCEPT.** BLOCKER 0 · MAJOR 0 · MINOR 2 (both informational/forward-looking).

- Trust-boundary PASS: `repo_id` is `$GITHUB_REPOSITORY` in production unconditionally; the
  `ontology-repo-id` override is triple-gated (`selftest_mode ∧ selftest_repo_id ∧
  gh_repo=="jrnb2024/standards-control-plane"`) — in a reusable workflow `$GITHUB_REPOSITORY`
  is the CALLER, so an adopter forcing `selftest-mode:true` cannot reach it. Identical anchor
  to the ratified WP-SCP-028 auth simulate seam. Self-asserted `ontology_role` is never read
  (proven by the no-self-assert fixture). Fail-open is warn-baseline-consistent and
  non-weaponisable (opa inputs are SCP-built + coerced; the rego is SCP-owned).
- **MINOR-1 (FOLDED).** At a future deny-promotion the `tests/`/`fixtures/`/`.example` skip
  becomes an evasion vector (a vendored copy hidden under `tests/` would escape a BLOCKING
  gate). No impact at warn-baseline. **Disposition:** added as item (c) to the inline D-059
  gate note in the materialiser step, and tracked as
  `FUP-WP-SCP-037-ARCH-006-MARKER-SKIP-EVASION-AT-DENY-PROMOTE-001` (fires only if/when a
  D-NNN deny-promotes SCP-R-013).
- **MINOR-2 (no action).** `ontology-repo-id` is a public reusable-workflow input but is
  correctly ignored unless identity-gated; security rests on `$GITHUB_REPOSITORY` integrity —
  the same assumption the estate already accepts for the auth seam. Documented in the input
  description.

## Lens 3 — COMPLETENESS_GOVERNANCE

**Verdict: ACCEPT.** BLOCKER 0 · MAJOR 0 · MINOR 2.

- Full plan "Files touched" + "Sequence" matrix verified present — no silent descope.
  `kg-studio` correctly ON `ONTOLOGY_AUTHORING_ALLOWLIST` per operator-ratified option A
  (plan draft deliberately left it out). Version bump v2.0.0→v2.1.0 is the right class
  (additive minor: fires a dormant warn rule + one new optional input), matching the v1.6.0
  auth-materialiser precedent. WARN_BASELINE coupling holds (SCP-R-013 in both sites since
  §1a, untouched). D-058 LINKAGE-not-VALUES respected (never reads ontology VALUES). Docs
  consistent across VERSIONING.md / version-manifest.json / STATUS.md / BACKLOG.md. FUP
  closed honoring both trust-boundary constraints.
- **MINOR-1 (RESOLVED).** This dispositions doc was forward-referenced but not yet authored —
  it is the output of this review round; authored here.
- **MINOR-2 (FUP).** Signals (2) bespoke `canonical_service` and (5) local `fallback` have
  opa unit coverage (`policies/tests/scp_r_013_test.rego`) but no dedicated end-to-end
  selftest fixture (the plan scoped exactly 4). Teeth-sharpening, not a descope. Tracked as
  `FUP-WP-SCP-037-ARCH-006-SIGNALS-2-5-E2E-FIXTURE-001` (P3).

## Local verification (pre-push)

- `opa test` per-rule (scp_common + SCP-R-013 + its test): 94% coverage (≥90 gate). Rego
  untouched → no unit-test regression.
- RED proof: empty input → 0 findings (dormant). GREEN proof: all 4 fixtures byte-match
  their oracles end-to-end through a faithful standalone materialiser probe
  (extractor → opa → to_finding → merge → sort).
- `actionlint` clean (no new issues); both workflows + version-manifest parse; the
  materialiser heredoc python compiles; selftest producer chain is linear (19 invocations).

## Disposition: **ACCEPT at R-FIXPOINT**

BLOCKER-1 fixed; safety MINOR-1 folded (inline note + FUP); completeness MINORs resolved
(this doc) / tracked (FUP). Two new FUPs filed. Operator-attended next: gated-merge → cut
v2.1.0 → cohort pin-bump so the 13 gated adopters pick up the firing rule → open a
D-NNN-style observation window.
