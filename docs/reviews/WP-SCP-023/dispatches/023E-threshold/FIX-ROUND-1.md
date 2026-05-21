# 023E — fix-round-1 audit (R1 → fix → R2 candidate)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-023-023e-threshold`
**Pre-fix-round-1 HEAD:** `2883087`

## R1 finding tally

3× parallel Sonnet R1: 2 CHANGES_REQUESTED + 1 APPROVED_WITH_FINDINGS.

| Lens | Verdict | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 2 | 3 | 2 |
| safety_bypass | CHANGES_REQUESTED | 0 | 1 | 3 | 1 |
| completeness | APPROVED_WITH_FINDINGS | 0 | 3 | 1 | 1 |
| **total raw** | — | **0** | **6** | **7** | **4** |

After dedup (cross-lens overlap on STATUS-row + cross-repo notification): **0 CRIT, 5 unique MAJ**.

## Per-finding disposition

### MAJ (5 unique, all inline-fixed)

| ID | Lens(es) | Disposition | Action |
|---|---|---|---|
| **COR-MAJ-001 / CMP-MAJ-002** | correctness, completeness | **INLINE-FIX** | STATUS.md 023D row still showed "this" (should be "#100"); 023E row absent. Both fixed via Python (Edit tool kept silent-dropping these specific changes — same pattern as 023D fix-round-1). |
| **COR-MAJ-002** | correctness | **INLINE-FIX** | DISPATCH-NOTE AC (iv) said "Tests confirm" + listed `test_log_attribution` as a modified file, but no such test existed. Added two tests: `test_log_attribution_falls_back_when_key_ring_empty` + `test_log_attribution_falls_back_when_key_ring_missing`. 12 MCP tests pass now (was 10). |
| **MAJ-SAFE-001** | safety | **INLINE-FIX** | `docs/gates/**` was absent from CODEOWNERS — USER-GATE-D Threshold A artefact had no code owner. Added `docs/gates/** @jrnb2024` + companion `docs/reviews/** @jrnb2024` (audit-trail of every dispatch + R{N} review JSON). Inserted before /CODEOWNERS self-protection per ORDERING INVARIANT. |
| **CMP-MAJ-001** | completeness | **INLINE-FIX** | Cross-repo notification (TF-023A-002) was named in DISPATCH-NOTE §IN but not delivered. Added `~/Projects/control-tower/governance/docs/notifications/SCP-SCORECARD-SURFACE-LIVE-2026-05-03.md` covering: what's live, adopter opt-in steps, ACC redeploy expectation, CT/mapp-estate-regression voluntary participation, Threshold A criteria. |
| **CMP-MAJ-003** | completeness | **INLINE-FIX** | USER-GATE-D criterion (i) was weaker than plan-doc §8 — allowed Threshold A with SCP-self + any 2 external. Tightened to "FLA mandatory" + explicit satisfied set `SCP-self + FLA + ≥1 of {PIM/recommender/mapp-doc-agent/control-tower}` per plan-doc §8 + §10 Q6. |

### MIN (7)

| ID | Disposition | Action |
|---|---|---|
| **COR-MIN-001** | **NO ACTION** | DISPATCH-NOTE risk surface §2 said fallback sentinel was "pending_021J"; code uses "key-ring-unreadable". Cosmetic doc-vs-code drift; the code is the source of truth. |
| **COR-MIN-002** | **NO ACTION** | DISPATCH-NOTE described USER-GATE-D as "4-criterion" in two places; actual file has 8 criteria. The artefact is the source of truth; DISPATCH-NOTE is slice-time scaffolding. |
| **COR-MIN-003** | **INLINE-FIX (USER-GATE-D criterion vi tightened)** | TF-023D-003 code-complete but key ring operationally empty. Tightened criterion (vi) to require BOTH code AND operational satisfaction — operator must generate + commit a key before checking the box. |
| **MIN-SAFE-001** | **NO ACTION** | `_resolve_audit_key_id` except clause covers (ValueError, OSError, AttributeError) — could broaden to (Exception,). Defensive broadening is a tradeoff: catches more failure modes but obscures genuine bugs. Current scope matches what `_current_signing_key_id` actually raises. |
| **MIN-SAFE-002** | **NO ACTION (operational tracking via USER-GATE-D vi)** | Audit attribution degraded until key ring populated. Tracked via USER-GATE-D criterion (vi) operational-state requirement. |
| **MIN-SAFE-003** | **CLOSED by inline-fix** | Cross-repo notification missing — same as CMP-MAJ-001. Now delivered. |
| **CMP-MIN-001** | **NO ACTION** | STATUS.md At-a-glance missing WP-SCP-023 in-flight row. WP-SCP-023 is live across the chain (023A/B/C/D merged); At-a-glance only carries closed WPs (019/020/021/022). The chain table tracks in-flight slices. Acceptable structural choice. |

### nit (4)

| ID | Disposition |
|---|---|
| COR-nit-001 | NO ACTION (SHA verification — manually verified via git log) |
| COR-nit-002 | NO ACTION (`_current_signing_key_id` error message stylistic) |
| nit-SAFE-001 | INLINE-FIX (USER-GATE-D criterion vi clarification — same as COR-MIN-003) |
| CMP-nit-001 | NO ACTION (wrapper inline comment "post-v1.2.0 (023D merge)" — clarifies what the SHA covers, not where v1.2.0 was tagged) |

## Inline-fix summary (~7 edits across 6 files)

1. `STATUS.md` 023D PR# pointer + 023E row inserted (COR-MAJ-001 / CMP-MAJ-002).
2. `tests/scp_mcp/test_tools/test_consult_scorecard.py` — 2 new `test_log_attribution_*` tests (COR-MAJ-002).
3. `CODEOWNERS` — `docs/gates/** @jrnb2024` + `docs/reviews/** @jrnb2024` (MAJ-SAFE-001).
4. `~/Projects/control-tower/governance/docs/notifications/SCP-SCORECARD-SURFACE-LIVE-2026-05-03.md` (CMP-MAJ-001 + MIN-SAFE-003 + closes TF-023A-002).
5. `docs/gates/USER-GATE-D.md` criterion (i) FLA-mandatory tightening (CMP-MAJ-003).
6. `docs/gates/USER-GATE-D.md` criterion (vi) code-AND-operational tightening (COR-MIN-003 / nit-SAFE-001).
7. `docs/gates/USER-GATE-D.md` criterion (vii) marked done with the cross-repo notification path.

## Forward-filed TFs

R1 surfaced no new TF candidates beyond what was already filed at 023C/D.

## Smoke-test post-fix

- 12 MCP tests pass (was 10 → added 2 new test_log_attribution tests).
- 53 scorecard tests pass overall.
- Pre-push wrapper green.

## R2 candidacy

R1 surfaced 0 CRIT, 5 unique MAJ (all inline-fixed including a real audit-trail safety gap on docs/gates/** + a real plan-doc-spec compliance gap on USER-GATE-D criterion (i)), 7 MIN (3 inline-fixed + 4 NO ACTION), 4 nit. Ready for R2 to verify no new CRIT/MAJ.
