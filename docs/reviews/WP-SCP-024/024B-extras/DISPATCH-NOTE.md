# DISPATCH-NOTE — WP-SCP-024 slice 024B-extras

**Date:** 2026-05-10
**Branch:** `feature/wp-scp-024-024b-extras` (off main, after 024B-core merges)
**Predecessor:** WP-SCP-024 024B-core (merged at 249aa9f). Original 024B work preserved at `feature/wp-scp-024-024b-extras-parking`. Split per `docs/reviews/WP-SCP-024/024B-core/SCOPE-CORRECTION-2026-05-09.md`.
**Successor target:** WP-SCP-024 024C PIM canary cascade.
**Decision filed:** D-047.

`cascade-status: not applicable` — this slice ships rollback + break-glass + CI wiring; not a cohort cascade slice.

## Backstory

024B-core merged at 249aa9f shipped scaffolder + adopter wrapper template + cascade-status CI enforcement script (CLI) + tests. This slice (024B-extras) ships the deferred deliverables.

Carry-forward findings from extras-parking R8-archive (preserved in `feature/wp-scp-024-024b-extras-parking`):
- **R8-CORR-001** (extras-parking): cascade-status regex first-match captures trailing inline prose. **CLOSED in 024B-core** via single-pass regex with full-value capture + closed-set validation.
- **R8-CORR-002** (extras-parking): prior-entry detection runs outside restore-mode guard, emitting spurious contradiction message. **APPLIES TO 024B-EXTRAS** — ensure restore-mode guard scoping is tight.
- **R8-CORR-003** (extras-parking): TF-ticket match pattern parameterises over canonicalised slug instead of plan-doc §2 invariant 2 literal regex. **CLOSED in 024B-core** (slug canonicalisation now spec-compliant).

## Why

024B-core delivered the WHAT (scaffolder + template + CI script + tests). This slice delivers the HOW (rollback + break-glass + CI integration):

1. **`enable-required-check.sh --restore` mode** proves invariant 7's <30-min rollback SLO is real, not aspirational. Operator-interactive demo at step 7 is merge-blocking AC and is recorded through the placeholder evidence path until the operator completes the real-repo round-trip.
2. **ADOPT-001 §12.8 break-glass procedure** documents the 3-gate playbook for federation-primitive failure recovery.
3. **`.github/workflows/check-invocation-log-entry.yml`** wires the CLI script (shipped in 024B-core) into GitHub Actions so cohort cascade slices 024C–F have automated CI enforcement.

Without 024B-extras, 024C cannot open. Plan-doc §6 cohort dispatcher precondition: 024C entry gates on BOTH 024B-core + 024B-extras merging + TF-024B-REQCHECK-ENABLE-001 closure (required-status-check `check-invocation-log-entry / check-invocation-log-entry` enabled on SCP main via `gh api PATCH repos/jrnb2024/standards-control-plane-/branches/main/protection`), plus FUP-ACC-INSTALL-TARGET-REPO-001 closure.

## Scope (in)

