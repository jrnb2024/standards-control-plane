# WP-SCP-022 — Round 1 review consolidation

**Date:** 2026-04-28
**Plan version reviewed:** v0.1
**Reviewers (3× parallel Sonnet R1, 500 ms stagger):**
- Lens: correctness — `r1-correctness/dispatcher-result.json`
- Lens: safety_bypass — `r1-safety/dispatcher-result.json`
- Lens: completeness_governance — `r1-completeness/dispatcher-result.json`
**Verdicts:** all three CHANGES_REQUESTED.
**Outcome:** Fixpoint NOT reached. Plan must return as v0.2 before merge.

## Aggregate counts

| Severity | Correctness | Safety | Completeness | Total (with overlap) |
|----------|-------------|--------|--------------|----------------------|
| CRIT     | 3           | 4      | 3            | 10 (≈7 unique)       |
| MAJ      | 4           | 6      | 6            | 16                   |
| MIN      | 1           | 3      | 5            | 9                    |
| nit      | 1           | 1      | 0            | 2                    |

## CRIT (must close before v0.2 merges)

### Slice-ordering errors (3 reviewers agreed)

1. **020K (CODEOWNERS) absent from Track 1.** WP-SCP-020 §3 makes 020K a
   precondition for 020D2; v0.1 omits it entirely. (C-CRIT-01 / C-022-01)
2. **020D2 placed at Track 1 position 8 immediately after 020D1**,
   inverting WP-SCP-020's canonical sequence (020D1 → 020H part 1 →
   020E.a → 020H part 2 → 020D2). (C-CRIT-02 / C-022-03)
3. **020E.a wrongly described as "FLA pin + branch protection"**.
   WP-SCP-020 §4 defines 020E.a as the *SCP-self pre-protection canary*
   (committed fixture branch demonstrating deny). FLA pin is 020I (deferred
   to WP-SCP-020.1, gated on §7 stability prereqs). (C-CRIT-03 / C-022-03)
4. **020E.b (post-protection canary) and 020E.c (waiver-suppression
   canary) silently dropped.** WP-SCP-020 §9 AC#3 requires all three.
   (C-MAJ-01 / C-022-02)

### Safety-protocol holes (safety lens only)

5. **Scope-boundary enforcement is post-hoc.** `codex_dispatch.py` flags
   out-of-scope edits but does not revert; symlinks inside scope_boundary
   pointing to targets outside it evade the `fnmatch` check entirely.
   (CRIT-BYPASS-001)
6. **Review packages staged at `/tmp` are world-writable.** The 500 ms
   stagger window allows a concurrent process to swap a doctored APPROVED
   verdict in. (CRIT-BYPASS-002)
7. **D-026 "no merge without 3× APPROVED" has no hard-stop.** Opus
   discretion is the sole guard; no dispatcher gate, no CI check, no
   branch-protection rule independently enforces the invariant.
   (CRIT-BYPASS-003)
8. **Prompt-injection through reviewer findings.** Fix-round packages
   pass consolidated reviewer findings — free text — directly into the
   resumed Codex prompt. A hallucinating or malicious reviewer can embed
   payloads in `claim` / `mitigation` fields that instruct Codex to drop
   a control. (CRIT-BYPASS-004)

## MAJ (close in v0.2 unless explicitly accepted with mitigation)

### Plan-content / spec-fidelity

- **020H part 1 wrongly includes ADOPT-001 §12 adopter guide.** Guide
  belongs to 020H part 3; release notes belong to part 1. (C-MAJ-02)
- **§4.3 consolidation logic leaves APPROVED_WITH_FINDINGS(MIN/nit-only)
  case undefined.** Orchestrator stalls or defaults to fix round.
  (C-MAJ-03)
- **§4.3 fix-round protocol does not specify where to extract
  `session_id`** for `resume_session_id` from the dispatcher result.
  (C-MAJ-04)
- **No programme-complete AC.** §9 has plan-complete + autonomous-run-
  complete but no closure path back to WP-SCP-020 §9 / WP-SCP-021 §9.
  (M-022-01)
- **U-022-02 already answered by WP-SCP-020 §14 U-sec-2.** Should be
  closed in this plan, not deferred to slice 020J. (M-022-02)
