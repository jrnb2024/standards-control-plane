# DISPATCH-NOTE — WP-SCP-024 slice 024D (control-tower cascade)

**Date:** 2026-05-25
**Branch:** `chore/wp-scp-024-024d-ct-onboarded-close-out` (off origin/main at `a406c53`)
**Predecessor:** 024C closed 2026-05-24 (PIM cohort adopter #1 LIVE; TF-PIM-001 closed end-to-end). TF-PIM-001 Path C v2 federation primitive shape inherited verbatim (axes C/D/E/F/G/H/I closures live in main).
**Decision reserved:** (inherits **D-045** pattern from 024C — per-adopter onboarding contract; no new D-NNN consumed by this slice).

- **Target:** jrnb2024/control-tower

**Adopter slug** (per plan-doc §5.2 invariant 2 regex format spec — `<owner>-<repo>` lowercased): `jrnb2024-control-tower`.

cascade-status: onboarded
`slice-type: cohort`

(Per WP-SCP-024 §5.2 invariant 2 enum the workflow accepts only `onboarded` / `onboarded-operator-bump` / `blocked-on-adopter-conflict` for cohort slices; this slice's ceremony is complete + branch-protection-flipped + CI-green so `onboarded` is the correct enum value. The ≥1-calendar-week + ≥1-Renovate-cycle bake observation is a separate AC tracked under "Acceptance criteria status" below, not encoded in the cascade-status field.)

**FLA pilot safety findings reviewed:** none new since 024C close 2026-05-24 (FLA-independent per invariant 4).

## Cross-repo coordination (plan-doc §5.5)

| Notification | Path | Status |
|---|---|---|
| Adopter-side onboarding ack (CT-internal notification documenting wrapper landing + App-install + secrets ceremony + smoke-test outcome) | `~/Projects/control-tower/governance/docs/notifications/SCP-024D-CT-WRAPPER-ONBOARDED-2026-05-25.md` (filed via CT PR #429; merged separately) | DRAFTED 2026-05-25 (CT PR #429 smoke-test GREEN) |
| Smoke-test PR | CT PR #429 (`docs(governance): SCP WP-SCP-024 024D — CT wrapper onboarded notification`) | OPENED 2026-05-25; `policy-check / scp/policy-check` GREEN on this PR's CI confirms full App-token-exchange + cross-repo checkout end-to-end working on CT |

## Why control-tower as adopter #2

Per WP-SCP-024 plan-doc §5.1 canary-first sequencing: PIM → **CT** → mapp-doc-agent + recommender paired → shopify-app last. CT is the second cohort adopter — high-traffic flagship; covers the auth-substrate-owning estate hub. Onboarding CT validates the federation primitive against an adopter with the largest D-NNN governance surface (D-001..D-053 + ASCs + auth-cascade work).

## Scope (in)

| Deliverable | Path | Notes |
|---|---|---|
| Cascade slice DISPATCH-NOTE | `docs/reviews/WP-SCP-024/024D-control-tower-cascade-slice/DISPATCH-NOTE.md` | This file. `cascade-status: onboarded` (ceremony complete; gate live; CI GREEN on smoke test). Bake observation is a separate AC tracked below. |
| Invocation-log entry | `docs/reviews/WP-SCP-020/branch-protection-log.md` | Operator-pasted from `enable-required-check.sh` output 2026-05-25T16:39:32Z. See appended entry. |
| STATUS.md chain entry | `STATUS.md` | 2026-05-25 chain entry row 7 (this PR). |
| TF for script regression | `docs/BACKLOG.md` Phase 12 row | FUP-WP-SCP-020-ENABLE-REQUIRED-CHECK-PRESERVE-EXTENDED-001 (P2) — `--preserve-existing-contexts` flag preserves contexts list but not other pre-existing branch-protection settings (CT's `required_linear_history` + `required_conversation_resolution` flipped false unintentionally; restored by operator post-discovery). |
| R-cycle archives | (none) | This slice is operator-attended ceremony close-out; no Codex Tier 2 dispatch + no R-cycle artefacts beyond the runtime smoke-test on CT PR #429. |

## Onboarding sequence (this slice — completed steps)

| WP-SCP-024 §5.2 step | State | Citation |
|---|---|---|
| 1. Scaffolder run + MANIFEST.json | ✅ 2026-05-25T03:29:34Z | `~/scp-scaffolds/024d-ct/MANIFEST.json` |
| 2. Wrapper shape conforms | ✅ | Caller-job perms incl. axis F; selftest-mode default-false; scp-sha mirrors @<SHA>; secrets: inherit (axis G); pin `15a56d60b179a1d0bb41f0e4996aa19f0ed5bcb8` |
| 3. Adopter PR opens | ✅ 2026-05-25 | CT PR #424 |
| 3a. CT PR #424 merged | ✅ 2026-05-25 `ae36510` | Wrapper file on CT main |
| 4a. **App-install ceremony** (per ADOPT-001 §12.7.16a) — Repository access added on `jrnb2024/control-tower` | ✅ 2026-05-25 | `scp-federation-primitive` App now installed on CT in addition to SCP-self |
| 4b. **Adopter secrets** — `SCP_FEDERATION_APP_ID` + `SCP_FEDERATION_APP_PRIVATE_KEY` set on `jrnb2024/control-tower` | ✅ 2026-05-25 | (operator's local terminal) |
| 4c. **App-token-exchange smoke test** | ✅ 2026-05-25 | CT PR #429 — `policy-check / scp/policy-check` GREEN in 20s; readback `3/4 rules enabled, 0 disabled, 1 not applicable` |
| 4d. **`enable-required-check.sh --preserve-existing-contexts`** | ✅ 2026-05-25T16:39:32Z | See appended invocation-log entry in `docs/reviews/WP-SCP-020/branch-protection-log.md` |
| 5. Invocation-log entry pasted | ✅ this PR | Below |
| 6. Post-merge live-state verification | ✅ | `gh api …/protection --jq '.required_status_checks.contexts'` returned `["ok", "validate PR body", "policy-check / scp/policy-check"]` |
| 7. Bake observation begins (≥1 calendar week + ≥1 Renovate-issued SHA pin bump cycle merged + observed clean) | ⏳ 2026-05-25 → ≥2026-06-01 | Renovate auto-PR + ≥1 successful merge required for invariant 8 closure |
| 8. `cascade-status: onboarded` declared on this DISPATCH-NOTE + slice close | ⏳ pending step 7 | Post-bake-clean PR |

## What didn't quite go to plan (operator transparency)

1. **App-install ceremony required two iterations.** First test run on CT PR #424 (and subsequently CT PR #429's initial CI) failed with `Error: The 'client-id' (or deprecated 'app-id') input must be set to a non-empty string`. Root cause: the App was installed on CT's repo (Repository access updated) but `SCP_FEDERATION_APP_ID` secret was not yet set on CT. Operator added `SCP_FEDERATION_APP_ID` → next run failed with `The 'private-key' input must be set to a non-empty string` (App ID propagated; private key not set). Operator added `SCP_FEDERATION_APP_PRIVATE_KEY` → next run GREEN. **TF-024D-001 (P3):** ADOPT-001 §12.7.16a should explicitly enumerate BOTH secrets (App ID + private key) as a single ceremony step, not just "App-install". Diagnosis is straightforward via the workflow error messages, but the ceremony shape can be tightened.

2. **`enable-required-check.sh` `--preserve-existing-contexts` flag is a partial preserve.** Diff between before / after on CT's branch protection (visible in the operator's terminal output 2026-05-25T16:39:32Z): contexts list correctly preserved (now `["ok", "validate PR body", "policy-check / scp/policy-check"]` per `--preserve-existing-contexts`), `required_signatures` flipped `false → true` (intentional per D-029 invariant), BUT `required_linear_history` flipped `true → false` AND `required_conversation_resolution` flipped `true → false` (unintentional). Operator restored both via post-script `gh api PATCH`. **TF-024D-002 / FUP-WP-SCP-020-ENABLE-REQUIRED-CHECK-PRESERVE-EXTENDED-001 (P2):** the unified PUT in `scripts/enable-required-check.sh` should preserve other pre-existing branch-protection settings the script doesn't touch (linear history, conversation resolution, restrictions, etc.). Current shape over-writes those with defaults. Filed for closure ahead of cohort onboarding 024E.

## Acceptance criteria status (per plan-doc §3)

| AC | State |
|---|---|
| AC-024-CASCADE-1 (operator-attended ceremony only) | ✅ — `enable-required-check.sh` refused-`CI=true` design preserved; operator ran from interactive terminal |
| AC-024-CASCADE-2 (bake observation closes per invariant 8) | ⏳ pending step 7 |
| AC-024-CASCADE-3 (cascade-status declared at close) | ⏳ pending step 8 |
| AC-024-CASCADE-4 (FLA-independent) | ✅ — no FLA dependencies invoked |
| AC-024-CASCADE-5 (Renovate-driven SHA pin bump cycle clean ≥1) | ⏳ pending Renovate auto-PR + merge |

## Forward-looking — 024D close-out criteria

This slice flips to closed when:
1. ≥1 calendar week has elapsed (target close window: ≥2026-06-01)
2. ≥1 Renovate-issued SHA pin bump on CT's wrapper merged + observed clean
3. No CT-contributor TFs filed asking for the gate to be relaxed/reverted
4. `cascade-status: onboarded` declared via a follow-up PR amending this DISPATCH-NOTE

Once 024D closes: **2 of 5 cohort adopters live**. Next slice: 024E (mapp-doc-agent + recommender paired).

## Cross-links

- SCP PR #424 (CT wrapper onboarding): https://github.com/jrnb2024/control-tower/pull/424
- CT PR #429 (App-token-exchange smoke + governance notification): https://github.com/jrnb2024/control-tower/pull/429
- WP-SCP-024 plan-doc: `docs/plans/WP-SCP-024-estate-cascade.md` §5.2
- ADOPT-001 §12.7.16a (App-install ceremony): `docs/adoption/ADOPT-001-project-onboarding.md`
- PIM 024C precedent (closed 2026-05-24): `docs/reviews/WP-SCP-024/024C/DISPATCH-NOTE.md`
- TF-PIM-001 Path C v2 (federation primitive shape CT inherits): D-050 § Amendment 2026-05-23
