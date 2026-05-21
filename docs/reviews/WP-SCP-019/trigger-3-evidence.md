# SVC-003 Freeze-Directive Trigger 3 — Evidence

**Trigger (programme plan §7 / `FREEZE_DIRECTIVE_SVC003.md`):**
*"Per-app migration plans drafted for apps not yet conformant."*

**Status:** Satisfied via hybrid approach ratified 2026-04-18 in the SCP ↔ CT
exchange captured at
`control-tower/governance/docs/notifications/SCP-FOLLOWUP-2026-04-18.md`
(CT commit `4fbae86`).

## Hybrid approach

Two evidence tracks, both acceptable:

1. **Central playbook (default).** One canonical playbook on Control Tower's
   `main` that every consumer repo references. Already published as:
   - `control-tower/governance/docs/ESTATE_CONSUMER_ADOPTION_GUIDE.md`
   - `control-tower/governance/docs/prompts/CT-SDK-ADOPTION-PROMPT.md`
   SCP accepts the central playbook as the default "plan per app."

2. **Per-app programme docs (as they emerge).** Individual consumer repos
   can publish their own governance-programme-level plan documents. Already
   satisfied for the Fashion Labelling Agent (FLA):
   - `fashion-labelling-agent/governance/docs/prompts/INFRA-023-SWAP-TO-CREATE-BFF-ROUTES.md`
   - `fashion-labelling-agent/governance/docs/prompts/INFRA-024-DROP-SESSION-VERIFIER-USEREF.md`
   Additional per-app docs will be added to the notification table below as
   consumer repos publish them.

Both tracks combined close trigger 3 in the letter of the programme plan's
§7 requirement.

## Scope caveat — `mode.api_key` migrations

The central playbook addresses user-session auth migration (CT-SSO /
`mode.user_oidc`). Per-app migrations from `mode.bearer_legacy` to
`mode.api_key` are a separate programme surface and are **not** considered
evidenced by this file. Those are gated on:

- `CT_AGENT_KEY_OPS.md` publishing (CT-led, target mid-to-late May 2026)
- The 2026-05-31 D-019 checkpoint outcome (see
  `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`)

Trigger 3's letter is satisfied now; the `mode.api_key` migration-planning
work is a separately-tracked programme.

## Per-app notification table (running)

| Consumer repo | Plan reference | Status | Notes |
|---|---|---|---|
| fashion-labelling-agent | `INFRA-023`, `INFRA-024` | draft | FLA PR #291 is the vendor-bump; full-governance 4-person approval in progress |
| control-tower (self) | `CT-016` + pending `CT_AGENT_KEY_OPS.md` | partial | Backend + admin UI shipped; ops doc target mid-to-late May 2026 |
| standards-control-plane (self) | `services.yml` + D-019 migration waiver | drafted, unexecuted | `mode.bearer_legacy` with close date 2026-06-30; waiver registration pending SCP-071 governance |

Additional consumer repos (acc, mapp-pim — the strangler-fig successor
to the deprecated market-feed monolith — brand-dna, recommender,
shopify-app, etc.) will be added as their own plans land. Per CT's
2026-04-18 estate bearer-token audit
(`control-tower/governance/docs/notifications/SCP-FOLLOWUP-2026-04-18-bearer-token-audit.md`)
the migration-priority ordering is:
mapp-pim → recommender → fashion-labelling → shopify-app → acc →
brand-dna → control-tower (self). *(Market Feed was removed from the
adoption chain on 2026-05-02 when it was deprecated; mapp-pim is its
successor.)*

## Evidence

- **Central playbook (Option A).** Authored and merged on
  `control-tower/main` as of 2026-04-18. See
  `ESTATE_CONSUMER_ADOPTION_GUIDE.md` and `CT-SDK-ADOPTION-PROMPT.md`.
- **CT's ratified hybrid position.** Recorded in
  `control-tower/governance/docs/notifications/SCP-FOLLOWUP-2026-04-18.md`
  §3 Q4.10 Option A / B, and CT's §4 commitments.
- **FLA per-app plan docs.** Linked above; FLA is the first worked
  example.

## Verdict

Trigger 3 is closed in the scope it covers (SDK adoption / user-session
migration). The `mode.api_key` migration-planning work downstream of
`CT_AGENT_KEY_OPS.md` is separately tracked and is not part of trigger 3.
