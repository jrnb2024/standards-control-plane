# SCP review response — `CT_AGENT_KEY_OPS.md` DRAFT

**From:** Standards Control Plane team
**To:** Control Tower team
**Date:** 2026-04-20
**Ref:**
- `control-tower/governance/docs/notifications/SCP-PING-AGENT-KEY-OPS-DRAFT-2026-04-19.md`
  (CT's review request)
- `control-tower/governance/docs/CT_AGENT_KEY_OPS.md` on
  `jrnb2024/control-tower/main@2a31601` (doc under review, PR #76)
- `control-tower/governance/docs/notifications/SCP-RESPONSE-2026-04-18.md`
  §3 Q4.b (the commitment SCP is discharging)

---

## Verdict

**Ratify for publish with three amendments.** Two primary asks accept
as written; three require targeted text changes before CT flips DRAFT
→ Published. One SCP-side follow-up fires regardless (ADOPT-001 §11.7
semantic-drift fix — covered in this PR).

No blocker to CT's mid-to-late-May publish target provided the three
amendments land on CT's side.

---

## Response to the five primary asks

### Ask 1 — `mode.service_rs256` framing ("RATIFIED, NOT OPERATIONAL") — **ACCEPT**

§2.1 text: "RATIFIED, NOT OPERATIONAL. The issuer endpoint, JWKS, and
consumer-side validation helpers are scoped in SVC-003 but not built.
Do not plan migration today; track via SCP rule SVC-003."

SCP view: accurate to state today. SVC-003 defines the approved-mode
shape; producer-side declaration shape lives in ADOPT-001 §11.6.
Operationalisation is a Model-A commitment (CT builds issuer +
JWKS) ratified in the 2026-04-18 handshake. CT's "track via SVC-003"
pointer is fine as a governance-surface reference — the operational
timeline is a separate CT commitment rather than something SVC-003
owns, but the phrasing does not mislead.

No amendment required.

### Ask 2 — Decision-heuristic threshold ("low-O(10) req/sec per caller") — **AMEND**

§2.2 current: "Decision heuristic (not a contract). If sustained p50
is low-O(10) req/sec per caller, `mode.api_key` is cheaper to adopt
and safer to revoke. If sustained p50 or burst routinely exceeds
that, `mode.service_rs256` is the target…"

Problem: "low-O(10)" is imprecise. It could read as ~10 req/s (CT's
intent) or as O(10) = "constant-order-of-magnitude" (which in
informal practice ranges 1–100). Consumers making a mode choice on
this heuristic cannot tell which.

The binding operational constraint is CT's per-request round-trip
latency for `mode.api_key`, not a request-rate threshold per se —
the rate only matters insofar as it drives total auth-latency budget
consumed.

**Proposed replacement text for §2.2:**

> **Decision heuristic (not a contract).** `mode.api_key` adds one
> CT round-trip per request (typically 30–80 ms depending on cache
> state at CT). For callers with sustained rates of ≤10 req/s per
> SA id, this overhead is usually negligible in total request
> latency. Above that, evaluate whether per-request auth overhead
> dominates your request budget — if yes, `mode.service_rs256` is
> the target once operational. If unsure, ask CT.

Concrete numeric threshold ("≤10 req/s per SA id") plus latency
framing ("30–80 ms per round-trip") gives consumers a falsifiable
heuristic. Retain the "not a contract" label.

CT can substitute its own measured round-trip latency if the 30–80
ms range is wrong — SCP does not have ground truth on that number.

### Ask 3 — Recommender `mode.bearer_legacy` waiver direction (§11.2) — **AMEND (path citation)**

§11.2 current: "Template reference:
`standards-control-plane/docs/adopt-001.md` §11."

Two inaccuracies in the citation:

1. **Path.** The file is at
   `standards-control-plane/docs/adoption/ADOPT-001-project-onboarding.md`,
   not `docs/adopt-001.md`.
2. **Section.** The `mode.bearer_legacy` declaration + waiver template
   is §11.7 specifically, not §11 generally.

**Proposed replacement:**

> Template reference:
> `standards-control-plane/docs/adoption/ADOPT-001-project-onboarding.md`
> §11.7 (`mode.bearer_legacy` producer track).

Substantive direction of §11.2 is correct: recommender opens an SCP
PR declaring `mode.bearer_legacy` with `sunset_date` gated on SVC-003
operationalisation, waiver entry in `output/findings/waivers.json`.
No other changes needed.

Note: ADOPT-001 §11.7 as of 2026-04-18 says the migration target for
`mode.bearer_legacy` is `mode.api_key` exclusively. CT's guidance
that recommender skip directly to `mode.service_rs256` when
operational creates a semantic drift against that text. SCP closes
the drift in this PR (see "SCP-side follow-up" below).

### Ask 4 — Shopify-app ↔ recommender coupling (§11.3) — **ACCEPT**

§11.3 reclassifies shopify-app as two coupled migrations (inbound
Shopify session HMAC vs outbound S2S to recommender via shared
`SERVICE_AUTH_SECRET`). The outbound path adopts `mode.service_rs256`
when recommender does, not before.

SCP view: accurate to the coupling that exists in shopify-app's
codebase today. This hardens `SCP-FOLLOWUP-2026-04-18-bearer-token-audit.md`
§Migration-priority item 4 ("Couples naturally to recommender
migration") into explicit gating — removes ambiguity about whether
shopify-app can adopt unilaterally. Good framing.

The optional parallel `mode.api_key` adoption for per-tenant
CT-integration surface (admin-side store management) is correctly
scoped as a separate migration surface from the shared-secret
coupling. Per-store SA id, uninstall-hook revoke, no self-service
provisioning — all sound.

No amendment required.

### Ask 5 — Phase 2 `X-CT-Timestamp` activation date (§3.4) — **AMEND (propose date)**

§3.4 current: "Phase 2 (activation date TBD — will be announced via
SCP)."

SCP proposes: **2026-09-01**.

Rationale:

- **Post-D-019 close window.** D-019's `mode.bearer_legacy` close
  date is 2026-06-30. A 2026-09-01 Phase 2 activation falls ~2
  months after the close, avoiding overlapping transitions. Two
  simultaneous contract-tightening events in the same window
  compounds risk for 3rd-party consumer teams.
- **Consumer runway.** Consumers adopting `mode.api_key` between
  mid-May (CT_AGENT_KEY_OPS publish) and end-June have ~2–3 months
  runway to add `X-CT-Timestamp` header emission on every
  SA-authenticated request. Small change per consumer but it has
  to be everywhere.
- **60-day notice commitment.** 2026-09-01 activation means CT
  announces the firm date by 2026-07-02 (60-day notice). That
  announcement is an SCP-owned outbound notification per CT's §3.4
  phrasing; SCP schedules it.
- **"Exercised before mandatory" principle.** By 2026-07-15 (mid
  notice window), ≥2 consumers should have adopted `mode.api_key`
  with `X-CT-Timestamp` emission voluntarily. Contract becomes
  mandatory only after real-traffic validation.

**Contingency.** If by **2026-07-15** fewer than 2 consumers have
adopted `mode.api_key` with `X-CT-Timestamp` emission in production,
SCP slides the Phase 2 date to **2026-11-01** and announces the
revised date by 2026-08-01 (60-day re-notice). Applies only on that
consumer-count shortfall.

**CT's ask** was "if SCP wants CT to propose a date, we will."
SCP instead proposes the date above and will carry the outbound
announcement. CT to update §3.4 with:

> **Phase 2 (activation 2026-09-01 — announced via SCP 2026-07-02,
> 60-day notice):** mandatory on every SA-authenticated endpoint.
> Contingency: if by 2026-07-15 fewer than 2 consumer apps have
> adopted `mode.api_key` with `X-CT-Timestamp` emission in
> production, SCP slides activation to 2026-11-01 and re-notices
> by 2026-08-01.

This proposal is open to CT push-back on the 30–80 ms latency
framing, or if CT has operational reason for earlier/later
activation. If CT ships an earlier consumer base (e.g. FLA adopts
mode.api_key faster than expected and exercises the header
immediately), 2026-09-01 might be pulled in by up to 30 days with
fresh 60-day notice. Open to signal.

---

## Response to secondary asks

### Model A ↔ Model B compatibility

The DRAFT is tightly Model A (CT as centralised issuer + JWKS
authority). That coupling is most visible in §2.2's matrix where
`mode.service_rs256` is paired with `iss=control-tower`, and in the
consumer guidance throughout that assumes a single issuer.

SCP view: this is acceptable given Model A was ratified 2026-04-18
and SVC-005 (federated issuer registry) remains backlog-only as
Model B contingency. If Model B ever fires, the §2.2 matrix row for
`mode.service_rs256` needs `iss` widened to a set — but that's a
forward-compatibility worry SCP owns, not a blocker on CT's publish
today.

No amendment required on Model A grounds.

### ADOPT-001 §11 / SVC-003 semantic drift

One substantive drift identified:

**ADOPT-001 §11.7 (as of 2026-04-18) states:** "migration target is
`mode.api_key` (Control Tower-issued agent keys), not
`mode.user_oidc`" — implying `mode.api_key` is the **exclusive**
migration target for `mode.bearer_legacy`.

**CT_AGENT_KEY_OPS.md §11.2 (DRAFT) states:** recommender does NOT
adopt `mode.api_key` — it waivers `mode.bearer_legacy` then migrates
directly to `mode.service_rs256` when operational.

These are in tension. CT's guidance is operationally sound
(recommender's 10+ Go services share an HS256 secret; round-trip
auth would regress throughput). SCP's ADOPT-001 §11.7 text was
drafted 2026-04-18 before this coupling was analysed.

**SCP closes the drift in this PR** by amending ADOPT-001 §11.7 to
include `mode.service_rs256` as a valid migration target from
`mode.bearer_legacy` when throughput or architectural constraints
make `mode.api_key` unsuitable. No further CT action required.

No other drift flagged after a full read.

---

## SCP-side follow-up commitments

Filed regardless of CT's amendment choices above:

1. **ADOPT-001 §11.7 update** (this PR): add `mode.service_rs256` as
   a valid migration target alongside `mode.api_key`. Scope-selection
   guidance uses the same decision heuristic §2.2 of the playbook
   carries (throughput / latency budget). See the diff in this PR.
2. **Phase 2 X-CT-Timestamp announcement**: SCP files an outbound
   notification to CT by **2026-07-02** (60-day notice before
   2026-09-01) confirming the Phase 2 date. Scheduled action.
3. **2026-07-15 consumer-count check**: SCP counts consumer apps
   that have adopted `mode.api_key` with `X-CT-Timestamp` emission
   in production. If <2, SCP slides Phase 2 to 2026-11-01 and
   re-notices by 2026-08-01.
4. **ADOPT-001 §11.5 Status callout removal**: when CT flips
   `CT_AGENT_KEY_OPS.md` DRAFT → Published, SCP removes the
   "ratified-but-ops-doc-pending" callout from §11.5 in a follow-up
   PR. Target: same week as CT publish.

---

## Impact on outstanding threads

- **§2.1 trigger-2 ack** (closed 2026-04-20, see
  `docs/reviews/WP-SCP-019/trigger-2-evidence.md`): unaffected by
  this review.
- **§2.3 D-019 2026-05-31 checkpoint**: SCP's path here is Option B
  from CT's briefing (invoke amending clause). Separate notification
  to follow — not bundled with this response. Rationale: the
  CT_AGENT_KEY_OPS.md publish timeline (mid-to-late May) means the 3
  Go apps (pim, recommender-as-waiver, shopify-app) have at most 3
  weeks from ops-doc publish to 2026-05-31 to open a `mode.api_key`
  adoption PR. That's insufficient. D-019 amending-decision clause
  should fire, setting the `mode.bearer_legacy` close date to
  2026-09-30. SCP will file the signal separately within the
  2026-05-15 CT deadline.

---

## References

- **Doc under review:**
  `control-tower/governance/docs/CT_AGENT_KEY_OPS.md` @
  `jrnb2024/control-tower/main@2a31601` (CT PR #76)
- **CT review request:**
  `control-tower/governance/docs/notifications/SCP-PING-AGENT-KEY-OPS-DRAFT-2026-04-19.md`
- **SCP ADOPT-001 §11.7 (source of drift):**
  `docs/adoption/ADOPT-001-project-onboarding.md` §11.7 — amended
  in this PR
- **SVC-003 approved-modes enum:** ADOPT-001 §11.1
- **Prior handshake:**
  `control-tower/governance/docs/notifications/SCP-RESPONSE-2026-04-18.md`
  §3 Q4.b
- **Trigger-2 closure:**
  `docs/reviews/WP-SCP-019/trigger-2-evidence.md`
- **D-019 checkpoint plan:**
  `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`

---

CT may mirror this file into
`control-tower/governance/docs/notifications/` under CT's naming
convention (briefing suggested
`SCP-RESPONSE-AGENT-KEY-OPS-REVIEW-2026-04-20.md`).

— SCP team
