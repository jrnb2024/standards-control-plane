# TF-PIM-001 Wave G v2 + Wave H — operator handoff (2026-05-23 PM)

**Status at handoff:** Wave D'.1 + Wave D'.2 MERGED. All 7 L31 SCP-side axes (C/D/E/F/G/H/I) closed. Remaining items are operator-attended cross-repo writes.

## What's been done autonomously this session

| Wave | PR | Status | Sha |
|---|---|---|---|
| Wave D'.1 — Codex Tier 2 dispatch closing L31 axis I | [#145](https://github.com/jrnb2024/standards-control-plane/pull/145) | ✅ MERGED | `6653cf9` |
| Wave D'.2 — docs chore (ADOPT-001 §12.7.16a/b + §12.7.10 v2 amendment + D-050 amendment) | [#146](https://github.com/jrnb2024/standards-control-plane/pull/146) | ✅ MERGED | _post-merge_ |

Methodology summary:
- Codex Tier 2 dispatch fired on Wave D'.1 WP-spec v0.3 (PR #144); 590s elapsed; 28/30 verify_commands pass; 0 scope_violations.
- 3-lens impl R-cycle on Wave D'.1: R1 → 2 HIGHs (convergent SCP-self short-circuit short-circuit removal + diff-size budget) → R-FIXPOINT MET at R2.
- 3-lens impl R-cycle on Wave D'.2: R1 → 2 CRITs (D-050 materialization + §12.7.7-vs-§12.7.10 contradiction) → R-FIXPOINT MET at R2 with operator-ratified pragmatic-fold pattern.
- 4 FUPs filed (FUP-WAVE-D-PRIME-001..006).

## Why this stopped here

Reading A item 4 (cross-repo write) — Wave G v2 + Wave H both touch the PIM repo. Per `feedback_autonomous_directive_scope_interpretation.md`, cross-repo writes are a canonical operator-attended trigger. The user's directive was "continue autonomously... canonically as per the original auth rollout plan" — autonomous through SCP-internal work, stand down at cross-repo boundary.

## Wave G v2 — operator-attended PIM canary re-fire

### Goal
Validate that Path C v2 (with axis G Option α + axis I `inputs.scp-sha` + axes D/E ADOPT-001 documentation) actually works end-to-end via PIM as the canary adopter.

### Pre-requisites (verify before firing)

- [ ] `gh api repos/jrnb2024/standards-control-plane/branches/main/protection --jq '.required_status_checks.contexts'` returns the expected required checks
- [ ] PIM's existing `policy-check-wrapper.yml` exists at `frontend-repo/.github/workflows/policy-check-wrapper.yml` (Wave G v1 history left it pinned to pre-axis-H SHA)
- [ ] PIM's GitHub App `scp-federation-primitive` install on PIM is verified per ADOPT-001 §12.7.16a — Repository access MUST be `jrnb2024/standards-control-plane` (NOT mapp-pim)
- [ ] SCP secrets `SCP_FEDERATION_APP_ID` + `SCP_FEDERATION_APP_PRIVATE_KEY` exist in SCP repo (Wave A — verified 2026-05-21)

### Procedure (~30 min, operator-attended)

1. **Identify post-Wave-D'.2 SCP main HEAD SHA** (replaces `<NEW_SCP_SHA>` in the canary wrapper):
   ```bash
   gh api repos/jrnb2024/standards-control-plane/branches/main --jq '.commit.sha'
   ```
   _Expected: post-Wave-D'.2 merge commit (>= `6653cf9`)._

2. **Open the canary wrapper bump PR in PIM**:
   ```bash
   cd /Users/amplience/Projects/mapp-pim
   git checkout -b chore/scp-wrapper-bump-wave-g-v2
   # Edit frontend-repo/.github/workflows/policy-check-wrapper.yml
   # Replace the canonical-wrapper shape from companion §6:
   #   - `uses: jrnb2024/standards-control-plane/.github/workflows/policy-check.yml@<NEW_SCP_SHA>`
   #   - `scp-sha: <NEW_SCP_SHA>` (axis I closure)
   #   - `secrets: inherit` (axis G Option α)
   #   - `attestations: write + id-token: write` at caller-job level (axis F)
   git add frontend-repo/.github/workflows/policy-check-wrapper.yml
   git commit -m "chore: bump scp-wrapper to Wave-D' SHA + adopt v2 wrapper shape"
   git push -u origin chore/scp-wrapper-bump-wave-g-v2
   gh pr create --title "..." --body "..."
   ```
   _Verbatim wrapper shape at SCP `docs/plans/TF-PIM-001-wave-d-prime-spec-draft.md` §6 lines 216-251._

