# Slice 021B — adversarial-review fixpoint record

**Slice:** WP-SCP-022 Track 2 / WP-SCP-021 §4 021B (MCP server scaffold + Ed25519 keygen + PyPI extras)
**Plan version reviewed:** slice as committed at 90c4890 (post-fix-round-2)
**Date:** 2026-04-28
**Round count:** 3 (R1 → fr1 → R2 → fr2 → R3 → fixpoint)
**Fix-round budget:** 2 used of 5
**Cumulative review spend:** ~$5–7 across 9 review dispatches + 2 codex fix-rounds

## Fixpoint criteria

Per WP-SCP-022 §4.3:

> All three either APPROVED or APPROVED_WITH_FINDINGS where every finding is MIN or nit (no CRIT, no MAJ) → Fixpoint reached → slice merges.

R3 verdicts:

| Lens | Verdict | Findings |
|------|---------|----------|
| correctness | APPROVED_WITH_FINDINGS | 0 CRIT, 0 MAJ, 2 MIN, 2 nit |
| safety_bypass | APPROVED_WITH_FINDINGS | 0 CRIT, 0 MAJ, 3 MIN, 3 nit |
| completeness_governance | APPROVED_WITH_FINDINGS | 0 CRIT, 0 MAJ, 5 MIN, 3 nit |

All three APPROVED_WITH_FINDINGS, MIN/nit only. **Fixpoint reached.**

## Round-by-round trajectory

| Round | Findings (CRIT/MAJ/MIN/nit) | Outcome |
|-------|------------------------------|---------|
| R1    | 0 / 8 / 10 / 6   | fr1 |
| R2    | 0 / 1 / 8+ / many | fr2 (closed: keygen atomic, key-id raw bytes, O_NOFOLLOW, fchmod, expanded secret regex, .gitignore patterns) |
| R3    | 0 / 0 / 10 / 8   | **Fixpoint** (closed: Windows platform guard for keygen) |

Total MAJ closed: 9. No CRITs at any round.

## Hash chain (machine-verifiable)

## sha256_chain
correctness: c92a685782ed53b51453e1709b9169f80abf4f8991bd63e117dc110ce18d4746
safety: f630aa69b0a0b29ed8e41bbbb4872aa495bae75d5c42608291d5dcb24f45b31c
completeness: 05a2c90b50770c3625c3fbcf4ecc57448f4229d2cf8af5f0fe4816f1a4771691
chain: b78e0ee96e9c37b508b128ba7de7e81c7f9bc32a82c50a8b33d4146a5f658023

## Recorded MIN/nit residuals

The 13 residuals from R3 (all MIN/nit) are recorded in
docs/reviews/WP-SCP-022/dispatches/021b/fix-round-2/review-*.json
files. Per §4.3 these do not block merge; they are addressable in
the post-merge cleanup PR or deferred to follow-up slices (021C
covers some MIN concerns about test coverage; 021I covers OAuth
which addresses some defence-in-depth nits).

## Verdict

**Slice 021B v1 reaches Gate-C fixpoint at R3.** Ready for merge.
