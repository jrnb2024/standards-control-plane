#!/usr/bin/env bash
# shellcheck shell=bash
# WP-SCP-020 slice 020G — adopter-side branch-protection helper.
#
# Configures a downstream adopter repo's default branch with the
# canonical SCP federation primitive required-status-check posture:
#
#   - required_status_checks.contexts = ["${SCP_REQUIRED_CONTEXT}"]
#     (default: "policy-check / scp/policy-check" — the rendered
#     check-run name from the canonical adopter wrapper)
#   - required_status_checks.strict = true (PR must be up-to-date
#     with base before evaluation)
#   - enforce_admins = true (no admin bypass)
#   - required_signatures = true (every commit verified-signed,
#     applied via dedicated sub-resource endpoint)
#
# This is the adopter-side analogue of SCP-self's
# `scripts/configure-020d2-required-check.sh`. Adopters with
# multi-maintainer teams MAY enable additional review gates;
# the script preserves any existing required_pull_request_reviews
# rather than nulling them out (per 020G R1 SAF-002 closure).
#
# ## Bootstrap-only — NOT run unattended
#
# This script writes durable state to a third-party repository
# (the adopter's branch protection). It refuses to run when CI=true
# or GITHUB_ACTIONS=true (the two standard CI env vars). Operator
# attention is required to:
#   - confirm the target via --plan first
#   - review the diff between before-state and after-state
#   - paste the emitted markdown log entry into the SCP repo's
#     `docs/reviews/WP-SCP-020/branch-protection-log.md` and merge.
#
# The log commit is part of the invocation procedure per
# WP-SCP-020 §4 020G(iii). The script emits a log block on EVERY
# completed invocation, including verification failures and partial-
# state apply failures (e.g. the unified PUT succeeds but the
# required_signatures POST fails) — the operator commits the
# resulting log entry whether the apply succeeded or partially
# failed, so the audit trail captures both outcomes.
#
# ## Required PAT scope
#
# `gh` must be authenticated with `administration:write` on the
# target repo (fine-grained PAT with single-repo scope strongly
# preferred over classic). The script cannot introspect token
# scope without making an authorised call; on the first PUT it
# will fail with HTTP 403 if the scope is insufficient. Run with
# `--plan` first to verify intent before any mutation.
#
# Reference: docs/DECISIONS.md D-022 (federation-primitive adoption);
# D-033 (the rendered context name `policy-check / scp/policy-check`
# established for the SCP self-dogfood gate, used here as the
# canonical adopter default); D-035 (this slice's invocation
# procedure); D-044 (WP-SCP-024 024B restore mode + prior-green-CI
# safety); WP-SCP-020 §4 020G; ADOPT-001 §12 (federation integration
# appendix — lands in 020H part 3).

set -euo pipefail

# ---------- Bootstrap-only guard ----------

