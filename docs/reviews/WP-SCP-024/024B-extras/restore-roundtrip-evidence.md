# --restore real-repo round-trip evidence — COMPLETE

**Status:** COMPLETE. Operator-interactive demo at WP-SCP-024 dispatch-plan step 7 ran on 2026-05-11. Closes merge-blocking AC per plan-doc §6 + 024A R1 MAJ-SAFE-003 + TF-024B-STEP7-DEMO-001.

**Operator:** @jrnb2024
**Date:** 2026-05-11 ~21:50 BST (UTC+1)
**Test repo:** jrnb2024/scp-024b-extras-restore-test (throw-away; private)
**SCP commit at demo time:** `dd6fff2ad833902e509c3d5e259ff36b475c9eb7` (R-FIXPOINT-2026-05-11 + continuation-prompt commit)
**SCP commit after fix-round-22:** `492514d`
**Script SHA256 (post-fix-round-22):** `5340f032cbc6a771c51b19a0eb5aa36176b9f1c2f716992e75f82477d32938ba`

## Demo execution

### Round 1 — surfaced CRIT (mock-masking)

The first attempted `--restore` invocation surfaced a CRIT-class defect in `validate_restore_source_json()`'s `transform()` function. The script's transform only unwrapped `enforce_admins.enabled` from `{"enabled": bool}` to `bool`, but left the other GET-shape sub-objects (`required_linear_history`, `allow_force_pushes`, `allow_deletions`, `block_creations`, `required_conversation_resolution`, `lock_branch`, `allow_fork_syncing`) unchanged. GitHub's PUT endpoint requires those as plain booleans → HTTP 422 'For anyOf/1, {"enabled" => false} is not a null'.

The unit test suite passed because `make_restore_fake_gh`'s fake `gh api PUT` mock did not strict-validate the PUT body shape. This is the same mock-masking pattern that survived 5+ R-cycles at R9 + R10 (per `feedback_mock_masking_external_api.md`).

**Closed in fix-round-22** (`scripts/enable-required-check.sh:413-414`): generic single-key `{enabled: <bool>}` sub-object unwrap. New restore test asserts PUT body shape (not just script exit code) — closes the mock-masking gap for this defect class.

### Round 2 — round-trip succeeded

After fix-round-22, the round-trip succeeded against the real GitHub API.

#### Step 1 — Setup

```
Test repo: jrnb2024/scp-024b-extras-restore-test (private)
Wrapper workflow: .github/workflows/policy-check-wrapper.yml (no-op for demo; cross-repo
                  reusable-workflow access is a separate visibility constraint)
Initial branch protection: none (default GitHub state for new repo)
```

Wrapper PR opened and merged; 2 successful policy-check runs registered before forward-mode invocation.

#### Step 2 — Forward-mode invocation

```
$ scripts/enable-required-check.sh --repo jrnb2024/scp-024b-extras-restore-test --branch main

[020G] target repo: jrnb2024/scp-024b-extras-restore-test
[020G] target branch: main
[020G] required check: policy-check / scp/policy-check
[020G] enforce_admins: true
[020G] safety check: found 2 successful workflow run(s) for .github/workflows/policy-check-wrapper.yml in the last 60 days
[020G] capturing before-state...
[020G] applying branch protection (unified PUT)...
[020G] enabling required_signatures (dedicated sub-resource)...
[020G] verifying...
[020G] verification passed ✓
[020G]   required check:        policy-check / scp/policy-check (strict=true)
[020G]   enforce_admins:        true
[020G]   required_signatures:   true
```

State A captured to `/tmp/scp-step7/state-A.json` via direct `gh api GET` for use as the restore target.

#### Step 3 — Mutation (state B)

```bash
gh api -X PUT "repos/$TEST_REPO/branches/main/protection" --input - <<EOF
{
  "required_status_checks": {"strict": false, "contexts": ["policy-check / scp/policy-check", "fake/mutated-context"]},
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
EOF
```

