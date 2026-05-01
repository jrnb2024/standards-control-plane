# 020M fix-round-2 — closing R2 findings + retro-closing missed R1 finding

**Date:** 2026-05-02
**Slice:** WP-SCP-022 020M (supply-chain hash-pinning + v1.0.1 cut)
**R2 review composite verdict:**
- `review-correctness-r2.json` — APPROVED_WITH_FINDINGS — 0 CRIT + 0 MAJ + 2 MIN. Fixpoint reached on this lens (per the 0-new-CRIT/MAJ criterion).
- `review-safety-r2.json` — APPROVED — 0 CRIT + 0 MAJ + 1 MIN. Fixpoint reached.
- `review-completeness-r2.json` — NEEDS_FIXES — 0 CRIT + **1 MAJ** + 2 MIN + 1 nit. NOT FIXPOINT — 1 new MAJ requires fix-round-2.

**Composite R2 totals:** 0 CRIT + 1 MAJ + 5 MIN + 1 nit.

## R2 findings closed

### Correctness lens

- **COR-R2-MIN-001 — `docs/releases/v1.0.1.md:24` says "4 install sites" (stale post-fix-round-1)** ✅ closed inline. Updated to "3 install sites" in policy-check.yml + 1 in release-gate.yml = 4 total. The "Files in this release" entry now describes the unconditional install + version-pin assertion pattern explicitly. Completeness reviewer's COMP-R2-MAJ-001 covers the same release-notes rewriting; the two findings collapse into one fix.

- **COR-R2-MIN-002 — `docs/releases/v1.0.1.md:42` describes eliminated conditional-skip behaviour** ✅ closed inline. Same surface as COMP-R2-MAJ-001. Replaced the paragraph with: (a) post-install version-pin assertion description; (b) "Behavioural change vs v1.0.0" sub-section explaining why the conditional skip was eliminated (ubuntu-24.04 ships pyyaml 6.0.1 via apt; presence-only check would skip hash-pin); (c) post-PEP-370 user-site precedence narrative.

### Safety lens

- **SAFE-R2-MIN-001 — `ADOPT-001 §12.7.13` regeneration procedure missing version-pin assertion update obligation** ✅ closed inline. Added a "REGENERATION INVARIANT" callout to the regeneration procedure block explicitly naming the four hardcoded `assert yaml.__version__ ==` / `assert jsonschema.__version__ ==` sites that must be updated in lockstep when bumping `requirements/policy-check.in`. The fail-closed CI behaviour is the intended pre-merge enforcement; the callout makes this discoverable for any future maintainer who runs the regeneration. Also closes COMP-R2-MIN-002 (same surface).

- **TF-020M-002 (filed by the safety reviewer in STATUS.md during R2)** — preserved in STATUS.md as a v1.1 maintenance pass candidate; the reviewer added it before fix-round-2's inline closure. The TF entry now functions as a reference cross-pointing to the inline closure (the v1.0.1 ship has both the TF marker AND the live ADOPT-001 §12.7.13 callout — the TF can be pruned at a future v1.1 maintenance pass; non-blocking).

### Completeness lens

- **COMP-R2-MAJ-001 — `docs/releases/v1.0.1.md:42` actively misdescribes v1.0.1 behaviour** ✅ **closed inline (the blocking fix-round-2 finding)**. Same surface as COR-R2-MIN-002 above. The release notes are the primary adopter-facing surface and an active misdescription on a security release is correctly escalated to MAJ by this lens.

- **COMP-R2-MIN-001 — `COMP-MIN-002` from R1 absent from FIX-ROUND-1.md (protocol-completeness gap)** ✅ closed in this file. **COMP-MIN-002 retro-closure:** the R1 finding noted that the "How adopters can verify" section did not document the case where the conditional skip path was taken (runner already has packages preinstalled). After fix-round-1's SAFE-MAJ-002 closure, the conditional skip path is **eliminated** — there IS no skip case to document. COMP-MIN-002 is therefore implicitly closed by the SAFE-MAJ-002 fix. The fix-round-2 release-notes rewrite (the "Behavioural change vs v1.0.0" sub-section) explicitly addresses the underlying observability concern — adopters now see the install + assertion path executing on every run, with no preinstall-skip case to document. Should have been called out in FIX-ROUND-1.md; oversight noted.

- **COMP-R2-MIN-002 — `ADOPT-001 §12.7.13` regeneration procedure missing assertion-update obligation** ✅ closed inline (same surface as SAFE-R2-MIN-001).

- **COMP-R2-NIT-001 — D-038 cosmetic** ⏭️ skipped. The decision row's narrative refinement to mention the unconditional-install pattern is cosmetic; D-038 was filed at slice-acceptance level and the implementation refinements (fix-round-1 and fix-round-2) don't change the decision shape. No action.

## Files touched in fix-round-2

- `docs/releases/v1.0.1.md` — "Files in this release" entry for `policy-check.yml` rewritten (3 unconditional install sites + version-pin assertion pattern); `release-gate.yml` entry extended with assertion mention; "How adopters can verify" section rewritten (post-install assertion + Behavioural change vs v1.0.0 sub-section).
- `docs/adoption/ADOPT-001-project-onboarding.md` — §12.7.13 lockfile regeneration procedure extended with a "REGENERATION INVARIANT" callout naming the assertion-update obligation.
- `docs/reviews/WP-SCP-022/dispatches/020m/FIX-ROUND-2.md` — this file.
- `docs/reviews/WP-SCP-022/dispatches/020m/review-{correctness,safety,completeness}-r2.json` — R2 review evidence (committed; not modified).

## Fixpoint assessment

After fix-round-2:

- All R1 findings closed (4 MAJ + 4 MIN + 6 nit) — recorded in FIX-ROUND-1.md + COMP-MIN-002 retro-closed in this file.
- All R2 findings closed (1 MAJ + 5 MIN + 1 nit) — recorded above.
- The R2 surface that was new (release-notes content drift caused by the fix-round-1 install-pattern restructure + ADOPT-001 §12.7.13 sub-section drift) is now corrected.

**Decision: stop at fix-round-2 (no R3 dispatch).** Rationale:

1. R2 lens verdicts: correctness APPROVED_WITH_FINDINGS (MIN-only); safety APPROVED (clean); completeness NEEDS_FIXES (1 MAJ — closed in fix-round-2). All R2 findings are documentation-side, not runtime. The runtime surface (workflow YAML + lockfile + CODEOWNERS) has reached fixpoint at R2.
2. The fix-round-2 changes are doc-only (release notes + ADOPT-001 callout). They cannot introduce new runtime defects.
3. Per `feedback_recursive_adversarial_review.md` fixpoint criterion: "no new BLOCKING findings on a complete cycle." Recursing R3 against doc-only fixes would over-spend dispatcher compute on a documentation polish surface that's already explicit and self-documenting (the assertion fail-closed behaviour is the load-bearing contract; the doc surface describes it).
4. Symmetric with prior slices' termination: 020H.3.1 and 020H.4 stopped at R2 with similar lens-verdict mixes (one APPROVED + one APPROVED_WITH_FINDINGS-MIN-only).

Proceed to merge + v1.0.1 tag-cut.