if [ "${CI:-}" = "true" ] || [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  echo "020G refuses to run in CI: this is an attended bootstrap script." >&2
  echo "If you need to run a dry-run from CI, unset CI/GITHUB_ACTIONS first AND pass --plan explicitly." >&2
  exit 1
fi

# ---------- (i) Header preconditions ----------

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

require_cmd gh
require_cmd jq
require_cmd git
require_cmd python3
require_cmd shasum

assert_gh_version() {
  local raw major minor
  raw="$(gh --version 2>/dev/null | head -1 | awk '{print $3}')"
  if [ -z "$raw" ]; then
    echo "could not determine gh CLI version" >&2
    exit 1
  fi
  major="$(printf '%s' "$raw" | cut -d. -f1)"
  minor="$(printf '%s' "$raw" | cut -d. -f2)"
  # 2.40 floor — the unified branch-protection PUT shape used here
  # has been stable since gh 2.x; anything older risks API drift.
  if [ "$major" -lt 2 ] || { [ "$major" -eq 2 ] && [ "$minor" -lt 40 ]; }; then
    echo "gh CLI ${raw} too old: 2.40+ required" >&2
    exit 1
  fi
}

assert_gh_version

SCP_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH_PROTECTION_LOG="${SCP_REPO_ROOT}/docs/reviews/WP-SCP-020/branch-protection-log.md"

# Per WP-SCP-020 §4 020G(i): "log-warn, don't block, since the
# script can't introspect token scope without making a call". The
# warning is loud (printed to stderr before any mutation) so the
# operator who skipped --plan still sees it.
echo "WARNING: this script requires gh authenticated with administration:write on the target repo." >&2
echo "         Recommended: fine-grained PAT scoped to the single target repo." >&2
echo "         Run with --plan first if you have not verified scope sufficiency." >&2

# ---------- (ii) Argument parsing ----------

REPO=""
BRANCH=""
REQUIRED_CONTEXT="${SCP_REQUIRED_CONTEXT:-policy-check / scp/policy-check}"
EXPECTED_WRAPPER_SHA=""
PLAN_ONLY=0
ENFORCE_ADMINS="true"
ACK_ADMIN_BYPASS=0
RESTORE_STATE=""
ACK_NO_PRIOR_GREEN_CI=0
ACK_NO_GATE2_VERIFICATION=0
ACK_RESTORE_ADMIN_DEGRADATION=0
ACK_RESTORE_REQUIRED_CHECKS_DEGRADATION=0

usage() {
  cat <<'EOF' >&2
Usage: enable-required-check.sh --repo OWNER/NAME --branch BRANCH [flags]

Required:
  --repo OWNER/NAME   Target repository (e.g. mapp-pim/mapp-pim).
  --branch BRANCH     Default branch to protect (typically `main`).

Flags:
  --required-check NAME    Override the required-check context name.
                           Default: "policy-check / scp/policy-check".
  --plan                   Print the PUT payload AND current branch-
                           protection state without applying. Use
                           this first to verify intent.
  --no-enforce-admins      Disable enforce_admins. NOT canonical;
                           requires a separate
                           --i-understand-this-bypasses-the-gate flag
                           to take effect (per 020G R1 SAF-003 closure).
  --i-understand-this-bypasses-the-gate
                           Required confirmation when combined with
                           --no-enforce-admins. Without this flag, the
                           script ignores --no-enforce-admins.
  --restore PRE-STATE.json  Restore branch protection from a captured
                           pre-state JSON emitted by a prior run.
  --i-understand-restore-removes-admin-enforcement
                           Required confirmation when a restore-state
                           would remove enforce_admins.
  --i-understand-restore-removes-required-checks
                           Required confirmation when a restore-state
                           would clear required_status_checks.contexts.
  --i-understand-this-repo-has-no-prior-green-ci
                           Override the forward-mode precondition that
                           the target repo has already green-CI'd once.
  --expected-wrapper-sha SHA
                           Optional forward-mode safety check: require
                           the adopter wrapper's `uses:` pin to match SHA
                           before re-arming the gate.
  --i-understand-no-gate-2-verification
                           Explicit override when re-arming without
                           proving Gate 2's wrapper SHA pin.
  --help / -h              Show this help.

Bootstrap-only — this script is NOT run unattended. It refuses to
run when CI=true or GITHUB_ACTIONS=true. Operator attention is
required for the apply, the diff review, and the invocation-log
commit afterward.

Reference: docs/DECISIONS.md D-022 (federation primitive adoption);
D-033 (rendered context-name `policy-check / scp/policy-check`);
D-035 (this slice's invocation procedure); WP-SCP-020 §4 020G.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --repo)
      [ $# -lt 2 ] && { echo "error: --repo requires a value" >&2; usage; exit 2; }
      REPO="$2"; shift 2 ;;
    --branch)
      [ $# -lt 2 ] && { echo "error: --branch requires a value" >&2; usage; exit 2; }
      BRANCH="$2"; shift 2 ;;
    --required-check)
      [ $# -lt 2 ] && { echo "error: --required-check requires a value" >&2; usage; exit 2; }
      REQUIRED_CONTEXT="$2"; shift 2 ;;
    --plan) PLAN_ONLY=1; shift ;;
    --enforce-admins) ENFORCE_ADMINS="true"; shift ;;
    --no-enforce-admins) ENFORCE_ADMINS="false"; shift ;;
    --i-understand-this-bypasses-the-gate) ACK_ADMIN_BYPASS=1; shift ;;
    --restore)
      [ $# -lt 2 ] && { echo "error: --restore requires a value" >&2; usage; exit 2; }
      RESTORE_STATE="$2"; shift 2 ;;
    --i-understand-this-repo-has-no-prior-green-ci) ACK_NO_PRIOR_GREEN_CI=1; shift ;;
    --expected-wrapper-sha)
      [ $# -lt 2 ] && { echo "error: --expected-wrapper-sha requires a value" >&2; usage; exit 2; }
      EXPECTED_WRAPPER_SHA="$2"; shift 2 ;;
    --i-understand-restore-removes-admin-enforcement) ACK_RESTORE_ADMIN_DEGRADATION=1; shift ;;
    --i-understand-restore-removes-required-checks) ACK_RESTORE_REQUIRED_CHECKS_DEGRADATION=1; shift ;;
    --i-understand-no-gate-2-verification) ACK_NO_GATE2_VERIFICATION=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown flag: $1" >&2; usage; exit 2 ;;
  esac
done

if [ -z "$RESTORE_STATE" ] && { [ "$ACK_RESTORE_ADMIN_DEGRADATION" -eq 1 ] || [ "$ACK_RESTORE_REQUIRED_CHECKS_DEGRADATION" -eq 1 ]; }; then
  echo "error: restore-only acknowledgement flags require --restore" >&2
  usage
  exit 2
fi

