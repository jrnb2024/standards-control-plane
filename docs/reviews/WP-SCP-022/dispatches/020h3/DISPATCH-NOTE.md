# WP-SCP-022 slice 020H part 3 — dispatch note

**Date:** 2026-04-30 (evening, post-Threshold-A)
**Tier:** orchestrator-applied (Tier 1 only)

## Justification for not invoking Codex executor

Per `feedback_four_tier_dispatch.md` in-line escalation guidance.
This slice's substantive surface is **one Markdown sub-section
appended to an existing canonical adopter doc** —
`docs/adoption/ADOPT-001-project-onboarding.md` §12.7 (~166 lines).
No code paths, no schema additions, no rule-engine surface,
no shell scripts. The plan §4 020H part 3 row defines all 11
sub-sections and the literal text shape for the canonical wrapper
snippet, so the orchestrator's authoring task collapses to
"transcribe the plan's sub-criteria into adopter-facing prose
with verified cross-references."

Codex Tier 3 would amount to round-tripping a transcription with
all the dispatch overhead and result-parsing cost. Orchestrator-
applied + R1 × 3 is the correct posture for documentation slices
of this shape (symmetric with 020G's note, where the substantive
surface was a derived shell script).

## Slice acceptance per WP-SCP-020 §4 020H part 3

The plan §4 row enumerates 11 sub-sections plus a minimal caller
wrapper. The diff's §12.7 sub-sections map 1-to-1:

- [x] **(minimal wrapper)** §12.7.1 — verbatim canonical YAML; uses
  `jrnb2024/standards-control-plane` (with trailing dash, closing
  TF-D1-001); declares `permissions: contents: read, statuses: write`
  per D-029 / 020C.1(vi); the fork-PR refusal `if:` is documented
  as **mandatory** (closing TF-D1-002).
- [x] **(i)** §12.7.2 — Renovate preset `extends:` snippet pinned by
  ref (`#renovate/v1.0.0`) plus the customManager-marker convention
  documented inline.
- [x] **(ii)** §12.7.3 — branch-protection setup via the 020G
  helper (`scripts/enable-required-check.sh`) + `--plan` first-run
  guidance + multi-maintainer review-shape preservation note.
- [x] **(iii)** §12.7.4 — break-glass three-gate model (CODEOWNERS
  approval + sibling D-NNN row + matching waivers.json entry); names
  `scripts/verify-bypass-pairing.sh` as the enforcement script and
  `SCP-E004` as the failure mode.
- [x] **(iv)** §12.7.5 — rollback procedure (revert wrapper `@SHA`
  + tag-comment + Renovate re-run); 4-hour target per plan §4
  020H.1 iv-e; flags `rule-regression` issue template as
  forward-looking (lands in 020H.1).
- [x] **(v)** §12.7.6 — Python evaluator vs Rego scope; conflict-gate
  failure-mode `SCP-E005` named.
- [x] **(vi)** §12.7.7 — error codes `SCP-E001`..`SCP-E006` table
  with failure-mode column; codes verified emitted by
  `.github/workflows/policy-check.yml` and `conflict-gate.yml`.
- [x] **(vii)** §12.7.8 — `SECURITY.md` pointer; flagged as
  forward-looking (publishes via WP-SCP-020 §4.1 follow-up
  `SCP-073.sec`); interim guidance: contact `@jrnb2024` directly.
- [x] **(viii)** §12.7.9 — pre-commit hook snippet invoking
  `scripts/scp-policy-check`; references the SHA-locked binary
  cache + offline support.