- **USER-GATE-B undefined.** Referenced in §3 only; absent from §2
  invariants and §9 ACs. (M-022-03)
- **Evidence-directory split unspecified.** Parent-plan deliverables
  (canary-evidence.md, branch-protection-log.md, release-signoff.md)
  vs WP-SCP-022 dispatch artefacts not partitioned. (M-022-04)
- **2026-05-31 D-021 + mid-May ADOPT-001 §11.5 callout removal absent
  from §8 risk register.** Both land in the same wall-clock window as
  Track 1 slices touching DECISIONS.md / ADOPT-001. (M-022-05)
- **ARCH-005 not actually a prereq for 020C.** §1 lists it as
  predecessor "for the rule-library work in 020C", but WP-SCP-020 §4
  020C defines exactly three rules (SCP-R-001/002/003) — none reference
  ARCH-005. (M-022-06)

### Safety-protocol hardenings

- **ACC scripts pinned by mtime not git SHA.** A change to ACC HEAD
  between plan-merge and slice dispatch silently alters dispatch security
  posture. (MAJ-BYPASS-005)
- **`pyproject.toml` partition incomplete — `[project.scripts]` not
  owned.** Track 1 may add `scp-policy-check`; Track 2 adds
  `scp-mcp-server`. (MAJ-BYPASS-006)
- **020J partial-apply has no rollback path / detect-before-proceed
  gate.** Tag-protection activated but signed-commits API timeout =
  inconsistent state. (MAJ-BYPASS-007)
- **OAuth expiry leaves stale-state execution window.** Resumed Codex
  session inherits cached file reads from before refresh. (MAJ-BYPASS-008)
- **User-gate enforcement is Opus-discretion-only.** Context-compressed
  Opus session can blow through. (MAJ-BYPASS-009)
- **Evidence files have no size cap or content sanitization.** Long
  transcripts / control characters / null bytes can corrupt audit trail.
  (MAJ-BYPASS-010)

## MIN / nit (capture in v0.2 or open follow-up rows)

- §9 PR count update post-020K insertion (8 → 12+). (C-MIN-01)
- §13 U-022-01 cost cap quantification — propose `$30/slice, $300
  aggregate` default. (C-nit-01 / m-022-03)
- D-021 reservation not noted in §10 / DECISIONS.md — risk Codex assigns
  D-021 to a new decision during run. (m-022-01)
- §2 Invariant #7 gate-name notation. (m-022-02)
- BACKLOG SCP-077-d048-followup external dependencies column (CT PR
  #202 + ACC PR #106). (m-022-04)
- D-023 forward-reference to WP-SCP-022 broken (this WP is the
  implementation programme, not the proposal-queue WP). (m-022-05)
- DPBM no enforcement gate — D-028 forward-looking declaration with no
  injection mechanism for future visual-output slices. (MIN-BYPASS-011)
- Fix-round budget exhaustion leaves working tree in modified state with
  no cleanup procedure. (MIN-BYPASS-012)
- Reviewer-independence bleed channel via Codex code comments quoting
  finding IDs. (MIN-BYPASS-013)
- STATUS.md not in scope_boundary partition table. (nit-BYPASS-014)

## Critical user-decision impact: autonomous-run scope

The CRIT findings (1)–(4) collapse the scope-question I asked the user
on 2026-04-28. The two-question prompt described the autonomous run as:

> "020B → B.1 → B.2 → 020C → 020C.1 → 020J → 020D1 → 020D2 (SCP self-
> dogfooded, tagged rc), pausing before 020H v1.0.0 release and before
> 020E.a first canary. About 13 slices."

This description was **incorrect against WP-SCP-020 §3 canonical
ordering**. WP-SCP-020's ordering shows that:

- 020D2 (enable required check on SCP main) cannot run before 020H part 2
  (v1.0.0 release tag) and 020E.a (pre-protection canary on SCP self).
- 020E.a is *not* the FLA canary; it's the SCP-self pre-protection
  canary, fully internal to SCP.
- 020H part 2 promotion to v1.0.0 records governance sign-off in
  `release-signoff.md` (named signer), which is a real human-input gate.

