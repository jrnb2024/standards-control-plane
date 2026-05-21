# TF-PIM-001 — 3-agent review synthesis (A/C/D shortlist)

**Reviewed:** 2026-05-20 PM after PR #128 merge at `f137403`
**Lenses dispatched:** sec / arch-skeptic / pragmatist (per `feedback_orchestrator_auth_surface_plan_review_default.md`)
**Mandate:** DO-NOT-EDIT (per `feedback_subagent_review_only_scope_must_be_enforced`); read-only Plan agents in isolated worktrees; Sonnet model
**Lens evidence files:**
- `sec-lens-r1.md`
- `arch-skeptic-lens-r1.md`
- `pragmatist-lens-r1.md`

---

## Convergence outcome — NON-CONVERGENT (2-1 split)

| Lens | Recommended | Strength |
|---|---|---|
| sec | **C** | Strong |
| arch-skeptic | **C** | Strong |
| pragmatist | **A** | Strong |

The review did not converge on a single path. Two lenses (sec + arch-skeptic) recommend Path C with strong conviction; one lens (pragmatist) recommends Path A with strong conviction. Each lens explicitly identifies the *other* path's recommendation as second-best from its own domain, but none of the three lenses voluntarily concedes its first choice.

This is exactly the **operator-attended convergence trigger** the orchestrator-attended review pattern is designed to surface. Per `feedback_orchestrator_auth_surface_plan_review_default.md`, the convergence step is operator-strategic when lenses cleanly divide along the trade-off axis they each own.

## Trade-off structure (the split, made explicit)

The split is not a misalignment of evidence — all three lenses cite the same plan-doc, the same code surface, the same DECISIONS.md rows. They diverge on **which axis of the trade-off is load-bearing for the current programme state**:

- **sec + arch-skeptic prioritise:** preservation of federation-primitive invariants (especially invariant 2 — adopter named secrets never seen by SCP code) + recoverability of failure modes. Path C preserves invariants; A's strategic-info exposure is permanent; D introduces a correlated bundle-pipeline failure surface that's structurally worse than C's bounded App-key custody risk.
- **pragmatist prioritises:** PIM's current degraded required-check state (relaxed since 2026-05-19) + v1.3.0 release-window closure + zero per-adopter integration cost. Path A is the only shortlist member that closes TF-PIM-001 within a 1-2 session window (Paths C/D measure in weeks).

Neither side dismisses the other's concern:

- The pragmatist lens explicitly acknowledges Path A's irreversibility as "load-bearing but not a pragmatist-domain concern at this stage" — explicitly deferring the security/architecture weighting to the other two lenses.
- The sec and arch-skeptic lenses do not contest the cohort-onboarding cost analysis; they weight the threat-model exposure higher.

## Convergence options for operator

Three convergence patterns are viable; the operator's call selects which:

1. **Ratify Path C (sec + arch-skeptic concordance).** Accept the 1-2 week implementation cost + per-adopter App-install ceremony in exchange for invariant preservation + recoverability. PIM's degraded required-check state persists 1-2 weeks longer than under Path A. v1.3.0 may ship before TF-PIM-001 closes (per D-049 §Sequencing, v1.3.0 is self-dogfood-only at warn; TF-PIM-001 is the artefact-gate on adopter-side consumption, not on v1.3.0 itself).

2. **Ratify Path A (pragmatist alone).** Accept the effective-irreversibility of repo-public visibility in exchange for zero per-adopter cost + 1-2 session closure. PIM's degraded required-check state closes immediately on flip. The sec/arch-skeptic concerns (strategic-info exposure permanent; supply-chain attack-surface visibility increased) are accepted as a one-time, principled trade-off. Compensating control: future internal-only artefacts route via a separate `standards-control-plane-private` repo per the plan-doc §5 Path A note.

3. **Trigger §10 STEP 1 escalation — re-open with E + F.** Treat the non-convergent A vs C split as a signal that the A/C/D shortlist itself is insufficient. Re-dispatch with E (public mirror) + F (hybrid) added — both invariant-preserving (sec/arch-skeptic acceptable) and potentially lower per-adopter cost than C (closer to pragmatist's preference). Note: arch-skeptic lens already evaluated E/F and concluded neither is Pareto-better than C; this STEP 1 escalation is operator-driven rather than lens-driven.

## What each lens would say to the operator (one-liners)

- **sec lens to operator:** "Path A's strategic exposure is irreversible; Path C's risks are all recoverable. Choose recoverable."
- **arch-skeptic lens to operator:** "Path A trades one runtime failure for permanent strategic exposure. The substitution is worse. Choose C."
- **pragmatist lens to operator:** "PIM is degraded today. v1.3.0 ships next session. Choose the path that closes TF-PIM-001 this week, not in three. Choose A."

## Lens-resolved decision points (cross-cutting agreement)

Despite the path-recommendation split, the lenses agree on several plan-doc §6 decision points:

- **Decision point 2 (distribution-mechanism).** All three lenses converge on retaining checkout-of-source (rules out Path D from any winning configuration). Paths A and C both retain checkout-of-source; Path D's release-artefact-download pivot is rejected by all three lenses (sec: attestation parity gap; arch-skeptic: correlated bundle-pipeline failure surface; pragmatist: Renovate-preset rewrite cost).
- **Decision point 4 (PAT/App custody).** Lenses align: if Path C is chosen, App credentials (not PATs); rotation under D-031 quarterly review extension; @jrnb2024 single-operator custody acknowledged with TF-PIM-001-SEC-001 + TF-PIM-001-ARCH-001 rotation SOP tracking.

These agreements hold regardless of which path is ultimately ratified.

## What does NOT need re-dispatch under any of the 3 convergence options

- Path B's exclusion (inverts §12.7.10) holds across all three options. Re-opening Path B requires explicit operator authorisation per plan-doc §10 STEP 2 (ASC-class).
- The plan-doc §5 6-path enumeration is sound — no missed alternative surfaced during review.
- The plan-doc §10 escalation path is sound — the staged guard (A/C/D → A/C/D/E/F → +B) reflects exactly the invariant-preserving frontier.

## Operator-attended sign-off shape (per `feedback_orchestrator_auth_surface_plan_review_default.md`)

The dispatch sign-off needs:

1. Operator-selected path: **A** or **C** (Path D rejected by all three lenses; E/F escalation if both A and C are deemed unacceptable).
2. Acknowledgement of the path's load-bearing trade-off (per the chosen lens's risk-surface enumeration).
3. Plan-doc closure amend: mark winning path; close losers as REJECTED-WITH-RATIONALE; cite this synthesis + the 3 lens evidence files.
4. Authorisation to author the D-NNN ADR (mandatory for both A and C per plan-doc §7 acceptance criterion 4).
5. Implementation slice opens after ADR ratifies.

## Tracked-forward items (cross-lens; not blocking sign-off)

- All TF-PIM-001-SEC-001..005 (App-credential surface; sec lens) apply only if Path C ratifies.
- All TF-PIM-001-ARCH-001..005 (App rotation + selftest + ADOPT-001 §12.7 update + multi-org coordination + D-NNN ADR; arch-skeptic lens) apply only if Path C ratifies.
- All TF-PIM-001-PRAG-001..004 (ADR + PIM restoration + scaffolder unblock + issue-tracker triage; pragmatist lens) apply only if Path A ratifies.

The post-ratification impl WP plan-doc inherits the chosen lens's TF set. The unchosen lens's TF items close as NOT-APPLICABLE-UNDER-RATIFIED-PATH with rationale.