- [x] **(ix)** §12.7.10 — adopter MUST NOT use `secrets: inherit`;
  rationale (privilege ceiling = caller's GITHUB_TOKEN).
- [x] **(x)** §12.7.11 — freshness-warning contract; flagged as
  **lands in 020H.1**, not yet emitted at v1.0.0; Renovate preset
  is the primary freshness signal until 020H.1 ships.
- [x] **(xi)** §12.7.12 — Actions-billing note; ~30s warm-start
  per PR run; cold-start adds 10–15s for binary download + SHA
  verification; ~2,000 PR runs/month on GitHub Free (2,000-minute
  budget ÷ 1 billed minute/run, since GitHub bills whole minutes
  per job rounded up — corrected per CORR-MIN-004 fix-round-1).

## Tracked-forward closures

This slice closes the three TF-D1-NNN items from the 020D1 R1 review:

- **TF-D1-001** (was COMP-MAJ-001) — repo name with trailing dash
  (`standards-control-plane-`) used consistently in §12.7.1 and
  §12.7.2. Closed.
- **TF-D1-002** (was COMP-MIN-001) — fork-PR refusal documented as
  **mandatory** in §12.7.1 with security rationale (fork PRs run
  with read-only GITHUB_TOKEN and cannot post the readback +
  workflow-context-injection risk surface). Closed.
- **TF-D1-003** (was COMP-MIN-002) — ADOPT-001 §12 federation
  appendix now exists; the 020D1 wrapper header reference is no
  longer a forward reference. Closed.

## Forward-looking flags (NOT closed by this slice)

The appendix references three artefacts that ship in subsequent slices:

- **`rule-regression` issue template** — §12.7.5; lands in 020H.1.
- **`SECURITY.md`** — §12.7.8; lands in WP-SCP-020 §4.1 follow-up
  `SCP-073.sec`.
- **Freshness-warning emit + `version-manifest.json`** — §12.7.11;
  lands in 020H.1.

Each flag is named explicitly in-line so adopters reading the
appendix at v1.0.0 do not assume the capability is live yet.

## Post-merge STATUS.md update — COMPLETED IN-FLIGHT

The two STATUS.md updates originally planned for the next slice's
PR were brought forward into this branch in fix-round-2 (commit
`f2c0c79`) per COMP-MAJ-003 + COMP-MAJ-007 closures. Specifically:

1. **Tracked-forward closure rows for TF-D1-001..003** — added in
   the new "Tracked-forward items from 020D1 (closed in 020H
   part 3)" section of STATUS.md (fix-round-2 commit `f2c0c79`).
2. **SCP-073.sec backlog row** — added to the "Post-Threshold-A
   backlog" section of STATUS.md (fix-round-2 commit `f2c0c79`).

Subsequent fix-rounds extended STATUS.md further:

- Fix-round-3 (commit `5f77763`): TF-020H3-001 closure deadline
  recorded as **2026-05-14**.
- Fix-round-5 (this commit): TF-020H3-001 also surfaced in the
  "Open scheduled follow-ups" table; TF-020H3-002 through
  TF-020H3-005 added to "Tracked-forward items from 020H part 3"
  for the four R1 completeness MIN/nit deferrals (no deadlines —
  cosmetic / v1.1 maintenance).