| Deliverable | Path | Notes |
|---|---|---|
| `enable-required-check.sh --restore` mode | `scripts/enable-required-check.sh` (modify) | New `--restore <pre-state.json>` flag reverses prior branch-protection mutation per plan-doc invariant 7. Existing forward-mode unchanged. **Key behaviours per extras-parking lessons:** (a) GET-shape JSON transformed to PUT-shape via Python helper (strips `_links`, `url`, `checks`, `required_signatures`); (b) `required_signatures` reset via dedicated DELETE/POST sub-resource calls; (c) APPLY_FAIL=0 wrap pattern (failed PUT continues to log emission); (d) posture-degradation flags `--i-understand-restore-removes-admin-enforcement`, `--i-understand-restore-removes-required-checks`, `--i-understand-restore-disables-required-signatures`, `--i-understand-restore-re-enables-force-pushes`, and `--i-understand-restore-re-enables-deletions` required when before-state would remove or re-enable those protections; (e) restore log block captures actual pre-restore state via `gh api -X GET` BEFORE PUT (not just the target good-state). |
| Forward-mode safety check | `scripts/enable-required-check.sh` (modify) | Refuses forward-mode invocation against repo with no successful `policy-check` workflow run on default branch in last 60 days. **Critical (R8 + R9 lessons):** workflow lookup by `path == ".github/workflows/policy-check-wrapper.yml"` (NOT by display name); query workflow-runs API WITHOUT `&branch=` filter (PR-triggered runs have head-branch = feature branch, not default; branch filter defeats gate). `--i-understand-this-repo-has-no-prior-green-ci` flag for cold-start. |
| `--expected-wrapper-sha` flag | `scripts/enable-required-check.sh` (modify) | Validates supplied SHA against actual git tags via `gh api repos/jrnb2024/standards-control-plane-/git/refs/tags/<tag>` (NOT just 40-char shape match). Used by Gate 3 of break-glass. **Mutex with `--i-understand-this-repo-has-no-prior-green-ci`** (R7 SAFE-MAJ-001 closure). |
| ADOPT-001 §12.8 break-glass procedure | `docs/adoption/ADOPT-001-project-onboarding.md` (modify) | New §12.8 (between §12.7.15 and §13). 3-gate playbook: Gate 1 (DISABLE via `--restore` capturing pre-break SHA); Gate 2 (FIX via SHA-pin to last known-good release tag — concrete `gh api .../tags/<tag>` resolution; NOT illustrative); Gate 3 (RE-ENABLE via Renovate-bumped fix release + `--expected-wrapper-sha <release-tag-sha>` REQUIRED — not optional/advisory). SLO <30 min from operator decision to merge-restored state. WARNING + CAUTION callouts for `--i-understand-no-gate-2-verification` escape hatch. |
| `.github/workflows/check-invocation-log-entry.yml` | NEW file | CI workflow wiring for the CLI script (shipped in 024B-core). Triggers on `pull_request: [opened, synchronize, reopened]` against main with path filter targeting `docs/reviews/WP-SCP-024/024[C-Z]*/**` + `docs/reviews/WP-SCP-020/branch-protection-log.md` + `STATUS.md`. **paths: `docs/reviews/WP-SCP-024/024[C-Z]*/**`** plus explicit `branch-protection-log.md` / `STATUS.md` triggers and job-body short-circuit: if `gh pr diff --name-only` finds no cascade-slice `DISPATCH-NOTE.md`, or the resolved slice is tooling (`024A`, `024B-core`, `024B-extras`, `024G`), the job exits 0 immediately. This closes the bootstrap defect from extras-parking R7 without permitting cohort slices to bypass enforcement. SHA-pinned actions (per D-038 supply-chain hardening). Single job invokes `scripts/check-invocation-log-entry.sh --diff-base origin/main --dispatch-note <found> --status-md STATUS.md --branch-protection-log docs/reviews/WP-SCP-020/branch-protection-log.md`. Required-status-check eligible. |
| `--restore` mode tests | `tests/check_invocation_log/test_check_invocation_log_entry.sh` (modify) | Add `run_restore_case` + `make_restore_fake_gh` helpers (mirrors extras-parking patterns). Tests: GET→PUT shape transform; APPLY_FAIL pattern (failed PUT still emits log); posture-degradation flag enforcement; `required_signatures` POST + DELETE sub-resource handling; required-signatures removal acknowledgement flag; absolute path normalisation; --expected-wrapper-sha tag-validation (release-tag SHA → exit 0; arbitrary SHA → exit 2); --restore + forward-mode-flag incompatibility (--no-enforce-admins, --plan, --i-understand-this-bypasses-the-gate, --expected-wrapper-sha + --i-understand-this-repo-has-no-prior-green-ci). |
| D-047 row | `docs/DECISIONS.md` | New decision ratifying --restore mode operational contract + ADOPT-001 §12.8 break-glass procedure + CI workflow wiring. |
| STATUS.md update | `STATUS.md` | "Today's chain (2026-05-10 — slice 024B-extras)" entry. |
| **Step 7 operator-interactive demo evidence** | `docs/reviews/WP-SCP-024/024B-extras/restore-roundtrip-evidence-PLACEHOLDER.md` | **MERGE-BLOCKING.** Operator-interactive after R-fixpoint reached. Real-repo round-trip on throw-away test repo: create test repo → invoke `enable-required-check.sh` forward-mode → capture pre-state → invoke `--restore` mode → verify branch-protection API response matches captured before-state byte-for-byte → commit evidence. NOT a dry-run mock. The placeholder path is the handoff target until the operator completes the demo. Closes plan-doc invariant 7 SLO + 024A R1 MAJ-SAFE-003. |

## Scope (out)

