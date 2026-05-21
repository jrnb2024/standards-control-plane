# POST-IMPL R1 — WP-SCP-024 slice 024C (PIM canary cascade)

**Slice:** 024C — PIM (`jrnb2024/mapp-pim`) canary onboarding
**Status:** **CEREMONY COMPLETE 2026-05-17** — bake observation pending
**Authored:** 2026-05-17 (post-merge of SCP-side PR #118 `710d80f`)
**Discipline:** post-impl R1 surface per `feedback_r1_surface_must_cite_ci.md` (citation-pair escalated 2026-05-16 third recurrence)

---

## 1. Citation pair (citation discipline)

Per the estate-wide rule that post-impl claims must cite BOTH the CI run + the PR-level aggregate gate.

### Citation A — CI run URL (terminal step green)

| Field | Value |
|---|---|
| Workflow | `check-invocation-log-entry` (the gate that was failing-by-design pre-Phase 3) |
| Run ID | `25998891890` |
| URL | https://github.com/jrnb2024/standards-control-plane-/actions/runs/25998891890 |
| Head SHA | `67f428d71372e34f91acd76976d23228131452e5` (step3 fix-commit after the cascade-status-line-format bug) |
| Conclusion | `success` |
| Created at | `2026-05-17T18:18:43Z` |

### Citation B — PR-level aggregate state at merge

`gh pr view 118 --repo jrnb2024/standards-control-plane- --json state,mergeStateStatus,mergedAt,mergeCommit,statusCheckRollup` returned:

```json
{
  "number": 118,
  "state": "MERGED",
  "mergeStateStatus": "UNKNOWN",
  "mergedAt": "2026-05-17T18:19:18Z",
  "mergeCommit": "710d80f361a83f9ad0e156ed92b4f6d40e8f3a55",
  "headRefOid": "67f428d71372e34f91acd76976d23228131452e5",
  "checks": [
    {"name": "validate PR body",                "conclusion": "SUCCESS"},
    {"name": "check-invocation-log-entry",      "conclusion": "SUCCESS"},
    {"name": "policy-check / scp/policy-check", "conclusion": "SUCCESS"},
    {"name": "scp/policy-check-readback",       "conclusion": "SUCCESS"}
  ]
}
```

`mergeStateStatus: UNKNOWN` is the expected post-merge value — the gate is no longer evaluated once the PR has been merged. The auditable pre-merge equivalent is "all 4 statusCheckRollup conclusions = SUCCESS at headRefOid `67f428d`", which gated the squash-merge.

### Citation discipline gap surfaced (citation-pair on operator-authored close-out side)

The 2026-05-17 `STATUS.md` "Last updated" header line + ACCEPTANCE-CHECKLIST row 6 closure both claim **"D-045 filed"**. Direct inspection of `docs/DECISIONS.md` shows D-040, D-041, D-042, D-043, D-044, D-047, D-048 as actual rows; **D-045 is referenced only in the D-044/D-045/D-046 reservation note (lines 29, 34, 44) — no row exists.** This is a citation-drift: the close-out narrative claims an artefact that hasn't been authored. Per D-040 single-operator-mode + `feedback_no_silent_descoping.md`, the D-045 row is operator-authored — this surface does NOT auto-file it. See §6 reminders.

---

## 2. R-cycle evidence (8 archives across R4 + R5 + R6)

| Cycle | Lens | Verdict | Archive | Top-level result |
|---|---|---|---|---|
| **R1** | correctness | APPROVED_WITH_FINDINGS | `r3-correctness.json` | 2 MIN + 1 nit |
| R1 | safety_bypass | APPROVED_WITH_FINDINGS | `r3-safety_bypass.json` | 2 MAJ + 3 MIN + 1 nit |
| R1 | completeness_governance | APPROVED_WITH_FINDINGS | `r3-completeness_governance.json` | 3 MAJ + 3 MIN + 3 nit |
| **R2** | correctness | APPROVED_WITH_FINDINGS | `r4-correctness.json` | 3 CONFIRMED-CLOSED + 2 nit |
| R2 | safety_bypass | APPROVED_WITH_FINDINGS | `r4-safety_bypass.json` | 5 CONFIRMED-CLOSED + 2 CONFIRMED-DEFERRAL + 1 MIN + 2 nit |
| R2 | completeness_governance | APPROVED_WITH_FINDINGS | `r4-completeness_governance.json` | 7 CONFIRMED-CLOSED + 1 new MAJ + 2 nit |

**Total across R1 + R2 (in-slice):** 0 CRIT + 6 MAJ + 8 MIN + 8 nit closed via R5 + R6 fix-rounds; 2 MAJ carried as TFs (see §5).

**Dispatch note:** R1 + R2 dispatched via `Agent` tool with `model: sonnet` (3 parallel reviews per cycle) rather than `claude_dispatch.py`. Pivot per `feedback_acc_hook_premature_target_repo_install.md` — `claude_dispatch.py` requires the ACC kernel hook installed locally on the cwd repo (sudo-attended); the hook is not installed on SCP. Same adversarial-review surface, same Sonnet model, same JSON schema enforcement; lost the `.acc/claude-dispatch-log/` audit artefacts but retained the findings + verdicts. **Recommended memory housekeeping:** extend `feedback_acc_hook_premature_target_repo_install.md` with the Agent-tool 3-lens pivot pattern as the canonical workaround for repos lacking the ACC hook (reusable across Recommender's upcoming WP-RECOMMENDER-DEPLOY-WORKFLOW-PATCH-001 Phase 1 R1, which will face the same gap).

---

## 3. PIM-side live-state verification

`gh api repos/jrnb2024/mapp-pim/branches/main/protection` (out-of-band read post-Phase-1 close, per R1 SAF-001 log-forgery surface closure):

```json
{
  "required_status_checks": ["lint", "test-platform", "contract-tests", "playwright-uat", "policy-check / scp/policy-check"],
  "enforce_admins": true,
  "required_signatures": true,
  "required_pull_request_reviews": {"required_approving_review_count": 0}
}
```

**Brownfield merge correct.** Before-state had 4 contexts (`lint`, `test-platform`, `contract-tests`, `playwright-uat`); after-state has 5 (the 4 preserved + the SCP canonical context). The R4 `--preserve-existing-contexts` flag operated exactly as designed — no destructive replacement of PIM's prior CI gates.

**PIM commit-signing verified pre-Phase-1** via `gh api repos/jrnb2024/mapp-pim/commits/main --jq '.commit.verification'` returning `verified: true, reason: "valid"` on HEAD + 10 most recent commits (GitHub-signed squash-merges + operator-GPG-signed locals). `--skip-required-signatures` NOT used for PIM. No FUP-PIM-COMMIT-SIGNING needed. `required_signatures: true` flip operationally safe and verified live.

**Invocation log entry committed.** `docs/reviews/WP-SCP-020/branch-protection-log.md` lines 47+ now carries the full block (operator handle `@jrnb2024`, script SHA256 `0a1b596…`, script git SHA `ca28766` = R6, structured `preserve-existing-contexts: true` + `skip-required-signatures: false` + `destructive-contexts-warning: false`, PUT payload, before/after JSON, live-state verification block).

---

## 4. R-FIXPOINT declaration

**Reached at criterion (a): 0 CRIT + 0 unique in-slice MAJ across R5 + R6 fix-rounds.** 2-fix-round cap (R5 = round 1, R6 = round 2) per operator GATE-2 spec; diminishing-returns invoked. No further fix-rounds will land on this slice — any post-merge findings open as new TFs or sub-slices.

Commit chain at merge:

```
710d80f  squash-merge: PR #118 → main (operator @jrnb2024, 2026-05-17T18:19:18Z)
  ├─ 67f428d  fix(024C): cascade-status line format for check-invocation-log-entry enforcer
  ├─ 509a211  docs(024C): cascade-status: onboarded + invocation-log entry  (Phase 3 close commit)
  ├─ 892c6c2  chore(024C): substitute R6 SHA placeholder
  ├─ ca28766  fix(024C): fix-round-6 — R2 closures (R-FIXPOINT)
  ├─ d8d2e36  fix(024C): fix-round-5 — R1 closures
  ├─ 7e89d64  merge main into branch
  ├─ 8a5c2b7  fix(024C): fix-round-4 — brownfield-adopter flags
  ├─ 68d0b68  fix(024C): fix-round-3 — orchestrator dispatch realignment
  ├─ c031234  fix(024C): fix-round-2
  ├─ 84eaf80  fix(024C): fix-round-1
  └─ 4ea2b41  slice opening + scaffolder run
```

All 11 commits signed `G` (operator GPG/SSH on locals; GitHub on the squash-merge).

---

## 5. Tracked-forward (carry-over from R1 + R2 + operator queue execution)

| TF | Source | State | Close condition |
|---|---|---|---|
| `TF-024C-R5-001-SIGNING-DEFERRAL-AUDIT` | R1 safety_bypass S-MAJ-02 | OPEN | Estate-side audit detecting adopters with `skip-required-signatures: true` in branch-protection-log AND `required_signatures.enabled=false` on live API. Minimum viable: scorecard-aggregator weekly poll per opt-in adopter; alternative: log-grep + STATUS.md TF-row auto-generation. Out of in-slice scope (touches CI workflows + scorecard-aggregator). Revisit when first adopter actually uses `--skip` — **PIM does not**. |
| `TF-024C-R5-002-CT-NOTIFICATION-AMENDMENT` | R1 completeness_governance G-MAJ-03 | OPEN | Amend `~/Projects/control-tower/governance/docs/notifications/SCP-ESTATE-CASCADE-START-2026-05-15.md` with R4 + R5 brownfield-adopter flags erratum. Cross-repo write — operator-mediated per `feedback_cross_project_coordination_patterns.md` Pattern 4. Draft amendment text complete in STATUS.md TF row (cites R4 `8a5c2b7` + R5 `d8d2e36` ACK addition + R5 destructive-replacement WARNING). Operator commits to CT main when convenient. |
| `FUP-024C-STEP3-CASCADE-STATUS-FORMAT-001` | Operator queue exec — step D first attempt | OPEN | `/tmp/pim-024c-step3-cascade-status-finalize.sh` flip-logic wrote `` `cascade-status: **onboarded** (finalised 2026-05-17)` `` (backtick-prefixed + markdown-bold + dropped closing backtick), failing the enforcer regex `^cascade-status:\s+([^\r\n]+?)\s*$`. Step D self-merge BLOCKED on first attempt; fix-commit `67f428d` replaced the line with bare `cascade-status: onboarded`. Script should be amended to honour the DISPATCH-NOTE template's "override this whole line at finalization" instruction (write bare line, no Markdown decoration). |
| `FUP-024C-STEP3-POLL-RACE-001` | Operator queue exec — step D first attempt | OPEN | Step D's `poll @0s` aborted on OLD HEAD's stale FAILURE before the new HEAD's check could re-fire. Sibling defect to step2b's same poll-@0s premature-terminal anti-pattern. Both scripts should align polling to HEAD (re-fetch `headRefOid` per iteration; only evaluate conclusions for checks at the current HEAD) before evaluating conclusions, per `feedback_r1_surface_must_cite_ci.md` axis #3 (citation must match HEAD evaluated at the moment of the assertion). |

---

## 6. Operator-authored close-out items

Per D-040 single-operator-mode + `feedback_no_silent_descoping.md`, these items are operator-authored. This surface verifies them rather than authoring them.

| Item | Verified state | Notes |
|---|---|---|
| **PR #118 self-merge** | ✅ DONE | `710d80f` 2026-05-17T18:19:18Z, mergedBy `jrnb2024` |
| **ACCEPTANCE-CHECKLIST row 6** | ✅ DONE | Closed via PR #121 `ce47c31`; row records all 3 sub-criteria + bake-observation pending + 2 TFs |
| **STATUS.md chain entry** | ✅ DONE | Entry #14 in 2026-05-17 chain documents Step-A-skip authorisation, Step-B/C/D execution, two step3-defect FUPs filed |
| **D-045 row in `docs/DECISIONS.md`** | ⚠️ **NOT YET FILED** | STATUS.md "Last updated" header + ACCEPTANCE-CHECKLIST row 6 both claim "D-045 filed ✓"; `grep "^\| D-045" docs/DECISIONS.md` returns no match. D-045 row is only mentioned in the reservation note (DECISIONS.md lines 29/34/44). DISPATCH-NOTE has a "D-045 proposed ratification text" subsection — use that as the basis for the actual row. Discrepancy surfaced here for operator close-out, not auto-filed. |
| **TF-024C-R5-002 CT notification amendment** | ⚠️ STILL OPEN (operator-paced) | Draft amendment text ready in STATUS.md TF row; commit to CT main when convenient per Pattern 4 cross-repo discipline |

---

## 7. Bake observation gate (Phase 2)

Slice closure (cascade-status: onboarded) recognises Phase 1 + Phase 3 ceremony complete. Per WP-SCP-024 §6 invariant 8, full ACCEPTANCE-CHECKLIST row 6 part (ii) closure requires:

- ≥1 calendar week elapsed from 2026-05-17 (target window-end: **2026-05-24 onward**)
- ≥1 Renovate-issued SHA pin bump merged clean on PIM main

The slice has been closed at ceremony level (cascade-status onboarded; required-check live; PIM-side gate enforcing); part (ii) is tracked separately and closes part (ii) of row 6 when the first Renovate-issued bump merges clean. R-024-07 fallback `cascade-status: onboarded-operator-bump` is available if Renovate doesn't fire in window.

---

## 8. Threshold A trajectory + cascade slice 2 (024D) unblock

PIM = 1 of 5 cohort adopters onboarded (Threshold A: ≥3 required). Sequencing per plan-doc §5.1: PIM → **control-tower (024D)** → mapp-doc-agent + recommender paired (024E) → shopify-app (024F). 024D opens after 024C bake-clean (artefact-based per CT reconciliation 2026-05-16 v0.2 — operator-decided when "treat the canary as proven" criterion is met; not a fixed calendar gate).

024D unblocks when:
- 024C bake-clean declared OR operator-artefact-attestation
- TF-024C-R5-002 CT notification amendment committed (so CT operator running 024D sees the brownfield-flag erratum)

WP-SCP-025 (parked per 2026-05-09 operator decision; D-035-rules re-scoped) remains parked post-024C; revisit per plan-doc §5.1 sequencing.

---

## 9. Stand-down state

**SCP-side 024C ceremony COMPLETE.** Awaiting:
1. Bake observation (≥1 week + ≥1 Renovate cycle) → closes ACCEPTANCE-CHECKLIST row 6 part (ii)
2. Operator D-045 row authoring → closes citation drift surfaced in §6
3. Operator TF-024C-R5-002 commit to CT main → closes operator-mediated Pattern 4 cross-repo work
4. 024D opens at operator discretion after bake-clean

Per `feedback_r1_surface_must_cite_ci.md` post-impl R1 discipline: this surface cites the CI URL + PR-level aggregate state at merge headSha, archives R1 + R2 evidence in `docs/reviews/WP-SCP-024/024C/r{3,4}-*.json`, lists carry-forward TFs with close conditions, surfaces D-045 citation drift for operator close-out, and records 2 step3-script defect FUPs (operator-detected during queue execution). 024C ships at ceremony level; full Threshold A close requires 2 more cohort adopters onboarded + bake-clean per slice.
