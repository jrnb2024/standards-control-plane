# Branch-protection invocation log

This log captures every invocation of `scripts/enable-required-check.sh`
against an adopter repo. The log commit is part of the invocation
procedure per WP-SCP-020 §4 020G(iii); without the log entry the
apply is unrecorded.

## Format

Each invocation appends a new section under "## Invocations" with:
- Timestamp (ISO 8601 UTC).
- Target repo + branch.
- Operator handle.
- Script SHA at invocation time (so a future audit can correlate
  the apply with the script source as it stood that day).
- The exact PUT payload applied.
- Before-state and after-state of the GitHub branch-protection
  configuration.
- `preserve-existing-contexts: {true|false}` — added in WP-SCP-024
  024C fix-round-4. Indicates whether the invocation merged the
  canonical context into the target branch's pre-existing
  required_status_checks.contexts (`true`, brownfield) or REPLACED
  them with a single-element list (`false`, greenfield default).
  Audit-grep this field to enumerate brownfield-adopter invocations.
- `skip-required-signatures: {true|false}` — added in WP-SCP-024
  024C fix-round-4. Indicates whether the invocation skipped the
  dedicated POST to `.../required_signatures`. When `true`, the
  adopter MUST have an open `FUP-<ADOPTER>-COMMIT-SIGNING` row in
  their governance tracker (per ADOPT-001 §12.7.3); audit-grep
  this field to enumerate adopters with deferred commit-signing
  enforcement.
- Optional CAUTION lines — emitted by the script when a posture-
  degrading flag was used (`--no-enforce-admins`,
  `--skip-required-signatures`, or the destructive context-
  replacement default detected with pre-existing non-canonical
  contexts). CAUTION lines render directly into the entry above
  the PUT-payload block so they are visible in the committed log.

## Why log on the SCP repo

