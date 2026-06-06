# WP-SCP-028 auth-canonical conformance — 3-lens R1 dispositions

**Date:** 2026-06-06. **Branch:** `wp-scp-028-auth-canonical-conformance`. **Session:** autonomous Pattern-3 run (D-057; dispatch `pattern3-20260606T080053Z-49248`).
**Change:** SCP-R-009 (auth-canonical-version-pin) / SCP-R-010 (auth-canonical-import-fence) / SCP-R-011 (auth-contract-claim-shape) — three **warn-baseline** Rego rules over CT's published auth canonical + 2 new schemas (`canonical-sdk-versions.schema.json`, `auth-contract-v1.schema.json`) + 3 `auth-*-disabled` opt-out keys in `rule-config.schema.json` + inline tests + bookkeeping. **Dormant** (vacuous-pass) until the companion materialisation workflow PR, per the SCP-R-006/R-030 precedent. v1.5.0.
**Auth surface:** mandatory 3-lens R1; a safety_bypass REJECT is a hard stop (D-058 + feedback_orchestrator_auth_surface_plan_review_default.md).
**Cosign:** prereq-3 MET 2026-06-05 (operator ran `cosign verify-blob` against the live CT contract → Verified OK; anchor identity `.../control-tower/.github/workflows/contract-manifest-publish.yml@refs/heads/main`). Deferral LIFTED — cosign is the real fail-closed anchor (enforced in the future companion; the rules fail-closed on a present-but-unverified manifest).

## Review structure (surfaced, not silent — R1 CG-MIN-004)
3 parallel lens-agents (correctness / safety_bypass / completeness_governance), each covering all 3 rules + the schemas jointly — rather than 9 per-rule dispatches (autonomous-prompt §3.5). Rationale: the rules share one input/suppression/dormancy pattern and the auth surface is best reviewed holistically (cross-rule interactions visible). Plus a focused R2 correctness re-verification after the fix-round.

## Verdicts

| Lens | R1 | After fold |
|---|---|---|
| correctness | **REJECT** (1 structural MAJ: R-009 stale routed through `deny`) | **ACCEPT** (R2 confirmed CLOSED) |
| safety_bypass | **ACCEPT** (no auth bypass) | ACCEPT |
| completeness_governance | **ACCEPT** with 2 doc-MAJ + MINs | ACCEPT (folded) |

**R-FIXPOINT MET. No safety_bypass REJECT (no §7.2 hard stop). Cure-worse R2: not triggered — the fix mirrors the already-accepted R-010/R-011 split; R2 found no new defect.**

## Findings + dispositions

