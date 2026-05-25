# DISPATCH-NOTE — WP-SCP-024 slice 024E (mapp-doc-agent — adopter #3 of 5)

**Date:** 2026-05-25
**Branch:** `chore/024e-mapp-doc-agent-close-out` (off origin/main at `c7266fb`)
**Predecessor:** 024D closed 2026-05-25 (control-tower cohort adopter #2 LIVE). v1.3.0 cut 2026-05-25 (R-007 + R-008 LIVE estate-wide). Scaffolder pins to v1.3.0 release SHA `d9cf52544eea7eb2b0cc5486187952eaef40b1e1`.
**Decision reserved:** (inherits **D-045** pattern from 024C/024D — per-adopter onboarding contract; no new D-NNN consumed by this slice).

- **Target:** jrnb2024/mapp-doc-agent

**Adopter slug** (per plan-doc §5.2 invariant 2 regex format spec — `<owner>-<repo>` lowercased): `jrnb2024-mapp-doc-agent`.

cascade-status: onboarded
`slice-type: cohort`

(Per WP-SCP-024 §5.2 invariant 2 enum the workflow accepts only `onboarded` / `onboarded-operator-bump` / `blocked-on-adopter-conflict` for cohort slices; this slice's ceremony is complete + branch-protection-flipped + CI-green so `onboarded` is the correct enum value. The ≥1-calendar-week + ≥1-Renovate-cycle bake observation is a separate AC tracked under "Acceptance criteria status" below, not encoded in the cascade-status field.)

**FLA pilot safety findings reviewed:** none new since 024D close 2026-05-25 (FLA-independent per invariant 4).

## Cross-repo coordination (plan-doc §5.5)

| Notification | Path | Status |
|---|---|---|
| Adopter-side wrapper landing | [jrnb2024/mapp-doc-agent#57](https://github.com/jrnb2024/mapp-doc-agent/pull/57) (merged `74fa341` 2026-05-25 PM) | MERGED with trailing-dash regression in wrapper (silently failed first run) |
| Adopter-side smoke-test + wrapper fix | [jrnb2024/mapp-doc-agent#58](https://github.com/jrnb2024/mapp-doc-agent/pull/58) (merged `950ee86` 2026-05-25 PM via `--admin`) | MERGED; `policy-check / scp/policy-check` GREEN end-to-end at 2026-05-25T20:26:30Z post-wrapper-fix |
| SCP-side scaffolder template fix | [jrnb2024/standards-control-plane#170](https://github.com/jrnb2024/standards-control-plane/pull/170) (merged `c7266fb` 2026-05-25 PM) | MERGED; future scaffolder runs emit correct repo path |

## Why mapp-doc-agent as adopter #3

Per WP-SCP-024 plan-doc §5.1 canary-first sequencing: PIM → CT → **mapp-doc-agent + recommender paired** → shopify-app last. mapp-doc-agent is the smaller-surface half of the paired slice — documentation-intelligence service (RAG + OpenSearch); minimal frontend; small `services.yml`; low onboarding risk + good signal on the rule library against a Node.js + Python codebase. Recommender (mf-intent-os) sibling onboarding was DEFERRED to morning 2026-05-26 per FUP-024E-RECOMMENDER-DEFER-MANIFEST-STALE-001 (Recommender's `manifest-verify` required check failing on `ErrManifestStale` — unrelated to SCP; separate workstream).

## Scope (in)

| Deliverable | Path | Notes |
|---|---|---|
| Cascade slice DISPATCH-NOTE | `docs/reviews/WP-SCP-024/024E-mapp-doc-agent-cascade-slice/DISPATCH-NOTE.md` | This file. `cascade-status: onboarded`. |
| Invocation-log entry | `docs/reviews/WP-SCP-020/branch-protection-log.md` | Operator-pasted from `enable-required-check.sh` output 2026-05-25T20:19:52Z. See appended entry. |
| STATUS.md chain entry | `STATUS.md` | 2026-05-25 chain entry row (this PR). |
| R-cycle archives | (none) | This slice is operator-attended ceremony close-out; no Codex Tier 2 dispatch + no R-cycle artefacts beyond the runtime smoke-test on adopter PR #58. |

## Onboarding sequence (this slice — completed steps + the bumps)

| Step | Time (UTC) | Action | Outcome |
|---|---|---|---|
| 1 | 2026-05-25 ~19:00 | SCP-side scaffolder run + wrapper PR #57 opened | Wrapper landed with trailing-dash regression (scaffolder template not updated post-repo-rename; see FUP-WP-SCP-024-SCAFFOLDER-RENAME-SWEEP-001). |
| 2 | 2026-05-25 ~19:01 | PR #57 wrapper-landing CI run | **FAILED** silently (GHA startup_failure; `actions/checkout` couldn't resolve `jrnb2024/standards-control-plane-`). Not surfaced in `gh pr checks` rollup as a normal FAILURE — appeared as "no jobs created". |
| 3 | 2026-05-25 ~19:??  | Operator merged PR #57 | Wrapper on main, but broken. |
| 4 | 2026-05-25 ~19:??  | Operator App-install on mapp-doc-agent + secrets propagation (`SCP_FEDERATION_APP_ID` + `SCP_FEDERATION_APP_PRIVATE_KEY`) | App installed + both secrets present (verified via `gh secret list`). |
| 5 | 2026-05-25T20:19:52Z | Operator ran `enable-required-check.sh --repo jrnb2024/mapp-doc-agent --branch main --preserve-existing-contexts` | Required-check flipped GREEN on script's verification phase. **HOWEVER** this happened BEFORE smoke-test verified GREEN — see FUP-WP-SCP-024-SMOKE-TEST-BEFORE-FLIP-001. mapp-doc-agent main was in a hard-blocked state for ~6 min until step 7. |
| 6 | 2026-05-25 ~20:22  | Smoke-test PR #58 opened + 1st CI run | **FAILED** (same trailing-dash regression visible end-to-end on the PR — surfaced the bug). |
| 7 | 2026-05-25 ~20:24  | Wrapper fix-up commit pushed to PR #58 branch | `0171f60` drops trailing-dash in 2 places. CI re-ran. |
| 8 | 2026-05-25T20:26:30Z | PR #58 policy-check / scp/policy-check | **GREEN** end-to-end. mapp-doc-agent fully LIVE. |
| 9 | 2026-05-25 ~20:?? | PR #58 merged via `--admin` (`required_signatures` + `enforce_admins` + missing CODEOWNERS reviewer triggered "base branch policy prohibits merge" without admin override) | Smoke-test landed at `950ee86`. |
| 10 | 2026-05-25 ~20:?? | SCP-side scaffolder template fix PR #170 merged at `c7266fb` | Closes the regression at source. Future adopters scaffolded post-merge are clean. |
| 11 | 2026-05-25 ~20:?? | This close-out PR opens | DISPATCH-NOTE + branch-protection-log entry + STATUS row. |

## What didn't quite go to plan (defects + follow-ups)

1. **Scaffolder template trailing-dash regression** — root cause was SCP PR #152 ("post-rename ref hygiene" merged 2026-05-24) updating SCP's own `policy-check.yml` cross-repo refs but missing the scaffolder template + the Renovate `# renovate: depName=...` marker. Closed at source via SCP PR #170. Forward-followup: FUP-WP-SCP-024-SCAFFOLDER-RENAME-SWEEP-001 (P2) — investigate how CT's wrapper (scaffolded post-rename 2026-05-25 AM) ended up with the CORRECT path despite the template carrying the bug. Most likely a manual post-scaffold edit; need to confirm + write a preflight test catching this for future renames.
2. **Operator flipped required-check before smoke-test verified GREEN.** Caused mapp-doc-agent main to be hard-blocked for ~6 minutes. Forward-followup: FUP-WP-SCP-024-SMOKE-TEST-BEFORE-FLIP-001 (P2) — extend `enable-required-check.sh` with a pre-flight check requiring a recent GREEN wrapper run on base branch, or explicit override flag.
3. **PR #57 wrapper-landing failed silently.** GHA startup_failure ("This run likely failed because of a workflow file issue" — no jobs created) doesn't surface in `gh pr checks` rollup as a normal FAILURE. The wrapper merged anyway. Forward-followup: same as item 2 — pre-flight check on `enable-required-check.sh` would have caught this.

## Acceptance criteria status

- **AC1 (cascade-status flipped):** ✓ — `cascade-status: onboarded` in this DISPATCH-NOTE.
- **AC2 (required-status-check live on main):** ✓ — `policy-check / scp/policy-check` REQUIRED on `jrnb2024/mapp-doc-agent@main` (verified via `gh api repos/jrnb2024/mapp-doc-agent/branches/main/protection`).
- **AC3 (≥1 calendar week bake observation):** ⏳ pending — bake observation starts 2026-05-25; target close ≥2026-06-01.
- **AC4 (≥1 Renovate-issued SHA bump cycle clean):** ⏳ pending — Renovate auto-PR expected within ~24h of v1.3.0 cut (already happened); verify wrapper bump auto-PR lands GREEN once it appears.
- **AC5 (no CT-side / adopter-side TF asking to relax gate):** ✓ at filing — no TF filed asking for relaxation.

## Sibling slice (Recommender) — DEFERRED

Recommender (mf-intent-os, adopter #4) was paired with mapp-doc-agent in the original 024E scope but onboarding was DEFERRED to morning 2026-05-26. PR `jrnb2024/mf-intent-os#194` CLOSED; branch `chore/scp-024e-onboarding` (with wrapper fix `37c0d75`) preserved. Cause: Recommender-internal `manifest-verify` required check failing on `ErrManifestStale` (CT contract manifest >24h stale; separate `claude/manifest-stale-24h-mid-cascade-int` investigation in flight). SCP-side gate verified GREEN end-to-end pre-defer (App installed + both secrets present + policy-check / scp/policy-check GREEN on re-run 26418500845). See FUP-024E-RECOMMENDER-DEFER-MANIFEST-STALE-001 for closure path.

## Bus-factor-1 disclosure

This slice continues the D-031 single-operator posture (operator @jrnb2024 holds App private key + executes ceremonies). 2026-07-21 quarterly D-031 review covers the App-key custody question.