The federation primitive is owned by SCP. Adopter-side branch
protection is a downstream effect of pinning the SCP wrapper —
the audit trail belongs at the federation source, not at the
adopter. This is symmetric with `docs/security/branch-protection.md`
(which documents SCP-self's own protections) and `docs/DECISIONS.md`
(which carries the federation-primitive decisions).

## Invocations

<!-- new entries appended below this line by `enable-required-check.sh` operators -->

_(no invocations recorded yet — this slice ships the log file
alongside the script; first real invocation against an adopter
will populate the first entry. Estate cascade rollout = WP-SCP-024.)_

---

## Invocation log entry

Append the block below to docs/reviews/WP-SCP-020/branch-protection-log.md on the SCP repo, commit on
a feature branch, open PR, merge:

~~~markdown
### 2026-05-17T18:07:27Z — jrnb2024/mapp-pim@main

- **Operator:** @jrnb2024
- **Script SHA256:** `0a1b596a56f081ea7eeac471abc18dc88d3736996e375eda6e6e78e05df5e06c` (hash of executed file)
- **Script git SHA:** `ca287664bee94830c674b817409f113dd4385195` (last committed; "not-in-git-clone" if N/A)
- **Required check:** `policy-check / scp/policy-check`
- **enforce_admins:** true
- **preserve-existing-contexts:** true
- **skip-required-signatures:** false
- **destructive-contexts-warning:** false
- **Plan-only:** no
- **PUT payload applied:**
```json
{
    "required_status_checks": {
        "strict": true,
        "contexts": [
            "contract-tests",
            "lint",
            "playwright-uat",
            "policy-check / scp/policy-check",
            "test-platform"
        ]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_pull_request_reviews",
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": false,
        "require_last_push_approval": false,
        "required_approving_review_count": 0
    },
    "restrictions": null,
    "required_linear_history": false,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "block_creations": false,
    "required_conversation_resolution": false,
    "lock_branch": false,
    "allow_fork_syncing": false
}
```
- **Before:**
```json
{
    "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection",
    "required_status_checks": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_status_checks",
        "strict": true,
        "contexts": [
            "lint",
            "test-platform",
            "contract-tests",
            "playwright-uat"
        ],
        "contexts_url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_status_checks/contexts",
        "checks": [
            {
                "context": "lint",
                "app_id": null
            },
            {
                "context": "test-platform",
                "app_id": null
            },
            {
                "context": "contract-tests",
                "app_id": null
            },
            {
                "context": "playwright-uat",
                "app_id": 15368
            }
        ]
    },
    "required_pull_request_reviews": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_pull_request_reviews",
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": false,
        "require_last_push_approval": false,
        "required_approving_review_count": 0
    },
    "required_signatures": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_signatures",
        "enabled": false
    },
    "enforce_admins": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/enforce_admins",
        "enabled": false
    },
    "required_linear_history": {
        "enabled": true
    },
    "allow_force_pushes": {
        "enabled": false
    },
    "allow_deletions": {
        "enabled": false
    },
    "block_creations": {
        "enabled": false
    },
    "required_conversation_resolution": {
        "enabled": false
    },
    "lock_branch": {
        "enabled": false
    },
    "allow_fork_syncing": {
        "enabled": false
    }
}
```
- **After:**
```json
{
    "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection",
    "required_status_checks": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_status_checks",
        "strict": true,
        "contexts": [
            "lint",
            "test-platform",
            "contract-tests",
            "playwright-uat",
            "policy-check / scp/policy-check"
        ],
        "contexts_url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_status_checks/contexts",
        "checks": [
            {
                "context": "lint",
                "app_id": null
            },
            {
                "context": "test-platform",
                "app_id": null
            },
            {
                "context": "contract-tests",
                "app_id": null
            },
            {
                "context": "playwright-uat",
                "app_id": 15368
            },
            {
                "context": "policy-check / scp/policy-check",
                "app_id": null
            }
        ]
    },
    "required_pull_request_reviews": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_pull_request_reviews",
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": false,
        "require_last_push_approval": false,
        "required_approving_review_count": 0
    },
    "required_signatures": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_signatures",
        "enabled": true
    },
    "enforce_admins": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/enforce_admins",
        "enabled": true
    },
    "required_linear_history": {
        "enabled": false
    },
    "allow_force_pushes": {
        "enabled": false
    },
    "allow_deletions": {
        "enabled": false
    },
    "block_creations": {
        "enabled": false
    },
    "required_conversation_resolution": {
        "enabled": false
    },
    "lock_branch": {
        "enabled": false
    },
    "allow_fork_syncing": {
        "enabled": false
    }
}
```
~~~

The log commit is part of the invocation procedure per WP-SCP-020
§4 020G(iii) + D-035; without it the apply is unrecorded.

## Live-state verification (Phase 1 close)

Output of `gh api repos/jrnb2024/mapp-pim/branches/main/protection` (post-apply, out-of-band read per R1 SAF-001 closure):

```json
{
  "required_status_checks": [
    "lint",
    "test-platform",
    "contract-tests",
    "playwright-uat",
    "policy-check / scp/policy-check"
  ],
  "enforce_admins": true,
  "required_signatures": true,
  "required_pull_request_reviews": 0
}
```

### 2026-05-24T00:24:11Z — jrnb2024/mapp-pim@main

- **Operator:** @jrnb2024
- **Script SHA256:** `0a1b596a56f081ea7eeac471abc18dc88d3736996e375eda6e6e78e05df5e06c` (hash of executed file)
- **Script git SHA:** `710d80f361a83f9ad0e156ed92b4f6d40e8f3a55` (last committed; "not-in-git-clone" if N/A)
- **Required check:** `policy-check / scp/policy-check`
- **enforce_admins:** true
- **preserve-existing-contexts:** true
- **skip-required-signatures:** false
- **destructive-contexts-warning:** false
- **Plan-only:** no
- **PUT payload applied:**
```json
{
    "required_status_checks": {
        "strict": true,
        "contexts": [
            "contract-tests",
            "lint",
            "playwright-uat",
            "policy-check / scp/policy-check",
            "test-platform"
        ]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_pull_request_reviews",
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": false,
        "require_last_push_approval": false,
        "required_approving_review_count": 0
    },
    "restrictions": null,
    "required_linear_history": false,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "block_creations": false,
    "required_conversation_resolution": false,
    "lock_branch": false,
    "allow_fork_syncing": false
}
```
- **Before:**
```json
{
    "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection",
    "required_status_checks": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_status_checks",
        "strict": true,
        "contexts": [
            "lint",
            "test-platform",
            "contract-tests",
            "playwright-uat"
        ],
        "contexts_url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_status_checks/contexts",
        "checks": [
            {
                "context": "lint",
                "app_id": 15368
            },
            {
                "context": "test-platform",
                "app_id": 15368
            },
            {
                "context": "contract-tests",
                "app_id": 15368
            },
            {
                "context": "playwright-uat",
                "app_id": 15368
            }
        ]
    },
    "required_pull_request_reviews": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_pull_request_reviews",
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": false,
        "require_last_push_approval": false,
        "required_approving_review_count": 0
    },
    "required_signatures": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_signatures",
        "enabled": true
    },
    "enforce_admins": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/enforce_admins",
        "enabled": true
    },
    "required_linear_history": {
        "enabled": false
    },
    "allow_force_pushes": {
        "enabled": false
    },
    "allow_deletions": {
        "enabled": false
    },
    "block_creations": {
        "enabled": false
    },
    "required_conversation_resolution": {
        "enabled": false
    },
    "lock_branch": {
        "enabled": false
    },
    "allow_fork_syncing": {
        "enabled": false
    }
}
```
- **After:**
```json
{
    "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection",
    "required_status_checks": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_status_checks",
        "strict": true,
        "contexts": [
            "lint",
            "test-platform",
            "contract-tests",
            "playwright-uat",
            "policy-check / scp/policy-check"
        ],
        "contexts_url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_status_checks/contexts",
        "checks": [
            {
                "context": "lint",
                "app_id": 15368
            },
            {
                "context": "test-platform",
                "app_id": 15368
            },
            {
                "context": "contract-tests",
                "app_id": 15368
            },
            {
                "context": "playwright-uat",
                "app_id": 15368
            },
            {
                "context": "policy-check / scp/policy-check",
                "app_id": 15368
            }
        ]
    },
    "required_pull_request_reviews": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_pull_request_reviews",
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": false,
        "require_last_push_approval": false,
        "required_approving_review_count": 0
    },
    "required_signatures": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/required_signatures",
        "enabled": true
    },
    "enforce_admins": {
        "url": "https://api.github.com/repos/jrnb2024/mapp-pim/branches/main/protection/enforce_admins",
        "enabled": true
    },
    "required_linear_history": {
        "enabled": false
    },
    "allow_force_pushes": {
        "enabled": false
    },
    "allow_deletions": {
        "enabled": false
    },
    "block_creations": {
        "enabled": false
    },
    "required_conversation_resolution": {
        "enabled": false
    },
    "lock_branch": {
        "enabled": false
    },
    "allow_fork_syncing": {
        "enabled": false
    }
}
```


### 2026-05-25T16:39:32Z — jrnb2024/control-tower@main

- **Operator:** @jrnb2024
- **Script SHA256:** `6619139051a2c04641bb884f16844c86acfdc40cd39dddc7a093e9c345aa1cc4` (hash of executed file)
- **Script git SHA:** `15a56d60b179a1d0bb41f0e4996aa19f0ed5bcb8` (last committed)
- **Required check:** `policy-check / scp/policy-check`
- **enforce_admins:** true
- **preserve-existing-contexts:** true
- **skip-required-signatures:** false
- **destructive-contexts-warning:** false
- **Plan-only:** no
- **WP-SCP-024 slice:** 024D (control-tower; cohort adopter #2)
- **PUT payload applied:**

```json
{
    "required_status_checks": {
        "strict": true,
        "contexts": [
            "ok",
            "policy-check / scp/policy-check",
            "validate PR body"
        ]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": {
        "url": "https://api.github.com/repos/jrnb2024/control-tower/branches/main/protection/required_pull_request_reviews",
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": false,
        "require_last_push_approval": false,
        "required_approving_review_count": 0
    },
    "restrictions": null,
    "required_linear_history": false,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "block_creations": false,
    "required_conversation_resolution": false,
    "lock_branch": false,
    "allow_fork_syncing": false
}
```

- **Before:**

```json
{
    "url": "https://api.github.com/repos/jrnb2024/control-tower/branches/main/protection",
    "required_status_checks": {
        "strict": true,
        "contexts": [
            "ok",
            "validate PR body"
        ],
        "checks": [
            {"context": "ok", "app_id": 15368},
            {"context": "validate PR body", "app_id": 15368}
        ]
    },
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": false,
        "require_last_push_approval": false,
        "required_approving_review_count": 0
    },
    "required_signatures": {"enabled": false},
    "enforce_admins": {"enabled": true},
    "required_linear_history": {"enabled": true},
    "allow_force_pushes": {"enabled": false},
    "allow_deletions": {"enabled": false},
    "block_creations": {"enabled": false},
    "required_conversation_resolution": {"enabled": true},
    "lock_branch": {"enabled": false},
    "allow_fork_syncing": {"enabled": false}
}
```

- **After:**

```json
{
    "url": "https://api.github.com/repos/jrnb2024/control-tower/branches/main/protection",
    "required_status_checks": {
        "strict": true,
        "contexts": [
            "ok",
            "validate PR body",
            "policy-check / scp/policy-check"
        ],
        "checks": [
            {"context": "ok", "app_id": 15368},
            {"context": "validate PR body", "app_id": 15368},
            {"context": "policy-check / scp/policy-check", "app_id": 15368}
        ]
    },
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": false,
        "require_last_push_approval": false,
        "required_approving_review_count": 0
    },
    "required_signatures": {"enabled": true},
    "enforce_admins": {"enabled": true},
    "required_linear_history": {"enabled": false},
    "allow_force_pushes": {"enabled": false},
    "allow_deletions": {"enabled": false},
    "block_creations": {"enabled": false},
    "required_conversation_resolution": {"enabled": false},
    "lock_branch": {"enabled": false},
    "allow_fork_syncing": {"enabled": false}
}
```

- **Side-effect observation (operator-flagged):** the unified PUT preserved the contexts list per `--preserve-existing-contexts` but DID NOT preserve CT's pre-existing `required_linear_history: true` + `required_conversation_resolution: true` settings (both flipped to false). `required_signatures: false → true` is intentional per D-029 invariant; the other two are unintentional regressions of CT-side preferences. Operator restored both via post-script `gh api PATCH` 2026-05-25T16:42Z. Filed forward as **FUP-WP-SCP-020-ENABLE-REQUIRED-CHECK-PRESERVE-EXTENDED-001 (P2)** in `docs/BACKLOG.md` Phase 12 — the `--preserve-existing-contexts` flag should extend to preserving other pre-existing branch-protection settings the script doesn't explicitly mutate. Sequenced for closure ahead of cohort onboarding 024E (mapp-doc-agent + recommender paired).

### 2026-05-25T20:19:52Z — jrnb2024/mapp-doc-agent@main

- **Operator:** @jrnb2024
- **Script SHA256:** `dc0436264bf2fe093a8a8491c83c5ac1e71a41ada98eeace1a47e9f98bd6939b` (hash of executed file)
- **Script git SHA:** `74c753aaf35ba68e561fe9298eef642b114345cf` (post FUP-WP-SCP-020-ENABLE-REQUIRED-CHECK-PRESERVE-EXTENDED-001 closure / PR #162)
- **Required check:** `policy-check / scp/policy-check`
- **enforce_admins:** true
- **preserve-existing-contexts:** true
- **skip-required-signatures:** false
- **destructive-contexts-warning:** false
- **Plan-only:** no
- **PUT payload applied:**

```json
{
    "required_status_checks": {
        "strict": true,
        "contexts": [
            "policy-check / scp/policy-check",
            "test"
        ]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": null,
    "restrictions": null,
    "required_linear_history": true,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "block_creations": false,
    "required_conversation_resolution": false,
    "lock_branch": false,
    "allow_fork_syncing": false
}
```

- **Before:** required-status-checks contexts = `["test"]`; `enforce_admins: false`; `required_signatures: false`; `required_linear_history: true`. Full Before JSON captured at `gh api repos/jrnb2024/mapp-doc-agent/branches/main/protection` snapshot at 2026-05-25T20:19:52Z.
- **After:** required-status-checks contexts = `["test", "policy-check / scp/policy-check"]`; `enforce_admins: true`; `required_signatures: true`; `required_linear_history: true` (preserved correctly per FUP-WP-SCP-020-ENABLE-REQUIRED-CHECK-PRESERVE-EXTENDED-001 closure).

- **Side-effect observation (operator-flagged):** Required-check flip happened BEFORE the smoke-test PR (#58) verified GREEN. PR #57 (wrapper landing) had a silent GHA startup_failure due to a wrapper trailing-dash regression (the scaffolder template inherited the pre-rename repo name `jrnb2024/standards-control-plane-`); the failure didn't surface in `gh pr checks` rollup the way a normal FAILURE would, and the wrapper merged with the bug. Smoke-test PR #58 surfaced the bug ~6 min after the required-check flip; wrapper fix-up commit landed GREEN at 2026-05-25T20:26:30Z. Mapp-doc-agent main was effectively hard-blocked for that ~6 min window. Filed forward as **FUP-WP-SCP-024-SMOKE-TEST-BEFORE-FLIP-001 (P2)** + **FUP-WP-SCP-024-SCAFFOLDER-RENAME-SWEEP-001 (P2)** in BACKLOG.md Phase 12. Scaffolder template fix shipped same session via SCP PR #170 (`c7266fb`).

### 2026-06-30T09:06:18Z — jrnb2024/mapp-size-allocation@main

- **Operator:** @jrnb2024
- **Script SHA256:** `0ab1ed6a3598f116b7acca6624ee6dd6a1d529140fed47902149c8e61eabced6`
- **Script git SHA:** `34371ea5536df2709bb54e5b92ac6df4e87d70af`
- **Required check:** `policy-check / scp/policy-check`
- **enforce_admins:** true · **preserve-existing-contexts:** true · **skip-required-signatures:** false · **Plan-only:** no
- **Context:** REACH-1 adoption-cascade **pilot-1** (first new adopter since the original 3; SCP reach review 2026-06-29). Wrapper landed warn-mode via adopter PR #233; `scorecard-emit: false` (private user-owned repo — `actions/attest` build-provenance unavailable).
- **CAUTION (smoke-test bypass — justified):** flipped with `--skip-smoke-test-i-understand-this-blocks-main`. The smoke-test wants a GREEN `policy-check-wrapper.yml` run on `main`, but the canonical wrapper is `pull_request`-only and never runs on `main` (mapp-pim / control-tower likewise have zero main-branch wrapper runs; they predate the guard). Bypass is safe here: adopter PR #233's `policy-check` ran **GREEN** on the exact content squash-merged to main — the precise "no silent startup_failure" evidence the smoke-test seeks, just on the PR ref. The script's own pre-check also found 30 successful wrapper runs in 60 days. Tooling inconsistency filed forward (smoke-test should accept a green PR run, or the wrapper template should run on main).
- **dismiss_stale_reviews warning:** N/A — single-operator adopter, `required_approving_review_count=0` (D-033); script's multi-maintainer warning ignorable per its own note.
- **Before:** contexts = `["ok"]`; `enforce_admins: false`; `required_signatures: false`; `strict: true`.
- **After:** contexts = `["ok", "policy-check / scp/policy-check"]`; `enforce_admins: true`; `required_signatures: true`; `strict: true`. Verification passed ✓. Full PUT/Before/After JSON in the apply output (2026-06-30T09:06:18Z). **→ mapp-size-allocation is the first enforced REACH-1 cascade adopter.**

### 2026-06-30T19:16:54Z — jrnb2024/ACC@main

- **Operator:** @jrnb2024
- **Script SHA256:** `4fc86c7cf7a572154425110177fa2e311e2e5f73ad9412d29f498267c2aa9a04` · **Script git SHA:** `9e3bbdc50fb67bff30c235e2c3dad1230c2401a1`
- **Required check:** `policy-check / scp/policy-check` · **enforce_admins:** true · **preserve-existing-contexts:** true · **skip-required-signatures:** false · **Plan-only:** no
- **Context:** REACH-1 cascade adopter #2 (the **ACC repo** — the acc-hook authority dogfooding SCP gating). Wrapper landed warm via PR #428 after acc repaired its own `backend (3.13)` build blocker (FastAPI 0.137 `include_router` introspection drift; acc PR #429 pinned `fastapi<0.137` + committed a CI lock).
- **🔑 First CLEAN flip (no smoke-test override):** the smoke-test-before-flip passed via the new any-branch fallback (#229, FUP-WP-SCP-024-SMOKE-TEST-BEFORE-FLIP-001 catch-22 fix) — *"no GREEN run on main (PR-only wrapper never runs there), but 2 GREEN wrapper run(s) found on other branches; proceeding."* No `--skip-smoke-test-i-understand-this-blocks-main` needed (unlike SA/the prior 3 adopters). Validates the fallback end-to-end on a real adopter.
- **required_signatures:** enabled — verified safe (acc commits GitHub-verified-signed; no Renovate; automation never commits).
- **Before:** contexts = `["dogfood-dry-run","closure-format","kernel-dangerous-label-enforce","backend (3.13)","frontend","install-ceremony-e2e"]`; `enforce_admins: true`; `required_signatures: false`; `strict: false`.
- **After:** contexts = the 6 above **+ `policy-check / scp/policy-check`**; `enforce_admins: true`; `required_signatures: true`; `strict: true` (preserve-existing-contexts kept all 6). Verification passed ✓. Full PUT/Before/After JSON in the apply output (2026-06-30T19:16:54Z). **→ ACC is the 6th enforced SCP adopter; REACH-1 cascade #2 complete.**

### 2026-06-30T20:49:24Z — jrnb2024/mf-intent-os@main (Recommender / Intent-OS)

- **Operator:** @jrnb2024
- **Script SHA256:** `4fc86c7cf7a572154425110177fa2e311e2e5f73ad9412d29f498267c2aa9a04` · **Script git SHA:** `9e3bbdc50fb67bff30c235e2c3dad1230c2401a1`
- **Required check:** `policy-check / scp/policy-check` · **enforce_admins:** true · **preserve-existing-contexts:** true · **skip-required-signatures:** false · **Plan-only:** no
- **Context:** REACH-1 cascade adopter #4 (Recommender, repo `mf-intent-os`). Federation secrets were ALREADY present on this repo → zero operator prereqs. Clean flip via the smoke-test any-branch fallback (#229), no override.
- **⚠️ Brief half-apply + immediate resolution (audit honesty):** the standalone one-line flip was run BEFORE wrapper PR #325 merged (its slow `build-and-smoke` was still finishing), so `policy-check` was momentarily required without the wrapper on main. Resolved at once by merging #325 (all 5 required checks green, 0 behind) → wrapper on main → consistent. 🔑 **LESSON reinforced: run the flip ONLY after the wrapper PR is merged.** The `onboard-*.sh` scripts enforce this ordering (merge-success guard); the standalone one-line flip does not — future Recommender-style "secrets already set" onboards should still merge first.
- **required_signatures:** enabled — verified safe (signed commits, no Renovate). `--preserve-existing-contexts` kept `test`/`build-and-smoke`/`guard`/`manifest-verify` + `required_linear_history: true` + `required_conversation_resolution: true`.
- **Before:** contexts = `["test","build-and-smoke","guard","manifest-verify"]`; `enforce_admins: true`; `required_signatures: false`; `strict: true`.
- **After:** the 4 above **+ `policy-check / scp/policy-check`**; `required_signatures: true`; `strict: true`. Verification passed ✓. Full PUT/Before/After JSON in the apply output (2026-06-30T20:49:24Z). **→ Recommender (mf-intent-os) is the 7th enforced SCP adopter.**