The user's stated intent — "Run to self-dogfood landing" — therefore
maps to one of two corrected scopes:

**Scope X:** Pause AFTER 020D1 (wrapper merged on SCP self, required
check NOT yet enforced). Autonomous slices: 020B → 020B.1 → 020B.2 →
020C → 020C.1 → 020J → 020K → 020D1 (8 slices in Track 1, ~4 in
Track 2). USER-GATE-A receives a wrapper-merged-not-yet-enforced state.
First gating happens later (post-gate).

**Scope Y:** Pause AFTER 020D2 (full self-enforcement live on SCP main).
Autonomous slices: 020B → 020B.1 → 020B.2 → 020C → 020C.1 → 020J →
020K → 020D1 → 020H part 1 → 020E.a → 020H part 2 → 020D2 (12 slices in
Track 1, ~4 in Track 2). USER-GATE-A still required mid-chain at the
v1.0.0 promotion step (release-signoff.md named signer is NOT
autonomous), so this is really USER-GATE-A0 (release sign-off) +
USER-GATE-A1 (post-D2 review). True self-dogfood end state.

User must clarify before v0.2 finalises.

## v0.2 fix-round plan

The R(F) round is authored by Opus (this agent), not dispatched to Codex
— plan rewrites are orchestration-level work. v0.2 must:

1. Reorder Track 1 to match WP-SCP-020 §3 canonical sequence (closes
   CRIT 1, 2, 3, 4).
2. Add 020E.b + 020E.c to Track 1 with explicit USER-GATE positioning.
3. Specify which scope (X or Y) the autonomous run targets per user
   clarification (post-question).
4. Tighten §4.3 verdict-consolidation logic with explicit
   APPROVED_WITH_FINDINGS(MIN/nit-only) clause + session_id extraction
   path.
5. Move dispatch packages from `/tmp` to in-repo `docs/reviews/WP-SCP-022/
   dispatches/<slice-id>/dispatch-package.json` *committed before
   dispatch* (closes CRIT-BYPASS-002).
6. Pin ACC scripts by git SHA at plan-merge time (closes
   MAJ-BYPASS-005).
7. Specify scope-boundary enforcement model — including symlink
   resolution and revert-on-violation behaviour — and document the
   gap if the dispatcher cannot be modified inside this WP (closes
   CRIT-BYPASS-001).
8. Specify prompt-injection sanitization for fix-round findings —
   strip control characters, collapse whitespace, length-cap each
   field, escape quotes (closes CRIT-BYPASS-004).
9. Specify hard-stop mechanism for 3× APPROVED — minimum:
   `fixpoint.md` includes machine-verifiable signature over the three
   reviewer JSONs; pre-merge check verifies signature before allowing
   merge (closes CRIT-BYPASS-003 partially; full closure needs CI gate
   in 020G, which is post-pause).
10. Add programme-complete AC, USER-GATE-B definition, evidence-directory
    partition, 2026-05-31 D-021 / mid-May ADOPT-001 risk rows, ARCH-005
    correction, U-022-02 closure (closes the M-022 set).
11. Resolve D-021 reservation note in §10 and DECISIONS.md (closes
    m-022-01).
12. Cost cap quantification — `$30/slice, $300 aggregate` default
    (closes C-nit-01 / m-022-03).
13. Other MIN/nits captured (correct §9 PR count, BACKLOG dep column,
    D-023 forward-reference, etc.).

After v0.2 lands, R2 review fires against v0.2: same three lenses; if
all-three APPROVED → fixpoint; if not → R3.

## Decisions captured by this consolidation

- The plan v0.1 was **incorrect** in slice ordering against WP-SCP-020.
  This is not a misunderstanding of the parent plan — it is a misread
  introduced during authoring. v0.2 must restore the canonical sequence.
- Scope of the autonomous run is **user-gated** and cannot be finalised
  until the user picks Scope X or Scope Y.
- The safety lens identified architecture-level concerns (scope-boundary,
  prompt-injection, hard-stop) that go beyond plan text; some
  mitigations require dispatcher-side changes that are out-of-scope for
  WP-SCP-022 itself but must be acknowledged + risk-registered.
