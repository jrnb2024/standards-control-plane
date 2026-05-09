# CT → SCP — Acknowledgement of D-035 6-rules retirement

**Date:** 2026-05-09
**From:** Control Tower (`/Users/amplience/Projects/control-tower`)
**To:** Standards Control Plane governance
**Re:** Inbound notification `governance/docs/notifications/SCP-D035-RULES-RETIRED-2026-05-09.md` (CT-side mirror), acknowledging operator decision to retire the 6 D-035-aligned SCP rules under the 2026-05-15 deadline.

---

## Acknowledged

CT has acknowledged the retirement of the 6 D-035-aligned SCP rules (`sdk_version_pin`, `ct_sdk_conformance`, `sdk_migration_waiver`, `sdk_adoption_schedule`, `bff_refresh_hardening`, `ct_auth_provider_memoization`) under their original 2026-05-15 deadline. Successor `WP-SCP-025-domain-rules-v1` is parked on SCP main per `04135f0` ("WP-SCP-025 parked + 6 D-035 rules retired under 2026-05-15 deadline").

## CT-side amendments landed

All three CT-side amendments requested in the inbound notification have landed on CT main as squash-merge commit `c252288` (PR #314 "docs: D-035 Phase 5 coordination — framing lock + briefing responses + Piece D convergence + SCP rules retirement"). Specifically:

- **Amendment 1** (Recommender response §Q6 retirement framing): applied — `docs/briefings/recommender-shopify-j1-rbac-response-2026-05-09.md` rewrites the SCP forward-look block to reference the retirement and successor batch.
- **Amendment 2** (Recommender response §Q8 SCP-deadline reference): applied — capacity argument now cites "slice 024B of the SCP estate cascade" rather than the retired 2026-05-15 deadline.
- **Amendment 3** (PLAN-CT-D-rollout.md §3 WP-D-SCP entry): applied — Option A taken. WP-D-SCP entry retained as a tombstone block flagged "RETIRED 2026-05-09" with successor pointer to WP-SCP-025; §1 scope, §4 dependency graph, §5 exit criterion 3, and §6 R-D-1 all reflect the retirement; WP-D-CONVERGE added as a new Piece D deliverable per the parallel ratification of the gate-convergence direction.
- **Amendment 4** (CT session-message "owner needed" carry-forward): retired. No CT-side owner is being recruited for the 6 rules.

## What is unchanged on CT side

- D-035 Phase 5 wave structure (Wave 1 = `returns-intelligence` only; VS deferred to Wave 1.5 pending Phase 8 merge + CT-side `client_credentials` blocker resolution).
- D-022 / WP-SCC-7 PROTECTED_TABLES posture.
- D-040 risk-scaled exception spec.

## Cross-references

- CT squash commit: `c252288` on CT main
- CT PR: jrnb2024/control-tower#314
- Inbound notification (CT-side mirror): `governance/docs/notifications/SCP-D035-RULES-RETIRED-2026-05-09.md` in CT repo (commit `0f1e45f` rebased to `c252288` on merge)
- SCP source merge: `04135f0` on SCP main
- SCP parked plan-doc: `docs/plans/WP-SCP-025-domain-rules-v1.md`

## Operational notes

- Recommender and PIM briefing responses (which carry the retirement-aware framing) ship as separate notifications dropped into Recommender and PIM repos.
- CT-side handshake template (`docs/standards/estate-auth-coordination-checklist.md`) will land as a small follow-on PR; SCP's complementary rule-applicability matrix (`docs/standards/scp-rule-applicability-when-touching-auth.md`) is the natural cross-link target. Coordination on the cross-link can happen at SCP's WP-SCP-025 kickoff if no earlier synchronisation point arises.

---

**Cross-project alignment closed-loop.** No further CT-side action expected unless the eventual WP-SCP-025 batch surfaces a rule that targets CT-owned permission-schema registration calls — at which point CT will respond to that specific rule's evidence pack request via SCP-RESPONSE.
