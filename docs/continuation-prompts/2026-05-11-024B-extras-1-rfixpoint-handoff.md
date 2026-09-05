# Continuation prompt — WP-SCP-024 024B-extras-1 R-fixpoint handoff (2026-05-11)

**Source state:** branch `feature/wp-scp-024-024b-extras` HEAD `e299af1`, pushed to origin, no PR yet.
**Last R-cycle:** R21 → criterion (a) (0 CRIT + 0 REAL unique MAJ after carve-filter+dedup).
**Outstanding work:** all operator-attended (step-7 demo + merge + REQCHECK-ENABLE + staging deploy), then strategic decision on next wave.

## Read first

Before doing anything, load context from these files (cheap, fast):
- `docs/reviews/WP-SCP-024/024B-extras/R-FIXPOINT-2026-05-11.md` — full trajectory + handoff
- `docs/plans/WP-SCP-024-estate-cascade.md` §6 — 024C gate conditions
- `STATUS.md` "Tracked-forward items" — 7 TFs against 024B-extras-2 + 4 estate TFs
- Memories listed in `~/.claude/projects/-Users-amplience-Projects-standards-control-plane/memory/MEMORY.md` — especially the 8 `feedback_*` entries; they encode hard-won protocol that must not be skipped

## Process is non-negotiable

This estate uses **four-tier dispatch + 3× Sonnet R1 review** as a hard standard since 2026-04-22 (see `feedback_four_tier_dispatch.md` + `feedback_protocol_over_shortcuts.md`). Do not invent shortcuts:

```
Tier 1 — Opus orchestrator (you)
   ↓ authors fix-round JSON specs + dispatch packages
Tier 2 — Codex executor (`codex exec --sandbox workspace-write`)
   ↓ applies changes from the spec; respects scope_boundary
Tier 3 — 3× parallel Sonnet R1 (correctness / safety_bypass / completeness_governance)
   ↓ structured SonnetReviewResult JSON; never recommend descoping
Tier 4 — Adversarial review to fixpoint (recurse until criterion (a)/(b)/c-resolved)
```

Canonical paths in `reference_four_tier_dispatch.md`:
- Dispatch scripts: `/tmp/codex-wp/scp/dispatch-*.sh`
- Schemas: `/Users/amplience/Projects/acc/schemas/sonnet_review_result.schema.json`
- Build helper: `/tmp/codex-wp/scp/build-extras-prompt.py`
- R1 input JSONs are reusable across rounds (they reference `context_paths`, not round numbers)

**Hard rule:** even when a slice "looks done", do not merge without 3× R1 review on the final state. The 2026-05-11 session was bumpy because the Sonnet monthly cap hit mid-R20; recovery cost was a continuation prompt + a quota probe, not a process skip. If cap hits again, file a continuation prompt; do not bypass.

## Operator-attended chain (do this first)

### Step A — Step-7 operator-interactive demo (~15-20 min, merge-blocking AC)

Runbook: `/tmp/codex-wp/scp/024c-kickoff-prep/STEP7-DEMO-RUNBOOK.md` (updated for post-carve state on 2026-05-11; `--expected-wrapper-sha` references removed; 6-flag count noted).

What it does:
1. Creates throw-away test repo `jrnb2024/scp-024b-extras-restore-test`
2. Configures adopter wrapper + greens at least one policy-check CI run on test repo `main`
3. Runs `scripts/enable-required-check.sh --repo jrnb2024/scp-024b-extras-restore-test --branch main` (forward mode; captures pre-state)
4. Mutates test-repo branch protection (`gh api -X PATCH … --input -`)
5. Runs `scripts/enable-required-check.sh --repo … --branch main --restore <pre-state.json>` (no `--expected-wrapper-sha` — it was carved to extras-2)
6. Verifies key-field jq match (post 2026-05-11 fix-round-21: also exclude `contexts_url` + `*_url` family from comparison)
7. Renames `docs/reviews/WP-SCP-024/024B-extras/restore-roundtrip-evidence-PLACEHOLDER.md` → `restore-roundtrip-evidence.md`, fills with demo log + operator sign-off + timestamp + SLO measurement
8. Updates `STATUS.md` to mark `TF-024B-STEP7-DEMO-001` closed
9. Deletes throw-away test repo