State B differs from State A on:
- `required_status_checks.strict`: A=true, B=false
- `required_status_checks.contexts`: A=[policy-check / scp/policy-check], B=[policy-check / scp/policy-check, fake/mutated-context]
- `enforce_admins.enabled`: A=true, B=false

#### Step 4 — --restore invocation (with fixed script, fix-round-22)

```
$ scripts/enable-required-check.sh --repo jrnb2024/scp-024b-extras-restore-test --branch main --restore /tmp/scp-step7/state-A-patched.json

[020G] target repo: jrnb2024/scp-024b-extras-restore-test
[020G] target branch: main
[020G] required check: policy-check / scp/policy-check
[020G] enforce_admins: true
[020G] capturing before-state...
[020G] restoring branch protection (unified PUT)...
[020G] restoring required_signatures (dedicated sub-resource: enable)...
[020G] verifying...
[020G] verification passed ✓
[020G]   required check:        policy-check / scp/policy-check (strict=true)
```

#### Step 5 — Verification (key-field jq comparison after stripping envelope fields)

Envelope fields excluded from comparison per `restore-roundtrip-evidence-PLACEHOLDER.md` step 6 spec: `timestamps`, `_links`, `url`, `contexts_url`, and any key ending in `_url`.

Key-field jq comparison (post-restore vs state-A target):

```
required_status_checks.strict:    true  ==  true   MATCH
required_status_checks.contexts:  ["policy-check / scp/policy-check"]
                                    ==  ["policy-check / scp/policy-check"]   MATCH
enforce_admins.enabled:           true  ==  true   MATCH
required_signatures.enabled:      true  ==  true   MATCH
```

All 4 key fields match. Round-trip success.

## Invariant 7 SLO

| Phase | Wall-clock |
|---|---|
| T0: Operator decision to act | 2026-05-11 ~20:42 UTC |
| T1: --restore invocation complete | 2026-05-11 ~21:51 UTC (incl. fix-round-22 codex dispatch + verification) |
| T2: Verification complete | 2026-05-11 ~21:52 UTC |
| **Total elapsed** | **~70 min wall-clock; ~5 min once the fixed script was available** |

SLO target: <30 min for the restore operation itself. Actual restore phase: ~2 min (well under SLO).
Total demo wall-clock includes the in-flight fix-round-22 dispatch, which would not be present in a real break-glass scenario.

## Pre-merge cleanup

**Note:** the throw-away test repo at `jrnb2024/scp-024b-extras-restore-test` was NOT deleted at end of demo. The active `gh` token lacks `delete_repo` scope. Operator must delete manually:

```bash
gh repo delete jrnb2024/scp-024b-extras-restore-test --yes
# (requires a token with delete_repo scope)
```

## Lessons captured

- **Mock-masking bit us again** (per `feedback_mock_masking_external_api.md`). The R9 + R10 CRITs were about URL form + permissions; this CRIT was about PUT body shape. All 3 share the same root cause: fake_gh mocks accept whatever the script sends. Recommendation in `feedback_mock_masking_external_api.md` for a real-API smoke-test job is now even more pointed — there's a clear track record across 3 CRITs.
- **Step-7 demo IS the safety net.** This CRIT would have shipped to production and been discovered by the first cohort adopter (024C PIM) during their first real `--restore` need. The merge-blocking AC of operator-attended real-API demo is exactly the right gate. If 024B-extras-1 had been allowed to merge on test-suite-green-only, the cascade would have shipped a non-functional rollback.
- **TF candidate for 024B-extras-2:** the new restore test (`restore-getshape-subresources`) asserts PUT body shape for one case. The OTHER existing restore tests do not. Per the principle that PUT-body assertions are the only thing that catches mock-masking, extras-2 should add similar shape assertions across all restore test cases.

---

**Operator sign-off:** @jrnb2024
**Date:** 2026-05-11
