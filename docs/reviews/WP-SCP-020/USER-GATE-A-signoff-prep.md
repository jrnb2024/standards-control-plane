# USER-GATE-A — Threshold A operator signoff

**Status:** AWAITING SIGNATURE.
**Gate position:** Threshold A — the WP-SCP-020 + WP-SCP-022 finish line.
**Prepared:** 2026-04-30 (afternoon).
**Operator:** James Brooke (@jrnb2024).

This is the terminal gate of WP-SCP-022. Once signed, the operator confirms that the federation primitive at v1.0.0 gates SCP's own main successfully — Threshold A is closed.

---

## Threshold A — definition

> **Threshold A:** SCP gates itself on its own `main` via the federation primitive's reusable workflow with a required-status-check, all three v1.0.0 Rego rules enforcing, conflict-gate green on every PR, and a v1.0.0 release tag cut.

## Threshold A — verification matrix

| Criterion | State | Evidence |
|---|---|---|
| Self-dogfood wrapper at `.github/workflows/policy-check-wrapper.yml` | ✅ | PR #57 (`351b7b7`); wrapper invokes the reusable workflow at `@9820489` |
| `scp/policy-check` is a required status check on `main` | ✅ | 020D2 applied 2026-04-30; verified via `gh api` |
| `enforce_admins: true` (no admin bypass) | ✅ | Same |
| `required_signatures: true` (every commit on main is verified-signed) | ✅ | 020J applied 2026-04-30 morning |
| `required_pull_request_reviews` (1 approving, dismiss stale, codeowners) | ✅ | 020D2 applied |
| All 3 v1.0.0 Rego rules enforcing | ✅ | `policies/SCP-R-001.rego`, `_002.rego`, `_003.rego` — waiver-aware via `policies/scp_common.rego` (PR #52) |
| Conflict-gate workflow operational | ✅ | `.github/workflows/conflict-gate.yml` + `tests/conflict_gate/` (PR #52); shared fixtures for 2 of 3 rules (TF-006 covers SCP-R-003) |
| `v1.0.0` release tag cut | ✅ | Tag `v1.0.0` at `04523fa`; release published at `https://github.com/jrnb2024/standards-control-plane/releases/tag/v1.0.0` |
| Pre-protection canary deny verified | ✅ | PR #59 (canary/deliberate-violation-pre); workflow-run-id 25172373569; structured finding payload at `docs/reviews/WP-SCP-020/canary-evidence.md` |
| Post-protection canary blocked | ✅ (effective) | PR #59 now `mergeStateStatus: BEHIND` post-020D2; cannot merge under strict=true even if rebased (CI would fail). Formal 020E.b slice + evidence doc are post-USER-GATE-A |

**All Threshold A conditions met.**

## Today's full chain (one session, 2026-04-30)

| # | PR / artefact | Slice | Outcome |
|---|---|---|---|
| 1 | PR [#53](https://github.com/jrnb2024/standards-control-plane/pull/53) | 020J | ✅ tag-protection + required_signatures applied |
| 2 | PR [#54](https://github.com/jrnb2024/standards-control-plane/pull/54) | governance | ✅ STATUS.md + AM continuation prompt |
| 3 | PR [#55](https://github.com/jrnb2024/standards-control-plane/pull/55) | docs | ✅ SCP overview demo deck |
| 4 | PR [#56](https://github.com/jrnb2024/standards-control-plane/pull/56) | 020K | ✅ CODEOWNERS wiring + D-031 (3-round R1 fixpoint) |
| 5 | PR [#57](https://github.com/jrnb2024/standards-control-plane/pull/57) | 020D1 | ✅ self-dogfood wrapper (advisory) |
| 6 | PR [#58](https://github.com/jrnb2024/standards-control-plane/pull/58) | 020H.1 | ✅ rc.1 release notes + lib bash fix |
| 7 | tag `v1.0.0-rc.1` | — | ✅ cut from `351b7b7` |
| 8 | PR [#59](https://github.com/jrnb2024/standards-control-plane/pull/59) | 020E.a | ✅ canary opened (DO-NOT-MERGE) |
| 9 | PR [#60](https://github.com/jrnb2024/standards-control-plane/pull/60) | 020E.a | ✅ canary evidence merged |
| 10 | PR [#61](https://github.com/jrnb2024/standards-control-plane/pull/61) | gate | ✅ USER-GATE-A0 signed |
| 11 | PR [#62](https://github.com/jrnb2024/standards-control-plane/pull/62) | 020H part 2 | ✅ release-signoff merged |
| 12 | tag `v1.0.0` | — | ✅ cut from `04523fa` |
| 13 | PR [#63](https://github.com/jrnb2024/standards-control-plane/pull/63) | 020D2 | ✅ required-check + branch protection applied |
| 14 | this | gate | 🛑 USER-GATE-A — awaiting signature |

**13 PRs landed, 2 release tags cut, 1 release published, 0 unsigned commits on main, 0 R1-review-blocking findings unaddressed, 2 canary CI fixpoints absorbed.**

## What you'd be signing off

> "I, @jrnb2024, confirm that as of 2026-04-30, the Standards Control Plane federation primitive at v1.0.0 gates the SCP repository's own `main` branch in enforced mode. Every PR to `main` from this point forward is bound by `scp/policy-check`, requires an approving review, requires verified-signed commits, and cannot be bypassed by admin override. WP-SCP-020 is closed; WP-SCP-022 reaches Threshold A."

## What changes after signature

Nothing operational — Threshold A is the *recognition* that the work is done. The federation primitive is already enforcing; signing closes the WP and authorises:

1. Auto-memory update: WP-SCP-022 marked closed; project_wp_scp_022_plan reflects Threshold A reached.
2. STATUS.md update marking the programme finish line.
3. Continuation note: post-Threshold A work flows to follow-up WPs:
   - **020E.b + 020E.c**: post-protection canary + waiver-suppression canary (formal evidence beyond the implicit BEHIND-blocked posture of PR #59).
   - **020F**: Renovate shared preset.
   - **020G**: branch-protection automation script for adopter onboarding.
   - **020H part 3**: ADOPT-001 §12 federation-integration appendix (closes TF-D1-001..003).
   - **020H.1**: VERSIONING.md + rule-RFC process + rollback detection (cron workflow).
   - **WP-SCP-022 proposal-queue**: structured proposal queue for new rules.
   - **WP-SCP-023**: cross-repo scorecards.
   - **WP-SCP-024**: estate cascade (FLA pilot, then PIM/recommender/etc.).

## Open issues at Threshold A

None blocking. Tracked-forward items:

- **TF-005..008** (from 020C.1) — all have resolution paths: 020D2 acceptance criterion, WP-SCP-023, OPA upstream attestation watch, v1.1.
- **TF-D1-001..003** (from 020D1 R1 review) — fold into 020H part 3 authorship.
- **TF-E.a-001** (from 020E.a) — cold-start vs warm-start measurement, picked up in 020E.c when scripts/replay-canary.sh lands.

## How to sign off

```bash
cd /Users/amplience/Projects/scp-track1
git checkout feature/wp-scp-022-user-gate-a-threshold-a-signoff
echo "USER-GATE-A signed by @jrnb2024 at $(date -u +'%Y-%m-%dT%H:%M:%SZ')" >> docs/reviews/WP-SCP-020/USER-GATE-A-signoff-prep.md
git add docs/reviews/WP-SCP-020/USER-GATE-A-signoff-prep.md
git commit -m "USER-GATE-A signed by @jrnb2024 — Threshold A reached"
git push
gh pr create --base main --head feature/wp-scp-022-user-gate-a-threshold-a-signoff \
  --title "USER-GATE-A signed — Threshold A reached. WP-SCP-022 + WP-SCP-020 closed." \
  --body "Operator signoff at the WP-SCP-022 finish line."
```

Then squash-merge.

## How to NOT sign off

If anything in the verification matrix doesn't look right, say so. We pause, reconcile, re-prepare.

---

## Signature

USER-GATE-A signed by @jrnb2024 at 2026-04-30T15:22:48Z.

**WP-SCP-022 reaches Threshold A. WP-SCP-020 federation primitive
v1.0.0 is closed.**

The signature commit is signed by SSH key `~/.ssh/git_signing_ed25519`
(GitHub signing key id 925245). `required_signatures` is enabled
on `main`; `enforce_admins: true`; `scp/policy-check` is required;
`required_pull_request_reviews` count 1 with dismiss-stale and
codeowner-reviews enforced. This very signoff PR will pass through
the gate it ratifies.

The post-Threshold-A backlog (020E.b/c, 020F, 020G, 020H part 3,
020H.1, WP-SCP-022 proposal-queue, WP-SCP-023, WP-SCP-024) opens
as separate WP threads.
