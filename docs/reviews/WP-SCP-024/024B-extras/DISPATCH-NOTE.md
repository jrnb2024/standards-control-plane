# DISPATCH-NOTE — WP-SCP-024 slice 024B-extras

**Date:** 2026-05-10
**Branch:** `feature/wp-scp-024-024b-extras` (off main, after 024B-core merges)
**Predecessor:** WP-SCP-024 024B-core (merged at 249aa9f). Original 024B work preserved at `feature/wp-scp-024-024b-extras-parking`. Split per `docs/reviews/WP-SCP-024/024B-core/SCOPE-CORRECTION-2026-05-09.md`.
**Successor target:** WP-SCP-024 024C PIM canary cascade.
**Decision filed:** D-047.

`cascade-status: not applicable` — this slice ships rollback + break-glass + CI wiring; not a cohort cascade slice.

## Scope split (2026-05-11)

Per `docs/reviews/WP-SCP-024/024B-extras/SCOPE-CORRECTION-2-2026-05-11.md`, the depth-defense surfaces below move to sibling slice `024B-extras-2`: wrapper-SHA verification, canonical-context guard, set-equality verify, transform inclusion list, and annotated-tag dereferencing. This branch now carries the reduced 024B-extras-1 contract: core `--restore`, ADOPT-001 §12.8 manual Gate 3, CI workflow wiring, the retained posture-degradation flags, and 024B-extras-2 is explicitly called out below where relevant.

## Backstory

024B-core merged at 249aa9f shipped scaffolder + adopter wrapper template + cascade-status CI enforcement script (CLI) + tests. This slice (024B-extras) ships the deferred deliverables.

Carry-forward findings from extras-parking R8-archive (preserved in `feature/wp-scp-024-024b-extras-parking`):
- **R8-CORR-001** (extras-parking): cascade-status regex first-match captures trailing inline prose. **CLOSED in 024B-core** via single-pass regex with full-value capture + closed-set validation.
- **R8-CORR-002** (extras-parking): prior-entry detection runs outside restore-mode guard, emitting spurious contradiction message. **CLOSED in 024B-extras** — prior_restore_evidence_present() is called only inside check_forward_mode_safety() which is guarded by RESTORE_MODE=0 (closure verified in R22 + R25 + R27 reviews).
- **R8-CORR-003** (extras-parking): TF-ticket match pattern parameterises over canonicalised slug instead of plan-doc §2 invariant 2 literal regex. **CLOSED in 024B-core** (slug canonicalisation now spec-compliant).
- **Fix-round-22** (2026-05-11): closed the CRIT restore mock-masking defect surfaced by the step-7 demo against the real GitHub API. `transform()` now unwraps any single-key `{enabled: <bool>}` sub-object to a plain boolean, and the new restore test asserts the captured PUT body shape via `put-body.json`. TF candidate for 024B-extras-2: add the same shape assertions across the rest of the restore cases.
- **Fix-round-23** (2026-05-11): closed the CI blocker for `policy-check / scp/policy-check` (required check on main). `lib/policy_check_invocation.sh` target-selection loop originally skipped `docs/reviews/*` paths as a broad hotfix (consistent with the `tests/conflict_gate/fixtures/*` exclusion closed in WP-SCP-022 020Q). Review-archive JSON files were governance artifacts, not policy input data; their inclusion in the conftest scan was a long-standing bug that this slice's fix-round-17+ committed enough archive files to surface. TF candidate for 024B-extras-2: add per-test coverage for the target-selection filter so the narrow audit-artifact exclusion is exercised directly.
- **Fix-round-24** (2026-05-11): closes R23 SAFE-R23-001/002 by narrowing the `docs/reviews/*` hotfix to audit-artifact JSON only. `docs/reviews/rule-proposals/` remains policy-evaluable, and `.md` files under `docs/reviews/` are still handled by the existing extension filter. TF candidate for 024B-extras-2: add target-selection coverage for the narrowed path-glob arm if the slice grows further.
- **Fix-round-25** (2026-05-11): closes R22 CRIT (SB-CRIT-001 / CORR-001): posture-degradation extractions for `allow_force_pushes` + `allow_deletions` now read from `RESTORE_PAYLOAD` (transformed) instead of `RESTORE_TARGET_JSON` (raw GET shape), so the `{enabled: true}` real-API shape is correctly unwrapped before the flag-check comparison. Tests added covering `{enabled: true}` flag-check path. Also closes CORR-003 (fake-gh status=success URL assertion) + MAJ-CG-001 (DISPATCH-NOTE step-7 AC bookkeeping). This is the **3rd CRIT** surfaced by mock-masking on this slice (R9, R10, fix-round-22 PUT, fix-round-25 guard-check); future federation-primitive work should consider the real-API smoke-test job recommendation in `feedback_mock_masking_external_api.md`.
- **Fix-round-26** (2026-05-12): closes R25 governance polish — 3 doc-only MAJ + 1 MIN. `restore-roundtrip-evidence.md` placeholder filled with fix-round-22 commit SHA; plan-doc §2 invariant 2 tooling enum updated to include 024B-extras-2; STATUS.md historical chain entry row 4 annotated with current-state pointer; `scripts/check-invocation-log-entry.sh` tooling-slice enum updated to include 024B-extras-2. No code regressions; doc/CLI parity with workflow. R26 should confirm criterion (a) for merge.
- **Fix-round-27** (2026-05-12): closes R26 CORR-001 (test assertions broken by fix-round-26 enum change — codex audit ran shellcheck only, missed test suite) + CMP-001 (STATUS.md chain entries for post-cap-recovery work added). Doc-only edits + test assertion text updates. **Process lesson:** fix-round verify_commands MUST always include the test suite, not just lint. Added a note to consider as a TF for 024B-extras-2.
- **Fix-round-28** (2026-05-12): closes R27 doc/test polish — 3 REAL MAJ + 1 MIN. CORR-002 closed (new test asserts required_signatures absent from restore PUT body); CMP-001 closed (R8-CORR-002 carry-forward status updated to CLOSED); CMP-002 closed (DISPATCH-NOTE Scope (out) row now includes all 3 024C gate preconditions); MIN-002 closed (D-047 rationale tightened). DISPATCH-NOTE status footer updated. Final fix-round before merge; R28 expects criterion (a).

