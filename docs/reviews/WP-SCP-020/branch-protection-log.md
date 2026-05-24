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