Commit message convention: `WP-SCP-024 024B-extras-1 step-7 demo evidence — TF-024B-STEP7-DEMO-001 closed`.

### Step B — Open PR + self-merge (~5 min, D-040 self-merge)

```bash
gh pr create --base main --head feature/wp-scp-024-024b-extras \
  --title "WP-SCP-024 024B-extras-1: --restore + §12.8 + CI workflow" \
  --body "$(cat <<'EOF'
## Summary
- `scripts/enable-required-check.sh --restore` mode with 6 posture-degradation acknowledgement flags
- ADOPT-001 §12.8 break-glass procedure (3-gate playbook, manual Gate 3)
- `.github/workflows/check-invocation-log-entry.yml` CI enforcement of cascade-status declarations
- D-047 ratifies operational contract; D-048 reserved for sibling 024B-extras-2 depth-defense slice
- Step-7 operator-interactive demo executed (evidence at `docs/reviews/WP-SCP-024/024B-extras/restore-roundtrip-evidence.md`)

## R-cycle history
21 R-cycles across two splits (build-direction + convergence-direction). Final R21 at criterion (a). Full trajectory in `docs/reviews/WP-SCP-024/024B-extras/R-FIXPOINT-2026-05-11.md`.

## Test plan
- [x] `shellcheck scripts/enable-required-check.sh` + tests/check_invocation_log/
- [x] `bash tests/check_invocation_log/test_check_invocation_log_entry.sh`
- [x] Step-7 real-repo round-trip demo
- [ ] Branch CI green
EOF
)"

# Wait for CI, then:
gh pr merge --merge --auto feature/wp-scp-024-024b-extras
```

Alternatively per D-040 pure self-merge: `git checkout main && git merge --no-ff feature/wp-scp-024-024b-extras && git push origin main`.

### Step C — TF-024B-REQCHECK-ENABLE-001 closure (~5 min)

```bash
# Get current required_status_checks contexts first
gh api repos/jrnb2024/standards-control-plane/branches/main/protection \
  --jq '.required_status_checks.contexts'

# Then PATCH adding "check-invocation-log-entry / check-invocation-log-entry"
gh api -X PATCH repos/jrnb2024/standards-control-plane/branches/main/protection \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "<existing context 1>",
      "<existing context 2>",
      "check-invocation-log-entry / check-invocation-log-entry"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null
}
EOF
```

Then append a STATUS.md chain entry under today's date: `TF-024B-REQCHECK-ENABLE-001 closed — required-status-check 'check-invocation-log-entry / check-invocation-log-entry' enabled on SCP main; cascade-status enforcement now blocks merge. Operator: @jrnb2024. Commit SHA: <new-main-HEAD>.`

**Do NOT modify `docs/reviews/WP-SCP-020/branch-protection-log.md`** — that log is reserved for adopter-side invocations per D-035. STATUS.md chain only.

### Step D — Staging deploy (~5-10 min)

Per `docs/deployment.md` §6:

```bash
ssh mapp-staging
cd /home/webapp/apps/standards-control-plane
git pull origin main
# .env.staging should already be configured; if not:
#   cp .env.staging.example .env.staging
#   edit for ENV=production / CT_APP_ID=scp / PUBLIC_BASE_URL=https://scp.brokapps.ai
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d --build
docker compose -f docker-compose.staging.yml --env-file .env.staging logs -f scp
```

Smoke tests after staging is up:
```bash
curl -fsS http://127.0.0.1:3787/health   # SVC-002 shape
curl -fsS http://127.0.0.1:3787/status-app/health | jq '.auth'  # expect oidc / oidc+bearer
curl -I https://scp.brokapps.ai          # operator-side, from your laptop
```