## Why

024B-core delivered the WHAT (scaffolder + template + CI script + tests). This slice delivers the HOW (rollback + break-glass + CI integration):

1. **`enable-required-check.sh --restore` mode** proves invariant 7's <30-min rollback SLO is real, not aspirational. Operator-interactive demo at step 7 was completed 2026-05-11 against `jrnb2024/scp-024b-extras-restore-test`; evidence at `docs/reviews/WP-SCP-024/024B-extras/restore-roundtrip-evidence.md`.
2. **ADOPT-001 §12.8 break-glass procedure** documents the 3-gate playbook for federation-primitive failure recovery.
3. **`.github/workflows/check-invocation-log-entry.yml`** wires the CLI script (shipped in 024B-core) into GitHub Actions so cohort cascade slices 024C–F have automated CI enforcement.

Without 024B-extras, 024C cannot open. Plan-doc §6 cohort dispatcher precondition: 024C entry gates on BOTH 024B-core + 024B-extras merging + TF-024B-REQCHECK-ENABLE-001 closure (required-status-check `check-invocation-log-entry / check-invocation-log-entry` enabled on SCP main via `gh api PATCH repos/jrnb2024/standards-control-plane-/branches/main/protection`), plus FUP-ACC-INSTALL-TARGET-REPO-001 closure.

## Scope (in)

