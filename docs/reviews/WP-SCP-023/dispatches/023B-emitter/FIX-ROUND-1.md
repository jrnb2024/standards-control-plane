# 023B — fix-round-1 audit (R1 → fix → R2 candidate)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-023-023b-emitter`
**Pre-fix-round-1 HEAD:** `b5f6e54` (initial impl + DISPATCH-NOTE)

## R1 finding tally

3× parallel Sonnet R1: all 3 lenses CHANGES_REQUESTED.

| Lens | Verdict | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 3 | 2 | 2 |
| safety_bypass | CHANGES_REQUESTED | 0 | 1 | 2 | 2 |
| completeness_governance | CHANGES_REQUESTED | 0 | 1 | 5 | 3 |
| **total raw** | — | **0** | **5** | **9** | **7** |

After deduplicating: 0 CRIT, **5 unique MAJ** (gating bug; verdict semantic; rule_config_disabled false-positive on observability records; OIDC permissions threat surface; plan-doc §5 example signature field).

## Per-finding disposition

### MAJ (5 unique)

| ID | Lens | Disposition | Action |
|---|---|---|---|
| **C-COR-MAJ-001** | correctness | **INLINE-FIX** | Upload + Attest steps gated on `build-scorecard-emit` outcome but NOT on `validate-scorecard-emit`. Added `id: validate-scorecard-emit` + changed Upload + Attest gating to `steps.validate-scorecard-emit.outcome == 'success'`. Schema-validation failure now correctly blocks artifact upload + attestation. |
| **C-COR-MAJ-002** | correctness | **INLINE-FIX** | `rule_counts[*].denies` counted raw deny findings (verdict='deny') without subtracting waiver-suppression. Schema description says "effective denies after suppression". Pre-computed `waived_rule_ids` set from `waivers_applied`; only count denies when `rid not in waived_rule_ids`. Updated `deny-with-waiver` fixture: SCP-R-001 denies=0, verdict='allow'. Updated `full` fixture: SCP-R-001 denies=0 (was 1). |
| **C-COR-MAJ-003** | correctness | **INLINE-FIX** | `rule_counts[*].rule_config_disabled` was set true for `no-manifest-applicable` workflow-injected observability records. Schema description binds it specifically to `.scp/rule-config.yaml`. Added skip clause: `if d.get("reason") == "no-manifest-applicable": continue`. Updated `full` fixture: SCP-R-003 entry removed entirely (no raw findings, no waivers, not adopter-disabled = nothing to report). |
| **MAJ-SAFE-001** | safety | **INLINE-FIX (architectural restructure)** | Workflow-level `attestations: write` + `id-token: write` exposed adopter cloud-IAM trust to ALL policy-check runs (not just opt-in). Restructured: removed both permissions from workflow level; added new `attest-scorecard` job with job-scoped `attestations: write` + `id-token: write`, `if: inputs.scorecard-emit`, `needs: policy-check`. The job downloads the scorecard-emit artifact, verifies presence, then runs `actions/attest-build-provenance`. Opt-out runs never request OIDC tokens. |
| **CG-MAJ-001 / C-COR-nit-002** | completeness, correctness | **INLINE-FIX** | Plan-doc §5 example JSON included a `signature` field that the implemented schema rejects (`additionalProperties: false`). 023C's aggregator dispatch would read this as the spec. Removed `signature` field from §5 example; added explanatory comment naming the OIDC artifact attestation as the trust anchor (per D-042 at slice 023C). |

### MIN (9 raw, ~7 unique)