if [ -n "$RESTORE_STATE" ] && { [ -n "$REPO" ] || [ -n "$BRANCH" ] || [ "$PLAN_ONLY" -eq 1 ] || [ "$ACK_ADMIN_BYPASS" -eq 1 ] || [ "$ACK_NO_PRIOR_GREEN_CI" -eq 1 ] || [ "$ACK_NO_GATE2_VERIFICATION" -eq 1 ] || [ -n "$EXPECTED_WRAPPER_SHA" ] || [ "$ENFORCE_ADMINS" != "true" ]; }; then
  echo "error: --restore is a standalone mode and cannot be combined with forward-mode flags" >&2
  usage
  exit 2
fi

if [ -z "$RESTORE_STATE" ] && { [ -z "$REPO" ] || [ -z "$BRANCH" ]; }; then
  echo "error: --repo and --branch are both required" >&2
  usage
  exit 2
fi

# Closes 020G R2 correctness CORR2-003: --i-understand-this-bypasses-
# the-gate is silently meaningless without --no-enforce-admins.
# Refuse the combination so an operator who pre-fills the long flag
# from history but forgets the trigger sees a clear error.
if [ "$ACK_ADMIN_BYPASS" -eq 1 ] && [ "$ENFORCE_ADMINS" = "true" ]; then
  echo "error: --i-understand-this-bypasses-the-gate is meaningless without --no-enforce-admins" >&2
  echo "       remove the ack flag, or pair it with --no-enforce-admins" >&2
  exit 2
fi

# Per 020G R1 safety SAF-003: --no-enforce-admins is a serious
# foot-gun. Refuse silently unless the explicit acknowledgement
# flag is also set. With the flag, escalate to a 5-second pause
# + visible warning so the operator who actually means it
# can't run on autopilot.
if [ "$ENFORCE_ADMINS" != "true" ]; then
  if [ "$ACK_ADMIN_BYPASS" -ne 1 ]; then
    echo "error: --no-enforce-admins ignored without --i-understand-this-bypasses-the-gate" >&2
    echo "       enforce_admins=true is the canonical SCP federation primitive posture." >&2
    exit 2
  fi
  echo "" >&2
  echo "================================================================" >&2
  echo "WARNING: --no-enforce-admins applied with explicit acknowledgement." >&2
  echo "         This means repository administrators can push directly" >&2
  echo "         to '$BRANCH' bypassing the SCP policy-check gate." >&2
  echo "         5-second pause to allow Ctrl-C..." >&2
  echo "================================================================" >&2
  sleep 5
fi

if [ -z "$RESTORE_STATE" ]; then
# Path-traversal guard on REPO + BRANCH (per 020G R1 safety SAF-006
# + 020G R2 correctness CORR2-002 — `owner/..` would have satisfied
# the original regex because `..` matches `[A-Za-z0-9._-]+`).
# Repo names match GitHub's ASCII rules; branch names disallow `..`
# or leading slashes that could be misread by url joining.
  if printf '%s' "$REPO" | grep -qE '(^|/)\.'; then
    echo "error: --repo '$REPO' contains path-traversal sequence (.., leading dot, dot-segment after /)" >&2
    exit 2
  fi
  if ! printf '%s' "$REPO" | grep -qE '^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$'; then
    echo "error: --repo '$REPO' does not match owner/name shape" >&2
    exit 2
  fi
  if printf '%s' "$BRANCH" | grep -qE '(^\.|/|\.\.)'; then
    echo "error: --branch '$BRANCH' invalid (no slashes, no .., no leading dot)" >&2
    exit 2
  fi

  if [ "$ACK_NO_PRIOR_GREEN_CI" -ne 1 ]; then
    # Fix-round-3: path-pin the workflow lookup rather than matching on display
    # name. The display name `policy-check` is not unique; the canonical wrapper
    # lives at .github/workflows/policy-check-wrapper.yml.
    WORKFLOW_ID="$(
      gh api "repos/${REPO}/actions/workflows" \
        --jq '.workflows[] | select(.path == ".github/workflows/policy-check-wrapper.yml") | .id' \
        | head -1 || true
    )"
    if [ -z "$WORKFLOW_ID" ]; then
      echo "ERROR: target ${REPO} has no workflow at .github/workflows/policy-check-wrapper.yml. Did the adopter wrapper PR merge? Did the operator land scaffold-downstream.sh emissions? Override with --i-understand-this-repo-has-no-prior-green-ci if you accept the risk." >&2
      exit 1
    fi
    if [ -n "$EXPECTED_WRAPPER_SHA" ]; then
      wrapper_pin="$(
        gh api "repos/${REPO}/contents/.github/workflows/policy-check-wrapper.yml" --jq '.content' \
          | python3 -c 'import base64, re, sys
content = base64.b64decode(sys.stdin.read()).decode("utf-8")
match = re.search(r"(?m)^[ \t]*uses:[ \t].*@([0-9a-f]{40})[ \t]*$", content)
if not match:
    raise SystemExit("error: could not extract adopter wrapper SHA pin")