| Deliverable | Path | Notes |
|---|---|---|
| `enable-required-check.sh --restore` mode | `scripts/enable-required-check.sh` (modify) | New `--restore <pre-state.json>` flag reverses prior branch-protection mutation per plan-doc invariant 7. Existing forward-mode unchanged. **Key behaviours per extras-parking lessons:** (a) GET-shape JSON transformed to PUT-shape via Python helper, with `_links`, `url`, `checks`, and `contexts_url` stripped and `required_signatures` preserved only long enough for restore-mode posture checks before the unified PUT strips it; (b) `required_signatures` reset via dedicated DELETE/POST sub-resource calls; (c) APPLY_FAIL=0 wrap pattern (failed PUT continues to log emission); (d) posture-degradation flags `--i-understand-restore-removes-admin-enforcement`, `--i-understand-restore-removes-required-checks`, `--i-understand-restore-disables-strict-mode`, `--i-understand-restore-disables-required-signatures`, `--i-understand-restore-re-enables-force-pushes`, and `--i-understand-restore-re-enables-deletions` required when before-state would remove, re-enable, or disable those protections; (e) restore log block captures actual pre-restore state via `gh api -X GET` BEFORE PUT (not just the target good-state). Fix-round-23 and Fix-round-24 narrowed the target-selection hotfix to audit-artifact JSON only after PR #113 surfaced the over-broad docs/reviews exclude. |
| Forward-mode safety check | `scripts/enable-required-check.sh` (modify) | Refuses forward-mode invocation against repo with no successful `policy-check` workflow run on default branch in last 60 days. **Critical (R8 + R9 lessons):** workflow lookup by `path == ".github/workflows/policy-check-wrapper.yml"` (NOT by display name); query workflow-runs API WITHOUT `&branch=` filter (PR-triggered runs have head-branch = feature branch, not default; branch filter defeats gate). `--i-understand-this-repo-has-no-prior-green-ci` flag for cold-start. |
| ~~`--expected-wrapper-sha` flag~~ | `scripts/enable-required-check.sh` (moved to 024B-extras-2) | Wrapper-SHA verification, annotated-tag dereferencing, and Gate 3 SHA pinning moved to the sibling slice per `SCOPE-CORRECTION-2-2026-05-11.md`. |
| ADOPT-001 §12.8 break-glass procedure | `docs/adoption/ADOPT-001-project-onboarding.md` (modify) | New §12.8 (between §12.7.15 and §13). 3-gate playbook: Gate 1 (DISABLE via `--restore` capturing pre-break SHA); Gate 2 (FIX via SHA-pin to last known-good release tag — concrete `gh api .../tags/<tag>` resolution; NOT illustrative); Gate 3 (manual RE-ENABLE after operator verification that `.github/workflows/policy-check-wrapper.yml` pins the release-tag SHA, then run `scripts/enable-required-check.sh` without `--expected-wrapper-sha`). |
| `.github/workflows/check-invocation-log-entry.yml` | NEW file | CI workflow wiring for the CLI script (shipped in 024B-core). Triggers on `pull_request: [opened, synchronize, reopened]` against main with path filter targeting `docs/reviews/WP-SCP-024/024[C-Z]*/**` + `docs/reviews/WP-SCP-020/branch-protection-log.md` + `STATUS.md`. **paths: `docs/reviews/WP-SCP-024/024[C-Z]*/**`** plus explicit `branch-protection-log.md` / `STATUS.md` triggers and job-body short-circuit: if `gh pr diff --name-only` finds no cascade-slice `DISPATCH-NOTE.md`, or the resolved slice is tooling (`024A`, `024B-core`, `024B-extras`, `024B-extras-2`, `024G`), the job exits 0 immediately. This closes the bootstrap defect from extras-parking R7 without permitting cohort slices to bypass enforcement. SHA-pinned actions (per D-038 supply-chain hardening). Single job invokes `scripts/check-invocation-log-entry.sh --diff-base origin/main --dispatch-note <found> --status-md STATUS.md --branch-protection-log docs/reviews/WP-SCP-020/branch-protection-log.md`. Required-status-check eligible. |
| `--restore` mode tests | `tests/check_invocation_log/test_check_invocation_log_entry.sh` (modify) | Add `run_restore_case` + `make_restore_fake_gh` helpers (mirrors extras-parking patterns). Tests: GET→PUT shape transform; APPLY_FAIL pattern (failed PUT still emits log); posture-degradation flag enforcement; `required_signatures` POST + DELETE sub-resource handling; required-signatures removal acknowledgement flag; strict-mode disable acknowledgement flag; absolute path normalisation; forward-mode safety; working-tree prior-entry detection; retained restore/forward mutexes; the shell harness no longer covers the carved-out wrapper-SHA / canonical-context / set-equality / inclusion-list surfaces. |
| D-047 row | `docs/DECISIONS.md` | New decision ratifying --restore mode operational contract + ADOPT-001 §12.8 break-glass procedure + CI workflow wiring. |
| STATUS.md update | `STATUS.md` | "Today's chain (2026-05-10 — slice 024B-extras)" entry. |
| **Step 7 operator-interactive demo evidence** | `docs/reviews/WP-SCP-024/024B-extras/restore-roundtrip-evidence.md` | **MERGE-BLOCKING.** Operator-interactive after R-fixpoint reached. Real-repo round-trip on throw-away test repo: create test repo → invoke `enable-required-check.sh` forward-mode → capture pre-state → invoke `--restore` mode → verify key protected fields comparison (strict, contexts, enforce_admins.enabled, required_signatures.enabled) via jq after stripping GitHub envelope fields (timestamps, _links, url, contexts_url) → commit evidence. NOT a dry-run mock. Committed after the demo completed 2026-05-11; closes TF-024B-STEP7-DEMO-001. |

