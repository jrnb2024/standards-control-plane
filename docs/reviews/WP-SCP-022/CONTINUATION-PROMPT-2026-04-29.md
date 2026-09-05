# WP-SCP-022 — Continuation prompt for fresh session (2026-04-29)

You are picking up the WP-SCP-022 autonomous chain. **Read this top-to-bottom before doing anything.**

## Mental model in three lines

- WP-SCP-022 is the meta-plan that orders WP-SCP-020 (federation primitive) and WP-SCP-021 (MCP server) implementation slices into two parallel autonomous-dispatch tracks. Plan is on `main` as PR #36 (v0.5, FIXPOINT at R5).
- **6 of 16 implementation slices merged**; 2 in flight on feature branches paused for fresh-session resume; 8 implementation slices remaining after the in-flight pair lands.
- Your job: drive every remaining slice through the four-tier dispatch + 3× adversarial review protocol per WP-SCP-022 §4 to fixpoint, merge each as its own PR, and prep three USER-GATE artefacts for the operator to sign at named milestones. Reach **020D2 (SCP gates itself)** + **021E (MCP scaffold complete)**.

## First five actions in order

1. **Read** these in this order — none take more than a few minutes:
   - `docs/reviews/WP-SCP-022/RESUME-NOTE-2026-04-29.md` — snapshot of pause-state, including codex-timeout diagnosis.
   - `docs/plans/WP-SCP-022-implementation-programme-plan.md` §4 (dispatch contract) + §3 (slice ordering).
   - `docs/plans/WP-SCP-020-policy-federation-primitive.md` §4 — table of all Track 1 slice deliverables. You'll come back to this row-by-row.
   - `docs/plans/WP-SCP-021-scp-as-mcp-server.md` §4 — same for Track 2.
   - Auto-memory `feedback_protocol_over_shortcuts.md` — non-negotiable invariants.
   - Auto-memory `project_wp_scp_022_plan.md` — current state snapshot.

2. **OAuth smoke test:**
   ```bash
   codex exec "reply with just hello and nothing else"
   claude -p "reply with just hello and nothing else"
   ```
   Both must return `hello`. If either fails: `codex login` / re-auth `claude`. Do not dispatch anything until both green.

3. **Confirm position:**
   ```bash
   cd /Users/amplience/Projects/standards-control-plane
   git checkout main && git pull --ff-only origin main
   git log --oneline -10
   # First line should be 285792a (pause-state commit). Below it: PR #45 (021D), #41 (020B.2), #40 (021C), #39 (020B.1), #38 (020B), #37 (021B), #36 (WP-SCP-022 plan).
   ```

4. **Re-create the in-flight worktrees** (origin retains both branches):
   ```bash
   git worktree add ~/Projects/scp-track1 feature/wp-scp-020c-rego-rules
   git worktree add ~/Projects/scp-track2 feature/wp-scp-021e-propose-stub
   ```
   Each branch has its `dispatch-package.json` + `consolidation-r1.json` + 3× R1 review JSONs + a `fix-round-1/dispatch-package.json` ready to retry.

5. **Run gate-check on both worktrees** before any dispatch:
   ```bash
   /Users/amplience/Projects/standards-control-plane/scripts/wp_scp_022_gate_check.sh --slice 020c
   /Users/amplience/Projects/standards-control-plane/scripts/wp_scp_022_gate_check.sh --slice 021e
   ```
   Both must report OK on symlink-escape, D-021 collision, and ACC pin manifest. If anything fails: pause and surface to user.

## Non-negotiable invariants (per `feedback_protocol_over_shortcuts.md`)

- **Per-slice PR.** Never batch slices.
- **Adversarial review every slice.** Three lenses, parallel dispatch with 500 ms stagger. No exceptions.
- **Recurse to fixpoint.** Per §4.3: all-three APPROVED, OR all-three APPROVED_WITH_FINDINGS where every finding is MIN/nit. CRIT or unmitigated MAJ → fix round.
- **Evidence committed in-repo.** `docs/reviews/WP-SCP-022/dispatches/<slice-id>/` for every slice — dispatch package, dispatcher result, three reviewer JSONs, consolidation, fixpoint.md with sha256_chain.
- **Reviewer-finding sanitization.** Run `scripts/sanitize_review_finding.py` before injecting findings into a fix-round prompt.
- **D-021 reservation respected.** Reserved for the 2026-05-31 atomic-workday filing. Codex executors must not assign D-021 to anything else. Gate helper checks via `--check-d021`.
- **Orchestrator-applied path is OK** when codex consistently times out — but the R(F+1) review still validates the result. The protocol's quality gate is the *review*, not the *implementer*. Do not skip review.

