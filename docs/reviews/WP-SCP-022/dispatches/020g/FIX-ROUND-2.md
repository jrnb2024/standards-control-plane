# WP-SCP-022 slice 020G — fix round 2

**Date:** 2026-04-30 (evening)
**Triggered by:** R2 review × 3 surfaced 1 MAJ + 10 MIN + 5 nit findings.

## R2 verdicts

| Lens | Verdict | NEW findings vs R1 |
|---|---|---|
| correctness | CONDITIONAL | 3 MIN + 1 nit |
| safety_bypass | NEEDS_REVISION | 1 MAJ + 4 MIN + 3 nit |
| completeness_governance | CONDITIONAL | 6 MIN + 2 nit |

R1 findings all closed. The 1 MAJ is real: SAF-R2-001 — partial-state apply (PUT succeeds, POST fails) skipped log emission entirely. Plus a notable secondary catch: CORR2-004 found the same `required_signatures: true` pattern in the SCP-self `configure-020d2-required-check.sh` — a latent bug that didn't bite only because 020J had already enabled signatures via the dedicated endpoint.

## Findings addressed in this fix round

### From safety (R2)

- **SAF-R2-001** (MAJ — partial-state apply skips log): **closed** — wrapped both `gh api -X PUT` and `gh api -X POST .../required_signatures` calls with `|| APPLY_FAIL=1`; sets `FAIL=1` on either failure; falls through to log emission so audit trail captures partial-state failures. Explicit stderr error message names which endpoint failed and what state the branch is in.
- **SAF-R2-002** (verification-passed log unconditional): **closed** — same fix as CORR2-001 (gated under `if [ "${FAIL:-0}" -ne 0 ]`).
- **SAF-R2-003** (`readlink -f` unavailability on macOS): **acknowledged** — tracked as TF-020G-003. Stock macOS without GNU coreutils: `readlink -f` falls back to bare `$0`. Practical impact bounded; documented.
- **SAF-R2-004** (SIGINT inheritance disables 5-second escape): **acknowledged** — non-blocking. The 5-second pause is one of three layers of friction (long ack-flag name + verbose warning + sleep); even if SIGINT is trapped, the prior layers visibly fired.
- **SAF-R2-005** (CI guard misses Jenkins/Azure/etc.): **acknowledged** — tracked as TF-020G-002. Most CI systems also set `CI=true`; the gap is theoretical. Add at WP-SCP-024 estate cascade time.
- **SAF-R2-006** (`BEFORE_STATUS` env-var collision): **acknowledged** — extremely improbable in practice (the var name is local-scope-implicit). Non-blocking.
- **SAF-R2-007** (history pre-fill of ack flag): **closed via CORR2-003** — the new "ack flag without --no-enforce-admins is an error" rule means a pre-filled ack flag with no other change either does nothing (operator runs without bypass) or errors loudly (operator forgot --no-enforce-admins).
- **SAF-R2-008** (arg-validation order): **acknowledged** — cosmetic; non-blocking.

### From correctness (R2)

- **CORR2-001** (`verification passed` always emits): **closed** — wrapped in `if FAIL=0` else-branch.
- **CORR2-002** (`owner/..` matches repo regex): **closed** — added explicit case-statement check rejecting `*..*`, `.*`, `*/.*`, `*/..*` patterns BEFORE the regex match.
- **CORR2-003** (silent ack flag without `--no-enforce-admins`): **closed** — added explicit error message + exit 2 when `ACK_ADMIN_BYPASS=1` and `ENFORCE_ADMINS=true`.
- **CORR2-004** (same `required_signatures` bug in 020D2 script): **closed** — removed `"required_signatures": true` from `configure-020d2-required-check.sh` unified PUT body; added separate `gh api -X POST .../required_signatures` call. Re-running the script now correctly applies signatures via the canonical sub-resource endpoint.

### From completeness (R2)

- **COMP-R2-001** (DISPATCH-NOTE acceptance (i) carries stale "rulesets API + admin flags" reasoning): **closed** — rewritten to "the unified branch-protection PUT shape used here has been stable since gh 2.x; 2.40 is a safety-margin floor".
- **COMP-R2-002** (DISPATCH-NOTE acceptance (ii) doesn't mention --i-understand-this-bypasses-the-gate): **closed** — extended to enumerate the new rules: silent ignore without trigger, 5-second pause when applied, error when ack flag set without trigger.
- **COMP-R2-003** (D-033 not referenced): **closed** — added D-033 to the script's reference comment block (the rendered context name `policy-check / scp/policy-check` originates in D-033).
- **COMP-R2-004** (CI guard message references --plan that's not yet evaluated): **closed** — message rewritten to be self-consistent: "If you need to run a dry-run from CI, unset CI/GITHUB_ACTIONS first AND pass --plan explicitly."
- **COMP-R2-005** (Bootstrap-only header omits log-emission-on-failure invariant): **closed** — added explicit invariant statement: "The script emits a log block on EVERY completed invocation, including verification failures and partial-state apply failures."
- **COMP-R2-006** (SAF-007 acknowledged-deferred has no TF entry): **closed** — added TF-020G-001 explicitly. Same pattern: TF-020G-002 (CI guard breadth), TF-020G-003 (readlink macOS gap).
- **COMP-R2-007** (branch-protection.md doesn't cross-reference branch-protection-log.md): **closed** — added the cross-reference and D-035 reference to the existing 020G bullet.
- **COMP-R2-008** (log block missing "PUT payload applied" field): **closed** — added a new "PUT payload applied" subsection to the emitted log block, between "Plan-only" and "Before".

## Files modified in this round

- `scripts/enable-required-check.sh` — partial-state apply trapping; conditional verification-passed log; repo path-traversal hardening; D-033 reference; CI guard message; bootstrap-only header invariant; ack-flag-without-trigger error; PUT-payload field in log block.
- `scripts/configure-020d2-required-check.sh` — same `required_signatures` fix (CORR2-004): removed from unified PUT, added separate POST.
- `docs/security/branch-protection.md` — 020G bullet adds branch-protection-log.md cross-reference + D-035.
- `docs/reviews/WP-SCP-022/dispatches/020g/DISPATCH-NOTE.md` — acceptance checklist (i) + (ii) updated; TF-020G-001..003 section added.
- `docs/reviews/WP-SCP-022/dispatches/020g/FIX-ROUND-2.md` — this file.

## Next step

R3 dispatch on the corrected artefact set. Per `feedback_recursive_adversarial_review.md`, recurse to fixpoint. R2 already returned CONDITIONAL (no MAJ/CRIT) on 2 of 3 lenses + NEEDS_REVISION on safety with 1 MAJ now closed. R3 should declare fixpoint or surface only administrative cleanup.
