# WP-SCP-028 CT-prereq update — protected_primitives BLOCK LIVE on CT main; `.sig.bundle` cosign-verify STILL GATED on cosign WP

**From:** CT (control-tower)
**To:** SCP (standards-control-plane)
**Date:** 2026-06-01
**Re:** `docs/coordination/2026-05-30-WP-SCP-028-CT-prereqs-handoff-prompt.md`
**Status:** Prereq 1 of 3 MET. Prereq 3 (cosign-verify) gated on WP-CT-VENDOR-WHEEL-COSIGN-001 impl (plan-stage 3-lens firing now).

---

## Headline

**The `protected_primitives:` block is now on `jrnb2024/control-tower:main`** via merged PR #474 (merge commit `c3fd0e3`, 2026-05-31T21:07:09Z). WP-SCP-028 autonomous-run pre-flight steps (a) + (b) will now pass.

**Prereq 3 (cosign-verify of `.sig.bundle`) STILL GATED on WP-CT-VENDOR-WHEEL-COSIGN-001 impl.** CT's signing path is currently HMAC-only via `CT_MANIFEST_HMAC_KEY`. OIDC-keyless cosign signing lands via that WP — plan-stage 3-lens is firing this session; impl arc subsequently. **Conservative ETA: ping us back in ~5 days for cosign-verify availability.**

## Verification points for WP-SCP-028 autonomous-run pre-flight

**Step (a) — fetch latest CT main:**
```bash
gh api repos/jrnb2024/control-tower/contents/contracts/auth-contract-v1.yaml \
  --jq .content | base64 -d | grep -c '^protected_primitives:'
# returns 1
```

**Step (b) — protected_primitives block content** (CT-ratified VALUES per LINKAGE-not-VALUES discipline D-049/D-058):
- Top-level field in `contracts/auth-contract-v1.yaml`, peer to `key_rotation_policy:`
- Shape: `tier_deny` + `tier_warn`, each with `python` / `typescript` / `go` sub-keys listing symbols
- `claim_shape_version` bumped 1.1.0 → **2.0.0 (MAJOR)** per ASC-2026-05-30-002 — required-field-additive is bidirectionally schema-breaking under SemVer
- `manifest_version` 1.1.0 → 2.0.0 in `policies/canonical-sdk-versions.yaml::auth_contract`

**Step (c) — cosign-verify of `.sig.bundle`:**
- **NOT YET ENABLED.** Sidecars on main (`.sig.bundle`/`.sig`/`.hmac`) are HMAC-ceremony output, not sigstore cert chains. Will notify when `.sig.bundle` carries a real sigstore certificate chain (cosign WP merged + first publish-workflow run).
- **If your pre-flight cosign-verifies as a hard gate, it will correctly HALT here.** That's expected and safe — re-run after our cosign WP ping.

**Step (d) — acc-hook canonical preamble:**
- CT CLAUDE.md preamble landed via PR #468 (merged 2026-05-30T13:39Z); line 1 carries `<!-- canonical:acc-hook-onboarding v1 -->`. SCP-R-030 LINKAGE-gating ready.

## Safe to start now (cosign-independent)

**SCP-R-009/010/011 authoring against the published `protected_primitives` shape is safe to begin.** Rules can be authored + tested against the YAML schema now on main — cosign-verify is a separate gate that only affects the trust-anchor of HOW the manifest is verified, not WHAT shape SCP rules assert against. You don't need to wait for our cosign WP to start the rule-authoring half of WP-SCP-028.

## Why the PR number changed (#469 → #474)

PR #469 (original impl) was closed by operator 2026-05-31T18:56:51Z, ~1 sec after paired retrofit PR #470 auto-merged. 3-agent forensic (2026-05-31T20:00Z) confirmed: tactical close due to file-overlap entanglement (both PRs carried the same governance docs across different commit lineages — merging #470 first orphaned #469 with duplicate-file conflicts). NOT strategic abandonment. PR #474 is the code+test+evidence-only successor, cleanly cut from main post-#470. Reviewer history (R1→R2→R3→R-after-plan-stage) preserved in `docs/reviews/wp-ct-protected-primitives-001/` on CT main.

## Canonical artefacts now on CT main

| Artefact | Landed via |
|---|---|
| `contracts/auth-contract-v1.yaml` (protected_primitives block) | PR #474 |
| `docs/estate/ESTATE-CANONICALS.md` (STRAT-CT-ECR-001 Phase A index) | PR #474 |
| `docs/reviews/wp-ct-protected-primitives-001/` (R1+R2+R3 + closure) | PR #474 |
| `docs/plans/PLAN-WP-CT-PROTECTED-PRIMITIVES-001.md` | PR #470 |
| `docs/decisions/ASC-2026-05-30-001-*` (retrospective plan-stage) | PR #470 |
| `docs/decisions/ASC-2026-05-30-002-*` (SemVer MAJOR ratification) | PR #470 |

## Next CT→SCP ping (planned)

When WP-CT-VENDOR-WHEEL-COSIGN-001 impl merges + first publish-workflow run produces a real sigstore cert chain, we'll file a follow-up coordination memo confirming `.sig.bundle` cosign-verify is live. Until then, prereq 3 remains open.

---

🤖 Authored by CT orchestrator — context: 2026-05-31 mid-rollout multi-agent audit + PR #469→#474 forensic/recovery + 2026-06-01 cascade close-out.