Dev tunnel (local laptop) is separate per `docs/deployment.md` §5 — start it only if you need to demo `scp-dev.brokapps.ai` to a collaborator.

**Note:** the 024B-extras-1 slice ships CLI tools + workflow files, not service-facing code. The staging deploy mostly carries the existing MCP/consult/audit service forward; the slice's own deliverables are exercised via the CI workflow + CLI tools, not via the running service.

### Step E — Rotate the leaked PAT

During the 2026-05-11 session, a `git remote -v` output exposed a GitHub PAT embedded in the remote URL (the `x-access-token:gho_…` form). The full token is in that session's conversation transcript. Rotate:

```bash
# Visit: https://github.com/settings/tokens
# Revoke gho_LtUS19Qm8Jiup* (or whatever the prefix matches)
# Generate a replacement
# Update git config (or use gh auth refresh and let gh manage credentials)
git remote set-url origin https://github.com/jrnb2024/standards-control-plane.git
gh auth refresh
```

## Strategic decision — what's the next wave?

Two unblocked tracks (both gated only on Steps A-C above):

### Track 1 — Adoption (024C PIM canary cascade)

What it is: the actual estate cascade begins. PIM is the canary per plan-doc §5.1 (smallest blast radius). The adopter PR + SCP-side cascade slice + post-bake observation window (≥1 week + ≥1 Renovate cycle) all live here.

Pre-staged: `/tmp/codex-wp/scp/024c-kickoff-prep/`
- `024C-DISPATCH-NOTE-SKELETON.md` — full DISPATCH-NOTE template
- `CT-NOTIFICATION-DRAFT.md` — cross-repo notification to control-tower governance
- `024c-r1-{correctness,safety_bypass,completeness_governance}.json` — R1 review packages

Why first: 024B-extras-1's operational contract is theoretically proven (tests + step-7 demo). 024C is where it gets proven in the wild on a real adopter under invariant 7's <30-min SLO. If extras-1's contract has gaps that the test suite + step-7 demo missed, the smallest-blast-radius adopter is where you want to find them.

Additional precondition: **FUP-ACC-INSTALL-TARGET-REPO-001 must close first.** ACC's `install_acc_hook.sh` currently hardcodes ROOT_DIR via BASH_SOURCE; per-repo install pattern needs work in ACC. SCP-side awaits that closure.

Estimated wall-clock under four-tier dispatch: ~3-4 days slice + ~1-2 weeks post-bake (operator-attended observation).

### Track 2 — Finish-yet-to-get-to (024B-extras-2 depth-defense)

What it is: re-apply the depth-defense surface that was carved out 2026-05-11 to bring the federation primitive to full design fidelity before adopter exposure widens. Branch already exists at `feature/wp-scp-024-024b-extras-2` (`fd62641`, preserves pre-carve state).

Pre-staged: `/tmp/codex-wp/scp/024b-extras-2-prep/DISPATCH-NOTE-SKELETON.md` — full scope + recovery procedure.

Scope re-applies:
- `--expected-wrapper-sha SHA` flag + `validate_expected_wrapper_sha_against_tags()` (annotated-tag dereferencing)
- `--i-understand-no-gate-2-verification` flag + conditional CAUTION/sleep + GATE2_CAUTION_LINE
- `--i-understand-wrapper-inaccessible` flag + wrapper-pin verification
- `--i-understand-restore-replaces-required-check-context` flag + canonical-context guard
- Set-equality verify phase (replaces grep -Fq substring)
- Transform inclusion list (replaces exclusion list)
- ADOPT-001 §12.8 Gate 3 automated procedure
- All 7 TF closures: SET-EQ-001 / RESTORE-PATH-CONTAINMENT-001 / COHORT-REGEX-MULTICHAR-001 / STEP7-FIXTURE-SEQ-001 / STAGED-RESTORE-TEST-001 / RESTORE-FILE-TOCTOU-001 / WORKFLOW-PIN-BASE-BRANCH-001

