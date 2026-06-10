# WP-SCP-025 v2.0.0 — R1 3-lens adjudication (2026-06-10)

**Bundle:** rule input contract (`policies/rule-inputs.yaml` + `lib/policy_check_invocation.sh` feed rewrite) + SCP-R-012 born-at-deny + SCP-R-008 unblinded-at-warn + amended D-053 + release prep. Branch `feat/wp-scp-025-v2-deny-promotion` (84eca35 + this session's amendment).
**Review shape:** 3 parallel adversarial lenses (correctness / safety_bypass / completeness_governance), session-dispatched per D-057 Pattern 3 (dispatch `pattern3-20260610T194403Z-4307`).
**Outcome: R-FIXPOINT — 0 CRIT, 0 unaddressed MAJ.** Verdicts: correctness REJECT (CRIT **refuted with evidence**, residual MAJ/MIN folded) · safety_bypass APPROVE_WITH_FINDINGS (1 MAJ → DEFERRED, operator gate) · completeness APPROVE_WITH_FINDINGS (1 MAJ + 1 MIN → FIXED).

## Dispositions

| ID | Lens | Sev | Finding | Disposition |
|---|---|---|---|---|
| COR-R1-001 | correctness | CRIT | "`regex.match` in OPA is start-anchored like Python `re.match`, so SCP-R-012's `(^|/)versions/` gate never matches `alembic/versions/…`; 12/17 rule tests FAIL" | **REFUTED with evidence.** OPA `regex.match` is Go `regexp.MatchString` — UNANCHORED substring semantics. Empirical: `opa eval 'regex.match(`(^\|/)versions/`, "alembic/versions/0045_drop.py")'` → `true`; all **17/17** `scp_r_012` tests PASS; suite 185/185 (run 2026-06-10, recorded below). The reviewer applied Python `re.match` semantics to Rego and asserted a test-failure state that does not exist. No code change. |
| COR-R1-002 | correctness | MAJ | `.search()` vs `.match()` choice in the feed's matcher is load-bearing and undocumented — a future "tidy-up" to `.match()` would silently unfeed nested migration paths | **FIXED** — rationale comment added at the match site in `lib/policy_check_invocation.sh` (anchors live in the contract patterns; `.match()` would recreate the P0 for `(^\|/)`-style path patterns). |
| COR-R1-003 | correctness | MIN | Feed test for migrations doesn't state it validates the feed only, not rule acceptance | **FIXED** — scope note added to the test docstring pointing at `scp_r_012_test.rego` + the e2e pairing in `docs/releases/v2.0.0.md` §Verification. |
| SAFE-R1-001 | safety_bypass | MAJ | SCP-R-012's marker regex `(?m)^\s*(#\|//)\s*scp:protected-table-attested\s*$` also matches a marker line INSIDE a docstring/string literal — trivially placeable without genuine attestation | **DEFERRED — operator approval requested in the PR body.** This is the RULE-006 §5 acknowledged design trade-off: the marker is a conformance *assertion*; a false assertion is a review/trust failure, not a control failure (same trust model as SCP-R-003's `scp:vendoring-attested`). Tightening (docstring-context exclusion) is regex-hostile in Rego and risks false negatives on legitimate placements. Filed as FUP-SCP-R012-MARKER-CONTEXT-001 for a future evidence-driven RFC if real abuse is observed. All 6 other attack vectors (feed evasion, contract tampering, fallback abuse, E002 propagation, secret-leak via surrogates, YAML/JSON injection) explicitly checked CLOSED by the lens. |
| COMP-R1-001 | completeness | MAJ | `policies/SCP-R-008.rego` header still said "promotion to deny is a v1.4.0+ separate RFC after ≥4 weeks" + deny-rule comment referenced the v1.4.0 promotion path — contradicts amended D-053 | **FIXED** — header rewritten (plumbing-dormant history + unblinded-at-v2.0.0 + evidence-based promotion); deny-rule comment updated to reference the amended D-053 §Amendment. |
| COMP-R1-002 | completeness | MIN | `docs/OVERVIEW.md` status header pre-v2.0.0 stale | **FIXED** — header refreshed to the 2026-06-10 staged state. |

## Post-fix verification (re-run after the folds)

- `python3 tests/workflow/test_prepare_manifest_targets.py` — 12/12 PASS
- `opa test policies/ --ignore testdata` — 185/185 PASS (incl. 17/17 scp_r_012)
- `scripts/scp-pre-push-verify.sh` — 3/3 SCP-R gates, coverage ≥90 per rule
- `bash -n lib/policy_check_invocation.sh` — clean; `actionlint` — no new findings
- e2e (new feed → surrogate → Rego): `sk_live_…` `.env` → R-008 finding (8-char truncation), unattested `op.drop_table` under `versions/` → R-012 finding, attested → clean, non-migration `.py` → passthrough

## Residual for the operator

1. **SAFE-R1-001 defer** — approve the RULE-006 §5 trust-model rationale (marker-in-docstring counts) or request the tightening RFC before merge.
2. Post-merge ceremony: D-053 DRAFT → ACCEPTED; `release-gate.yml` dry-run; tag `v2.0.0`.
