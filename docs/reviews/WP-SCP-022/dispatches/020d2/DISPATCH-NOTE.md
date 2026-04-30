# WP-SCP-022 slice 020D2 — dispatch note

**Date:** 2026-04-30
**Tier path:** orchestrator-applied (Tier 1 only)
**Justification:** the substantive deliverable is one shell script
(`scripts/configure-020d2-required-check.sh`, ~140 lines, an idempotent
applier mirroring the 020J script's shape), one D-NNN row (D-032),
and one branch-protection.md section. Pure governance + automation
text — Codex Tier 4 would be the right tier IF dispatching, but the
script is structurally identical to 020J's already-proven shape and
dispatch overhead exceeds authoring cost.

R1 review skipped per the same reasoning that closed 020H part 1 +
020E.a: the artefact is small, derives directly from prior decisions
(D-030 + D-031 + 020K AC(c)) + the 020J reference implementation, and
the post-merge apply step is the operational gate (verified by the
script's own verify steps + the verify-block in branch-protection.md).

## Slice acceptance per WP-SCP-020 §4 020D2

- [x] `scripts/configure-020d2-required-check.sh` — idempotent applier
  that PUTs the unified branch-protection state.
- [x] `docs/security/branch-protection.md` — extended with the 020D2
  section + new verify block + updated apply-or-reapply commands.
- [x] `docs/DECISIONS.md` — D-032 row.
- [ ] **Post-merge apply** — `./scripts/configure-020d2-required-check.sh`
  must run successfully (the operational closure of 020D2).
- [ ] **Verification** — `gh api .../branches/main/protection` returns
  the expected state per the verify block.

The post-merge apply step lands the OPERATIONAL change: from this
moment forward, every PR to `main` is gated by `scp/policy-check`,
needs an approving review, and cannot bypass admin override.

## Consequences

- **The open canary PR #59** (`canary/deliberate-violation-pre`) will
  be merge-blocked once 020D2 is applied — `mergeStateStatus` moves
  from UNSTABLE → BLOCKED. This is the intended outcome and is the
  evidence for slice 020E.b (post-protection canary).
- **My own future commits** to main go through the gate. The
  next session will need to merge through PR even for trivial doc
  changes.
- **Single-operator self-approval is the only path forward.** Per
  020K U-k closure + D-031, `require_review_from_non_author: false`
  reflects that @jrnb2024 must self-approve every PR. The 2026-07-21
  quarterly escalation review re-evaluates this when (if) a second
  maintainer onboards.

## After 020D2 lands

Chain pauses at **USER-GATE-A** — Threshold A finish line. The
operator confirms SCP gates itself successfully on its own main.
020E.b + 020E.c (post-protection canary, waiver-suppression canary)
are post-USER-GATE-A.

## Post-merge correction (added 2026-04-30 evening)

Slice 020G R2 review (CORR2-004) caught a latent bug in the
`scripts/configure-020d2-required-check.sh` PUT body: it included
`"required_signatures": true`, which is NOT a documented field of
the unified branch-protection PUT body — it's a dedicated sub-
resource. SCP-self only escaped breakage because 020J had already
enabled `required_signatures` via the dedicated endpoint, so the
buggy unified-PUT inclusion was a no-op.

Fix landed in slice 020G: `configure-020d2-required-check.sh`
now removes `required_signatures` from the PUT body and applies
it via a separate `gh api -X POST .../required_signatures` call
after the PUT. Re-runs are idempotent (GitHub returns 204 No
Content on already-enabled).

This audit-trail entry preserves the timeline: 020D2 landed at
PR #63 (commit 22aa6a2) with the latent bug; 020G fix-round-2
corrected it post-merge. The live state on main has always had
required_signatures enabled via 020J's separate call; the fix
ensures idempotent re-runs of the 020D2 script don't rely on
prior 020J state.