print(match.group(1))
'
      )"
      if [ "$wrapper_pin" != "$EXPECTED_WRAPPER_SHA" ]; then
        echo "error: adopter wrapper SHA pin '$wrapper_pin' does not match expected '$EXPECTED_WRAPPER_SHA' (return to Gate 2; do not re-enable yet)" >&2
        exit 2
      fi
    fi
    prior_green_cutoff="$(
      python3 -c 'import datetime; print((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%SZ"))'
    )"
    prior_green_ci="$(
      gh api "repos/${REPO}/actions/runs?workflow_id=${WORKFLOW_ID}&status=success&created=>=${prior_green_cutoff}&branch=${BRANCH}" \
        --jq '.workflow_runs[]' \
        | head -1 || true
    )"
    if [ -z "$prior_green_ci" ]; then
      echo "ERROR: target ${REPO} has no successful policy-check workflow runs in the last 60 days; refuse to enable required-check before wrapper has green-CI'd at least once. Override with --i-understand-this-repo-has-no-prior-green-ci if you accept the risk." >&2
      exit 1
    fi
  fi
fi

if [ -f "$BRANCH_PROTECTION_LOG" ]; then
  prior_log_entry_marker="— ${REPO}@${BRANCH}"
  if grep -Fq -- "$prior_log_entry_marker" "$BRANCH_PROTECTION_LOG"; then
    if [ -z "$EXPECTED_WRAPPER_SHA" ] && [ "$ACK_NO_GATE2_VERIFICATION" -ne 1 ]; then
      echo "error: prior invocation log entry already exists for ${REPO}@${BRANCH}; pass --expected-wrapper-sha <release-tag-sha-from-gate-2> or --i-understand-no-gate-2-verification before re-arming" >&2
      exit 2
    fi
  fi
fi

# Closes 020G R3 safety SAF-R3-002: REQUIRED_CONTEXT is included
# verbatim in the emitted markdown log block; backticks or
# newlines would corrupt the operator's pasteable log entry. Reject
# obvious markdown-injection chars. The actual GitHub Actions
# check-run name space is bounded (alphanumerics, slashes, spaces,
# hyphens, parentheses) — no legitimate name needs backticks or
# newlines.
case "$REQUIRED_CONTEXT" in
  *'`'*|*$'\n'*|*$'\r'*)
    echo "error: --required-check '$REQUIRED_CONTEXT' contains markdown-corrupting chars (backtick, CR, LF)" >&2
    exit 2 ;;
esac
if [ "${#REQUIRED_CONTEXT}" -gt 200 ]; then
  echo "error: --required-check value is ${#REQUIRED_CONTEXT} chars; max 200" >&2
  exit 2
fi

log() {
  printf '[020G] %s\n' "$*"
}