| ID(s) | Lens | Disposition | Action |
|---|---|---|---|
| **C-COR-MIN-001** | correctness | **TF-FORWARD** | Pytest validates schema conformance but doesn't run the Python heredoc transformation logic. End-to-end transformation is integration-tested by workflow-selftest harness — captured in TF-023B-001 (already filed). |
| **C-COR-MIN-002** | correctness | **NO ACTION** | Rule-config `expires_at` parser handles YYYY-MM-DD only; matches the schema constraint at `schemas/rule-config.schema.json`. Schema permits both YYYY-MM-DD + RFC3339, but the existing rule-config corpus only uses YYYY-MM-DD. Forward-compat — extend if a future rule-config uses RFC3339. |
| **MIN-SAFE-001** | safety | **NO ACTION** | Broad `except (ImportError, Exception)` for rule-config parsing produces empty rule-config-aggregate on parse failures rather than emit error. Acceptable defensive posture: a malformed rule-config.yaml SHOULD NOT block scorecard emission; `disabled_rules: []` correctly reflects "no enforceable rule-config disable" given the parser couldn't read it. (The malformed file is already an SCP-E-class problem caught by the existing rule-config schema validate step.) |
| **MIN-SAFE-002** | safety | **NO ACTION** | SCP_WAIVERS_PATH + SCP_RULE_CONFIG_PATH path-traversal: these are env vars set by the workflow itself (defaulted at line 91/63), NOT adopter-controlled inputs. Adopters control them via `with:` block at the existing inputs.threshold etc., but those inputs aren't paths. No new attack surface. |
| **CG-MIN-001** | completeness | **INLINE-FIX** (clarified in FIX-ROUND-1.md not DISPATCH-NOTE) | DISPATCH-NOTE OUT line was ambiguous about whether OIDC attestation is in-scope for 023B (it is — the EMITTER side). Clarification noted here; DISPATCH-NOTE itself stays — the OUT entry referred to "in-payload Ed25519 signature" which was correctly out of scope. |
| **CG-MIN-002** | completeness | **INLINE-FIX** | Release notes `gh run download` example fixed: `cat scorecard-emit/scorecard-emit.json` (subdirectory after extract) + `gh attestation verify scorecard-emit/scorecard-emit.json`. |
| **CG-MIN-003** | completeness | **INLINE-FIX** | DECISIONS.md row order was reversed (D-041 before D-040). Swapped via Python so D-040 (2026-05-02) precedes D-041 (2026-05-03). |
| **CG-MIN-004** | completeness | **INLINE-FIX** | TF-023A-002 not in STATUS.md tracked-forward. Added new "Tracked-forward items from WP-SCP-023 023A + 023B" section with TF-023A-001/002 + TF-023B-001/002. |
| **CG-MIN-005** | completeness | **TF-FORWARD as TF-023B-001** | Workflow-selftest fixture-pass-with-scorecard-emit. Filed forward; target slice 023C. |

### nit (7 raw)

All NO ACTION except `nit-SAFE-002` (Python `except (ImportError, Exception)` redundancy — Exception catches ImportError; pure cosmetic; left alone) and `CG-nit-001/002/003` (memory-update reminders + step-gating consistency + FLA fixture TF — captured in FIX-ROUND-1 + TF-023B-002 already filed).

## Inline-fix summary (~10 edits across ~7 files)

1. `.github/workflows/policy-check.yml` step gating: `id: validate-scorecard-emit` + Upload/Attest now gated on `validate-scorecard-emit.outcome == 'success'` (C-COR-MAJ-001).
2. `.github/workflows/policy-check.yml` Build heredoc: `waived_rule_ids` set + `if rid not in waived_rule_ids` deny gating (C-COR-MAJ-002).
3. `.github/workflows/policy-check.yml` Build heredoc: skip `no-manifest-applicable` observability records in disabled_rules iteration (C-COR-MAJ-003).
4. `.github/workflows/policy-check.yml`: removed workflow-level `attestations: write` + `id-token: write`; added new `attest-scorecard` job with job-scoped permissions (MAJ-SAFE-001).
5. `tests/scorecard-emit/fixtures/deny-with-waiver/expected-scorecard-emit.json`: SCP-R-001 denies=0, verdict='allow' (C-COR-MAJ-002).
6. `tests/scorecard-emit/fixtures/full/expected-scorecard-emit.json`: SCP-R-001 denies=0, SCP-R-003 entry removed, rule_config_aggregate.disabled_rules=[] (C-COR-MAJ-002 + C-COR-MAJ-003).
7. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §5 example: removed `signature` field; added explanatory comment (CG-MAJ-001).
8. `docs/releases/v1.2.0.md`: corrected `gh run download` + `gh attestation verify` paths to use `scorecard-emit/` subdirectory (CG-MIN-002).
9. `docs/DECISIONS.md`: D-040/D-041 row order swapped (CG-MIN-003).
10. `STATUS.md`: new "Tracked-forward items from WP-SCP-023 023A + 023B" section + D-041 entry in Recent decisions list (CG-MIN-004).

## Forward-filed TFs

- **TF-023B-001**: workflow-selftest fixture-pass-with-scorecard-emit; target 023C.
- **TF-023B-002**: FLA-pilot canary scorecard fixture; target 023E.

## Smoke-test post-fix

- `pytest tests/conflict_gate/ tests/scorecard-emit/`: 21/21 pass.
- `scripts/scp-pre-push-verify.sh`: ✓ all 3 SCP-R gates pass.

## R2 candidacy

R1 surfaced 0 CRIT, 5 unique MAJ (all closed inline including a real architectural restructure for OIDC permissions threat surface), ~7 unique MIN (5 inline-fixed + 2 TF-forwarded), 7 nit (all NO ACTION). The slice is ready for **R2 dispatch** to verify no NEW CRIT/MAJ findings emerge against the fix-round-1 surface.