## Scope (out)

- TF-024B-EXTRAS-2-SET-EQ-001 (open). The set-equality verify fix is deferred to sibling slice 024B-extras-2 and does not block 024C.
- 024C PIM cascade kickoff. Unblocked when (1) this slice merges, (2) FUP-ACC-INSTALL-TARGET-REPO-001 closes, AND (3) TF-024B-REQCHECK-ENABLE-001 closes (required-status-check `check-invocation-log-entry / check-invocation-log-entry` enabled on SCP main).
- TF-023E-002 closure. Carry-forward.
- D-021 May-31 atomic-workday filing. Independent track.

## Carry-forward known findings (from extras-parking r8-archive)

These were surfaced in extras-parking R8 but not closed at parking time. Address proactively in this slice:

1. **R8-SAFE-001** (extras-parking): `--i-understand-no-gate-2-verification` is a backdoor; D-044 trust-model claim 'Gate 2 wrapper-SHA pin is explicit operator consent' becomes inaccurate when bypassed. Mitigation: WARNING + CAUTION callouts in ADOPT-001 §12.8 + log-block CAUTION line (deferred to 024B-extras-2 with `--i-understand-no-gate-2-verification` flag per SCOPE-CORRECTION-2) + D-047 rationale acknowledging escape hatch.
2. **R8-SAFE-002** (extras-parking): Gate 3 forward-mode prior-entry detection misses uncommitted Gate-1 entries. Mitigation: also check working-tree diff via `git diff HEAD branch-protection-log.md`.
3. **R8 Bootstrap** (extras-parking): workflow self-blocks introducing slice's own PR. **CLOSED in 024B-extras** via `paths:` whitelist `docs/reviews/WP-SCP-024/024[C-Z]*/**` (cohort-only trigger; naturally excludes `024[AB]` slice prefixes) + explicit `branch-protection-log.md` / `STATUS.md` triggers + job-body short-circuit on tooling slices or missing cascade-slice DISPATCH-NOTE.

## Acceptance criteria

- [ ] `--restore` mode logic correct (GET→PUT transform; APPLY_FAIL; posture-degradation flags; required_signatures sub-resource; pre-restore state capture; restore log block).
- [ ] Forward-mode safety check uses path-pinned workflow lookup (not display name) + no branch filter on workflow-runs API.
- [ ] ADOPT-001 §12.8 break-glass procedure: 3-gate playbook with REQUIRED (not advisory) prerequisite checks; concrete tag-SHA resolution commands; manual Gate 3 verification before re-enable.
- [ ] `.github/workflows/check-invocation-log-entry.yml` wires CLI script with `paths: 024[C-Z]*/**` + explicit branch-protection-log.md / STATUS.md triggers + SHA-pinned actions.
- [ ] Tests cover all `--restore` mode behaviours + forward-mode safety check + workflow integration.
- [ ] D-047 filed.
- [x] **Operator-interactive `--restore` real-repo round-trip demo evidence committed** (`docs/reviews/WP-SCP-024/024B-extras/restore-roundtrip-evidence.md`).
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
| 1 | Codex executor: --restore mode + safety check + ADOPT-001 §12.8 + workflow wiring + tests + D-047 + STATUS | Codex T3 | ~45 min |
| 2 | Manual scope check + verify-commands | Opus | ~5 min |
| 3 | 3× sequential Sonnet R1 review (64k cap) | Sonnet | ~30 min |
| 4 | Fix-rounds (expected 1-2 for the smaller 024B-extras-1 surface) | Codex + Sonnet | variable |
| 5 | **Operator-interactive `--restore` real-repo round-trip demo** | Operator interactive (gh PAT, throw-away test repo) | ~15 min |
| 6 | Final R-fixpoint + self-merge | Opus | ~10 min |

Target: 024B-extras merged within ~3-4 hours wall-clock + operator demo gating window.

## Reservation guard

D-047 reserved for this slice. Codex must NOT assign D-047 to anything else.

---

**Status:** ACTIVE (post-fix-round-28; R27 closures landed). R-fixpoint expected at R28 confirmation, then merge.