- 024C PIM cascade kickoff. Unblocked when this slice merges + FUP-ACC-INSTALL-TARGET-REPO-001 closes.
- TF-023E-002 closure. Carry-forward.
- D-021 May-31 atomic-workday filing. Independent track.

## Carry-forward known findings (from extras-parking r8-archive)

These were surfaced in extras-parking R8 but not closed at parking time. Address proactively in this slice:

1. **R8-SAFE-001** (extras-parking): `--i-understand-no-gate-2-verification` is a backdoor; D-044 trust-model claim 'Gate 2 wrapper-SHA pin is explicit operator consent' becomes inaccurate when bypassed. Mitigation: WARNING + CAUTION callouts in ADOPT-001 §12.8 + log-block CAUTION line + D-047 rationale acknowledging escape hatch.
2. **R8-SAFE-002** (extras-parking): Gate 3 forward-mode prior-entry detection misses uncommitted Gate-1 entries. Mitigation: also check working-tree diff via `git diff HEAD branch-protection-log.md`.
3. **R8 Bootstrap** (extras-parking): workflow self-blocks introducing slice's own PR. **CLOSED in 024B-extras** via paths-ignore `024[AB]*/**` + `STATUS.md` / branch-protection-log ignores + job-body short-circuit on tooling slices or missing cascade-slice DISPATCH-NOTE.

## Acceptance criteria

- [ ] `--restore` mode logic correct (GET→PUT transform; APPLY_FAIL; posture-degradation flags; required_signatures sub-resource; pre-restore state capture; restore log block).
- [ ] Forward-mode safety check uses path-pinned workflow lookup (not display name) + no branch filter on workflow-runs API.
- [ ] `--expected-wrapper-sha` validates against git tags, and Gate 3 requires it when prior restore evidence exists.
- [ ] ADOPT-001 §12.8 break-glass procedure: 3-gate playbook with REQUIRED (not advisory) prerequisite checks; concrete tag-SHA resolution commands; WARNING + CAUTION callouts for escape hatches.
- [ ] `.github/workflows/check-invocation-log-entry.yml` wires CLI script with `paths: 024[C-Z]*/**` + explicit branch-protection-log.md / STATUS.md triggers + SHA-pinned actions.
- [ ] Tests cover all `--restore` mode behaviours + forward-mode safety check + workflow integration.
- [ ] D-047 filed.
- [ ] **Operator-interactive `--restore` real-repo round-trip demo evidence committed** (`docs/reviews/WP-SCP-024/024B-extras/restore-roundtrip-evidence-PLACEHOLDER.md`).
- [ ] 3-lens R1+R2 fixpoint (0 CRIT + 0 MAJ).
- [ ] CI green.
- [ ] Self-merge per D-040.

## Cross-repo coordination

None for 024B-extras. Cascade-start announcement files at 024C kickoff per plan-doc §5.5.

## FLA pilot safety findings reviewed

none new since 2026-05-09 — internal slice; no FLA implications.

## Protocol deviation note

Same deviation as 024B-core: direct `codex exec` / `claude -p` (kernel hook in ACC only; FUP-ACC-INSTALL-TARGET-REPO-001 still open). Compensating manual steps apply.

## Sequencing

| Phase | Work | Mode | Wall |
|---|---|---|---|
| 0 | DISPATCH-NOTE finalised + spec_paths verified | Opus | done (this draft) |
| 1 | Codex executor: --restore mode + safety check + --expected-wrapper-sha + ADOPT-001 §12.8 + workflow wiring + tests + D-047 + STATUS | Codex T3 | ~45 min |
| 2 | Manual scope check + verify-commands | Opus | ~5 min |
| 3 | 3× sequential Sonnet R1 review (64k cap) | Sonnet | ~30 min |
| 4 | Fix-rounds (expected 1-2 given carry-forward findings pre-addressed) | Codex + Sonnet | variable |
| 5 | **Operator-interactive `--restore` real-repo round-trip demo** | Operator interactive (gh PAT, throw-away test repo) | ~15 min |
| 6 | Final R-fixpoint + self-merge | Opus | ~10 min |

Target: 024B-extras merged within ~3-4 hours wall-clock + operator demo gating window.

## Reservation guard

D-047 reserved for this slice. Codex must NOT assign D-047 to anything else.

---

**Status:** ACTIVE (post-024B-core merge). Awaiting operator-interactive step-7 evidence completion and R-fixpoint review.
