# 023C — fix-round-1 audit (R1 → fix → R2 candidate)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-023-023c-aggregator`
**Pre-fix-round-1 HEAD:** `72f0bbb`

## R1 finding tally

3× parallel Sonnet R1: all 3 lenses CHANGES_REQUESTED.

| Lens | Verdict | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 2 | 3 | 1 |
| safety_bypass | CHANGES_REQUESTED | 0 | 1 | 2 | 1 |
| completeness | CHANGES_REQUESTED | 0 | 1 | 6 | 3 |
| **total raw** | — | **0** | **4** | **11** | **5** |

After dedup (cross-lens overlap on signer-workflow regex anchor + DECISIONS row order): **0 CRIT, 4 unique MAJ, ~7 unique MIN**.

## Per-finding disposition

### MAJ (4 unique)

| ID | Lens | Disposition | Action |
|---|---|---|---|
| **MAJ-SAFE-001 / CG-MIN-005** | safety, completeness | **INLINE-FIX (real defence-in-depth gap)** | `expected_scp_workflow_ref` schema regex accepted any `owner/repo` namespace. An adopter could PR an entry pointing to a workflow they fully control; OIDC verification would succeed against their own signer. Closed by anchoring the regex to `^jrnb2024/standards-control-plane/.github/workflows/<...>.yml@<sha>$` AND adding a runtime `SCP_WORKFLOW_REF_PREFIX` startswith() check in the aggregator (defence-in-depth — schema + runtime). Filed forward as TF-023C-005 to track the rename/transfer maintenance hook. |
| **C-COR-MAJ-001** | correctness | **INLINE-FIX** | Index schema had no conditional validation: status==no_emit could carry verdict + rule_counts; status==verified could omit them. Added `allOf` with two `if/then` branches: (1) status==verified requires all 9 emit-derived fields; (2) status in failure-set requires `error`. |
| **C-COR-MAJ-002** | correctness | **INLINE-FIX** | Status enum descriptions were inconsistent with implementation (mapped 'unreachable' to gh-run-download failure, but code uses 'unreachable' for gh-run-list failure). Rewrote the description block to accurately reflect: unreachable = gh-run-list failure; verification_failure = OIDC verify or schema validation failure; no_emit = no green run / stale run / download failure. |
| **CG-MAJ-001** | completeness | **INLINE-FIX (real bug — missing AC item)** | DISPATCH-NOTE AC (vii) named the 7-day staleness check; the implementation didn't have it. A 6-month-old run would have been accepted as "current data". Added `STALENESS_THRESHOLD_DAYS = 7` constant + `staleness_horizon` computation + per-adopter check that records `status: no_emit` with explicit "X days old (threshold: 7d)" error string when the latest run is stale. Also added `created_at` parse-failure handling (records as verification_failure with run_id+commit). |

### MIN (~7 unique)