restore_branch_protection() {
  local restore_path="$1"
  local restore_meta
  local restore_repo
  local restore_branch
  local restore_before_json
  local restore_put_json
  local restore_admin_enforcement_enabled
  local restore_required_checks_have_contexts
  local restore_current_state
  local restore_after_json
  local restore_ts
  local restore_operator
  local restore_script_path
  local restore_script_sha256
  local restore_script_git_sha

  if [ ! -f "$restore_path" ]; then
    echo "error: --restore file not found: $restore_path" >&2
    exit 2
  fi

  if ! restore_meta="$(python3 - "$restore_path" <<'PY'
import json
import sys
from pathlib import Path

state = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if not isinstance(state, dict):
    raise SystemExit("restore JSON must be an object")
for key in ("repo", "branch", "before"):
    if key not in state:
        raise SystemExit(f"restore JSON missing required key: {key}")
if not isinstance(state["repo"], str) or not state["repo"]:
    raise SystemExit("restore JSON 'repo' value must be a non-empty string")
if not isinstance(state["branch"], str) or not state["branch"]:
    raise SystemExit("restore JSON 'branch' value must be a non-empty string")
before = state["before"]
if not isinstance(before, dict):
    raise SystemExit("restore JSON 'before' value must be an object")
for key in ("required_status_checks", "enforce_admins", "required_pull_request_reviews"):
    if key not in before:
        raise SystemExit(f"restore JSON 'before' missing required key: {key}")

required_status_checks = before.get("required_status_checks")
if not isinstance(required_status_checks, dict):
    raise SystemExit("restore JSON 'before' missing or malformed key: required_status_checks")
enforce_admins = before.get("enforce_admins")
if not isinstance(enforce_admins, dict) or not isinstance(enforce_admins.get("enabled"), bool):
    raise SystemExit("restore JSON 'before' missing or malformed key: enforce_admins.enabled")
required_pull_request_reviews = before.get("required_pull_request_reviews")
if required_pull_request_reviews is not None and not isinstance(required_pull_request_reviews, dict):
    raise SystemExit("restore JSON 'before' missing or malformed key: required_pull_request_reviews")
restrictions = before.get("restrictions")

def scrub(value):
    if isinstance(value, dict):
        return {
            key: scrub(subvalue)
            for key, subvalue in value.items()
            if key not in {"url", "_links", "checks"}
        }
    if isinstance(value, list):
        return [scrub(item) for item in value]
    return value

before_scrubbed = scrub(before)
restore_admin_enforcement_enabled = enforce_admins["enabled"]
restore_required_checks_have_contexts = isinstance(required_status_checks.get("contexts"), list) and len(required_status_checks.get("contexts")) > 0

before_scrubbed["enforce_admins"] = restore_admin_enforcement_enabled
before_scrubbed["required_status_checks"] = {
    "strict": required_status_checks.get("strict"),
    "contexts": required_status_checks.get("contexts"),
}

if required_pull_request_reviews is None:
    before_scrubbed["required_pull_request_reviews"] = None
else:
    before_scrubbed["required_pull_request_reviews"] = scrub(required_pull_request_reviews)

if isinstance(restrictions, dict) and {"users", "teams", "apps"} <= set(restrictions):
    unexpected = sorted(set(restrictions) - {"users", "teams", "apps", "url", "_links"})
    if unexpected:
        print("[020G] WARNING: restore pre-state restrictions contained unexpected fields: {}; restoring users/teams/apps only".format(", ".join(unexpected)), file=sys.stderr)
    before_scrubbed["restrictions"] = scrub({
        "users": restrictions["users"],
        "teams": restrictions["teams"],
        "apps": restrictions["apps"],
    })
else:
    before_scrubbed["restrictions"] = None

print(state["repo"])
print(state["branch"])
print("true" if restore_admin_enforcement_enabled else "false")
print("true" if restore_required_checks_have_contexts else "false")
print(json.dumps(before, separators=(",", ":")))
print(json.dumps(before_scrubbed, separators=(",", ":")))
PY
  )"; then
    exit 1
  fi

  restore_repo="$(printf '%s' "$restore_meta" | sed -n '1p')"
  restore_branch="$(printf '%s' "$restore_meta" | sed -n '2p')"
  restore_admin_enforcement_enabled="$(printf '%s' "$restore_meta" | sed -n '3p')"
  restore_required_checks_have_contexts="$(printf '%s' "$restore_meta" | sed -n '4p')"
  restore_before_json="$(printf '%s' "$restore_meta" | sed -n '5p')"
  restore_put_json="$(printf '%s' "$restore_meta" | sed -n '6p')"

  if [ -z "$restore_repo" ] || [ -z "$restore_branch" ] || [ -z "$restore_before_json" ] || [ -z "$restore_put_json" ]; then
    echo "error: invalid --restore file" >&2
    exit 2
  fi

  if printf '%s' "$restore_repo" | grep -qE '(^|/)\.'; then
    echo "error: --restore repo '$restore_repo' contains path-traversal sequence (.., leading dot, dot-segment after /)" >&2
    exit 2
  fi
  if ! printf '%s' "$restore_repo" | grep -qE '^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$'; then
    echo "error: --restore repo '$restore_repo' does not match owner/name shape" >&2
    exit 2
  fi
  if printf '%s' "$restore_branch" | grep -qE '(^\.|/|\.\.)'; then
    echo "error: --restore branch '$restore_branch' invalid (no slashes, no .., no leading dot)" >&2
    exit 2
  fi
  case "$restore_branch" in
    *'`'*|*$'\n'*|*$'\r'*)
      echo "error: --restore branch '$restore_branch' contains markdown-corrupting chars (backtick, CR, LF)" >&2
      exit 2
      ;;
  esac

  if [ "$restore_admin_enforcement_enabled" = "false" ] || [ "$restore_required_checks_have_contexts" != "true" ]; then
    if [ "$restore_admin_enforcement_enabled" = "false" ]; then
      echo "[020G] WARNING: restore pre-state would remove admin enforcement (enforce_admins.enabled=false)" >&2
    fi
    if [ "$restore_required_checks_have_contexts" != "true" ]; then
      echo "[020G] WARNING: restore pre-state would clear required status checks (required_status_checks.contexts empty or null)" >&2
    fi
    if [ "$restore_admin_enforcement_enabled" = "false" ] && [ "$ACK_RESTORE_ADMIN_DEGRADATION" -ne 1 ]; then
      echo "[020G] WARNING: pass --i-understand-restore-removes-admin-enforcement to continue" >&2
      exit 2
    fi
    if [ "$restore_required_checks_have_contexts" != "true" ] && [ "$ACK_RESTORE_REQUIRED_CHECKS_DEGRADATION" -ne 1 ]; then
      echo "[020G] WARNING: pass --i-understand-restore-removes-required-checks to continue" >&2
      exit 2
    fi
  fi

  printf '[020G] restoring branch protection for %s@%s\n' "$restore_repo" "$restore_branch" >&2
  restore_current_state="$(gh api -X GET "repos/${restore_repo}/branches/${restore_branch}/protection" 2>/dev/null || echo '{"_note":"capture-failed"}')"
  APPLY_FAIL=0
  printf '%s' "$restore_put_json" | gh api -X PUT "repos/${restore_repo}/branches/${restore_branch}/protection" \
    -H "Accept: application/vnd.github+json" \
    --input - >/dev/null || APPLY_FAIL=1

  restore_after_json="$(gh api -X GET "repos/${restore_repo}/branches/${restore_branch}/protection" 2>/dev/null || true)"
  if [ -z "$restore_after_json" ]; then
    restore_after_json='{"_note":"capture-failed"}'
  fi
  restore_ts="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  restore_operator="$(gh api user --jq '.login' 2>/dev/null || echo unknown)"
  restore_script_path="$(readlink -f "$0" 2>/dev/null || printf '%s' "$0")"
  restore_script_sha256="$(shasum -a 256 "$restore_script_path" | awk '{print $1}')"
  restore_script_git_sha="$(git -C "$(dirname "$restore_script_path")" log -1 --format=%H -- "$(basename "$restore_script_path")" 2>/dev/null || true)"
  restore_script_git_sha="${restore_script_git_sha:-not-in-git-clone}"

  cat <<EOF
