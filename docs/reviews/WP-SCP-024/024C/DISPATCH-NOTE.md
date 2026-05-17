# DISPATCH-NOTE — WP-SCP-024 slice 024C (PIM canary cascade)

**Date:** 2026-05-15
**Branch:** `feature/wp-scp-024-024c-pim-canary` (off origin/main at `38ccdbe`)
**Predecessor:** FUP-ACC-INSTALL-TARGET-REPO-001 closed 2026-05-15 (ACC PRs #199 + #202); 024B-extras chain fully closed (024B-extras-3 merged at `e549c71`); TF-024B-REQCHECK-ENABLE-001 functionally closed (branch protection on SCP main has `check-invocation-log-entry` in required_status_checks).
**Decision reserved:** **D-045** — to be ratified on slice close.

- **Target:** jrnb2024/mapp-pim

(Branch qualifier `main` is prose-only — the CI parser expects bare `<owner>/<repo>` per check-invocation-log-entry.sh regex.)

**Adopter slug** (per plan-doc §5.2 invariant 2 regex format spec — `<owner>-<repo>` lowercased): `mapp-pim-mapp-pim`.

`cascade-status: PENDING` — declared at slice close after operator-attended PIM-side ceremony completes + bake observation window elapses. Per the `check-invocation-log-entry` workflow's `resolve-dispatch` step (`.github/workflows/check-invocation-log-entry.yml`), this PR stays in DRAFT until `cascade-status` is finalized to one of `{onboarded, onboarded-operator-bump, blocked-on-adopter-conflict}` — `PENDING` is not in the enumerated set so the workflow fails by design until Phase 3 close. (Field format here is bare per the CI parser; operator overrides this whole line at finalization.)
`slice-type: cohort`

**FLA pilot safety findings reviewed:** none new since 2026-05-15 (FLA pilot state confirmed stable as of 024C kickoff; FLA-independent per invariant 4).

## Cross-repo coordination (plan-doc §5.5)

| Notification | Path | Status |
|---|---|---|
| Estate cascade start announcement (this slice's kickoff; incorporates TF-023A-002 deferred WP-SCP-023 v1.2.0 release notification) | `~/Projects/control-tower/governance/docs/notifications/SCP-ESTATE-CASCADE-START-2026-05-15.md` | DRAFTED 2026-05-15 (this slice opening) |
| ACC kickoff awareness (PIM canary is now active; ACC kernel-hook install ceremony begins post-cascade) | inline reference in this DISPATCH-NOTE + ACC PR #199 closure (which already names SCP cascade as the unblocked downstream) | COVERED by ACC PR #199 close-doc |

## Why PIM as canary

Per plan-doc §5.1 canary-first sequencing: smallest cooperative adopter first, control-tower second (high-traffic flagship), mapp-doc-agent + recommender paired third, shopify-app last. PIM = `jrnb2024/mapp-pim`. Minimal blast radius; cooperative; well-understood CI shape.

## Scope (in)

| Deliverable | Path | Notes |
|---|---|---|
| Cascade slice DISPATCH-NOTE | `docs/reviews/WP-SCP-024/024C/DISPATCH-NOTE.md` | This file. `cascade-status:` declared at slice close. |
| Invocation-log entry | `docs/reviews/WP-SCP-020/branch-protection-log.md` | Recorded ONLY when `cascade-status:` is `onboarded` or `onboarded-operator-bump` (invariant 2). Operator-pasted from `enable-required-check.sh` output post-invocation. |
| D-045 ratification | `docs/DECISIONS.md` | Per-adopter onboarding contract + canary-first sequencing + post-bake observation window. Reserved at 024A plan-doc merge; consumed at slice close. |
| STATUS.md chain entry | `STATUS.md` | 2026-05-15+ chain entry recording slice flow. |
| ACCEPTANCE-CHECKLIST update | `docs/reviews/WP-SCP-024/024A-plan-doc/ACCEPTANCE-CHECKLIST.md` | Row 6 (024C AC) updated with slice closure status post-bake. |
| R-cycle archives | `docs/reviews/WP-SCP-024/024C/r{1,2,...}-*.json` | 3-lens R1 review + fix-rounds. |

## Scope (out)

- Adopter PR on `jrnb2024/mapp-pim` — separate PR on the adopter repo, opened in parallel by the operator. Scaffolder-emitted artefacts at `~/Projects/scp-scaffolds/024c-pim/` (see operator runbook below).
- ACC kernel hook install on PIM — `sudo bash scripts/install_acc_hook.sh --target-repo /path/to/pim` from ACC repo. Operator-attended.
- `enable-required-check.sh` invocation against PIM — operator-attended (bootstrap-only; refuses CI=true).
- Bake observation window — ≥1 calendar week + ≥1 Renovate-issued SHA pin bump merged + observed clean on PIM main.
- 024D (control-tower) — opens after 024C bake-clean.

## Adopter PR scope (separate PR on jrnb2024/mapp-pim)

Scaffolder invocation (2026-05-15) — operator-reproducible:

```bash
cd ~/Projects/standards-control-plane
scripts/scaffold-downstream.sh \
  --adopter-repo jrnb2024/mapp-pim \
  --default-branch main \
  --scp-sha 41a529908ef5355b82ca924ef0502fa5ec2fcc11 \
  --scorecard-emit false \
  --output-dir ~/Projects/scp-scaffolds/024c-pim
```

Scaffolder output at `~/Projects/scp-scaffolds/024c-pim/`:

```
.github/workflows/policy-check-wrapper.yml   # the wrapper pinning SCP v1.0.0 @ 41a5299 (canonical downstream pin)
.github/CODEOWNERS-snippet.txt               # append to PIM's CODEOWNERS (if any)
CASCADE-PR-BODY.md                           # canonical PR body for the adopter PR
MANIFEST.json                                # scaffolder audit emission
```

Pin: `jrnb2024/standards-control-plane-@41a529908ef5355b82ca924ef0502fa5ec2fcc11` — canonical downstream pin SHA per `scripts/scaffold-downstream.sh` `V1_0_0_SCP_SHA` constant. The annotated v1.0.0 tag-object resolves to commit `04523fac` per `git rev-parse v1.0.0^{commit}`, but adopter pins consistently use the canonical-downstream constant `41a5299` (a post-v1.0.0-rc.1 stabilizer commit). Variable-name misnomer (`V1_0_0_SCP_SHA` ≠ actual v1.0.0 commit) filed as `FUP-SCP-V1-0-0-SHA-NAMING-001` (P3 hygiene defer; do NOT fix during PLAN-AUTH-FOUNDATION-007 in-flight). Per `project_wp_scp_024_plan.md` memory and TF-023E-002 (still open), v1.0.0 (canonical `41a5299` form) is the current pin recommendation until 023E follow-up restructures `attest-scorecard` into a separate workflow file.

## Cascade-status decision tree (declared at slice close)

Per plan-doc §5.2 + invariant 2:

- **`onboarded`** (Renovate path): adopter PR merged + `enable-required-check.sh` invocation logged + ≥1 calendar week elapsed + ≥1 Renovate-issued SHA pin bump merged clean. Slice MUST modify `docs/reviews/WP-SCP-020/branch-protection-log.md` with invocation entry matching target.
- **`onboarded-operator-bump`** (R-024-07 fallback): same as above BUT Renovate didn't fire (e.g., PIM has Renovate disabled or cohort-not-extended) AND operator manually bumped the SHA. Slice MUST add `TF-024X-renovate-mapp-pim-mapp-pim` row to STATUS.md matching invariant 2 regex spec.
- **`blocked-on-adopter-conflict`** (invariant 10): adopter has pre-existing conflicting workflow (e.g., stale `policy-check.yml` from prior experiment). Slice MUST NOT modify branch-protection-log.md AND MUST reference `TF-024X-conflict-mapp-pim-mapp-pim` in this DISPATCH-NOTE matching invariant 2 regex spec. New sub-slice opens on conflict resolution.

## D-045 — proposed ratification text

To be filed in `docs/DECISIONS.md` at slice close:

> **D-045 | 2026-05-XX | Adopt the WP-SCP-024 per-adopter onboarding contract as estate doctrine.** Each cohort cascade slice ships (a) adopter wrapper PR on the adopter repo with SCP federation primitive SHA-pinned per VERSIONING.md (D-036) AND (b) `enable-required-check.sh` invocation entry under `docs/reviews/WP-SCP-020/branch-protection-log.md` (operator-run per D-035; refuses CI=true) AND (c) post-bake observation window of ≥1 calendar week + ≥1 Renovate-issued SHA pin bump cycle merged clean before declaring `cascade-status: onboarded` AND (d) opt-in scorecard-emit follow-up sub-slice deferred until TF-023E-002 closes AND the adopter repo visibility allows OIDC artefact attestation per TF-023E-001 (per plan-doc §2 invariant 2 item d) AND (e) canary-first sequencing per plan-doc §5.1 (PIM → control-tower → mapp-doc-agent + recommender paired → shopify-app). Per-adopter rollback per invariant 7 (`enable-required-check.sh --restore <pre-state.json>` + `git revert` on adopter wrapper; <30-min SLO). PIM (this slice) is the canary; per-slice closure pattern reused by 024D/024E/024F unchanged. | ACCEPTED | Closes 024A R1 MAJ-SAFE-002 + ratifies invariants 1/4/7/8 in slice-procedure form. PIM canary surfaces any federation-primitive bugs at minimal estate blast radius before 024D opens against the higher-traffic control-tower repo.

## Acceptance criteria

- [ ] Scaffolder output produced at `~/Projects/scp-scaffolds/024c-pim/` (CASCADE-PR-BODY + wrapper + CODEOWNERS snippet + MANIFEST)
- [ ] SCP-side cascade slice DISPATCH-NOTE merged (this file)
- [ ] Operator-attended: PIM adopter PR opened on jrnb2024/mapp-pim with scaffolded artefacts + CASCADE-PR-BODY.md
- [ ] Operator-attended: `install_acc_hook.sh --target-repo /path/to/pim` run on PIM checkout
- [ ] Operator-attended: PIM adopter PR merged
- [ ] Operator-attended: `enable-required-check.sh --repo jrnb2024/mapp-pim --branch main --preserve-existing-contexts` invoked (flag is MANDATORY for PIM — brownfield; see Step 3) + invocation log block pasted into `docs/reviews/WP-SCP-020/branch-protection-log.md`
- [ ] Bake observation: ≥1 calendar week elapsed
- [ ] Bake observation: ≥1 Renovate-issued SHA pin bump cycle merged + observed clean on PIM main
- [ ] `cascade-status:` finalized in this DISPATCH-NOTE
- [ ] D-045 row filed in `docs/DECISIONS.md`
- [ ] STATUS.md chain entry recording slice closure
- [ ] ACCEPTANCE-CHECKLIST row 6 updated (CLOSED + cite slice closure date + cascade-status value)
- [ ] 3-lens R1 fixpoint at criterion (a) or (b)
- [ ] PR + self-merge per D-040

## Operator runbook (Phase 1 — PIM-side ceremony)

Three operator-attended steps. All bootstrap-only (`enable-required-check.sh` refuses `CI=true` / `GITHUB_ACTIONS=true`).

### Step 1: Install ACC kernel hook on PIM checkout

Prerequisite: PIM repo cloned locally at `/path/to/pim` (replace placeholder with actual absolute path before running).

**Step 1a — operator confirmation (dry-run-equivalent).** `install_acc_hook.sh` does not currently expose a `--plan` mode; resolve the target path + validate preconditions manually before invoking with sudo:

```bash
TARGET_PIM=$(realpath /path/to/pim)
echo "TARGET_PIM resolves to: $TARGET_PIM"   # operator: verify this is the intended PIM repo
git -C "$TARGET_PIM" rev-parse --git-dir >/dev/null && echo "git repo: OK"
[ -w "$TARGET_PIM" ] && echo "writable: OK"
[ ! -d "$TARGET_PIM/.acc" ] && echo "no existing .acc/: OK"
```

All three checks must echo OK before proceeding. (PR #199 install script will re-validate; this dry-run prevents accidental sudo against the wrong path.)

**Step 1b — actual install.**

```bash
cd ~/Projects/acc   # ACC repo with the --target-repo flag from PR #199 (merged 2026-05-14)
sudo bash scripts/install_acc_hook.sh --target-repo "$TARGET_PIM"
```

ACC PR #202's direct-write fallback handles dispatcher `active-dispatch.json` writing — verified by operator-smoke on Recommender + RI before merge.

### Step 2: Open adopter PR on jrnb2024/mapp-pim

**Step 2a — review CODEOWNERS snippet placeholder.** The scaffolder emits `.github/CODEOWNERS-snippet.txt` with a placeholder `@<adopter-CODEOWNERS-account>` for the adopter-side reviewer. Open the file + replace the placeholder with PIM's actual CODEOWNERS account (e.g., `@jrnb2024` if single-operator on PIM too) BEFORE appending. Blindly appending the placeholder creates an invalid CODEOWNERS entry that GitHub silently treats as no-coverage — removing CODEOWNERS protection on the wrapper file.

```bash
cd /path/to/pim
git checkout -b feat/scp-federation-primitive-adoption
cp -r ~/Projects/scp-scaffolds/024c-pim/.github/workflows/policy-check-wrapper.yml .github/workflows/
# Step 2a — substitute placeholder BEFORE appending:
sed 's/@<adopter-CODEOWNERS-account>/@jrnb2024/' \
  ~/Projects/scp-scaffolds/024c-pim/.github/CODEOWNERS-snippet.txt \
  >> .github/CODEOWNERS   # only if PIM already has a CODEOWNERS file; else create with the substituted content
git add -A
git commit -m "feat: adopt SCP federation primitive (policy-check wrapper @ v1.0.0)"
git push -u origin feat/scp-federation-primitive-adoption
gh pr create --base main --head feat/scp-federation-primitive-adoption \
  --title "feat: adopt SCP federation primitive (policy-check wrapper)" \
  --body-file ~/Projects/scp-scaffolds/024c-pim/CASCADE-PR-BODY.md
```

Wait for CI to pass on the adopter PR (the wrapper should pass against PIM's existing code — purely additive). Self-merge per single-operator mode.

### Step 3: Enable required-check on PIM + log invocation

**Brownfield-adopter precondition (PIM-specific).** PIM main currently has 4 pre-existing required checks (`lint`, `test-platform`, `contract-tests`, `playwright-uat`) that the default greenfield invocation would silently remove (`enable-required-check.sh` builds the PUT payload with `contexts: [$REQUIRED_CONTEXT]` — a single-element list, not an append). `--preserve-existing-contexts` (added in 024C fix-round-4) merges `policy-check / scp/policy-check` into the existing list via `jq`'s `unique` operator with idempotent dedup. This flag is **mandatory** for the PIM invocation; omitting it produces a destructive context replacement. See ADOPT-001 §12.7.3 brownfield-adopter section for full discussion. PIM commit-signing status was verified pre-Step-3 via `gh api repos/jrnb2024/mapp-pim/commits/main --jq '.commit.verification'` (returned `verified: true, reason: "valid"` on HEAD + 10 most recent commits — all GitHub-signed squash-merges or operator-GPG-signed locals); `required_signatures: true` is operationally safe to flip, so `--skip-required-signatures` is NOT used for PIM.

```bash
cd ~/Projects/standards-control-plane
scripts/enable-required-check.sh --repo jrnb2024/mapp-pim --branch main --preserve-existing-contexts --plan   # dry-run first; review the merged PUT payload + before-state
scripts/enable-required-check.sh --repo jrnb2024/mapp-pim --branch main --preserve-existing-contexts          # apply (merge canonical into existing 4 checks → 5)
```

Script emits an invocation log markdown block at the end of its output. The block records both flags as structured fields (`preserve-existing-contexts: true`, `skip-required-signatures: false`) so the audit trail captures which path was taken. Paste that block (verbatim, including operator name, script SHA256, before/after API JSON) into `docs/reviews/WP-SCP-020/branch-protection-log.md` as a new entry under the existing list.

**Step 3a — post-merge live-state verification (closes R1 SAF-001 log-forgery surface).** Independent of the script's emitted log block, also verify the live API state matches what the log claims:

```bash
gh api repos/jrnb2024/mapp-pim/branches/main/protection \
  | jq '{required_status_checks: .required_status_checks.contexts, enforce_admins: .enforce_admins.enabled, required_signatures: .required_signatures.enabled}'
```

The output MUST show `"policy-check / scp/policy-check"` AND the 4 pre-existing checks (`lint`, `test-platform`, `contract-tests`, `playwright-uat`) in `required_status_checks` AND `enforce_admins.enabled = true` AND `required_signatures.enabled = true`. Paste the JSON output into the DISPATCH-NOTE under a `## Live-state verification (Phase 1 close)` subsection. This out-of-band read defends against a forged or copy/paste-wrong log entry in single-operator mode.

Then commit the log entry + the live-state verification block to this 024C slice branch + push.

### Step 4: Bake observation

- Wait ≥1 calendar week with the required-check enabled on PIM main.
- Watch for the first Renovate-issued SHA pin bump PR on PIM (Renovate-driven preset cascade). Merge it after CI passes.
- Observe ≥1 calendar day post-Renovate-merge that PIM main CI continues passing.
- Then return to this branch + declare `cascade-status: onboarded` (or `onboarded-operator-bump` per the §5.2 fallback if Renovate didn't fire).

### Rollback path (if bake fails)

If PIM CI degrades post-required-check enable (e.g., wrapper conflict surfaces, federation-primitive bug shipped), execute per-adopter rollback per invariant 7 (<30-min SLO):

**A. Restore branch protection on PIM** (replay the captured pre-state):

```bash
cd ~/Projects/standards-control-plane
# The pre-state JSON is captured in the invocation log entry's "Before" block;
# extract to a temp file:
PRE_STATE_JSON=$(mktemp)
# (operator: paste the "Before" JSON from branch-protection-log.md into $PRE_STATE_JSON,
#  then run the restore)
scripts/enable-required-check.sh --restore "$PRE_STATE_JSON"
rm -f "$PRE_STATE_JSON"
```

The script's `--restore` mode (024B-extras-1 + 024B-extras-2 depth-defense surface) reverts to the captured state. Posture-degradation acknowledgement flags may be needed depending on what the pre-state restores (e.g., `--i-understand-restore-removes-required-checks` if the pre-state had no required checks).

**B. Revert adopter PR on PIM** (remove the wrapper):

```bash
cd /path/to/pim
git checkout main
git revert <adopter-PR-merge-commit-SHA>
git push origin main
```

**C. Declare cascade-status: blocked-on-adopter-conflict in this slice** (per invariant 10):

- File `TF-024X-conflict-mapp-pim-mapp-pim` row in STATUS.md matching the §5.2 regex spec.
- Add the TF reference to this DISPATCH-NOTE.
- Do NOT modify `docs/reviews/WP-SCP-020/branch-protection-log.md` (CI asserts log was NOT modified for blocked-on-adopter-conflict close).
- Open a follow-up sub-slice when the underlying issue is resolved.

## Sequencing

| Phase | Work | Mode | Wall |
|---|---|---|---|
| 0 | SCP-side DISPATCH-NOTE + scaffolder run | Opus (autonomous) | ~30 min |
| 0.5 | 3-lens R1 review on SCP-side stub | Sonnet | ~25-30 min |
| 0.6 | Fix-rounds on SCP-side stub | Codex + Sonnet | ~1 hr (small surface) |
| 1 | PIM-side install + adopter PR + enable-required-check | Operator | ~30-60 min |
| 2 | Bake observation window | Calendar | **≥1 week + ≥1 Renovate cycle** |
| 3 | Cascade-status declaration + D-045 ratification + STATUS.md chain | Opus | ~15 min |
| 4 | Final R-cycle + self-merge | Opus | ~30 min |

Target: 024C closes ~2 weeks wall-clock; bake observation is the long pole, not engineering.

## Tracked-forward (status at slice opening)

None new at slice open. May surface post-bake:
- If Renovate doesn't fire: file `TF-024X-renovate-mapp-pim-mapp-pim`
- If conflict surfaces: file `TF-024X-conflict-mapp-pim-mapp-pim` + open sub-slice

## Slice opening checklist

- [x] DISPATCH-NOTE drafted (this file)
- [x] Branch `feature/wp-scp-024-024c-pim-canary` opened off main `38ccdbe`
- [x] Scaffolder run against PIM (`~/Projects/scp-scaffolds/024c-pim/`)
- [ ] 3-lens R1 review on SCP-side stub
- [ ] Operator-attended Phase 1 (install + adopter PR + enable-required-check)
- [ ] Bake observation Phase 2 (≥1 week + Renovate cycle)
- [ ] Phase 3 closure (cascade-status declaration + D-045 + STATUS.md + R-fixpoint + self-merge)
