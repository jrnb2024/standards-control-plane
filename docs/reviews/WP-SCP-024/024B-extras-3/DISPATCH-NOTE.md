# DISPATCH-NOTE — WP-SCP-024 slice 024B-extras-3 (defensive hardening)

**Date:** 2026-05-14
**Branch:** `feature/wp-scp-024-024b-extras-3-validator-hardening` (off origin/main at `dbbebb5`)
**Predecessor:** WP-SCP-024 024B-extras-2 merged at `13572fe` on 2026-05-13 (PR #114) + governance remediation PR #115 merged at `dbbebb5` 2026-05-13.
**Decision filed:** None (no new D-NNN required — defensive hardening only; sits under D-048's depth-defense umbrella).

`cascade-status: not applicable` — tooling slice; defensive hardening of existing depth-defense surface.
`slice-type: tooling`

## Backstory

Two TFs filed during 024B-extras-2 R-cycles remained open at merge time. Both are defensive-hardening items (not security bypasses); both are bounded engineering work; neither gates 024C. Closing them in a small sibling slice keeps the 024B-extras lineage cleanly chained.

## Scope (in)

| Deliverable | Path | Notes |
|---|---|---|
| `TOP_LEVEL_TOGGLE_KEYS` validator hardening | `scripts/enable-required-check.sh` | Extend the Python validator in `validate_restore_source_json()` to assert each `TOP_LEVEL_TOGGLE_KEYS` field (`required_linear_history`, `allow_force_pushes`, `allow_deletions`, `block_creations`, `required_conversation_resolution`, `lock_branch`, `allow_fork_syncing`) present in the pre-state JSON is EITHER `bool` OR a `dict` with `set(keys()) <= {"enabled", "url"}` AND `isinstance(value.get("enabled"), bool)`. Raise with a clear diagnostic citing the offending field name on mismatch. Absent fields remain fine. Closes TF-024B-EXTRAS-2-TOGGLE-VALIDATOR-001. |
| Workflow base-branch pin | `.github/workflows/check-invocation-log-entry.yml` | Invoke `scripts/check-invocation-log-entry.sh` from `origin/main` rather than PR HEAD. Pattern: `git show origin/main:scripts/check-invocation-log-entry.sh > /tmp/check-invocation-log-entry.sh && bash /tmp/check-invocation-log-entry.sh ...` (the existing `actions/checkout@de0fac... with fetch-depth: 0` step already provides the `origin/main` ref). Closes TF-024B-EXTRAS-2-WORKFLOW-PIN-BASE-BRANCH-001. |
| RED-phase tests (committed first) | `tests/check_invocation_log/test_check_invocation_log_entry.sh` | 7 test cases asserting the validator rejects malformed toggle shapes + 2 no-regression guards. Committed at `744e4d1` (RED). After implementation, tests go GREEN. |
| STATUS.md TF closure markers | `STATUS.md` | Mark both TFs closed 2026-05-14 with slice + commit-SHA reference. |
| STATUS.md chain entry | `STATUS.md` | 2026-05-14 chain entry recording the slice. |
| DISPATCH-NOTE (this file) | `docs/reviews/WP-SCP-024/024B-extras-3/DISPATCH-NOTE.md` | Scope + checklist. |

## Scope (out)

- 024C PIM canary cascade — hard-gated on FUP-ACC-INSTALL-TARGET-REPO-001 (ACC-side, not SCP-side).
- New D-NNN — defensive hardening under D-048 umbrella; no new doctrine surface.
- Operator-attended residue (PAT rotation, throw-away repo cleanup, staging deploy) — hard environmental blockers.

## Acceptance criteria

- [ ] RED-phase tests committed first (TDD discipline)
- [ ] Validator hardening: malformed toggle shapes rejected with exit 2 + clear diagnostic
- [ ] Workflow base-branch pin: `.github/workflows/check-invocation-log-entry.yml` invokes script from `origin/main` ref
- [ ] All new tests pass (GREEN)
- [ ] Existing tests still pass (no regression)
- [ ] shellcheck clean on script + tests
- [ ] 3-lens R1 review reached fixpoint at criterion (a) or (b)
- [ ] STATUS.md TF closure markers + chain entry
- [ ] PR + self-merge per D-040

## Sequencing

| Phase | Work | Mode | Wall |
|---|---|---|---|
| 0 | Pre-flight: branch off main; RED tests committed | Manual | done (744e4d1) |
| 1 | Codex T3 single pass: validator hardening + workflow base-branch pin | Codex | ~15 min |
| 2 | 3-lens R1 review | Sonnet | ~25-30 min |
| 3 | Fix-rounds to fixpoint | Codex + Sonnet | ~1-2 hrs (expect ≤2 R-cycles given small surface) |
| 4 | Self-merge + STATUS.md closures | Opus | ~10 min |

Target: 024B-extras-3 merged within ~2-3 hours wall-clock (small surface; advisory hardening).

## Carry-forward TFs from extras-2 (status at slice opening)

- TF-024B-EXTRAS-2-TOGGLE-VALIDATOR-001 — **closes in this slice**
- TF-024B-EXTRAS-2-WORKFLOW-PIN-BASE-BRANCH-001 — **closes in this slice**

No other open TFs in the 024B-extras lineage. After this slice, the 024B-extras chain (core + extras-1 + extras-2 + extras-3) is fully closed at the tooling-slice tier.

## Slice opening checklist

- [x] DISPATCH-NOTE drafted (this file)
- [x] Branch `feature/wp-scp-024-024b-extras-3-validator-hardening` opened off main `dbbebb5`
- [x] RED-phase tests committed (744e4d1)
- [ ] Codex dispatch to implement validator hardening + workflow base-branch pin
- [ ] 3-lens R1 review
- [ ] Fix-rounds to fixpoint
- [ ] PR + self-merge per D-040

This slice does NOT gate 024C. The cohort cascade remains hard-gated on FUP-ACC-INSTALL-TARGET-REPO-001 (ACC-side).
