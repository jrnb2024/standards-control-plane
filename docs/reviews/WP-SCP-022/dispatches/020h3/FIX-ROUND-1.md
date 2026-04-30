# 020h3 fix-round-1 (post-r1, pre-r2)

**Date:** 2026-04-30 (evening)

## Triggers

R1 dispatch returned:
- **Correctness** (`review-correctness.json`): APPROVED_WITH_FINDINGS — 4 MIN + 1 nit, no CRIT/MAJ.
- **Safety / bypass** (`review-safety.json`): BLOCKED — 3 MAJ (SAFE-003, SAFE-009, SAFE-011) + 8 MIN + 1 nit.
- **Completeness / governance** (`review-completeness.json`): timed out at 900 s; retry dispatched at 1800 s ceiling (`review-completeness-r1retry.json`).

## Closures applied to `docs/adoption/ADOPT-001-project-onboarding.md` §12.7

See DISPATCH-NOTE.md "Fix-round-1 closures" table for the per-finding mapping.

Headlines:

- **SAFE-003 (MAJ).** §12.7.4 rewritten with two-mode break-glass: multi-maintainer (Gate 1 machine-enforced via `count >= 1` + CODEOWNER + non-author) vs single-operator (Gate 1 documentation-only per D-033's `count = 0` correction; Gates 2 + 3 are the machine-enforced checks). Removes the operationally-wrong "self-approval is structurally impossible" phrasing.
- **SAFE-009 (MAJ).** §12.7.4 final paragraph names `.scp/rule-config.yaml` `disable: true` as a parallel bypass surface NOT covered by `verify-bypass-pairing.sh`; demands CODEOWNERS protection per §11.10; explains the SCP-E006 + expired-config grace ramp interaction.
- **SAFE-011 (MAJ).** Reviewer's mitigation explicitly contemplates a follow-up. §12.7.13 added with a v1.0.0 supply-chain-posture disclosure naming the OPA + Conftest SHA256 verification in place and the Regal SHA256 gap. Tracked as **TF-020H3-001 → slice 020H.2** in DISPATCH-NOTE + STATUS.md (post-Threshold-A backlog). Not closed in this slice.
- **SAFE-001, 002, 004, 005, 006, 007, 008, 010, 012** — text additions or rewordings in §12.7.1 / §12.7.2 / §12.7.3 / §12.7.5 / §12.7.7 / §12.7.9 / §12.7.10 / §12.7.11. See DISPATCH-NOTE table for the per-finding closure summary.
- **CORR-MIN-001..004 + CORR-nit-001** — text edits in §12.7.1 / §12.7.7 / §12.7.12.

## Closures NOT applied (deferred)

- **SAFE-011 (MAJ)** — workflow change (Regal SHA256 verification). Tracked as TF-020H3-001 → slice 020H.2. See DISPATCH-NOTE for closure path.

No findings recommended descoping; the protocol-over-shortcuts invariant holds (`feedback_protocol_over_shortcuts.md`).

## Re-review

Fix-round-1 closures invalidate the prior R1 review packages' baseline. R2 lens dispatch (correctness + safety + completeness) recurses next, scoped to the post-fix-round-1 §12.7 + the new §12.7.13 disclosure + DISPATCH-NOTE. Per `feedback_recursive_adversarial_review.md`, recurse until no new BLOCKING findings.