## Sequence of work (8 slices + 1 in-flight pair + 3 user gates)

### Phase A: Resume in-flight pair (today's pause)

**A1. Slice 020C (Track 1, 3 starter Rego rules + tests + CODEOWNERS + workflow steps).**
- R1 already filed; 1 CRIT + 10 MAJ to close. Read `~/Projects/scp-track1/docs/reviews/WP-SCP-022/dispatches/020c/consolidation-r1.json` for canonical findings.
- Try retry codex fr1 first: `~/Projects/acc/scripts/codex_dispatch.py --package <fr1 package> --cwd ~/Projects/scp-track1`. Use `timeout_seconds: 3000` (50 min).
- If codex times out within 5 min of dispatch: orchestrator-apply per §4.3. Edit the files in the worktree directly per the consolidation findings. Run the verify_commands. Commit + push.
- R2 review (3 lenses, parallel). If fixpoint per §4.3 → write fixpoint.md with hash chain → open PR → merge. If not → fr2.
- Headline R1 issues: `scp_r_002_is_waiver_payload` silent-bypass for non-object arrays; missing `schemas/waivers-file.schema.json` reference (now exists on main, check the path); SCP-R-002 missing required `reason` field (schema drift); deny payload uses `msg` not `message` (mismatch with `schemas/policy-check-summary.schema.json`); SCP-R-003 fixture coverage gaps; opa test ≥90% has no CI enforcement gate.

**A2. Slice 021E (Track 2, propose() hardening).**
- R1 filed; 6 MAJ to close. Read `~/Projects/scp-track2/docs/reviews/WP-SCP-022/dispatches/021e/consolidation-r1.json`.
- Same retry-then-orchestrator-apply pattern.
- Headline R1 issues: rate-limit `caller_id` from `os.getpid()` resets on server restart (DoS vector); `_current_signing_key_id()` returns sentinel string `'unconfigured-signing-key'` silently when keyring missing — leaks into proposal envelopes; SIGKILL between proposal-write and branch-create leaves orphan; `ProposeRequest.body` no `max_length` cap; banner text diverges from AC#4 spec.