Decision filed: D-048 (reserved).

Why first: the 7 deferred TFs all live here. Doing extras-2 before any adopter touches the primitive means the cohort onboards against full-fidelity infrastructure. Avoids needing to coordinate cross-slice fixes if extras-2 changes need to land on top of 024C/D/E/F cascade work.

Estimated wall-clock: ~4-5 hours under four-tier dispatch (recovery procedure says cherry-pick the depth-defense diff onto a fresh branch off main — single-commit slice for a clean new R-cycle).

### Operator framing

The plan-doc explicitly says extras-2 does **NOT** gate 024C. Both are technically green-lit after Steps A-C complete. The question is sequencing preference.

**My (Opus-author of this prompt) recommendation:** 024B-extras-2 first, then 024C — but it's close.

Reasoning:
- 024B-extras-2 is bounded surface (~4-5 hr autonomous), and the carve-preserved branch means the work is mostly already done. New R-cycle starts from a known-good state.
- 024C exposes a real adopter (PIM) to the primitive. If extras-2 ships first, the cohort onboards against the design-target version, not the carve-down version. Cleaner story for D-045 ratification.
- The 7 TFs are real follow-ups; the longer they sit, the more chance one of them surfaces during 024C and forces an in-flight cross-slice fix.
- Counter-argument: 024C is THE point of WP-SCP-024 and gives evidence that the cascade story works. Starting with the more visible win has momentum value.

If wall-clock matters more than ordering purity: do 024C and 024B-extras-2 in parallel (separate branches, separate R-cycles). They don't share scope. This is the four-tier dispatcher's whole point — slices are independent under codex-exec.

## Learnings from the 2026-05-09 → 2026-05-11 arc (read before next slice)

The 8 `feedback_*` memories already encode these patterns. Recap of which fired and what got validated this arc:

1. **`feedback_split_not_descope.md`** — fired 2026-05-09 (build-direction split: 024B → core+extras). 7 fix-rounds closed 5-6 MAJ each but introduced 2-3 new defects per round in just-added code; classic surface-too-large signal.

2. **`feedback_asymptotic_trajectory_split.md`** — fired 2026-05-11 (convergence-direction split: 024B-extras → 1+2). 16 R-cycles with MAJ oscillating 4-8, latent depth-finds dominating. Carve diagnosis was correct: survived slice hit criterion (a) within 5 post-carve rounds with **zero** latent depth-finds. This is now the canonical worked example for the memory.

3. **`feedback_mock_masking_external_api.md`** — fired at R9 + R10 (two consecutive CRITs survived 5+ R-cycles because `make_restore_fake_gh` mocked the wrong URL form + workflow lacked `pull-requests: read`). Memory recommends real-API smoke-test job for federation-primitive workflows. Filed as a TF candidate for 024B-extras-2 or a future cross-slice hardening pass.

4. **`feedback_reviewer_stale_code_reads.md`** — fired R18 + R19 (~30% of correctness MAJ were findings citing pre-fix-round code). Verify via grep/sed before fix-round. R20 + R21 showed 0% stale rate, suggesting the cap-hit cache reset may have helped — or the slice being smaller post-carve gave the reviewer less room to confuse states.

5. **`feedback_reviewer_training_cutoff_false_positives.md`** (NEW 2026-05-11) — fired R21 (CORR-002 claimed `actions/checkout@v6.0.2` was post-cutoff and unverifiable). Live `gh api repos/actions/checkout/git/refs/tags/v6.0.2` returned exact SHA match. Distinct failure mode from stale-code-read: verify against live registry, not against repo state.

