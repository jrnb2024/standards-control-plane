# WP-SCP-023 slice 023E — Threshold A scaffolding + SCP self-dogfood opt-in (dispatch note)

**Date:** 2026-05-03
**Tier:** orchestrator-applied (Tier 1).
**Closes:** TF-023C-001 (SCP self-dogfood opt-in). Scaffolds Threshold A — the actual sign-off remains operator-driven and gated on real adopter coordination outside this PR.
**Cuts:** no version bump. SCP-self wrapper pin bump is a wrapper-side change, not a federation-primitive surface change.

## Honest scoping

The original WP-SCP-023 plan-doc §6 row 5 says Threshold A requires "≥3 estate adopters opted in (FLA + 2 of {PIM, recommender, mapp-doc-agent, control-tower})." That is **external coordination** that cannot complete from inside the SCP repo — adopters PR their entries to `docs/scorecards/opt-in-registry.yaml`, which they have to actually do.

This slice does what CAN be done end-to-end from inside SCP:

1. **SCP self-dogfood opt-in** (TF-023C-001): bump the SCP self-wrapper pin past v1.2.0 + set `scorecard-emit: true`. This gives the aggregator a 1-adopter test corpus before real adopters arrive — the SCP repo becomes the first row in `output/scorecards/index.json`.

2. **USER-GATE-D scaffold + gating doctrine** at `docs/gates/USER-GATE-D.md`: ratifies the criteria + the operator sign-off process. The artefact lands as **NOT-YET-SIGNED** with the criteria checklist; @jrnb2024 signs it when ≥3 real adopters have opted in.

3. **TF-023A-002 cross-repo notification** can finally land: the v1.2.0 release announcement to ACC / CT / mapp-estate-regression is appropriate now that the exposure surface is live + the SCP self-dogfood demonstrates the flow end-to-end.

4. **TF-023D-003 closure** (the `_log_tool_invocation` `key_id="pending_021J"` audit-trail gap): plan-doc named this as a Threshold A gate. Replace with active key_id from `docs/security/mcp-signing-keys.pub`.