---

## Invocation log entry

Append the block below to docs/reviews/WP-SCP-020/branch-protection-log.md on the SCP repo, commit on a feature branch, open PR, merge:

~~~markdown
### ${restore_ts} — ${restore_repo}@${restore_branch}

- **MODE:** restore
- **Operator:** @${restore_operator}
- **Script SHA256:** \`${restore_script_sha256}\` (hash of executed file)
- **Script git SHA:** \`${restore_script_git_sha}\` (last committed; "not-in-git-clone" if N/A)
- **Plan-only:** no
- **Restoring TO (original captured before-state):**
\`\`\`json
$(printf '%s' "$restore_before_json" | python3 -m json.tool 2>/dev/null || printf '%s' "$restore_before_json")
\`\`\`
- **Before:**
\`\`\`json
$(printf '%s' "$restore_current_state" | python3 -m json.tool 2>/dev/null || printf '%s' "$restore_current_state")
\`\`\`
- **After:**
\`\`\`json
$(printf '%s' "$restore_after_json" | python3 -m json.tool 2>/dev/null || printf '%s' "$restore_after_json")
\`\`\`
~~~

The Before/After JSON blocks are authoritative; scalar mirrors are omitted to avoid stale copies of branch-protection fields.
The log commit is part of the invocation procedure per WP-SCP-020 §4 020G(iii) + D-035; without it the restore is unrecorded.
EOF

  if [ "$APPLY_FAIL" -eq 1 ]; then
    return 1
  fi
  return 0
}

if [ -n "$RESTORE_STATE" ]; then
  if ! restore_branch_protection "$RESTORE_STATE"; then
    exit 1
  fi
  exit 0
fi

log "target repo: $REPO"
log "target branch: $BRANCH"
log "required check: $REQUIRED_CONTEXT"
log "enforce_admins: $ENFORCE_ADMINS"
[ "$PLAN_ONLY" = "1" ] && log "MODE: plan-only (no API mutation)"

# ---------- Construct PUT payload ----------
#
# Per 020G R1 correctness CORR-003: required_signatures is a
# DEDICATED sub-resource and is NOT a documented field of the
# unified branch-protection PUT body. Apply it separately via
# the /required_signatures endpoint after the main PUT. The
# unified PUT body therefore omits required_signatures.
#
# Per 020G R1 safety SAF-002: required_pull_request_reviews must
# be PRESERVED if it already exists. We capture before-state and
# splice the existing review-shape into the PUT payload rather
# than nulling it out.

build_payload() {
  local existing_reviews="$1"
  jq -n \
    --arg context "$REQUIRED_CONTEXT" \
    --argjson admins "$ENFORCE_ADMINS" \
    --argjson reviews "$existing_reviews" \
    '{
       required_status_checks: {
         strict: true,
         contexts: [$context]
       },
       enforce_admins: $admins,
       required_pull_request_reviews: $reviews,
       restrictions: null,
       required_linear_history: false,
       allow_force_pushes: false,
       allow_deletions: false,
       block_creations: false,
       required_conversation_resolution: false,
       lock_branch: false,
       allow_fork_syncing: false
     }'
}

# ---------- Capture before-state ----------

log "capturing before-state..."
BEFORE_RAW="$(gh api -X GET "repos/${REPO}/branches/${BRANCH}/protection" 2>&1)" || BEFORE_STATUS=$?
BEFORE_STATUS="${BEFORE_STATUS:-0}"

if [ "$BEFORE_STATUS" -eq 0 ]; then
  BEFORE_JSON="$BEFORE_RAW"
elif printf '%s' "$BEFORE_RAW" | grep -q "Branch not protected"; then
  BEFORE_JSON='{"_note":"no protection currently configured"}'
else
  echo "error: gh api GET branch protection failed; cannot proceed safely" >&2
  echo "$BEFORE_RAW" >&2
  exit 1
fi

# Extract existing required_pull_request_reviews, default to null
# if absent. Either way, we send what was there.
EXISTING_REVIEWS="$(printf '%s' "$BEFORE_JSON" | jq '.required_pull_request_reviews // null')"

# Per WP-SCP-022 020H pt 3 R3 SAFE-R3-003 closure (2026-04-30):
# multi-maintainer adopters MUST set dismiss_stale_reviews: true to
# close the post-approval-malicious-push attack surface (see
# ADOPT-001 §12.7.4). This script preserves the adopter's existing
# review-shape verbatim and does NOT set dismiss_stale_reviews; emit
# a stderr WARNING if it is currently false or absent so the operator
# is prompted to configure it explicitly.
DISMISS_STALE_VAL="$(printf '%s' "$EXISTING_REVIEWS" | jq -r '
  if . == null then "absent"
  elif (.dismiss_stale_reviews // false) == true then "true"
  else "false"
  end
')"
if [ "$DISMISS_STALE_VAL" != "true" ]; then
  echo "[020G] WARNING: required_pull_request_reviews.dismiss_stale_reviews is ${DISMISS_STALE_VAL} on the target repo" >&2
  echo "[020G] WARNING: multi-maintainer SCP adopters MUST set dismiss_stale_reviews: true (ADOPT-001 §12.7.4)" >&2
  echo "[020G] WARNING: this script preserves the existing review-shape verbatim and does not set this for you" >&2
  echo "[020G] WARNING: configure it via 'gh api -X PATCH repos/<owner>/<repo>/branches/<branch>/protection/required_pull_request_reviews -F dismiss_stale_reviews=true'" >&2
  echo "[020G] WARNING: single-operator adopters with required_approving_review_count=0 (per D-033) can ignore this warning" >&2
fi

PAYLOAD="$(build_payload "$EXISTING_REVIEWS")"

if [ "$PLAN_ONLY" = "1" ]; then
  log "current branch-protection state (before):"
  printf '%s\n' "$BEFORE_JSON" | jq .
  log "plan (would PUT to repos/${REPO}/branches/${BRANCH}/protection):"
  printf '%s\n' "$PAYLOAD" | jq .
  log "post-PUT, would also enable required_signatures via the dedicated sub-resource."
  log "to apply, re-run without --plan"
  exit 0
fi

# ---------- Apply ----------

# Closes 020G R2 safety SAF-R2-001: trap a non-zero exit during
# the apply phase so partial state still emits an audit-trail
# log entry. Otherwise `set -e` skips log emission entirely on
# any HTTP 403/network failure during the dedicated POST step.

APPLY_FAIL=0

log "applying branch protection (unified PUT)..."
printf '%s' "$PAYLOAD" | gh api -X PUT "repos/${REPO}/branches/${BRANCH}/protection" \
  -H "Accept: application/vnd.github+json" \
  --input - >/dev/null || APPLY_FAIL=1

if [ "$APPLY_FAIL" -ne 0 ]; then
  echo "ERROR: unified PUT failed; partial branch-protection state may exist on ${REPO}@${BRANCH}" >&2
  echo "       continuing to log emission so the failure is auditable, then exiting non-zero" >&2
  FAIL=1
else
  log "enabling required_signatures (dedicated sub-resource)..."
  gh api -X POST "repos/${REPO}/branches/${BRANCH}/protection/required_signatures" >/dev/null || APPLY_FAIL=1
  if [ "$APPLY_FAIL" -ne 0 ]; then
    echo "ERROR: required_signatures POST failed; status-checks/admins/reviews are set but signatures are NOT" >&2
    echo "       continuing to log emission so the partial-state failure is auditable, then exiting non-zero" >&2
    FAIL=1
  fi
fi

# ---------- Verify ----------

log "verifying..."
AFTER_JSON="$(gh api -X GET "repos/${REPO}/branches/${BRANCH}/protection")"

CHECKS_STRICT="$(printf '%s' "$AFTER_JSON" | jq -r '.required_status_checks.strict // false')"
CHECKS_CONTEXTS="$(printf '%s' "$AFTER_JSON" | jq -r '.required_status_checks.contexts // [] | join(",")')"
APPLIED_ADMINS="$(printf '%s' "$AFTER_JSON" | jq -r '.enforce_admins.enabled // false')"
SIGS_ENABLED="$(printf '%s' "$AFTER_JSON" | jq -r '.required_signatures.enabled // false')"

# Closes 020G R3 correctness CORR3-001 + safety SAF-R3-001:
# preserve any FAIL=1 set by the apply-phase trap. Initialising
# FAIL=0 unconditionally would launder an apply-failure into a
# false-success when the pre-existing state happens to satisfy
# the verify checks. Default to 0 only if not already set.
FAIL="${FAIL:-0}"
[ "$CHECKS_STRICT" = "true" ] || { echo "verify FAIL: required_status_checks.strict=${CHECKS_STRICT}" >&2; FAIL=1; }
printf '%s' "$CHECKS_CONTEXTS" | grep -q -F "$REQUIRED_CONTEXT" || { echo "verify FAIL: contexts missing ${REQUIRED_CONTEXT} (got: ${CHECKS_CONTEXTS})" >&2; FAIL=1; }
[ "$APPLIED_ADMINS" = "$ENFORCE_ADMINS" ] || { echo "verify FAIL: enforce_admins=${APPLIED_ADMINS} (expected ${ENFORCE_ADMINS})" >&2; FAIL=1; }
[ "$SIGS_ENABLED" = "true" ] || { echo "verify FAIL: required_signatures=${SIGS_ENABLED}" >&2; FAIL=1; }

# Closes 020G R2 correctness CORR2-001 + safety SAF-R2-002: only
# emit "verification passed" when FAIL=0. Previously this line
# emitted unconditionally after the fall-through, producing a
# misleading false-success message on stdout when verification had
# actually failed.
if [ "${FAIL:-0}" -ne 0 ]; then
  echo "verification failed; see message(s) above" >&2
  echo "" >&2
  echo "Even on failure, capture an invocation log entry so the audit trail" >&2
  echo "records the failure. The before/after blocks below show the partial" >&2
  echo "state and aid post-mortem." >&2
  # fall through to log emission so an audit entry exists
else
  log "verification passed ✓"
  log "  required check:        ${CHECKS_CONTEXTS} (strict=${CHECKS_STRICT})"
  log "  enforce_admins:        ${APPLIED_ADMINS}"
  log "  required_signatures:   ${SIGS_ENABLED}"
fi

# ---------- Emit invocation log ----------
#
# Per 020G R1 safety SAF-001 + correctness CORR-002:
# the audit trail records the SHA256 of the actually-running
# script content (not the last-committed git SHA, which can lie if
# the operator has uncommitted changes or runs from outside an SCP
# clone). The git-SHA is recorded as a secondary identifier when
# available.

# Self-hash via $0. Exits non-zero only if the script can't read
# itself, which is essentially impossible at this point.
SCRIPT_PATH="$(readlink -f "$0" 2>/dev/null || printf '%s' "$0")"
SCRIPT_SHA256="$(shasum -a 256 "$SCRIPT_PATH" | awk '{print $1}')"

# Try to also report the last-committed git SHA if we're inside an
# SCP-shaped clone. Empty fallback is explicit.
SCRIPT_GIT_SHA="$(git -C "$(dirname "$SCRIPT_PATH")" log -1 --format=%H -- "$(basename "$SCRIPT_PATH")" 2>/dev/null || true)"
SCRIPT_GIT_SHA="${SCRIPT_GIT_SHA:-not-in-git-clone}"

OPERATOR="$(gh api user --jq '.login' 2>/dev/null || echo unknown)"
TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

LOG_FILE="docs/reviews/WP-SCP-020/branch-protection-log.md"

# Emit the log block. Use ~~~~ outer fence so inner ``` JSON
# fences nest correctly (CommonMark requires the closing fence
# to match the opening fence character; fence types ~~~ and ```
# do not collide). Closes 020G R1 correctness CORR-001.