### correctness
- **[CORR-MAJ-001 → FIXED]** SCP-R-009 routed BOTH downgrade (below `minimum_secure_version`) and stale (behind `canonical_version`) findings through a single `scp_r_009_raw_findings` → `deny`. At D-059 deny-promotion a *stale* pin would wrongly block a merge. **Fix:** split into `scp_r_009_deny_findings` (fail-closed + downgrade) → `deny` and `scp_r_009_warn_findings` (stale) → `warn`, mutually exclusive at `not scp_r_009_lt(version, floor)`; mirrors R-010/R-011. R2 confirmed `scp_r_009_raw_findings` fully removed, no double-counting, dormancy + downgrade/fail-closed semantics unchanged.
- **[CORR-MAJ-002 → FIXED]** The two stale tests asserted `deny==1` (consistent with the broken rule). **Fix:** updated to `deny==0 && warn==1`; the new `warn` output path is now covered.
- **[CORR-MIN-001 → FIXED]** Suppression-observability records guarded on `count(deny_findings) > 0`, so a suppressed warn-only finding emitted no audit record. **Fix:** added `scp_r_NNN_any_findings` (deny>0 OR warn>0) to all three rules + a warn-only-suppression test each (closes R2-COV-MIN-001 — the helper's warn branch is now exercised).
- **[CORR-NIT-001 → FIXED]** `lang_symbol_map`/`protected_primitives` `additionalProperties:false` → `true` (forward-compat for new CT tiers/languages; LINKAGE tolerance).
- **[CORR-NIT-002 → noted]** R-009 test fixture versions diverge from live CT values — intentional self-consistent test data (LINKAGE: the rule reads the manifest at eval time, not the fixture).

### safety_bypass (ACCEPT — no REJECT)
- Fail-closed VERIFIED: present-but-unverified manifest → finding (never silently trusted); absent input → vacuous (dormant). Opt-out keys are strictly rule-scoped (no cross-rule suppression). Waiver/disable suppression is fully fail-closed (inherited from scp_common; null `expires_at` → expired). SCP-R-006-pattern parity.
- **[SB-MIN-001] (pre-D-059)** The `*_verified` flag is the trust boundary — its integrity depends on the **companion materialisation workflow** (it, not the adopter, runs cosign + sets the flag). The companion PR must prove the flag is assembled solely from the workflow's own cosign run, not adopter-repo files, BEFORE D-059 deny-promotion. Tracked: `FUP-WP-SCP-028-VERIFIED-FLAG-TRUST-BOUNDARY-001`.
- **[SB-MIN-002] (pre-D-059)** R-010 import-fence has inherent static-extractor evasion surface (dynamic getattr alias, case-variant rename, indirect re-export, conditional import). Honest limitation of the dormant rule + future extractor; the companion PR must document the evasion surface so D-059 doesn't assume exhaustiveness. Tracked: `FUP-WP-SCP-028-IMPORT-FENCE-EVASION-DOC-001`.
- **[SB-MIN-003/SB-MIN-004] (pre-D-059)** Severity-split clarification for D-059: confirm whether a `declared_claim_shape_version` MAJOR-lag (currently WARN, an annotation-drift signal distinct from the AST-level `claims_uses_old_shape` DENY) should be elevated at deny-promotion. Documented for the D-059 reviewer; no rule change at warn-baseline.

### completeness_governance
- **[CG-MAJ-001 → FIXED]** R-010 §3.2 `_legacy`/`_internal`/`_v1`-suffix warn condition not implemented. **Fix:** explicit DEFERRED note in the R-010 header (the live contract expresses severity via tier sets, not suffixes; needs companion extraction). Tracked: `FUP-WP-SCP-028-LEGACY-SUFFIX-WARN-001`.
- **[CG-MAJ-002 → FIXED]** R-009 §3.1 deny-condition-2 (SHA-pin vs tagged) not implemented. **Fix:** explicit DEFERRED note in the R-009 header. Tracked: `FUP-WP-SCP-028-SHA-PIN-DETECT-001`.
- **[CG-MIN-002 → FIXED]** VERSIONING "Current members" reworded to "Live members … / Target members pending their companion workflow PR" (009/010/011).
- **Decision compliance VERIFIED:** warn-baseline only; DORMANT (no `policy-check.yml` edit in the diff); v1.4.0→**v1.5.0** (v1.4.0 was SCP-R-030); D-059 RESERVED not consumed (no D-059 ADR); `scp_common.rego` NOT modified (helpers rule-local per the per-rule-coverage discipline); LINKAGE-not-VALUES (no CT issuer/symbol/version VALUES in rule bodies — verified by grep; schemas tolerate CT extras).
- **[CG-MIN-005 → noted]** D-059 reservation is inline in DECISIONS Last-Updated (not a separate table row). The inline note + BACKLOG + STATUS references suffice; a row can be added when D-059 is consumed.
- **[CG-MIN-003 → noted]** The workflow-extracted adopter input shapes (`adopter_ct_auth_deps` / `adopter_source_files` / `adopter_auth_handlers`) have no schema — documented in the rule headers; a schema is a companion-PR concern (pre-existing SCP-R-006 pattern). Tracked: `FUP-WP-SCP-028-ADOPTER-INPUT-SCHEMA-001`.

## Tracked-forward (none blocking; all pre-D-059 / companion concerns)
`FUP-WP-SCP-028-VERIFIED-FLAG-TRUST-BOUNDARY-001` · `FUP-WP-SCP-028-IMPORT-FENCE-EVASION-DOC-001` · `FUP-WP-SCP-028-SHA-PIN-DETECT-001` · `FUP-WP-SCP-028-LEGACY-SUFFIX-WARN-001` · `FUP-WP-SCP-028-ADOPTER-INPUT-SCHEMA-001` · claim-shape MAJOR-lag severity clarification (D-059).

## CI evidence
To be appended once green: `policy-check / scp/policy-check` (incl. `opa test --threshold 90` per-rule coverage + regal lint + opa fmt) + `check-invocation-log-entry` + `r1-evidence-check`.