The only remaining post-merge action is to mark **020H part 3
landed** (with the squash-merge PR # + commit SHA) in the
"Post-Threshold-A backlog" table. That edit lands in the next
slice's PR (likely 020H.1 or 020H.2) since it requires the merge
SHA which is not knowable until merge.

## What this PR does NOT do

- Does NOT ship the freshness-warning emit (deferred to 020H.1).
- Does NOT publish `SECURITY.md` (deferred to WP-SCP-020 §4.1
  `SCP-073.sec`).
- Does NOT publish the `rule-regression` issue template
  (deferred to 020H.1).
- Does NOT introduce SCP-E007+ codes — error-code table is the
  v1.0.0-shipped set only.
- Does NOT modify any code path. Documentation-only diff.

## R1 review

3× parallel Sonnet R1 review (correctness / safety_bypass /
completeness_governance). Recurse to fixpoint per
`feedback_recursive_adversarial_review.md`.

### R1 outcome

- **Correctness** (`review-correctness.json`, ~10 min, 4 MIN + 1 nit, APPROVED_WITH_FINDINGS): all 12 correctness criteria passed. CORR-MIN-001..004 + CORR-nit-001 closed in fix-round-1 below.
- **Safety / bypass** (`review-safety.json`, ~10 min, 3 MAJ + 8 MIN + 1 nit, BLOCKED): three majors flagged the operationally-corrected single-operator break-glass description (D-033 contradiction), the rule-config alternative bypass surface, and the Regal binary SHA256 gap. SAFE-001..010 + SAFE-012 closed in fix-round-1; SAFE-011 tracked as TF-020H3-001 → slice 020H.2 with a §12.7.13 supply-chain disclosure inserted.
- **Completeness / governance** (`review-completeness.json`, timed out at 900 s on first attempt; retry at 1800 s — see retry result file).

### Fix-round-1 closures (in this branch, post-r1)

| Finding | Closure |
|---|---|
| CORR-MIN-001 (SCP-E002 description too narrow) | §12.7.7 SCP-E002 row broadened to cover all 6 invocation pre-condition paths. |
| CORR-MIN-002 (SCP-E006 ::error:: red X confusion) | §12.7.7 SCP-E006 row footnoted with the GitHub UI rendering caveat. |
| CORR-MIN-003 (D-029 cross-reference depth) | §12.7.1 permissions comment now reads `D-029 / 020C.1(vi)` to match the live wrapper. |
| CORR-MIN-004 (billing math: ~2,400 → ~2,000) | §12.7.12 corrected — GitHub bills whole minutes per job. |
| CORR-nit-001 (dangling parenthesis) | §12.7.1 comment trailing `)` removed. |
| SAFE-001 (CODEOWNERS for adopter wrapper) | §12.7.1 adds CODEOWNERS recommendation for the caller wrapper, symmetric with §11.10. |
| SAFE-002 (forward-compat secrets:inherit) | §12.7.10 second paragraph names the forward-compat risk explicitly. |
| SAFE-003 (D-033 single-operator contradiction — MAJ) | §12.7.4 rewritten with two-mode breakdown: multi-maintainer = machine-enforced Gate 1, single-operator = documentation-only Gate 1 (count=0, accepted bus-factor-1 cost). |
| SAFE-004 (rollback race vs Renovate bump PR) | §12.7.5 step 0 added — close any open `scp-federation`-labelled PR before reverting. |
| SAFE-005 (renovate/v* protection inline) | §12.7.2 adds inline D-034 disclosure + adopter-side verification command. |
| SAFE-006 (administration:write scope discipline) | §12.7.3 adds PAT-scope discipline note (single-use, immediate revocation). |
| SAFE-007 (pre-commit clone SHA pinning) | §12.7.9 adds clone-pinning instructions and divergence-invalidates note. |
| SAFE-008 (manual freshness fallback) | §12.7.11 adds quarterly manual check during the 020H.1 gap period. |
| SAFE-009 (rule-config alternative bypass — MAJ) | §12.7.4 final paragraph names rule-config as a parallel bypass surface, requires CODEOWNERS protection per §11.10, references SCP-E006 + expired-config grace ramp. |
| SAFE-010 (check-run vs commit-status context) | §12.7.3 names the check-run vs commit-status distinction; helper defaults are correct per D-033. |
| SAFE-011 (Regal SHA256 gap — MAJ) | §12.7.13 adds supply-chain-posture disclosure; tracked as **TF-020H3-001 → slice 020H.2** (post-Threshold-A backlog). NOT closed in this slice. |
| SAFE-012 (Gate 2 content-check substring loose) | §12.7.4 documents the limitation; human reviewers MUST verify D-NNN row authorization intent. |

### Tracked-forward items (TF-020H3-NNN)

- **TF-020H3-001** (was SAFE-011 MAJ, deferred-with-disclosure):
  Regal binary downloaded at hardcoded `0.40.0` without SHA256
  verification. OPA + Conftest are SHA256-verified via
  `scripts/scp-policy-check.lock`; Regal is absent from the
  lockfile. A compromised Regal binary executes in the runner
  with `GITHUB_TOKEN` access. Lint-only role bounds the bypass
  surface but the ACE primitive remains. **Closure path:** open
  slice **020H.2** as a workflow-change PR adding Regal to
  `scripts/.tool-versions` + `scripts/scp-policy-check.lock` per
  platform + `verify_sha256` call after the Regal download in
  `policy-check.yml`. (Note: "020H.2" is a NEW post-Threshold-A
  slice in the dot-N naming series; not the already-merged "020H
  part 2" promote-to-v1.0.0 slice — SCP uses `part N` for the
  v1.0.0-cut sequence and `.N` for post-Threshold-A follow-ups,
  mirroring `020H.1`.) **Closure deadline:** before v1.0.1 release
  OR within 14 calendar days of 020H part 3 merge (whichever
  comes first); for a 2026-04-30 merge, that is **2026-05-14**.
  If deferred beyond this window, escalate to user review.
  Tracked in STATUS.md "Tracked-forward items from 020H part 3"
  + this DISPATCH-NOTE.

## Files

- `docs/adoption/ADOPT-001-project-onboarding.md` — appended §12.7
  (federation primitive — adopter integration), updated through
  fix-round-1 to close all R1 correctness + safety findings except
  SAFE-011.
- `docs/reviews/WP-SCP-022/dispatches/020h3/DISPATCH-NOTE.md` —
  this file.
- `docs/reviews/WP-SCP-022/dispatches/020h3/review-{correctness,safety,completeness,completeness-r1retry}.json`
  — R1 dispatch evidence.
