# D-019 2026-05-31 checkpoint — Option B signal

**From:** Standards Control Plane team
**To:** Control Tower team
**Date:** 2026-04-20
**Ref:**
- `control-tower/governance/docs/notifications/SCP-BRIEFING-V5-CLOSURE-2026-04-20.md`
  §2.3 (CT's request for signal by 2026-05-15)
- `control-tower/governance/docs/notifications/SCP-FOLLOWUP-2026-04-18.md`
  §3 Q5 (checkpoint ratification text — "SCP-RESPONSE §3 Q5 trigger
  text is quotable" per CT briefing)
- `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md` (SCP's checkpoint
  plan record)

---

## Signal

**SCP commits to Option B.** On 2026-05-31, SCP will invoke D-019's
amending-decision clause and slide the `mode.bearer_legacy`
deprecation close date from **2026-06-30 to 2026-09-30**. CT and the
three heavy-lift Go app teams (pim, recommender, shopify-app) should
treat **2026-09-30** as the operative estate-close date from this
signal forward.

This is the decision signal CT requested in SCP-BRIEFING-V5-CLOSURE
§2.3 ("signal by ~2026-05-15"). Filed 2026-04-20 — 25 days ahead of
CT's deadline — to give consumer-team planning maximum runway.

---

## Rationale — why the checkpoint will fire as projected

The 2026-05-31 checkpoint fires Option B if fewer than 2 of
{pim, recommender, shopify-app} have opened a `mode.api_key` adoption
PR (threshold interpretation in
`docs/reviews/WP-SCP-019/d019-may31-checkpoint.md` §Threshold
interpretation). The calendar evidence makes that outcome materially
certain:

1. **`CT_AGENT_KEY_OPS.md` publish.** Per SCP-RESPONSE §3 Q4.b and
   confirmed in CT's 2026-04-19 DRAFT-review ping, target publish is
   mid-to-late May 2026. Worst case 2026-05-28; best case 2026-05-15.
2. **Go-app migration arcs are multi-week.** Per
   `control-tower/governance/docs/notifications/SCP-FOLLOWUP-2026-04-18-bearer-token-audit.md`
   (CT's estate inventory) and `CT_AGENT_KEY_OPS.md` §11.1–§11.3:
   pim requires ~8–12 new scope registrations before the first SA
   create; recommender's first step is a waiver PR, not an adoption
   PR; shopify-app's inbound surface is Shopify HMAC (not CT) while
   its outbound S2S path is coupled to recommender's arc. None of
   the three is primed to open a first `mode.api_key` PR within 3–16
   days of ops-doc publish — the implied window.
3. **Recommender's path is waiver-first.** Per
   `CT_AGENT_KEY_OPS.md` §11.2 (DRAFT, reviewed in
   `docs/reviews/WP-SCP-019/ct-agent-key-ops-review-response.md`),
   recommender is directed to declare `mode.bearer_legacy` with a
   waiver and migrate to `mode.service_rs256` when operational —
   NOT to adopt `mode.api_key`. Recommender therefore cannot
   contribute to the checkpoint count by design. The threshold
   becomes ≥ 2 of 2 ({pim, shopify-app}) rather than ≥ 2 of 3.
4. **Shopify-app outbound coupling.** Per `CT_AGENT_KEY_OPS.md`
   §11.3, shopify-app's outbound S2S path migrates **when
   recommender does**, not before. Only the per-tenant CT-integration
   surface (optional, admin-side only) is available to shopify-app
   as an independent `mode.api_key` adoption. That is not the load-
   bearing migration.

The practical threshold reduces to: pim opens its `mode.api_key` PR
in ≤ 3 weeks post-ops-doc-publish. Possible — but a single-point-of-
failure count ≥ 2 is implausible.

---

## What this signal commits

Effective from this filing (2026-04-20):

- **Estate close date is 2026-09-30** for CT-side rollout planning,
  consumer-team communications, and any outbound CT messaging about
  the `mode.bearer_legacy` deprecation window.
- CT may reference this signal when communicating to pim, recommender,
  and shopify-app teams; the 2026-06-30 date should no longer be
  quoted in external comms from 2026-04-20 forward.

Effective from 2026-05-31 (the checkpoint date per the ratified
plan):

- **D-021 filed** as the amending decision. Draft text lives in
  `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md` §Pre-written
  amending decision draft; SCP substitutes the observed PR count
  into the `{outcome}` placeholder.
- **SCP's own `services.yml`** `mode.bearer_legacy`
  `deprecation_close_date` field updates from `"2026-06-30"` to
  `"2026-09-30"`.
- **`output/findings/waivers.json` `scp-bearer-legacy-migration`**
  `expires_at` updates to `2026-09-30T23:59:59Z` once the waiver is
  first registered (currently pending SCP-071 governance-owner
  confirmation; update happens at registration).
- **Outcome record** added to `d019-may31-checkpoint.md` §Outcome.

---

## Governance provenance — why SCP signals early but files D-021 on
2026-05-31

CT's briefing phrasing ("Operationally, this is D-019 amending-
decision clause invocation") treats signal and invocation as
equivalent. SCP decouples them deliberately:

- **Signal (this file, 2026-04-20).** Commits SCP's operational
  position; unblocks CT's consumer-team communications; gives the 3
  Go app teams the runway they need.
- **Invocation (D-021 filing, 2026-05-31).** Preserves evidence-
  based decision recording at the ratified checkpoint date. D-021's
  trigger text cites the observed PR count, not a forecast. If the
  evidence flips (unlikely but possible — a surprise pim or
  shopify-app adoption PR in May), D-019 stands and this signal is
  retracted.

The governance rigor of waiting for actual evidence matters because
D-021 is a formal decision record. The operational signal matters
because consumer teams need to plan weeks in advance. The two
concerns separate cleanly.

---

## Open thread — threshold-language confirmation

`d019-may31-checkpoint.md` §Threshold interpretation still lists SCP's
reading of "opened a `mode.api_key` adoption PR" as pending CT
confirmation. This signal does not presuppose confirmation — the
rationale above holds even if CT's interpretation is narrower
(e.g. merged-PR-only rather than draft-PR-acceptable) because the
narrower interpretation makes the Option-B case stronger, not weaker.
CT may confirm or adjust the threshold language in a response to this
signal; threshold-language confirmation does not need to gate
Option-B planning.

If CT's interpretation is materially broader than SCP's reading
(e.g. "any PR touching auth path counts"), SCP will re-evaluate
whether the signal should be retracted. SCP does not expect that
outcome.

---

## Impact on other threads

- **Trigger-2 ack** (closed 2026-04-20, see
  `docs/reviews/WP-SCP-019/trigger-2-evidence.md`): unaffected.
- **CT_AGENT_KEY_OPS.md review** (filed 2026-04-20, see
  `docs/reviews/WP-SCP-019/ct-agent-key-ops-review-response.md`):
  unaffected. CT's mid-to-late May publish target stands.
- **SVC-003 freeze directive**: all three triggers closed; this
  signal is downstream of the freeze picture.
- **SCP self-waiver registration** (`scp-bearer-legacy-migration`
  in `waivers.json`, blocked on SCP-071 governance owner): when
  registered, `expires_at` uses the 2026-09-30 date from this signal.

---

## References

- **CT briefing (source of the 2026-05-15 ask):**
  `control-tower/governance/docs/notifications/SCP-BRIEFING-V5-CLOSURE-2026-04-20.md`
  §2.3
- **Checkpoint plan (SCP-side):**
  `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`
- **Trigger text source:**
  `control-tower/governance/docs/notifications/SCP-FOLLOWUP-2026-04-18.md`
  §3 Q5
- **CT_AGENT_KEY_OPS review response (supporting rationale):**
  `docs/reviews/WP-SCP-019/ct-agent-key-ops-review-response.md`
  §Impact on outstanding threads
- **CT estate bearer-token audit:**
  `control-tower/governance/docs/notifications/SCP-FOLLOWUP-2026-04-18-bearer-token-audit.md`
- **D-019 decision row:** `docs/DECISIONS.md` D-019
- **D-021 pre-written draft:**
  `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md` §Pre-written
  amending decision draft

---

CT may mirror this file into
`control-tower/governance/docs/notifications/` under CT's naming
convention (briefing suggested
`SCP-SIGNAL-D-019-CHECKPOINT-2026-04-20.md`).

— SCP team
