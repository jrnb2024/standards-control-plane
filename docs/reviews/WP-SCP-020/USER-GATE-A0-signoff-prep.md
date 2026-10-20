# USER-GATE-A0 — operator signoff package

**Status:** AWAITING SIGNATURE.
**Gate position:** between WP-SCP-020 slice 020E.a and slice 020D2.
**Prepared:** 2026-04-30 (afternoon).
**Operator:** James Brooke (@jrnb2024).

This is the human-input gate that pauses the WP-SCP-022 execution chain before the federation primitive's gate is promoted from advisory → required. Once signed, slice 020D2 enables `scp/policy-check` as a required status check on `main` with `enforce_admins=true`, then cuts `v1.0.0` from the resulting `main`.

---

## What you'd be signing off

> "I, @jrnb2024, accept the operational state of the federation primitive at v1.0.0-rc.1 and authorise WP-SCP-022 to flip `scp/policy-check` from advisory to required on the SCP repository's `main` branch, then cut `v1.0.0`."

The signature is recorded as a commit signed by your SSH key; that commit lands on `main` via this signoff PR.

## Threshold A progress at this gate

```
020A    plan + D-022/D-023                          ✅ landed
020B    reusable workflow                           ✅ landed (PR #36)
020B.1  workflow-selftest harness                   ✅ landed (PR #38)
020B.2  scripts/scp-policy-check local repro        ✅ landed (PR #41)
020C    3 starter Rego rules                        ✅ landed (PR #49)
020C.1  waiver-aware + conflict-gate + read-back    ✅ landed (PR #52)
020J    tag-protection v* + signed-commits          ✅ landed (PR #53) + applied
020K    CODEOWNERS wiring                           ✅ landed (PR #56)
020D1   self-dogfood wrapper (advisory mode)        ✅ landed (PR #57)
020H.1  v1.0.0-rc.1 release notes + tag             ✅ landed (PR #58) + tagged
020E.a  pre-protection canary                       ✅ landed (PR #60)
🛑 USER-GATE-A0  ← YOU ARE HERE
020H.2  observability dashboards                    ⏳ next
020D2   required-status-check + cut v1.0.0          ⏳
🛑 USER-GATE-A   Threshold A signoff (FINISH LINE)   ⏳
```

## Today's work (one session, 2026-04-30)

10 PRs landed, 1 release tag cut, 0 unsigned commits on `main` since the morning:

| # | PR | Slice | Notes |
|---|---|---|---|
| 1 | [#53](https://github.com/jrnb2024/standards-control-plane/pull/53) | 020J | tag-protection v* + required_signatures applied |
| 2 | [#54](https://github.com/jrnb2024/standards-control-plane/pull/54) | governance | STATUS.md + AM continuation prompt |
| 3 | [#55](https://github.com/jrnb2024/standards-control-plane/pull/55) | docs | SCP overview demo deck (python-pptx + 8 mermaid diagrams) |
| 4 | [#56](https://github.com/jrnb2024/standards-control-plane/pull/56) | 020K | CODEOWNERS wiring + D-031 (3-round R1 fixpoint, 2 MAJ + 8 MIN + 11 nit closed) |
| 5 | [#57](https://github.com/jrnb2024/standards-control-plane/pull/57) | 020D1 | self-dogfood wrapper (advisory mode); first real-PR self-gate |
| 6 | [#58](https://github.com/jrnb2024/standards-control-plane/pull/58) | 020H.1 | v1.0.0-rc.1 release notes + lib targets-array CI fix |
| 7 | tag | — | `v1.0.0-rc.1` cut from PR #57 merge SHA `351b7b7` |
| 8 | [#59](https://github.com/jrnb2024/standards-control-plane/pull/59) | 020E.a | DO-NOT-MERGE canary demonstrating SCP-R-001 deny |
| 9 | [#60](https://github.com/jrnb2024/standards-control-plane/pull/60) | 020E.a | canary evidence doc |
| 10 | this | gate | USER-GATE-A0 signoff prep |

**Risk-weighted ETA delivered:** the morning estimate was "floor: 020D1 past; mid case: USER-GATE-A0 awaiting signoff; stretch: Threshold A reached." Actual: USER-GATE-A0 awaiting signoff (mid case).

## What you should verify before signing

### 1. The federation primitive deny works on a real PR

PR [#59](https://github.com/jrnb2024/standards-control-plane/pull/59) is the live demonstration. Open the PR; the `policy-check / scp/policy-check` check is FAILED; the structured finding payload at `docs/reviews/WP-SCP-020/canary-evidence.md` shows the Rego rule rejecting an out-of-set `deprecation_close_date`.

### 2. The self-dogfood wrapper is in place

`.github/workflows/policy-check-wrapper.yml` exists on `main`. It invokes the reusable workflow at `@9820489...` (the 020K merge commit). Every PR to main from this point forward runs through the gate (currently advisory).

### 3. Branch protection state

```bash
gh api repos/jrnb2024/standards-control-plane/branches/main/protection \
  | python3 -m json.tool | head -25
```

Expected:
- `required_signatures.enabled: true` (live since 020J morning).
- `required_status_checks: null` (NOT yet enforcing — that's what 020D2 changes).
- `enforce_admins: false` (NOT yet on — 020D2 sets to `true`).

### 4. v1.0.0-rc.1 release exists

[Releases page](https://github.com/jrnb2024/standards-control-plane/releases/tag/v1.0.0-rc.1) — the rc.1 release is published with the full release notes (3 rules, error codes, tracked-forward items).

### 5. CODEOWNERS coverage is broad enough

```bash
cat CODEOWNERS
```

13 path rules cover policies, schemas, lib, tests, .github, renovate, DECISIONS.md, security/adoption/plans/integrations docs, output/findings/control-tower/ci, and CODEOWNERS itself. The 020K R1+R2+R3 review surfaced 7 MAJ + 4 MIN + 6 nit findings; all closed.

### 6. The one open canary (PR #59) is correctly marked DO-NOT-MERGE

Check the PR title + body. If you accidentally merge it, the canary fixture is broken and `services.yml` lands a deliberate violation on `main`. Don't merge it.

## What 020D2 will do once you sign

1. Run `gh api -X PUT repos/jrnb2024/standards-control-plane/branches/main/protection` to set:
   - `required_status_checks: {strict: true, contexts: ["scp/policy-check"]}`
   - `enforce_admins: true`
   - `required_pull_request_reviews: {required_approving_review_count: 1, dismiss_stale_reviews: true, require_review_from_non_author: false}` (per 020K personal-account closure).
2. Cut `v1.0.0` tag from the resulting `main` head.
3. Publish the GitHub release for `v1.0.0` (promote rc.1 → v1.0.0; release notes copy from `docs/releases/v1.0.0-rc.1.md` with the rc.1 → v1.0.0 delta noted).
4. Open PR #61 for the v1.0.0 release-signoff doc at `docs/reviews/WP-SCP-020/release-signoff.md`.

After 020D2 lands, the chain stops at **USER-GATE-A** (Threshold A signoff — the finish line). 020E.b + 020E.c (post-protection canary, waiver-suppression canary) are post-USER-GATE-A.

## Open issues

None blocking. Tracked-forward items TF-005..008 (from 020C.1) and TF-D1-001..003 (from 020D1) all have resolution paths in v1.1+ or 020H part 3 (the canonical adopter template authorship slice).

## How to sign off

```bash
cd /Users/amplience/Projects/scp-track1
git checkout feature/wp-scp-022-user-gate-a0-signoff-prep
# Review this doc one more time, then:
echo "USER-GATE-A0 signed by @jrnb2024 at $(date -u +'%Y-%m-%dT%H:%M:%SZ')" >> docs/reviews/WP-SCP-020/USER-GATE-A0-signoff-prep.md
git add docs/reviews/WP-SCP-020/USER-GATE-A0-signoff-prep.md
git commit -m "USER-GATE-A0 signed by @jrnb2024 — authorising 020D2"
git push
gh pr create --base main --head feature/wp-scp-022-user-gate-a0-signoff-prep \
  --title "USER-GATE-A0 signed — authorising 020D2 (required check + v1.0.0)" \
  --body "Operator signoff before promoting scp/policy-check to required."
```

Then squash-merge the PR. Once it lands on `main`, I will resume the chain at slice 020D2.

## How to NOT sign off

If anything in the verification list above doesn't look right, say so. We pause the chain, fix the concern (or revert work if needed), and re-prepare the signoff doc.

---

## Signature

USER-GATE-A0 signed by @jrnb2024 at 2026-04-30T15:02:54Z.

The signature commit is signed by SSH key `~/.ssh/git_signing_ed25519`
(GitHub signing key id 925245). `required_signatures` is enabled
on `main` since 2026-04-30 morning, so this commit is verified-signed
end to end.

Authorised: WP-SCP-022 to proceed with slices **020H part 2**
(promote v1.0.0-rc.1 → v1.0.0 with release-signoff.md) and
**020D2** (enable `scp/policy-check` as required status check on
`main` with `enforce_admins=true` + branch-protection per 020K
personal-account closure).

After 020D2 lands, the chain stops at **USER-GATE-A** — Threshold A.