3. **Watch the PR's `policy-check / scp/policy-check` check**:
   - SUCCESS → Wave G v2 PASSES; proceed to Wave H
   - FAILURE → inspect SCP-E001 annotation (`scp-sha` mismatch?) or `actions/checkout` error (SHA unreachable?) or other policy violation. Diagnose, fix-forward on the same PR or open ASC if architectural.

4. **Merge the canary wrapper bump PR** — if green.

### Failure-mode decision tree (per plan-doc §7.6)

- **`SCP-E001 inputs.scp-sha required for v2 cross-repo workflow_call`** → adopter didn't pass `scp-sha:` input. Fix: add to wrapper.
- **`SCP-E001 ... must be 40-char lowercase hex`** → malformed `scp-sha:` value. Fix: paste valid SHA.
- **`actions/checkout` fails on `.scp-runtime`** → `scp-sha` doesn't exist on SCP. Fix: re-paste current SCP main HEAD.
- **App-token-exchange fails** → operator's App-install Repository access misconfigured per §12.7.16a. Fix: re-configure App install.
- **Other policy violations** → substantive (not auth-architecture); diagnose per existing per-rule annotations.

## Wave H — PIM main required-check restoration (~20 min, operator-attended)

### Goal
Restore the `policy-check / scp/policy-check` required-check on PIM's `main` branch protection (relaxed 2026-05-19 per the `feedback_dev_first_staging_manual.md` precedent + PIM Phase 4 unblock).

### Procedure

1. **Confirm Wave G v2 canary green** on PIM `main` (post-merge).

2. **Apply branch protection** via SCP's adopter-helper script:
   ```bash
   cd /Users/amplience/Projects/standards-control-plane
   scripts/enable-required-check.sh --repo jrnb2024/mapp-pim --branch main
   ```
   _Per D-035 (020G adopter-helper invocation), this is the canonical pattern. The script applies branch protection in two API calls (unified PUT for status-checks/admins/reviews + dedicated POST to `required_signatures`), refuses to run in CI, emits an invocation-log block._

3. **Log the invocation** in `docs/reviews/WP-SCP-020/branch-protection-log.md` per D-035 (paste the script's emitted log block).

4. **Verify required-check is now enforced**:
   ```bash
   gh api repos/jrnb2024/mapp-pim/branches/main/protection --jq '.required_status_checks.contexts'
   # Expect: includes 'policy-check / scp/policy-check'
   ```

5. **TF-PIM-001 final close** — once Wave H verified:
   - Update STATUS.md with TF-PIM-001 CLOSED ratchet
   - Flip TF-PIM-001 entry in BACKLOG.md to CLOSED
   - Optionally: announce on operator's notification venue per `feedback_cross_project_coordination_patterns.md` P3

## Open FUPs (P3 follow-ups; not blocking Wave G v2/H)

- **FUP-WAVE-D-PRIME-001** — WP-spec verify_command[5] malformed grep chain (L26 decorative-not-runnable class). Rewrite to runnable probe in next federation-primitive WP-spec.
- **FUP-WAVE-D-PRIME-002** — WP-spec budget calibration: future federation-primitive WP-specs targeting workflow-selftest expansion should budget `~25 lines/new-fixture-job × N-fixtures`.
- **FUP-WAVE-D-PRIME-003** — companion spec §11 line 453-454 display-width line-break splitting memory-file reference. Single-line cleanup.
- **FUP-WAVE-D-PRIME-004** — companion spec §12 MED-002 stale §12.7.7 reference; R1 fold moved to §12.7.10.
- **FUP-WAVE-D-PRIME-005** — D-050 amendment uses templatic placeholders ("Wave D' amendment PR"); post-merge housekeeping should materialize PR #145 / #146 / Wave G v2 / Wave H references.
- **FUP-WAVE-D-PRIME-006** — D-050 amendment references operator-local memory path; estate readers lack access. Either remove or move to in-repo governance location.

## References

- WP-spec (Wave D'.1): `docs/governance/work-packages/tf-pim-001-wave-d-prime-axis-i.json`
- Companion (verbatim source): `docs/plans/TF-PIM-001-wave-d-prime-spec-draft.md`
- Plan-doc v0.7: `docs/plans/TF-PIM-001-impl-path-c-app-credential.md` §11.5+§11.6
- ASC: `~/.claude/projects/-Users-amplience-Projects/memory/ASC-2026-05-22-001.md`
- Reading A: `~/.claude/projects/-Users-amplience-Projects/memory/feedback_autonomous_directive_scope_interpretation.md`
- L31 estate memo: `~/.claude/projects/-Users-amplience-Projects/memory/feedback_content_semantic_verification_gap.md`
- Pre-authored Wave G v2 wrapper shape: companion §6 lines 216-251
- Pre-existing canary PR on PIM (from Wave G v1; do-not-merge): `jrnb2024/mapp-pim#259`
