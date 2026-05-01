# WP-SCP-022 slice 020H.4 — rule-config disable canary (dispatch note)

**Date:** 2026-05-01
**Tier:** orchestrator-applied (Tier 1 only)
**Closes:** WP-SCP-022 020H.1 R1 SAFE-MIN-005 → TF-020H1-004 (rule-config disable canary missing).

**Slice naming.** "020H.4" is the next post-Threshold-A dot-N slice (mirrors 020H.1, 020H.2, 020H.3, 020H.3.1). Distinct from the already-merged "020H **part** 1/2/3" (pre-Threshold-A v1.0.0-cut sequence). See STATUS.md "Naming note" in the post-Threshold-A backlog section for the established convention.

## Justification for not invoking Codex executor

Per `feedback_four_tier_dispatch.md` in-line escalation guidance.
The slice's surface is **3 small mechanical changes**:

- One canary branch (`canary/rule-config-disabled`) — already created + pushed + verified-via-DO-NOT-MERGE-PR `#81`. Not in this PR's diff (the canary lives on its own branch, mirroring the pattern of `canary/deliberate-violation-pre` / `canary/waived-violation`).
- `scripts/replay-canary.sh` — one-line registry entry + 5-line header comment update.
- `docs/reviews/WP-SCP-020/canary-evidence.md` — new Canary 4 section with baseline observations.
- `STATUS.md` — TF-020H1-004 marked closed; 020H.3.1 marked landed (carrier-slice obligation backfill from 020H.3.1); 020H.4 IN FLIGHT row; "Last updated" bump.

Codex Tier 3 dispatch overhead would exceed the marginal benefit; orchestrator-applied + R1 × 3 is the right posture (symmetric with 020H.3.1 dispatch note).

## Slice acceptance

- [x] **(i) New canary branch.** `canary/rule-config-disabled` created from main + pushed; SHA `841d350f55c330258469f286328a8281b49bc28b`. PR `#81` opened + labelled DO-NOT-MERGE for permanent fixture preservation. Mirrors PR `#59` (canary 1) + the open canary 3 PR.
- [x] **(ii) Canary content.** `services.yml` carries deliberate SCP-R-001 violation (`deprecation_close_date: "2099-12-31"`, outside the allowed set — same shape as canary 1). `.scp/rule-config.yaml` (force-added because `.scp/` is `.gitignore`d at root for normal adopter workflow) carries SCP-R-001 `disable: true` + justification + far-future expires_at, conformant with `schemas/rule-config.schema.json`.
- [x] **(iii) Workflow verification.** Workflow run `25211284467` (job `73922292656`) on the canary branch verified the expected outcome:
  - `policy-check / scp/policy-check`: PASS (deny suppressed by rule-config).
  - `findings count after suppression`: 0.
  - `waivers_applied count`: 0 (distinct from canary/waived-violation which has 1).
  - `disabled_rules count`: 2 (SCP-R-001 from rule-config + SCP-R-003 from no-manifest-applicable observability).
- [x] **(iv) `scripts/replay-canary.sh` registry.** New entry `rule-config-disabled|canary/rule-config-disabled|SUCCESS|0|0` added; header comment block updated to enumerate the four canaries (1+2 share a branch, 3 = waiver, 4 = rule-config).
- [x] **(v) `docs/reviews/WP-SCP-020/canary-evidence.md` baseline.** New Canary 4 section (~120 lines) with: branch SHA, PR link, workflow run/job link, wall-clock, why-this-canary rationale, the deliberate-violation + suppression snippets, verdict table, structured-finding JSON dump, discriminating-signature comparison vs Canary 3 (waivers vs rule-config), what-this-canary-proves narrative, and TF-E.c-001 cross-reference (the `disabled_rules[*].expires_at` empty-string projection bug also affects this canary's rule-config-override entry — same pre-existing bug).
- [x] **(vi) STATUS.md updates.** TF-020H1-004 marked ✅ closed in 020H.4; 020H.3.1 row backfilled with PR #80 + commit `d3e3c73` (carrier-slice obligation from 020H.3.1); 020H.4 IN FLIGHT row added; "Last updated" bumped to 2026-05-01 reflecting the 020H.3.1 + 020H.4 transition.

## Out of scope / forward-looking

- **Tighter registry tuple including `disabled_rules` count.** The current `replay-canary.sh` script tracks verdict + findings + waivers count; extending the tuple to include disabled_rules would catch a "disable still works but observability record dropped" regression class. Documented in the canary-evidence.md baseline as forward-compat. NOT filed as a TF item — the slice's stated scope is "add the canary; existing infrastructure consumes it"; tightening the script is a separate slice if a regression in the future surfaces the need.
- **TF-E.c-001 (canary 3 + canary 4 `disabled_rules[*].expires_at` projection bug).** Pre-existing, documented at canary 3's section + canary 4's section. Resolution: post-Threshold-A audit of the JSON-summary projection step in `policy-check.yml`. Already tracked at canary-evidence.md; no new TF needed.
- **Adopter documentation update for the rule-config canary.** ADOPT-001 §12.7 doesn't currently mention the canary corpus by name; adopters interact with rule-config via §12.7.4 (break-glass / bypass surfaces) + §11.10 (CODEOWNERS coverage of `.scp/rule-config.yaml`). The canary is an SCP-internal monitoring concern. No ADOPT-001 update needed.

## R1 review

3× parallel Sonnet R1 review (correctness / safety_bypass / completeness_governance). Recurse to fixpoint per `feedback_recursive_adversarial_review.md`.

## Files

- `scripts/replay-canary.sh` — registry entry + header comment.
- `docs/reviews/WP-SCP-020/canary-evidence.md` — new Canary 4 section.
- `STATUS.md` — TF-020H1-004 closure + 020H.3.1 backfill + 020H.4 IN FLIGHT + Last-updated bump.
- `docs/reviews/WP-SCP-022/dispatches/020h4-rule-config-canary/DISPATCH-NOTE.md` — this file.

(The canary branch + DO-NOT-MERGE PR are not in this PR's diff — they live on `canary/rule-config-disabled` + PR #81 respectively, mirroring the established pattern.)