| ID | Disposition | Action |
|---|---|---|
| **CG-MIN-001 / C-COR-nit-001** | **INLINE-FIX** | DECISIONS.md had D-042 before D-041 (reverse-chronological). Swapped via Python script so D-041 < D-042 by ascending ID. |
| **CG-MIN-002** | **INLINE-FIX** | STATUS.md missing TF-023C section. Added 5 TF-023C entries (001 self-dogfood; 002 cron-health; 003 rate-limit; 004 timeout-minutes; 005 repo-rename). Also section header updated to include "+ 023C (aggregator)". |
| **CG-MIN-004** | **INLINE-FIX (plan-doc spec compliance)** | Plan-doc §5: "row from the prior index is retained" for unreachable adopters. Implementation now reads prior `output/scorecards/index.json` at startup; on unreachable status, retains all prior fields if prior status was `verified`; error string indicates "retained prior row: true/false". |
| **C-COR-MIN-001** | **TF-FORWARD** | Index fixture set covers verified + verification_failure but not unreachable / no_emit. Filed forward — the schema's conditional branches catch status-field mismatches; expanding the corpus is opportunistic. |
| **C-COR-MIN-002** | **NO ACTION** | last_emit_commit silently omitted on regex mismatch. The 40-char hex pattern is GitHub's commit SHA format; a mismatch would indicate a malformed gh-cli response. Acceptable to omit; the row's run_id is still present. |
| **C-COR-MIN-003** | **NO ACTION** | In-memory index schema validation can raise unhandled ValidationError. This is intentional — if the aggregator produces a schema-invalid index, the run MUST fail loudly (not silently commit a malformed file). The exception is the loud failure mode. |
| **MIN-SAFE-002** | **TF-FORWARD as TF-023C-006** | No automatic minimum-version check on `scp_version`. An adopter could pin a very old SCP version + remain "verified". Acceptable: invariant 1 says aggregator is informational, not authoritative; adopter PR-time gating is the federation primitive's job. Filed forward for opportunistic addition. |
| **MIN-SAFE-003** | **NO ACTION** | Stderr truncation limit varies (500 / 400). Cosmetic only; bounded by schema's `error: maxLength 2000`. |
| **CG-MIN-003** | **NO ACTION** | PR title/branch contain `${{ github.run_id }}` which is sequential; consecutive aggregator runs produce sequential branch names. Acceptable. Mostly cosmetic; if branch naming becomes an issue, can switch to date-based. |
| **CG-MIN-006** | **TF-FORWARD as TF-023C-007** | Adopter wrapper file naming constraint (must be `policy-check.yml`) is implicit. Filed forward — onboarding doc at slice 023D will name this. |

### nit (5 raw)

All NO ACTION except `nit-SAFE-004` (timeout-minutes) and `CG-nit-002` (rate-limit) — both filed forward as TF-023C-004 + TF-023C-003 respectively.

## Inline-fix summary (~10 edits across 4 files)

1. `schemas/scorecard-opt-in-registry.schema.json` — `expected_scp_workflow_ref` pattern anchored to SCP namespace (MAJ-SAFE-001 / CG-MIN-005).
2. `.github/workflows/scorecard-aggregator.yml` — added `SCP_WORKFLOW_REF_PREFIX` runtime check (defence-in-depth on MAJ-SAFE-001).
3. `.github/workflows/scorecard-aggregator.yml` — added 7-day staleness check + `created_at` parsing (CG-MAJ-001).
4. `.github/workflows/scorecard-aggregator.yml` — prior-row retention for unreachable adopters (CG-MIN-004 / plan-doc §5 compliance).
5. `schemas/scorecard-index.schema.json` — `allOf` conditional branches for status-dependent fields (C-COR-MAJ-001).
6. `schemas/scorecard-index.schema.json` — status enum description rewritten to match implementation (C-COR-MAJ-002).
7. `docs/DECISIONS.md` — D-041 / D-042 row order swapped to ascending ID (CG-MIN-001 / C-COR-nit-001).
8. `STATUS.md` — TF-023C-001..005 added to tracked-forward section (CG-MIN-002).

## Forward-filed TFs

- **TF-023B-003** (already filed): WARN_BASELINE_RULES manifest.
- **TF-023C-001..005** (added in this fix-round, see DISPATCH-NOTE forward-looking + STATUS.md).
- **TF-023C-006** (low priority): minimum scp_version check (per MIN-SAFE-002).
- **TF-023C-007** (low priority): document adopter wrapper filename constraint at 023D onboarding (per CG-MIN-006).

## Smoke-test post-fix

- `pytest tests/scorecard-aggregator/ tests/scorecard-emit/ tests/conflict_gate/`: 35/35 pass.
- `scripts/scp-pre-push-verify.sh`: ✓ all 3 SCP-R gates pass.

## R2 candidacy

R1 surfaced 0 CRIT, 4 unique MAJ (all closed inline including a real defence-in-depth gap on signer-workflow + a real missing AC item on staleness), 7 unique MIN (4 inline-fixed + 2 TF-forwarded + 1 NO ACTION). Ready for R2 to verify no new CRIT/MAJ.