cat <<EOF
---

## Invocation log entry

Append the block below to ${LOG_FILE} on the SCP repo, commit on
a feature branch, open PR, merge:

~~~markdown
### ${TS} — ${REPO}@${BRANCH}

- **Operator:** @${OPERATOR}
- **Script SHA256:** \`${SCRIPT_SHA256}\` (hash of executed file)
- **Script git SHA:** \`${SCRIPT_GIT_SHA}\` (last committed; "not-in-git-clone" if N/A)
- **Required check:** \`${REQUIRED_CONTEXT}\`
- **enforce_admins:** ${ENFORCE_ADMINS}
- **Plan-only:** no
- **PUT payload applied:**
\`\`\`json
$(printf '%s' "$PAYLOAD" | python3 -m json.tool 2>/dev/null || printf '%s' "$PAYLOAD")
\`\`\`
- **Before:**
\`\`\`json
$(printf '%s' "$BEFORE_JSON" | python3 -m json.tool 2>/dev/null || printf '%s' "$BEFORE_JSON")
\`\`\`
- **After:**
\`\`\`json
$(printf '%s' "$AFTER_JSON" | python3 -m json.tool 2>/dev/null || printf '%s' "$AFTER_JSON")
\`\`\`
~~~

The log commit is part of the invocation procedure per WP-SCP-020
§4 020G(iii) + D-035; without it the apply is unrecorded.
EOF

# Closes 020G R1 safety SAF-010: the script exits non-zero on
# verification failure even though the log block IS emitted, so
# the operator's calling shell still sees a hard fail.
if [ "${FAIL:-0}" -ne 0 ]; then
  exit 1
fi