**A3. After both merge: USER-GATE-C.**
- 021E merge closes Track 2's autonomous run scope. Track 2 done.
- Prep `docs/reviews/WP-SCP-022/gates/USER-GATE-C.md` draft. Required content per §3 USER-GATE-C definition:
  - PR URLs of all 4 Track 2 slices (021B/C/D/E).
  - Confirmation `scp-mcp-server` is installable from PyPI as `standards-control-plane[mcp]` extra (or commit a follow-up that publishes; the install pathway exists in 021B's pyproject.toml).
  - Public Ed25519 signing key published at `scp://security/signing-keys` resource AND mirrored at `docs/security/mcp-signing-keys.pub` (the placeholder file from 021B; user runs `scp-mcp-server keygen` post-merge to populate operationally).
  - Required `Signed:` or `Signer:` line + commit author email in `SCP_OPERATOR_EMAILS` allowlist (default `jrnb2024:james@brokai.net` per `scripts/wp_scp_022_gate_check.sh`).
- Surface this to the user with: "Here's the gate artefact draft; please commit it signed and the chain advances. Gate helper will verify."
- After user signs: `scripts/wp_scp_022_gate_check.sh --gate USER-GATE-C` must return 0.

### Phase B: Track 1 chain to USER-GATE-A0 (6 slices)

**B1. Slice 020C.1 — waiver-aware Rego + Python/Rego conflict-gate.**
- Per WP-SCP-020 §4 020C.1: workflow reads caller's waivers.json; rules consume `data.waivers`; `deny` only on no matching unexpired waiver. Conflict-gate adapter at `tests/conflict_gate/adapter.py`. CI job `rego-vs-python-conflict`. Caller-side `.scp/rule-config.yaml` override. Read-back of disabled rules to JSON summary + commit-status text.
- Five sub-criteria (i)–(vi). Build dispatch package, dispatch, review, fix to fixpoint, merge.

**B2. Slice 020J — `v*` tag-protection rule + required-signed-commits on `main`.**
- Precondition for 020D1.
- **CAUTION:** Slice 020J makes two GitHub REST API calls. Per WP-SCP-022 §8 R-022-13, the dispatch package's instruction MUST require Codex to (a) capture the numeric `id` returned by `POST /repos/{owner}/{repo}/tags/protection` in `docs/reviews/WP-SCP-020/branch-protection-log.md` BEFORE invoking the second call; (b) verify both API calls returned 200 OK before reporting `status=complete`; (c) on partial-apply, invoke `gh api -X DELETE /repos/{owner}/{repo}/tags/protection/<numeric-id>` to roll back. The required-signed-commits endpoint is `POST` (NOT `PATCH`) per the GitHub REST docs. The plan §8 R-022-13 has the full verify_commands for this slice.
- This is the kernel-dangerous slice. `reasoning_effort: xhigh`. `timeout_seconds: 3600`.

**B3. Slice 020K — `CODEOWNERS` wiring (personal-account / single-operator path).**
- Precondition for 020D2.
- Per WP-SCP-020 §14 U-k resolution: `@jrnb2024` on `policies/**`, `renovate/**`, `.github/workflows/**`, `docs/DECISIONS.md`, `output/findings/waivers.json`. Branch-protection `require_review_from_non_author=false` (solo operator). Bus-factor-1 risk live; quarterly escalation review 2026-07-21 named in STATUS.md.
- Note: a CODEOWNERS file already exists from slice 020C (you ensured `policies/**` reviewers there). 020K extends it to the other paths.

**B4. Slice 020D1 — SCP self-dogfood wrapper merged on SCP self.**
- Per WP-SCP-020 §4 020D1: SCP's own repo adds `.github/workflows/policy-check-wrapper.yml` calling the reusable workflow at `@<commit-SHA-of-v1.0.0-rc.1>`. **Branch protection on `main` does NOT yet include the check.** Merge commit must be signed (Sigstore/GPG).
- Subtle: this wrapper points at v1.0.0-rc.1 which doesn't exist yet (cut in 020H part 1, immediately next). Either chain dispatch them as a pair, OR write the wrapper with a placeholder pin that 020H part 1 updates as part of its work. Per WP-SCP-020 §3 ordering, 020D1 → 020H part 1 → 020E.a → ... so the placeholder approach is cleaner.

**B5. Slice 020H part 1 — Cut `v1.0.0-rc.1` tag.**
- From the 020D1 merge commit. Release notes enumerate: exact 3 rules; error codes SCP-E001..E006; known limitations. Tag must be signed.
- Update the 020D1 wrapper's `@<commit-SHA>` to point at the rc.1 tag's commit if it was a placeholder.

**B6. Slice 020E.a — SCP-self pre-protection canary.**
- Committed fixture branch `canary/deliberate-violation-pre` with deliberate Rego violation. `gh pr view --json` dump stored. Failing workflow-run-id recorded. Cold-start + warm-start wall-clock times recorded (closure of m-devex-12). Evidence in `docs/reviews/WP-SCP-020/canary-evidence.md`.
- This is the **operational-test slice** — the first real exercise of the workflow against a real PR with a real failing fixture. The canary-run-id is what USER-GATE-A0 references.

**→ USER-GATE-A0** (your input). Prep `docs/reviews/WP-SCP-020/release-signoff.md` draft:
- Required lines: `Signed:` (or `Signer:`), `Date:` ISO-8601, `Canary-Run-Id:` from 020E.a evidence.
- Operator commits the file signed (commit author in `SCP_OPERATOR_EMAILS` allowlist).
- `scripts/wp_scp_022_gate_check.sh --gate USER-GATE-A0` returns 0.

### Phase C: Track 1 close-out (2 slices + USER-GATE-A)

**C1. Slice 020H part 2 — Promote `v1.0.0-rc.1` → `v1.0.0`.**
- Governance sign-off recorded in the just-signed `release-signoff.md`.
- Tag the v1.0.0 release.

**C2. Slice 020D2 — Enable required status check on SCP `main` with `enforce_admins=true`.**
- This is the moment SCP starts gating itself.
- Per WP-SCP-020 §4 020D2: `scp/policy-check` required on `main`. `required_approving_review_count=1`, `dismiss_stale_reviews: true`, `require_review_from_non_author: false` (single-operator). Break-glass procedure published in ADOPT-001 §12 (forthcoming, post-pause; OK to land 020D2 without it — § operational).
- Closes the autonomous-run scope.

**→ USER-GATE-A** (your input). Prep `docs/reviews/WP-SCP-022/gates/USER-GATE-A.md` with the 12 Track 1 slice PR URLs, branch-protection API confirmation (`gh api repos/<owner>/<repo>/branches/main/protection`), and a "fresh PR runs the check green" demonstration.

## At the end of all this

When USER-GATE-A0 + USER-GATE-A + USER-GATE-C are all signed and committed:
- SCP enforces its own Rego gate on its own `main` (workflow + 3 rules + branch protection + canaries demonstrated).
- MCP server scaffold + tools + resources + propose-stub installable from PyPI with verified public key.
- Estate cascade (FLA, ACC, RI, etc.) is `WP-SCP-024` — out of this autonomous-run scope.
- Post-pause Track 1 work (020E.b/E.c canaries, 020F Renovate preset, 020G branch-protection automation, 020H part 3 adopter guide, 020H.1 versioning + RFC + rollback detection, 020I FLA pilot) is `WP-SCP-022.1` — separate WP.
- Post-pause Track 2 work (021F adopter guide, 021G ACC integration, 021H HTTP transport, 021I auth, 021J observability, 021K self-consume) also `WP-SCP-022.1` or split.

Update STATUS.md to record the autonomous-run-complete state. Update auto-memory `project_wp_scp_022_plan.md` to "complete; ready for `WP-SCP-024` estate cascade prep."

## Cost / time envelope

- **Per slice budget** (per WP-SCP-022 §8 R-022-07): $30. **Aggregate budget**: $300.
- **Spent so far across all sessions**: ~$110 (5 plan-review rounds + 6 slice-fixpoint cycles + dispatcher-timeout retries).
- **Estimated to complete**: ~$200 more. Total ~$310 — slightly over the proposed cap. If the chain is approaching the cap, surface to user before each subsequent slice dispatch.
- **Wall-clock per slice**: 60–90 min observed. 9 slices remaining + 3 gates = ~9–13 hours of orchestration.

## Codex-timeout pattern (operational note)

If codex times out repeatedly (>2 dispatches in a row hitting timeout with 0 files written):
1. Bump `timeout_seconds` to 3000.
2. If still timing out: orchestrator-apply per §4.3. Read consolidation, edit files directly, commit, push.
3. R(F+1) reviewers still validate the result regardless of who wrote the code.
4. Surface the timeout pattern to user if it persists across 3+ slices — there may be a sandbox issue.

## Pinned dispatch infrastructure (do not drift without an amending decision)

- **ACC repo pinned at HEAD** `b253363f38ccb7f0278ebde993c33117897e9aab` (per `docs/reviews/WP-SCP-022/acc-pin-manifest.json` on main).
- **Dispatch scripts**:
  - `~/Projects/acc/scripts/codex_dispatch.py` blob `9d2083d8...0820816`
  - `~/Projects/acc/scripts/claude_dispatch.py` blob `805e86c3...d17a30`
- **Dispatcher schemas**:
  - `~/Projects/acc/schemas/codex_work_package.schema.json` blob `2320352c...1f1f01`
  - `~/Projects/acc/schemas/codex_dispatch_result.schema.json` blob `17a08335...aab4c`
  - `~/Projects/acc/schemas/sonnet_review_result.schema.json` blob `9300aa6d...b45af`
- Run `scripts/wp_scp_022_gate_check.sh --check-acc-pin` before any dispatch session. Drift = pause for user review.

## Per-slice runbook in one block

For each remaining slice:

```
# 1. Branch + worktree setup
git branch feature/wp-scp-<slice-id>-<short-name> main
git worktree add ~/Projects/scp-trackN feature/wp-scp-<slice-id>-<short-name>
mkdir -p ~/Projects/scp-trackN/docs/reviews/WP-SCP-022/dispatches/<slice-id>

# 2. Build dispatch package per §4.1 contract
# - package_id: wp-scp-<NNN><slice-id>
# - instruction: cite WP-SCP-020 §4 row <slice-id> verbatim with sub-criteria
# - spec_paths: parent plan + WP-SCP-022 plan + relevant existing files
# - scope_boundary: tight glob list
# - verify_commands: include actively-asserting checks (grep -q ! for buggy patterns)
# - timeout_seconds: 1800 default; 3000 for heavy slices; 3600 for kernel-dangerous (020J)
# - reasoning_effort: high (default); xhigh for 020J

# 3. Commit dispatch package + push
cd ~/Projects/scp-trackN
git add docs/reviews/WP-SCP-022/dispatches/<slice-id>/dispatch-package.json
git commit -m "Slice <slice-id> dispatch package (pre-dispatch evidence)"
git push -u origin feature/wp-scp-<slice-id>-<short-name>

# 4. Gate-check
~/Projects/standards-control-plane/scripts/wp_scp_022_gate_check.sh --slice <slice-id>

# 5. Codex dispatch (long-running; use background)
~/Projects/acc/scripts/codex_dispatch.py \
  --package ~/Projects/scp-trackN/docs/reviews/WP-SCP-022/dispatches/<slice-id>/dispatch-package.json \
  --cwd ~/Projects/scp-trackN \
  > ~/Projects/scp-trackN/docs/reviews/WP-SCP-022/dispatches/<slice-id>/dispatcher-result.json

# 6. Commit codex output + push (if any)
cd ~/Projects/scp-trackN
git add -A
git commit -m "WP-SCP-022 slice <slice-id>: <one-line summary>"
git push

# 7. Build 3× review packages (correctness / safety_bypass / completeness_governance)
# - Output paths: dispatches/<slice-id>/review-{lens}-package.json
# - context_paths: the files Codex changed + the parent plan row + the consolidation if any

# 8. Dispatch 3 reviewers in parallel (500ms stagger)
for L in correctness safety completeness; do
  ~/Projects/acc/scripts/claude_dispatch.py \
    --package <slice-dir>/review-$L-package.json \
    --cwd <worktree> \
    > <slice-dir>/review-$L.json &
  sleep 0.5
done
wait

# 9. Read verdicts. Per §4.3:
# - All-three APPROVED → fixpoint
# - All-three APPROVED_WITH_FINDINGS where every finding is MIN/nit → fixpoint
# - Otherwise → fr1

# 10. If not fixpoint: build fr1 dispatch package
# - sanitize R1 findings via scripts/sanitize_review_finding.py
# - inline sanitized findings into instruction
# - same scope_boundary; expand only if review insists (cross-slice fix)
# - re-run codex (if it times out twice, orchestrator-apply)
# - re-run reviewers; recurse to fixpoint or escalate at fr5

# 11. At fixpoint: write fixpoint.md with sha256_chain
# - leaves: sha256(<terminal review result JSON>) for each lens
# - root: sha256(corr || safety || completeness)
# - Run `scripts/wp_scp_022_gate_check.sh --check-hash-chain <slice-id>` to verify

# 12. Open PR + merge (squash + delete branch)
gh -R jrnb2024/standards-control-plane pr create --base main --head <branch> --title "..." --body "..."
gh -R jrnb2024/standards-control-plane pr merge <PR#> --squash --delete-branch

# 13. Sync main + clean up worktree
cd ~/Projects/standards-control-plane
git checkout main && git pull --ff-only origin main
git worktree remove ~/Projects/scp-trackN
git branch -D feature/wp-scp-<slice-id>-<short-name>
```

## When finished

Report to user: "WP-SCP-022 autonomous run complete. SCP gates itself on its own main (PR <020D2 number> merged); MCP scaffold (021E) + USER-GATE-C signed. Estate cascade (WP-SCP-024) is the next programme."