6. **`feedback_fill_rcycle_wait_windows.md`** — fired repeatedly. While codex-exec ran or Sonnet R1 dispatched, used the time to pre-stage next-round JSON, draft R-FIXPOINT skeleton, update memory, verify tests, archive prior round outputs. Never "standing by". The cap-hit pause itself produced a clean continuation prompt because waits had been pre-used to author handoff infrastructure.

7. **`feedback_protocol_over_shortcuts.md`** — held the line at the cap-hit. The temptation to "we're close, just merge" was real. Filing a continuation prompt + waiting for quota was correct.

8. **Operator instinct on splits** — both splits were operator-decided. The Opus orchestrator surfaced trajectory data + recommendation; the operator made the call. This is the right division — orchestrator collects evidence; operator commits to scope decisions.

### New process improvements worth codifying

- **Verify-grep narrowness**: fix-round-20 verify command `grep -qE "024B-extras-2" docs/reviews/.../DISPATCH-NOTE.md` passed because the scope-split clause already mentioned it — missed that the tooling-slice enumeration was still wrong. Lesson: verify-grep must target the SPECIFIC change site (e.g., `grep -qE "024A.*024B-core.*024B-extras-2.*024G"`), not any-occurrence-of-the-token. Could fit into `feedback_protocol_over_shortcuts.md` if the pattern recurs.

- **Cross-repo D-NNN namespace collisions**: `project_d048_dpbm.md` went stale because CT D-048 (DPBM upstream) and SCP D-048 (reserved for 024B-extras-2) collided in the user's mental model. The `project_d_nnn_prefixing.md` memory does cover this but the SCP-side D-028 ACCEPTED status wasn't reflected in the DPBM memory. Periodic memory-audit-against-DECISIONS.md would catch this. Worth a future automation.

- **Reviewer findings include false-positive class beyond stale-code-reads**: this session surfaced training-cutoff false positives as a new class. Future R-cycles should expect 3 false-positive classes:
  - Stale-code-read (cache artefact)
  - Training-cutoff (world-knowledge artefact)
  - Cross-lens-duplicate-of-deferred-TF (already-carved scope)

  All three classes look like MAJ findings on first glance; all three should be filtered before fix-round dispatch.

## Quick state-check on resume

```bash
cd /Users/amplience/Projects/standards-control-plane
git status -sb                # Should be clean
git log --oneline -3          # e299af1 should be HEAD
git branch -vv | grep "024b-extras"   # 024b-extras tracks origin, 024b-extras-2 local-only
ls docs/reviews/WP-SCP-024/024B-extras/R-FIXPOINT-2026-05-11.md   # present
ls docs/reviews/WP-SCP-024/024B-extras/restore-roundtrip-evidence-PLACEHOLDER.md   # still PLACEHOLDER if step-7 not run
```

If the PLACEHOLDER file is renamed to `restore-roundtrip-evidence.md`, step-7 is done and Steps A is complete; proceed to Step B (merge).

If a PR exists at `gh pr list --head feature/wp-scp-024-024b-extras --state all`, check its merge state.

If the branch is merged into main (`git log main --oneline --grep="024B-extras-1"`), proceed to Step C (REQCHECK) + Step D (staging).

## What success looks like at end of this continuation

1. ✅ `restore-roundtrip-evidence.md` committed with operator sign-off
2. ✅ branch merged into `main` per D-040 self-merge
3. ✅ `check-invocation-log-entry / check-invocation-log-entry` added to main's `required_status_checks`
4. ✅ staging redeployed at `scp.brokapps.ai`; `/health` returns SVC-002 shape; `/status-app/health` reports `auth.mode = oidc` (or `oidc+bearer`)
5. ✅ Strategic decision made: next slice opens (024C or 024B-extras-2 — or both in parallel)
6. ✅ Leaked PAT rotated

Then the conversation can either continue into the chosen next-wave slice or close out cleanly.

---

**Status as of 2026-05-11 ~15:30 BST:** R-fixpoint declared at commit `e299af1`. Branch pushed. All autonomous work complete. Awaiting operator-attended chain.
