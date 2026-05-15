# DISPATCH-NOTE — WP-SCP-024 slice 024C (PIM canary cascade)

**Date:** 2026-05-15
**Branch:** `feature/wp-scp-024-024c-pim-canary` (off origin/main at `38ccdbe`)
**Predecessor:** FUP-ACC-INSTALL-TARGET-REPO-001 closed 2026-05-15 (ACC PRs #199 + #202); 024B-extras chain fully closed (024B-extras-3 merged at `e549c71`); TF-024B-REQCHECK-ENABLE-001 functionally closed (branch protection on SCP main has `check-invocation-log-entry` in required_status_checks).
**Decision reserved:** **D-045** — to be ratified on slice close.
**Target:** `mapp-pim/mapp-pim@main`

`cascade-status:` **PENDING** — declared at slice close after operator-attended PIM-side ceremony completes + bake observation window elapses. Per workflow `resolve-dispatch` enforcement, this PR stays in DRAFT until `cascade-status:` is finalized to one of `{onboarded, onboarded-operator-bump, blocked-on-adopter-conflict}`.
`slice-type: cohort`

## Why PIM as canary

Per plan-doc §5.1 canary-first sequencing: smallest cooperative adopter first, control-tower second (high-traffic flagship), mapp-doc-agent + recommender paired third, shopify-app last. PIM = `mapp-pim/mapp-pim`. Minimal blast radius; cooperative; well-understood CI shape.

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

- Adopter PR on `mapp-pim/mapp-pim` — separate PR on the adopter repo, opened in parallel by the operator. Scaffolder-emitted artefacts at `~/Projects/scp-scaffolds/024c-pim/` (see operator runbook below).
- ACC kernel hook install on PIM — `sudo bash scripts/install_acc_hook.sh --target-repo /path/to/pim` from ACC repo. Operator-attended.
- `enable-required-check.sh` invocation against PIM — operator-attended (bootstrap-only; refuses CI=true).
- Bake observation window — ≥1 calendar week + ≥1 Renovate-issued SHA pin bump merged + observed clean on PIM main.
- 024D (control-tower) — opens after 024C bake-clean.

## Adopter PR scope (separate PR on mapp-pim/mapp-pim)

Scaffolder output at `~/Projects/scp-scaffolds/024c-pim/`:

```
.github/workflows/policy-check-wrapper.yml   # the wrapper pinning SCP v1.0.0 @ 04523fac
.github/CODEOWNERS-snippet.txt               # append to PIM's CODEOWNERS (if any)
CASCADE-PR-BODY.md                           # canonical PR body for the adopter PR
MANIFEST.json                                # scaffolder audit emission
```

Pin: `jrnb2024/standards-control-plane-@04523fac026499de70d8559e59c6b4c4bb282a9c` (v1.0.0 tag SHA). Per `project_wp_scp_024_plan.md` memory and TF-023E-002 (still open), v1.0.0 is the current canonical pin recommendation (post-v1.2.0 SHAs trip wrapper-permissions startup_failure on user-owned private repos until 023E follow-up restructures `attest-scorecard` into a separate workflow file).

## Cascade-status decision tree (declared at slice close)

Per plan-doc §5.2 + invariant 2:

- **`onboarded`** (Renovate path): adopter PR merged + `enable-required-check.sh` invocation logged + ≥1 calendar week elapsed + ≥1 Renovate-issued SHA pin bump merged clean. Slice MUST modify `docs/reviews/WP-SCP-020/branch-protection-log.md` with invocation entry matching target.
- **`onboarded-operator-bump`** (R-024-07 fallback): same as above BUT Renovate didn't fire (e.g., PIM has Renovate disabled or cohort-not-extended) AND operator manually bumped the SHA. Slice MUST add `TF-024X-renovate-jrnb2024-mapp-pim` row to STATUS.md matching invariant 2 regex spec.
- **`blocked-on-adopter-conflict`** (invariant 10): adopter has pre-existing conflicting workflow (e.g., stale `policy-check.yml` from prior experiment). Slice MUST NOT modify branch-protection-log.md AND MUST reference `TF-024X-conflict-jrnb2024-mapp-pim` in this DISPATCH-NOTE matching invariant 2 regex spec. New sub-slice opens on conflict resolution.

## D-045 — proposed ratification text

To be filed in `docs/DECISIONS.md` at slice close:

> **D-045 | 2026-05-XX | Adopt the WP-SCP-024 per-adopter onboarding contract as estate doctrine.** Each cohort cascade slice ships (a) adopter wrapper PR on the adopter repo with SCP federation primitive SHA-pinned per VERSIONING.md (D-036) AND (b) `enable-required-check.sh` invocation entry under `docs/reviews/WP-SCP-020/branch-protection-log.md` (operator-run per D-035; refuses CI=true) AND (c) post-bake observation window of ≥1 calendar week + ≥1 Renovate-issued SHA pin bump cycle merged clean before declaring `cascade-status: onboarded` AND (d) canary-first sequencing per plan-doc §5.1 (PIM → control-tower → mapp-doc-agent + recommender paired → shopify-app). Per-adopter rollback per invariant 7 (`enable-required-check.sh --restore <pre-state.json>` + `git revert` on adopter wrapper). PIM (this slice) is the canary; per-slice closure pattern reused by 024D/024E/024F unchanged. | ACCEPTED | Closes 024A R1 MAJ-SAFE-002 + ratifies invariants 1/4/7/8 in slice-procedure form. PIM canary surfaces any federation-primitive bugs at minimal estate blast radius before 024D opens against the higher-traffic control-tower repo.

## Acceptance criteria

- [ ] Scaffolder output produced at `~/Projects/scp-scaffolds/024c-pim/` (CASCADE-PR-BODY + wrapper + CODEOWNERS snippet + MANIFEST)
- [ ] SCP-side cascade slice DISPATCH-NOTE merged (this file)
- [ ] Operator-attended: PIM adopter PR opened on mapp-pim/mapp-pim with scaffolded artefacts + CASCADE-PR-BODY.md
- [ ] Operator-attended: `install_acc_hook.sh --target-repo /path/to/pim` run on PIM checkout
- [ ] Operator-attended: PIM adopter PR merged
- [ ] Operator-attended: `enable-required-check.sh --repo mapp-pim/mapp-pim --branch main` invoked + invocation log block pasted into `docs/reviews/WP-SCP-020/branch-protection-log.md`
- [ ] Bake observation: ≥1 calendar week elapsed
- [ ] Bake observation: ≥1 Renovate-issued SHA pin bump cycle merged + observed clean on PIM main
- [ ] `cascade-status:` finalized in this DISPATCH-NOTE
- [ ] D-045 row filed in `docs/DECISIONS.md`
- [ ] STATUS.md chain entry recording slice closure
- [ ] ACCEPTANCE-CHECKLIST row 6 updated (CLOSED + cite slice closure date + cascade-status value)
- [ ] 3-lens R1 fixpoint at criterion (a) or (b)
- [ ] PR + self-merge per D-040

## Operator runbook (Phase 2 — PIM-side ceremony)

Three operator-attended steps. All bootstrap-only (`enable-required-check.sh` refuses `CI=true` / `GITHUB_ACTIONS=true`).

### Step 1: Install ACC kernel hook on PIM checkout

Prerequisite: PIM repo cloned locally at `/path/to/pim`.

```bash
cd ~/projects/acc   # ACC repo with the new --target-repo flag from PR #199
sudo bash scripts/install_acc_hook.sh --target-repo /path/to/pim
```

Validation per ACC PR #199: PIM must be a git repo, writable, and have no existing `.acc/` directory (refuse-on-existing prevents accidental clobber). ACC PR #202's direct-write fallback handles the dispatcher `active-dispatch.json` writing — verified by operator-smoke on Recommender + RI before merge.

### Step 2: Open adopter PR on mapp-pim/mapp-pim

```bash
cd /path/to/pim
git checkout -b feat/scp-federation-primitive-adoption
cp -r ~/Projects/scp-scaffolds/024c-pim/.github/workflows/policy-check-wrapper.yml .github/workflows/
cat ~/Projects/scp-scaffolds/024c-pim/.github/CODEOWNERS-snippet.txt >> .github/CODEOWNERS  # only if PIM already has a CODEOWNERS file
git add -A
git commit -m "feat: adopt SCP federation primitive (policy-check wrapper @ v1.0.0)"
git push -u origin feat/scp-federation-primitive-adoption
gh pr create --base main --head feat/scp-federation-primitive-adoption \
  --title "feat: adopt SCP federation primitive (policy-check wrapper)" \
  --body-file ~/Projects/scp-scaffolds/024c-pim/CASCADE-PR-BODY.md
```

Wait for CI to pass on the adopter PR (the wrapper should pass against PIM's existing code — purely additive). Self-merge per single-operator mode.

### Step 3: Enable required-check on PIM + log invocation

```bash
cd ~/Projects/standards-control-plane
scripts/enable-required-check.sh --repo mapp-pim/mapp-pim --branch main --plan   # dry-run first; review the PUT payload + before-state
scripts/enable-required-check.sh --repo mapp-pim/mapp-pim --branch main          # apply
```

Script emits an invocation log markdown block at the end of its output. Paste that block (verbatim, including operator name, script SHA256, before/after API JSON) into `docs/reviews/WP-SCP-020/branch-protection-log.md` as a new entry under the existing list.

Then commit the log entry to this 024C slice branch + push.

### Step 4: Bake observation

- Wait ≥1 calendar week with the required-check enabled on PIM main.
- Watch for the first Renovate-issued SHA pin bump PR on PIM (Renovate-driven preset cascade). Merge it after CI passes.
- Observe ≥1 calendar day post-Renovate-merge that PIM main CI continues passing.
- Then return to this branch + declare `cascade-status: onboarded` (or `onboarded-operator-bump` per the §5.2 fallback if Renovate didn't fire).

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
- If Renovate doesn't fire: file `TF-024X-renovate-jrnb2024-mapp-pim`
- If conflict surfaces: file `TF-024X-conflict-jrnb2024-mapp-pim` + open sub-slice

## Slice opening checklist

- [x] DISPATCH-NOTE drafted (this file)
- [x] Branch `feature/wp-scp-024-024c-pim-canary` opened off main `38ccdbe`
- [x] Scaffolder run against PIM (`~/Projects/scp-scaffolds/024c-pim/`)
- [ ] 3-lens R1 review on SCP-side stub
- [ ] Operator-attended Phase 1 (install + adopter PR + enable-required-check)
- [ ] Bake observation Phase 2 (≥1 week + Renovate cycle)
- [ ] Phase 3 closure (cascade-status declaration + D-045 + STATUS.md + R-fixpoint + self-merge)
