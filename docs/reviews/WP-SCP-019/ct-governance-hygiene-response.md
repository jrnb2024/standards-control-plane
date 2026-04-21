# SCP → CT: governance-hygiene response + closeout ack

**From:** Standards Control Plane team
**To:** Control Tower team
**Date:** 2026-04-21
**Ref:**
- `control-tower/governance/docs/notifications/SCP-BRIEFING-GOVERNANCE-HYGIENE-2026-04-20.md`
  (CT's four hygiene asks; silence-accepted deadline 2026-05-15)
- `control-tower/governance/docs/notifications/SCP-CONFIRM-D-019-THRESHOLD-2026-04-20.md`
  (CT's threshold-interpretation confirmation + three non-blocking
  corner cases §2.1–§2.3)
- `control-tower/governance/docs/notifications/CT-OPEN-THREADS-2026-04-20.md`
  (CT's live thread tracker)

---

## 1. Closeout ack — CT's 2026-04-20 responses all received

All three of SCP's 2026-04-20 filings are now addressed from CT's
side, with the following SCP-side record:

| SCP filing (SCP PR) | CT response | SCP ack |
|---|---|---|
| Trigger-2 evidence ack (PR #27, `f178e23`) | Mirrored into CT's tree as `SCP-ACK-TRIGGER-2-2026-04-20.md` (CT PR #88). | Noted. No further SCP action. Trigger-2 thread closed both sides. |
| CT_AGENT_KEY_OPS review response (PR #28, `ce03b26`) | All three SCP amendments applied CT-side in CT PR #89 (§2.2 concrete rate/latency substitution; §11.2 path citation; §3.4 Phase 2 date + 60-day notice + 2026-07-15 contingency). Mirrored as `SCP-RESPONSE-AGENT-KEY-OPS-REVIEW-2026-04-20.md`. | Noted. SCP awaits CT's DRAFT → Published flip (CT-side T1, target mid-to-late May 2026, blocked on CT T10 test gaps). SCP's callout-removal PR fires the same week as the flip. |
| D-019 Option-B signal (PR #29, `e801868`) | Mirrored as `SCP-SIGNAL-D-019-CHECKPOINT-2026-04-20.md`; threshold interpretation confirmed verbatim via `SCP-CONFIRM-D-019-THRESHOLD-2026-04-20.md`; amending banners propagated across CT materials in CT PR #91. | Noted with thanks for the fast turnaround. Threshold corner-case response below at §4. |

SCP's own `STATUS.md` and ADOPT-001 §11 updated 2026-04-21 to reflect
CT's completed work and the operative 2026-09-30 close date.

## 2. Prefixing convention (ask #1) — **ACCEPTED**

SCP accepts CT's proposed prefixing convention (filed CT-side in
`docs/decisions/README.md` on CT PR #92):

- Cross-repo citations in SCP materials prefix CT's decision IDs as
  `CT D-NNN`.
- SCP's own decision IDs are cited as `D-NNN` in SCP materials, or
  as `SCP D-NNN` when crossing the repo boundary or where clarity
  demands.
- Neither register renumbers existing rows.

SCP applies the discipline from this response forward. Historical
SCP materials (already-filed reviews / notifications from 2026-04-18
→ 2026-04-20) will **not** be retroactively prefixed — the existing
context makes the D-NNN referents unambiguous, and a sweep would
churn the audit trail for little gain. If CT disagrees, flag in a
response and SCP will scope a one-pass retroactive edit.

Any future SCP decision row with a numeric collision against CT's
register will still be filed with SCP's next sequential D-NNN — the
prefixing convention handles the disambiguation, so renumbering is
unnecessary.

## 3. SCP-071 self-waiver registration (ask #2) — **COMMITMENT**

Current state: `scp-bearer-legacy-migration` is referenced in
`services.yml` and the ADOPT-001 §11.7 example shape, but the actual
`output/findings/waivers.json` record is not yet registered. The
governance-owner confirmation for `approved_by` is still open as an
SCP-071 follow-up.

**SCP's commitment:** register the waiver on or before 2026-05-31 as
part of the D-021 filing work. `expires_at` uses the Option-B-signal
date `2026-09-30T23:59:59Z` directly (rather than registering at
`2026-06-30` and amending a day later). This collapses the two
registration passes into one and aligns the waiver record with the
D-021 amending decision it downstream-of.

Concretely, the 2026-05-31 SCP workday delivers:

1. D-021 filed in `docs/DECISIONS.md` with observed `mode.api_key`
   adoption-PR count substituted into the pre-written draft.
2. `services.yml` `deprecation_close_date` field updated from
   `"2026-06-30"` to `"2026-09-30"` (per Option-B signal §What this
   signal commits).
3. `output/findings/waivers.json` `scp-bearer-legacy-migration`
   registered with `approved_by`, `created_at`, and
   `expires_at: "2026-09-30T23:59:59Z"`.

CT's 2026-05-15 ping-date (T5) is earlier than this commitment. SCP
acknowledges CT may still ping at 2026-05-15 per T5's own schedule;
the ping won't find the waiver registered yet (by design — we want
the single atomic 2026-05-31 update). If CT prefers earlier
registration at 2026-06-30 with a scheduled amendment on 2026-05-31,
flag in response; SCP will split the passes.

## 4. Threshold corner cases §2.1–§2.3 (ask #3) — **ALL ACCEPTED**

SCP accepts CT's stated reading of all three corner cases as filed in
`SCP-CONFIRM-D-019-THRESHOLD-2026-04-20.md`. No amendments to the
threshold language. Reasoning per case:

### §2.1 — Multi-PR on same branch (declaration + validation split)

**CT's reading:** if both PRs are open by 2026-05-31 and the
combined tree satisfies both criteria (declaration in `services.yml`
+ begins-validating code), the pair counts as one.

**SCP accepts.** The intent of the threshold is evidence of
substantive adoption work, not a syntactic-PR-count rule. A
consumer splitting declaration and validation across two PRs on the
same branch for review-size reasons is not gaming the checkpoint —
the combined tree makes the commitment audit-visible. SCP's singular
"a PR" wording is a drafting artefact, not a substantive constraint.

### §2.2 — Revert / rescind between 2026-04-20 and 2026-05-31

**CT's reading:** a PR that is opened in late April and then reverted
or closed unmerged before 2026-05-31 does NOT count. The PR must be
open and live on 2026-05-31.

**SCP accepts.** This matches the spirit of the checkpoint: the
checkpoint asks whether the consumer is committed to migration as of
2026-05-31, not whether the consumer was ever committed at some
point in April. A late-April open followed by a late-May close is
evidence of pullback, which is exactly the signal Option B responds
to.

### §2.3 — PR against non-default branch

**CT's reading:** if a consumer opens the qualifying PR against a
feature branch (`feat/svc-003-adoption` or similar) rather than
`main`, and that branch isn't merged to the consumer's `main` by
2026-05-31, the PR still counts — declaration of intent is
audit-visible on the branch, and the "begins validating" code is on
the branch.

**SCP accepts.** The checkpoint asks whether the team has committed
to the migration arc, not whether the arc has landed in production.
A team doing disciplined branch-based development should not be
penalised for not having merged yet. The threshold is about
commitment evidence, not release status.

### Summary

All three corner cases are accepted as CT stated. SCP records the
acceptance here as the authoritative SCP-side reading for the
2026-05-31 outcome recording (D-021). CT's default silence-accepted
fallback was not needed — explicit acceptance is cleaner for the
audit trail.

## 5. Bearer-token-audit path fix (ask #4) — **NOTED**

CT PR #91's correction of the stale `standards-control-plane/docs/adopt-001.md §11`
citation to the correct
`standards-control-plane/docs/adoption/ADOPT-001-project-onboarding.md §11.7`
is noted. No SCP action required. The same path-drift fix was
applied SCP-side in the CT_AGENT_KEY_OPS §11.2 review amendment (PR
#28) — both sides now consistent.

## 6. SCP-side calendar reiterated (no change from CT's view)

For cross-reference against CT's T3/T4/T5 in
`CT-OPEN-THREADS-2026-04-20.md`:

| Date | SCP action | CT view |
|---|---|---|
| 2026-05-15 | CT ping-date for T5 (SCP-071 waiver). SCP expects no action at 2026-05-15 per §3 above — waiver registers at 2026-05-31. | Passive monitor (T5). |
| 2026-05-31 | D-021 filed; SCP `services.yml` `deprecation_close_date` updated to `2026-09-30`; SCP self-waiver registered with `expires_at: "2026-09-30T23:59:59Z"`. | Passive monitor (T4). No CT action unless SCP retracts signal. |
| mid-to-late May (CT-triggered) | SCP removes ADOPT-001 §11.5 Status callout in a follow-up PR, same week as CT flips DRAFT → Published. | Unblocks on CT T1 completion. |
| 2026-07-02 | SCP files Phase 2 `X-CT-Timestamp` activation notice (60-day advance of proposed 2026-09-01 activation). | Passive. |
| 2026-07-15 | SCP consumer-count contingency check. If <2 consumers have adopted `mode.api_key` with `X-CT-Timestamp` emission, slide activation to 2026-11-01 and re-notice by 2026-08-01. | CT surfaces the consumer-count evidence to SCP; SCP owns the slide decision (T3). |
| 2026-09-30 | Operative `mode.bearer_legacy` close date per D-021; SVC-003 fires `bearer-legacy-close-date-passed` on services still declaring the mode without renewed waiver. | — |

## 7. Open items from SCP's side (none new)

SCP has no new asks for CT. Threads SCP is watching passively from
CT's side:

- **T1** — `CT_AGENT_KEY_OPS.md` DRAFT → Published flip. SCP's
  callout-removal PR is coupled to this.
- **T10** — CT-side test-coverage gaps blocking T1.
- **T2** — CT's direct outbound comms to pim / recommender /
  shopify-app teams for the 2026-09-30 operative date. No hard
  deadline; informational for consumer planning.

All remaining active threads (T7 ACC port, T8 RI ct_events, T9
market-feed successor, T11 INFRA-034 v2, T12 FLA test gaps) sit
outside SCP's scope of direct action and are tracked by CT-side or
FLA-side owners.

## 8. References

- **CT governance-hygiene brief (source of asks):**
  `control-tower/governance/docs/notifications/SCP-BRIEFING-GOVERNANCE-HYGIENE-2026-04-20.md`
- **CT threshold confirmation (source of §2.1–§2.3):**
  `control-tower/governance/docs/notifications/SCP-CONFIRM-D-019-THRESHOLD-2026-04-20.md`
- **CT open-threads tracker:**
  `control-tower/governance/docs/notifications/CT-OPEN-THREADS-2026-04-20.md`
- **SCP Option-B signal (source of operative date):**
  `docs/reviews/WP-SCP-019/d019-option-b-signal.md`
- **D-021 pre-written draft:**
  `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md` §Pre-written
  amending decision draft
- **SCP self-waiver reference:** `services.yml` root + ADOPT-001
  §11.7 example shape + pending `output/findings/waivers.json`
  registration.

---

CT may mirror this file into
`control-tower/governance/docs/notifications/` under CT's naming
convention (suggested `SCP-RESPONSE-GOVERNANCE-HYGIENE-2026-04-21.md`).

— SCP team
