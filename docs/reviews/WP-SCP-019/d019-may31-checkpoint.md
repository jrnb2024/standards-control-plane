# D-019 2026-05-31 Checkpoint

Records the checkpoint ratified in the SCP ↔ CT exchange of 2026-04-18
(`control-tower/governance/docs/notifications/SCP-FOLLOWUP-2026-04-18.md`
§3 Q5 and §4). This checkpoint governs whether D-019's `mode.bearer_legacy`
deprecation close date of `2026-06-30` stands or is amended.

**Status update (2026-04-20).** SCP has filed an Option-B signal to
CT committing to fire this checkpoint on 2026-05-31, sliding the
close date to `2026-09-30`. See
`docs/reviews/WP-SCP-019/d019-option-b-signal.md`. The formal D-021
amending decision still records on 2026-05-31 based on observed
evidence (see §SCP-side invocation plan below), but CT, pim,
recommender, and shopify-app teams should plan against `2026-09-30`
as the operative close date from this signal forward.

## Checkpoint language

Ratified verbatim from CT's §3 Q5:

> "If, by 2026-05-31, fewer than 2 of {pim, recommender, shopify-app}
> have opened a `mode.api_key` adoption PR, SCP invokes D-019's
> amending-decision clause and amends the deprecation close date to
> 2026-09-30. Otherwise D-019 stands."

### Threshold interpretation (SCP, pending CT confirmation)

SCP's reading of "opened a `mode.api_key` adoption PR":

- A PR in the target app's repo that:
  1. adds `mode.api_key` to the service's
     `auth_contract.accepted_modes` declaration in its `services.yml`,
     AND
  2. begins validating against CT-issued service-account keys (even
     if the old bearer path is still accepted alongside during
     rollout).
- Draft PR status is sufficient. Merged status is **not** required.
- A PR that does only (1) without (2) does **not** count.
- A PR that does only (2) without (1) does **not** count (no declared
  contract change = no audit-visible commitment).

Awaiting explicit CT confirmation of this interpretation. Captured in
the 2026-04-18 SCP→CT reply as an open clarification ask. If CT
confirms a different threshold, this section is updated before
2026-05-31.

## Rationale

Original D-019 (commit `ea9f7e0`, 2026-04-18) set `2026-06-30` as the
estate close date for `mode.bearer_legacy`, against a then-implicit
assumption that `mode.api_key` would be a drop-in target by that date.

CT's 2026-04-18 audits revealed:

- The CT admin surface backing `mode.api_key` is **live today**
  (CT-016 backend + Next.js admin page;
  `SCP-FOLLOWUP-2026-04-18-admin-ui-audit.md`).
- The operational doc (`CT_AGENT_KEY_OPS.md`) is **not yet published**;
  CT-led authoring, target mid-to-late May 2026.
- Three Go apps (pim, recommender, shopify-app) are the heavy-lift
  migrations (multi-week arcs each).

The calendar risk therefore concentrates on whether those three apps
start their migrations before the original close date. The May 31
checkpoint converts that risk into an observable signal:

- **≥ 2 of 3 Go apps with a PR open by 2026-05-31** → the forcing
  function is working; D-019 holds.
- **< 2 of 3** → evidence the estate needs more runway; SCP amends D-019
  to 2026-09-30 before the 2026-06-30 date arrives.

This preserves the forcing function through most of May without the
estate hitting June with no movement on the heavy-lift apps.

## SCP-side invocation plan

### Standing action — 2026-05-31

On 2026-05-31, SCP checks the status of:

- `pim` — any open PR declaring `mode.api_key` per threshold above?
- `recommender` — any open PR declaring `mode.api_key` per threshold
  above?
- `shopify-app` — any open PR declaring `mode.api_key` per threshold
  above?

Count the number that satisfy the threshold.

- **≥ 2 satisfy:** D-019 stands. Record this in
  `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md` under "Outcome"
  with links to the qualifying PRs. No action on D-019 itself.
- **< 2 satisfy:** SCP invokes the amending clause. Steps:
  1. Open PR against `standards-control-plane` with the draft
     amending decision row below (as D-021).
  2. Update `services.yml` at repo root — change
     `auth_contract.accepted_modes[mode.bearer_legacy].deprecation_close_date`
     from `"2026-06-30"` to `"2026-09-30"`.
  3. Notify CT (ping on the SCP-FOLLOWUP thread or equivalent).
  4. Record the invocation and the PR link in this file under
     "Outcome".
  5. Revisit the checkpoint in the same way at a new trigger date
     if one is defined in the amending decision.

### Pre-written amending decision draft (fires only if checkpoint triggers)

To be appended to `docs/DECISIONS.md` on invocation, with the
`{outcome}` placeholder replaced with the actual PR count observed:

```
| D-021 | 2026-05-31 | Amend D-019's `mode.bearer_legacy`
deprecation close date from 2026-06-30 to 2026-09-30 per the
2026-05-31 checkpoint in
`docs/reviews/WP-SCP-019/d019-may31-checkpoint.md` — {outcome} of 3
required Go apps (pim, recommender, shopify-app) met the adoption-PR
threshold, below the ≥ 2 required | ACCEPTED | Original D-019 date
assumed `CT_AGENT_KEY_OPS.md` would publish earlier than mid-to-late
May and that all three Go-app migrations would begin in parallel; the
checkpoint evidence shows the estate needs a further 3-month runway
to complete the heavy-lift migrations without hitting the original
date cold |
```

SCP also updates its own `services.yml` `deprecation_close_date` to
match. No other rule, schema, or evaluator change required — the
close-date check is date-comparison-only and picks up the new date
automatically.

## Outcome (to be filled on 2026-05-31)

**Date:** _(to be filled)_

**Go-app PR status on checkpoint date:**

- `pim`: _(PR link / none)_
- `recommender`: _(PR link / none)_
- `shopify-app`: _(PR link / none)_

**Count satisfying threshold:** _(to be filled)_ of 3

**D-019 action:** _(stands / amended to 2026-09-30)_

**Amending decision reference (if applicable):** _(D-02X reference)_