What this slice does **NOT** do (because it can't):
- ≥3 real adopters opting in. Each of FLA / PIM / recommender / mapp-doc-agent / control-tower needs their own PR.
- USER-GATE-D operator sign-off (the artefact is scaffolded; signing waits for criteria satisfaction).
- TF-023D-004 drift section (needs ≥2 verified adopters; deferred to first weekly run after Threshold A).

## Scope decision — IN

| Item | Rationale |
|---|---|
| Bump `.github/workflows/policy-check-wrapper.yml` SHA pin past v1.2.0 (target: HEAD of main with 023D landed → `5ff2acd`) + add `with: scorecard-emit: true` | TF-023C-001 closure. The SCP repo opts itself in as the first adopter — gives the aggregator a 1-adopter test corpus + exercises the entire emit + verify + aggregate + render path on real workflow runs. |
| Add SCP-self entry to `docs/scorecards/opt-in-registry.yaml` matching the new pin | Required for the aggregator to pick up SCP-self's emits. |
| `docs/gates/USER-GATE-D.md` (NEW; status: `not-yet-signed`) | Threshold A operator sign-off artefact per WP-SCP-020 USER-GATE-A pattern. Lists the 4 criteria as a checklist; signs off when satisfied. |
| Update `docs/security/mcp-signing-keys.pub` audit — replace `_log_tool_invocation` `key_id="pending_021J"` with the active key_id read at invocation time (TF-023D-003 closure) | Per plan-doc §10 forward question — Threshold A gate. Closure makes consult_scorecard's audit trail attributable. |
| Cross-repo notification to ACC / CT / mapp-estate-regression (TF-023A-002 closure) — append a note to `~/Projects/control-tower/governance/docs/notifications/` per `reference_ct_notifications.md` | The exposure surface is live; v1.2.0 is shipped; SCP-self has dogfooded. Time to announce. |
| `STATUS.md` 023E chain row + scheduled review date for Threshold A operator sign-off | Convention. |
| Memory updates: `project_post_threshold_a_state.md` (023D + 023E landed); `project_wp_scp_023_state.md` (NEW; full chain summary) | Post-merge close-out artefacts. |

## Scope decision — OUT

| Item | Rationale |
|---|---|
| ≥3 real adopters opting in | External coordination — not actionable from inside SCP. |
| USER-GATE-D actually-signed | Awaits criteria satisfaction. Operator-driven. |
| Drift section in markdown (TF-023D-004) | Needs ≥2 verified adopters; tracked-forward. |
| MCP server redeploy on acc.brokapps.ai (TF-023D-005) | Out-of-band ACC deployment cycle. |

## Tier-justification

Orchestrator-applied + 3-lens R1 (per `feedback_four_tier_dispatch.md`). All deliverables are mechanical doc + scaffold work. No code design rework. If R1 surfaces a design CRIT/MAJ, escalate.

## Slice acceptance

- [ ] **(i) Self-dogfood opt-in.** `policy-check-wrapper.yml` SHA pin bumped past 5d4341b (023B merge); `with: scorecard-emit: true` added. Pin is a real merged commit on origin/main.
- [ ] **(ii) opt-in-registry entry.** `docs/scorecards/opt-in-registry.yaml` carries the SCP-self entry with `expected_scp_workflow_ref` matching the wrapper pin.
- [ ] **(iii) USER-GATE-D scaffold.** `docs/gates/USER-GATE-D.md` exists with status `not-yet-signed` + 4-criterion checklist + operator-signature stub.
- [ ] **(iv) TF-023D-003 closure.** `_log_tool_invocation` reads the active key_id from `docs/security/mcp-signing-keys.pub`. Tests confirm.
- [ ] **(v) Cross-repo notification.** Append note to `~/Projects/control-tower/governance/docs/notifications/` announcing v1.2.0 + scorecard exposure surface.
- [ ] **(vi) STATUS.md** 023E chain row + scheduled-follow-ups for Threshold A.
- [ ] **(vii) `policies/VERSIONING.md`** updates if any (likely none — no public-surface change).
- [ ] **(viii) Pytest passes** + pre-push wrapper green.
- [ ] **(ix) Adversarial review reaches fixpoint.**
- [ ] **(x) PR + CI green + operator-merge.**
- [ ] **(xi) Close-out: memory updates + project_wp_scp_023_state.md.**

## Risk surface

1. **SCP self-dogfood pin bump** — wrapper updates `policy-check.yml` invocation. Could fail CI if v1.2.0 surface change breaks something. Mitigation: 023B was MINOR (additive); existing wrapper should continue working with `scorecard-emit: true` opt-in. Test on this PR.
2. **`_log_tool_invocation` key_id read** — could fail at MCP-call time if `docs/security/mcp-signing-keys.pub` doesn't exist or is malformed. Mitigation: try/except wrap with fallback to "pending_021J" on read failure; logs INFO not ERROR.
3. **opt-in-registry self-entry SHA mismatch** — the `expected_scp_workflow_ref` SHA must match the wrapper pin SHA. If they drift, the aggregator records `verification_failure`. Mitigation: explicit comment in the registry + STATUS.md note ("update both together").
4. **Cross-repo notification appropriateness** — sending the v1.2.0 + scorecard announcement now (before any non-SCP adopter) is "preemptive" but accurate. Adopters can read + plan; opt-in is voluntary.

## R1 review focus

- **Correctness**: pin bump SHA points at a real merged commit; opt-in-registry SHA matches; key_id closure compiles + tests; USER-GATE-D criteria align with plan-doc §8.
- **Safety**: key_id read failure falls back gracefully; opt-in-registry self-entry doesn't introduce a self-trust loop (the aggregator verifies SCP-self emits via OIDC just like any adopter); USER-GATE-D scaffold doesn't accidentally bind operator commitment.
- **Completeness**: Threshold A gate criteria explicit + measurable; scheduled review date for operator sign-off; TF closures recorded; ADOPT-001 §12.7.15 still accurate.

## Files

### Modified
- `.github/workflows/policy-check-wrapper.yml` (pin bump + scorecard-emit: true)
- `docs/scorecards/opt-in-registry.yaml` (SCP-self entry)
- `src/standards_control_plane/mcp_server/tools.py` (TF-023D-003 closure: key_id reader)
- `tests/scp_mcp/test_tools/test_consult_scorecard.py` (test_log_attribution)
- `STATUS.md` (023E row + scheduled follow-ups)
- `docs/DECISIONS.md` (Last Updated)

### Added
- `docs/gates/USER-GATE-D.md` (NEW; not-yet-signed scaffold)
- `~/Projects/control-tower/governance/docs/notifications/...` (cross-repo announcement note)
- `docs/reviews/WP-SCP-023/dispatches/023E-threshold/{DISPATCH-NOTE.md, ...}`

## Forward-looking

- **WP-SCP-023 closure** — once Threshold A reached (3 adopters opted in + USER-GATE-D signed), WP-SCP-023 marked closed in STATUS.md.
- **WP-SCP-024 plan-doc** — next-substantive WP per the user's directive.
