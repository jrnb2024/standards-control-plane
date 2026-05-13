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
# procedure); WP-SCP-020 §4 020G; ADOPT-001 §12 (federation
# integration appendix — lands in 020H part 3).

set -euo pipefail

SCRIPT_PATH="$(readlink -f "$0" 2>/dev/null || printf '%s' "$0")"
REPO_ROOT="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"

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
OPERATOR=""
REQUIRED_CONTEXT="${SCP_REQUIRED_CONTEXT:-policy-check / scp/policy-check}"
PLAN_ONLY=0
ENFORCE_ADMINS="true"
ACK_ADMIN_BYPASS=0
RESTORE_MODE=0
RESTORE_PRE_STATE=""
EXPECTED_WRAPPER_SHA=""
NO_PRIOR_GREEN_CI=0
ACK_RESTORE_ADMIN_REMOVAL=0
ACK_RESTORE_REQUIRED_CHECKS_REMOVAL=0
ACK_RESTORE_DISABLES_STRICT_MODE=0
ACK_RESTORE_REPLACES_REQUIRED_CHECK_CONTEXT=0
ACK_RESTORE_SIGNATURES_REMOVAL=0
ACK_RESTORE_FORCE_PUSHES=0
ACK_RESTORE_DELETIONS=0
ACK_NO_GATE2_VERIFICATION=0
ACK_WRAPPER_INACCESSIBLE=0
GATE2_CAUTION_LINE=""
WRAPPER_INACCESSIBLE_CAUTION_LINE=""
WRAPPER_INACCESSIBLE_NOOP_LINE=""
WORKFLOW_LOOKUP_PATH=".github/workflows/policy-check-wrapper.yml"

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
  --restore PRE-STATE.json
                           Restore branch protection from a captured
                           pre-state JSON file.
  --expected-wrapper-sha SHA
                           Assert the caller pins the wrapper to a
                           known release-tag SHA.
  --i-understand-this-repo-has-no-prior-green-ci
                           Bypass the forward-mode prior-green-CI safety
                           check for cold-start adopters.
  --i-understand-restore-removes-admin-enforcement
                           Confirm a restore target that removes admin
                           enforcement.
  --i-understand-restore-removes-required-checks
                           Confirm a restore target that removes required
                           status checks.
  --i-understand-restore-disables-strict-mode
                           Confirm a restore target that disables strict
                           mode.
  --i-understand-restore-replaces-required-check-context
                           Confirm a restore target that replaces the
                           canonical required-check context with a
                           non-canonical set.
  --i-understand-restore-disables-required-signatures
                           Confirm a restore target that disables
                           required signatures.
  --i-understand-restore-re-enables-force-pushes
                           Confirm a restore target that re-enables
                           allow_force_pushes.
  --i-understand-restore-re-enables-deletions
                           Confirm a restore target that re-enables
                           allow_deletions.
  --i-understand-no-gate-2-verification
                           Confirm break-glass Gate 2 bypass during
                           emergency recovery.
  --i-understand-wrapper-inaccessible
                           Confirm wrapper-content inaccessibility
                           bypass during Gate 3 verification.
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
      RESTORE_MODE=1
      RESTORE_PRE_STATE="$2"
      shift 2 ;;
    --expected-wrapper-sha)
      [ $# -lt 2 ] && { echo "error: --expected-wrapper-sha requires a value" >&2; usage; exit 2; }
      EXPECTED_WRAPPER_SHA="$2"
      shift 2 ;;
    --i-understand-this-repo-has-no-prior-green-ci) NO_PRIOR_GREEN_CI=1; shift ;;
    --i-understand-restore-removes-admin-enforcement) ACK_RESTORE_ADMIN_REMOVAL=1; shift ;;
    --i-understand-restore-removes-required-checks) ACK_RESTORE_REQUIRED_CHECKS_REMOVAL=1; shift ;;
    --i-understand-restore-disables-strict-mode) ACK_RESTORE_DISABLES_STRICT_MODE=1; shift ;;
    --i-understand-restore-replaces-required-check-context) ACK_RESTORE_REPLACES_REQUIRED_CHECK_CONTEXT=1; shift ;;
    --i-understand-restore-disables-required-signatures) ACK_RESTORE_SIGNATURES_REMOVAL=1; shift ;;
    --i-understand-restore-re-enables-force-pushes) ACK_RESTORE_FORCE_PUSHES=1; shift ;;
    --i-understand-restore-re-enables-deletions) ACK_RESTORE_DELETIONS=1; shift ;;
    --i-understand-no-gate-2-verification) ACK_NO_GATE2_VERIFICATION=1; shift ;;
    --i-understand-wrapper-inaccessible) ACK_WRAPPER_INACCESSIBLE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown flag: $1" >&2; usage; exit 2 ;;
  esac
done

if [ -z "$REPO" ] || [ -z "$BRANCH" ]; then
  echo "error: --repo and --branch are both required" >&2
  usage
  exit 2
fi

if [ "$RESTORE_MODE" -eq 0 ]; then
  if [ "$ACK_RESTORE_ADMIN_REMOVAL" -eq 1 ] || [ "$ACK_RESTORE_REQUIRED_CHECKS_REMOVAL" -eq 1 ] || [ "$ACK_RESTORE_DISABLES_STRICT_MODE" -eq 1 ] || [ "$ACK_RESTORE_REPLACES_REQUIRED_CHECK_CONTEXT" -eq 1 ] || [ "$ACK_RESTORE_SIGNATURES_REMOVAL" -eq 1 ] || [ "$ACK_RESTORE_FORCE_PUSHES" -eq 1 ] || [ "$ACK_RESTORE_DELETIONS" -eq 1 ]; then
    echo 'error: --i-understand-restore-* flags are restore-mode-only; remove them or run with --restore <pre-state.json>' >&2
    exit 2
  fi
fi

if [ "$RESTORE_MODE" -eq 1 ]; then
  if [ -z "$RESTORE_PRE_STATE" ]; then
    echo "error: --restore requires a pre-state JSON path" >&2
    exit 2
  fi
  if [ "$PLAN_ONLY" -eq 1 ]; then
    echo "error: --restore cannot be combined with --plan" >&2
    exit 2
  fi
  if [ "$ENFORCE_ADMINS" != "true" ]; then
    echo "error: --restore cannot be combined with --no-enforce-admins" >&2
    exit 2
  fi
  if [ "$ACK_ADMIN_BYPASS" -eq 1 ]; then
    echo "error: --restore cannot be combined with --i-understand-this-bypasses-the-gate" >&2
    exit 2
  fi
  if [ -n "$EXPECTED_WRAPPER_SHA" ]; then
    echo "error: --restore cannot be combined with --expected-wrapper-sha" >&2
    exit 2
  fi
  if [ "$NO_PRIOR_GREEN_CI" -eq 1 ]; then
    echo "error: --restore cannot be combined with --i-understand-this-repo-has-no-prior-green-ci" >&2
    exit 2
  fi
  if [ "$ACK_NO_GATE2_VERIFICATION" -eq 1 ]; then
    echo "error: --restore cannot be combined with --i-understand-no-gate-2-verification" >&2
    exit 2
  fi
  if [ "$ACK_WRAPPER_INACCESSIBLE" -eq 1 ]; then
    echo "error: --restore cannot be combined with --i-understand-wrapper-inaccessible" >&2
    exit 2
  fi
fi

if [ "$NO_PRIOR_GREEN_CI" -eq 1 ] && [ "$ACK_NO_GATE2_VERIFICATION" -eq 1 ]; then
  echo "error: --i-understand-this-repo-has-no-prior-green-ci is incompatible with --i-understand-no-gate-2-verification; the bypass flag requires prior --restore evidence (Gate 3 re-enable), not cold-start state" >&2
  exit 2
fi

if [ "$RESTORE_MODE" -eq 1 ]; then
  RESTORE_PRE_STATE="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$RESTORE_PRE_STATE")"
  TMP_ROOT="$(python3 - <<'PY'
import os
import tempfile

print(os.path.realpath(tempfile.gettempdir()))
PY
)"
  case "$RESTORE_PRE_STATE" in
    "$REPO_ROOT"/*|"$TMP_ROOT"/*) ;;
    *)
      echo "error: --restore path '$RESTORE_PRE_STATE' resolves outside repo root '$REPO_ROOT' or temp root '$TMP_ROOT'" >&2
      exit 2
      ;;
  esac
  RESTORE_TARGET_JSON="$(cat "$RESTORE_PRE_STATE")"
fi

if ! OPERATOR="$(gh api user --jq '.login' 2>/dev/null)" || [ -z "$OPERATOR" ]; then
  echo "error: could not resolve GitHub operator identity via 'gh api user'; verify 'gh auth status' and network reachability" >&2
  exit 2
fi

if [ -n "$EXPECTED_WRAPPER_SHA" ] && [ "$ACK_NO_GATE2_VERIFICATION" -eq 1 ]; then
  echo "error: --expected-wrapper-sha cannot be combined with --i-understand-no-gate-2-verification" >&2
  exit 2
fi

if [ "$NO_PRIOR_GREEN_CI" -eq 1 ] && [ -n "$EXPECTED_WRAPPER_SHA" ]; then
  echo "error: --expected-wrapper-sha cannot be combined with --i-understand-this-repo-has-no-prior-green-ci" >&2
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

# Path-traversal guard on REPO + BRANCH (per 020G R1 safety SAF-006
# + 020G R2 correctness CORR2-002 — `owner/..` would have satisfied
# the original regex because `..` matches `[A-Za-z0-9._-]+`).
# Repo names match GitHub's ASCII rules; branch names disallow `..`
# or leading slashes that could be misread by url joining.
case "$REPO" in
  .*|*/.*)
    echo "error: --repo '$REPO' contains path-traversal sequence (leading dot or dot-segment after /)" >&2
    exit 2 ;;
esac
case "$REPO" in
  *..*)
    echo "error: --repo '$REPO' contains path-traversal sequence (..)" >&2
    exit 2 ;;
esac
if ! printf '%s' "$REPO" | grep -qE '^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$'; then
  echo "error: --repo '$REPO' does not match owner/name shape" >&2
  exit 2
fi
case "$BRANCH" in
  ""|*/*|*..*|.*) echo "error: --branch '$BRANCH' invalid (no slashes, no .., no leading dot)" >&2; exit 2 ;;
esac

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

validate_restore_source_json() {
  python3 -c "$(cat <<'PY'
import json
import sys

try:
    data = json.load(sys.stdin)
except Exception as exc:  # pragma: no cover - defensive diagnostics
    print(f"error: unable to parse restore pre-state JSON: {exc}", file=sys.stderr)
    sys.exit(2)

if not isinstance(data, dict):
    print("error: restore pre-state JSON must be an object", file=sys.stderr)
    sys.exit(2)

required_types = {
    "required_status_checks": (dict, type(None)),
    "enforce_admins": dict,
    "required_pull_request_reviews": (dict, type(None)),
    "restrictions": (dict, type(None)),
    "required_signatures": (dict, type(None)),
}
for key, types in required_types.items():
    if key not in data:
        print(f"error: restore pre-state JSON missing required key '{key}'", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data[key], types):
        print(f"error: restore pre-state JSON key '{key}' has unexpected type", file=sys.stderr)
        sys.exit(2)

rsc = data.get("required_status_checks")
if rsc is not None:
    contexts = rsc.get("contexts")
    if not isinstance(contexts, list):
        print("error: required_status_checks.contexts must be a list", file=sys.stderr)
        sys.exit(2)
    for item in contexts:
        if not isinstance(item, str):
            print(f"error: required_status_checks.contexts must contain only strings (got {type(item).__name__}: {item!r})", file=sys.stderr)
            sys.exit(2)
    strict = rsc.get("strict")
    if not isinstance(strict, bool):
        print(f"error: required_status_checks.strict must be a boolean, got {type(strict).__name__}: {strict!r}", file=sys.stderr)
        sys.exit(2)

enforce_admins = data.get("enforce_admins")
if "enabled" not in enforce_admins:
    print("error: restore pre-state JSON: enforce_admins.enabled is absent; required key", file=sys.stderr)
    sys.exit(2)
enabled = enforce_admins.get("enabled")
if not (
    enabled is None
    or isinstance(enabled, bool)
    or (isinstance(enabled, int) and enabled in (0, 1))
):
    print("error: enforce_admins.enabled must be a boolean", file=sys.stderr)
    sys.exit(2)

ALLOWED_REQUIRED_STATUS_CHECKS_KEYS = ("strict", "contexts")
ALLOWED_REQUIRED_PULL_REQUEST_REVIEW_KEYS = (
    "dismissal_restrictions",
    "dismiss_stale_reviews",
    "require_code_owner_reviews",
    "required_approving_review_count",
    "require_last_push_approval",
    "bypass_pull_request_allowances",
)
ALLOWED_RESTRICTIONS_KEYS = ("users", "teams", "apps")
TOP_LEVEL_TOGGLE_KEYS = (
    "required_linear_history",
    "allow_force_pushes",
    "allow_deletions",
    "block_creations",
    "required_conversation_resolution",
    "lock_branch",
    "allow_fork_syncing",
)


def compact_actor_lists(node):
    def compact(items, field):
        out_items = []
        for item in items or []:
            if isinstance(item, dict):
                item = item.get(field, "")
            if isinstance(item, str) and item:
                out_items.append(item)
        return out_items

    return {
        "users": compact(node.get("users", []), "login"),
        "teams": compact(node.get("teams", []), "slug"),
        "apps": compact(node.get("apps", []), "slug"),
    }


def transform(node):
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            if key in {"_links", "url", "checks", "enforcement_level", "contexts_url"} or key.endswith("_url"):
                continue
            if key == "enforce_admins" and isinstance(value, dict):
                out[key] = bool(value.get("enabled", False))
            elif key in TOP_LEVEL_TOGGLE_KEYS:
                # GitHub GET returns these as {enabled: bool} objects despite the API
                # docs documenting bool. Unwrap; the PUT body requires plain bool.
                if isinstance(value, dict) and set(value.keys()) <= {"enabled", "url"} and isinstance(value.get("enabled"), bool):
                    out[key] = bool(value["enabled"])
                elif isinstance(value, bool):
                    out[key] = value
            elif key == "restrictions" and isinstance(value, dict):
                # Use an inclusion list for the documented branch-restriction keys.
                out[key] = compact_actor_lists(value)
            elif key == "required_status_checks" and value is None:
                out[key] = {"strict": False, "contexts": []}
            elif key == "required_status_checks" and isinstance(value, dict):
                # Use an inclusion list so undocumented nested fields do not leak into the PUT body.
                out[key] = {
                    nested_key: value.get(nested_key, [] if nested_key == "contexts" else False)
                    for nested_key in ALLOWED_REQUIRED_STATUS_CHECKS_KEYS
                    if nested_key in value
                }
            elif key == "required_pull_request_reviews" and isinstance(value, dict):
                # Use an inclusion list so undocumented nested fields do not leak into the PUT body.
                out[key] = {}
                for nested_key in ALLOWED_REQUIRED_PULL_REQUEST_REVIEW_KEYS:
                    if nested_key not in value:
                        continue
                    nested_value = value[nested_key]
                    if nested_key in {"dismissal_restrictions", "bypass_pull_request_allowances"} and isinstance(nested_value, dict):
                        out[key][nested_key] = compact_actor_lists(nested_value)
                    else:
                        out[key][nested_key] = transform(nested_value)
            else:
                out[key] = transform(value)
        return out
    if isinstance(node, list):
        return [transform(item) for item in node]
    return node

print(json.dumps(transform(data)))
PY
)"
}

json_file_to_pretty_stdout() {
  local file="$1"
  python3 - "$file" <<'PY'
import json
import sys

path = sys.argv[1]
try:
    with open(path) as fh:
        data = json.load(fh)
except Exception:
    with open(path) as fh:
        sys.stdout.write(fh.read())
else:
    print(json.dumps(data, indent=2, sort_keys=False))
PY
}

json_string_to_pretty_stdout() {
  python3 - <<'PY'
import json
import sys

payload = sys.stdin.read()
try:
    data = json.loads(payload)
except Exception:
    sys.stdout.write(payload)
else:
    print(json.dumps(data, indent=2, sort_keys=False))
PY
}

sanitize_context_for_log() {
  local context="$1"
  context="${context//$'\r'/ }"
  context="${context//$'\n'/ }"
  context="${context//\`/\\\`}"
  if [ "${#context}" -gt 200 ]; then
    context="${context:0:200}"
  fi
  printf '%s' "$context"
}

# Checks for ANY uncommitted/working-tree restore evidence in the branch-protection-log.md — intentionally cross-repo scope. Used by the forward-mode warning that a pending restore commit may exist.
prior_restore_evidence_present() {
  local log_path="$1"
  local target="$2"
  local target_escaped committed_blob="" working_tree_diff="" committed_history_diff=""
  # shellcheck disable=SC2016
  target_escaped="$(printf '%s' "$target" | sed 's/[][\\.*^$()+?{}|\\/]/\\\\&/g')"
  if [ -f "$log_path" ]; then
    committed_blob="$(cat "$log_path")"
  fi
  working_tree_diff="$(git -C "$REPO_ROOT" diff HEAD -- "$log_path" 2>/dev/null || true)"
  committed_history_diff="$(git -C "$REPO_ROOT" log -p -- "$log_path" 2>/dev/null || true)"
  printf '%s\n%s\n%s' "$committed_blob" "$working_tree_diff" "$committed_history_diff" | awk -v target="$target_escaped" '
    BEGIN { found = 0; in_block = 0 }
    {
      line = $0
      ash = $0
      sub(/^[+]/, "", line)
      if (line ~ /^### /) {
        pat = "(^|[^A-Za-z0-9._/-])" target "([^A-Za-z0-9._/-]|$)"
        in_block = (match(line, pat) > 0)
      }
      if (ash !~ /^[+]/) next
      if (in_block && line ~ /\*\*Restoring TO:\*\*/) {
        found = 1
        exit
      }
    }
    # only added lines are counted as new prior-restore evidence; removed lines are ignored.
    END { exit !found }
  '
}

# Note: handles a single level of annotated-tag indirection (lightweight
# commit or one-level annotated). Doubly-annotated tags (tag-of-tag) are
# not currently supported; SCP release tags are vN.M.K lightweight or
# single-annotated.
validate_expected_wrapper_sha_against_tags() {
  local expected_sha="$1"
  local tag_list_json matched_tag="" matched_tag_lines=""
  tag_list_json="$(gh api --paginate "repos/jrnb2024/standards-control-plane-/git/refs/tags?per_page=100")"
  matched_tag_lines="$(
    TAG_LIST_JSON="$tag_list_json" python3 - "$expected_sha" <<'PY'
import json
import os
import sys

expected_sha = sys.argv[1]
payload = os.environ.get("TAG_LIST_JSON", "").strip()
decoder = json.JSONDecoder()
docs = []

while payload:
    payload = payload.lstrip()
    if not payload:
        break
    doc, idx = decoder.raw_decode(payload)
    docs.append(doc)
    payload = payload[idx:]

for doc in docs:
    items = doc if isinstance(doc, list) else [doc]
    for entry in items:
        if not isinstance(entry, dict):
            continue
        ref = entry.get("ref", "")
        obj = entry.get("object") or {}
        obj_type = obj.get("type") or "commit"
        obj_sha = obj.get("sha", "")
        if obj_type == "commit" and obj_sha == expected_sha:
            print(f"{ref}\tcommit\t")
        elif obj_type == "tag":
            print(f"{ref}\ttag\t{obj_sha}")
PY
  )"
  while IFS=$'\t' read -r ref kind tag_sha; do
    [ -n "$ref" ] || continue
    case "$kind" in
      commit)
        matched_tag="${ref#refs/tags/}"
        break
        ;;
      tag)
        local annotated_commit_sha=""
        annotated_commit_sha="$(
          gh api "repos/jrnb2024/standards-control-plane-/git/tags/${tag_sha}" --jq '.object.sha' 2>/dev/null || true
        )"
        if [ "$annotated_commit_sha" = "$expected_sha" ]; then
          matched_tag="${ref#refs/tags/}"
          break
        fi
        ;;
    esac
  done <<EOF
$matched_tag_lines
EOF
  if [ -z "$matched_tag" ]; then
    echo "error: --expected-wrapper-sha '$expected_sha' was not found in the release-tag SHA cache" >&2
    exit 2
  fi
  if ! printf '%s' "$matched_tag" | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo "error: --expected-wrapper-sha matched non-release tag '$matched_tag'; only vN.M.K release tags are accepted" >&2
    exit 2
  fi
  log "expected wrapper SHA validated against release tag: ${matched_tag}"
}

check_forward_mode_safety() {
  local created_since workflow_id workflow_runs_json run_count wrapper_content prior_restore_evidence=0

  if [ "$NO_PRIOR_GREEN_CI" -eq 1 ]; then
    if prior_restore_evidence_present "docs/reviews/WP-SCP-020/branch-protection-log.md" "${REPO}@${BRANCH}"; then
      echo "error: --i-understand-this-repo-has-no-prior-green-ci is incompatible with prior restore evidence for ${REPO}@${BRANCH} found in docs/reviews/WP-SCP-020/branch-protection-log.md" >&2
      echo "       the cold-start escape hatch is for adopters without history; prior-restore evidence indicates Gate 3 (post-break-glass re-enable) — use --expected-wrapper-sha or --i-understand-no-gate-2-verification" >&2
      exit 2
    fi
    workflow_id="$(gh api --paginate "repos/${REPO}/actions/workflows?per_page=100" --jq '.workflows[] | select(.path == "'"$WORKFLOW_LOOKUP_PATH"'") | .id' | head -n1)"
    if [ -z "$workflow_id" ]; then
      echo "error: --i-understand-this-repo-has-no-prior-green-ci requires the wrapper workflow file '$WORKFLOW_LOOKUP_PATH' to be present in ${REPO}; add the wrapper PR first" >&2
      exit 2
    fi
    created_since="$(python3 - <<'PY'
from datetime import datetime, timedelta, timezone
print((datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%SZ"))
PY
)"
    workflow_runs_json="$(gh api "repos/${REPO}/actions/runs?status=success&created=%3E%3D${created_since}&workflow_id=${workflow_id}")"
    run_count="$(printf '%s' "$workflow_runs_json" | jq '.workflow_runs | length')"
    if [ "$run_count" -gt 0 ]; then
      log "CAUTION: --i-understand-this-repo-has-no-prior-green-ci rejected for ${REPO}@${BRANCH}; successful workflow runs exist"
      echo "error: --i-understand-this-repo-has-no-prior-green-ci is for cold-start adopters with no successful workflow-runs. Found ${run_count} successful runs on this repo, indicating a non-cold-start state. Use --expected-wrapper-sha for Gate 3 re-enable instead." >&2
      exit 2
    fi
    log "safety check bypassed via --i-understand-this-repo-has-no-prior-green-ci"
    return 0
  fi

  workflow_id="$(gh api --paginate "repos/${REPO}/actions/workflows?per_page=100" --jq '.workflows[] | select(.path == "'"$WORKFLOW_LOOKUP_PATH"'") | .id' | head -n1)"
  if [ -z "$workflow_id" ]; then
    echo "error: no workflow with path '$WORKFLOW_LOOKUP_PATH' found in ${REPO}" >&2
    exit 2
  fi

  created_since="$(python3 - <<'PY'
from datetime import datetime, timedelta, timezone
print((datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%SZ"))
PY
)"
  workflow_runs_json="$(gh api "repos/${REPO}/actions/runs?status=success&created=%3E%3D${created_since}&workflow_id=${workflow_id}")"
  run_count="$(printf '%s' "$workflow_runs_json" | jq '.workflow_runs | length')"
  if [ "$run_count" -eq 0 ]; then
    echo "error: no successful workflow runs found for workflow path '$WORKFLOW_LOOKUP_PATH' in the last 60 days" >&2
    echo "       use --i-understand-this-repo-has-no-prior-green-ci only for cold-start adopters" >&2
    exit 2
  fi
  log "safety check: found ${run_count} successful workflow run(s) for ${WORKFLOW_LOOKUP_PATH} in the last 60 days"

  if prior_restore_evidence_present "docs/reviews/WP-SCP-020/branch-protection-log.md" "${REPO}@${BRANCH}"; then
    prior_restore_evidence=1
  fi
  if [ "$ACK_NO_GATE2_VERIFICATION" -eq 1 ] && [ "$prior_restore_evidence" -ne 1 ]; then
    echo "error: --i-understand-no-gate-2-verification requires prior --restore evidence for ${REPO}@${BRANCH}; the bypass is a Gate 3 re-enable mechanism, not a cold-start escape hatch" >&2
    exit 2
  fi

  if [ "$prior_restore_evidence" -eq 1 ]; then
    if [ "$ACK_NO_GATE2_VERIFICATION" -eq 1 ]; then
      cat >&2 <<'WARN'
++ CAUTION: Gate 2 wrapper-SHA verification bypassed via --i-understand-no-gate-2-verification.
++ This proceeds in 5 seconds. Press Ctrl-C to abort.
WARN
      sleep 5
      GATE2_CAUTION_LINE="- **CAUTION:** Gate 3 invoked with --i-understand-no-gate-2-verification — wrapper SHA NOT verified against release-tag SHA. Operator @${OPERATOR} acknowledges break-glass risk."
    fi
    if [ -z "$EXPECTED_WRAPPER_SHA" ] && [ "$ACK_NO_GATE2_VERIFICATION" -ne 1 ]; then
      echo "error: prior --restore evidence detected for ${REPO}@${BRANCH}; --expected-wrapper-sha <release-tag-sha> is required" >&2
      echo "       pass --i-understand-no-gate-2-verification to bypass Gate 2 verification (audited via CAUTION log entry)" >&2
      exit 2
    fi
  fi

  if [ -n "$EXPECTED_WRAPPER_SHA" ]; then
    if ! prior_restore_evidence_present "docs/reviews/WP-SCP-020/branch-protection-log.md" "${REPO}@${BRANCH}"; then
      echo "error: --expected-wrapper-sha requires prior --restore evidence for ${REPO}@${BRANCH} in docs/reviews/WP-SCP-020/branch-protection-log.md" >&2
      echo "       check both the committed log file and the working tree diff" >&2
      exit 2
    fi
    validate_expected_wrapper_sha_against_tags "$EXPECTED_WRAPPER_SHA"
    _wrapper_raw="$(gh api "repos/${REPO}/contents/.github/workflows/policy-check-wrapper.yml" --jq '.content' 2>/dev/null || true)"
    if [ -n "$_wrapper_raw" ]; then
      wrapper_content="$(printf '%s' "$_wrapper_raw" | base64 -d 2>/dev/null)" || {
        echo "ERROR: fetched adopter wrapper content but base64 decode failed — API response may be malformed" >&2
        echo "       pass --i-understand-wrapper-inaccessible if wrapper is genuinely unreachable" >&2
        exit 2
      }
    else
      wrapper_content=""
    fi
    if [ -n "$wrapper_content" ]; then
      # Heuristic note: GitHub Actions requires `uses:` to be a scalar,
      # so line-oriented grep is a pragmatic match for the runtime shape.
      # A future hardening step could parse the YAML with python3 +
      # yaml.safe_load() and inspect jobs.*.steps[].uses directly.
      if printf '%s' "$wrapper_content" | grep -vE '^[[:space:]]*#' | grep -qE '^[[:space:]]*uses:[[:space:]]+[^#]*standards-control-plane[^#]*@'"${EXPECTED_WRAPPER_SHA}"; then
        log "verified: adopter wrapper pins to ${EXPECTED_WRAPPER_SHA}"
      else
        echo "ERROR: adopter wrapper does NOT pin to ${EXPECTED_WRAPPER_SHA}" >&2
        echo "       update the wrapper SHA pin before invoking Gate 3 re-enable" >&2
        exit 2
      fi
    else
      if [ "$ACK_WRAPPER_INACCESSIBLE" -ne 1 ]; then
        echo "ERROR: adopter wrapper content is inaccessible from current context" >&2
        echo "       pass --i-understand-wrapper-inaccessible to continue without wrapper-pin verification" >&2
        exit 2
      fi
      log "CAUTION: wrapper-pin not verified — adopter wrapper content inaccessible; operator acknowledged via --i-understand-wrapper-inaccessible"
      WRAPPER_INACCESSIBLE_CAUTION_LINE="- **CAUTION:** Gate 3 wrapper content was inaccessible from the current context; operator acknowledged via --i-understand-wrapper-inaccessible before proceeding."
      cat >&2 <<'WARN'
+++ CAUTION: adopter wrapper content is inaccessible from current context.
+++ This proceeds in 5 seconds. Press Ctrl-C to abort.
WARN
      sleep 5
    fi
    if [ "$ACK_WRAPPER_INACCESSIBLE" -eq 1 ] && [ -n "$wrapper_content" ]; then
      echo "WARNING: --i-understand-wrapper-inaccessible passed but wrapper is readable; verification was performed normally. Remove the flag to suppress this warning." >&2
      WRAPPER_INACCESSIBLE_NOOP_LINE="- **NOTE:** --i-understand-wrapper-inaccessible passed but wrapper was readable; verification was performed normally."
    fi
  fi
}

log() {
  printf '[020G] %s\n' "$*"
}

log "target repo: $REPO"
log "target branch: $BRANCH"
log "required check: $REQUIRED_CONTEXT"
log "enforce_admins: $ENFORCE_ADMINS"
[ "$PLAN_ONLY" = "1" ] && log "MODE: plan-only (no API mutation)"

if [ "$RESTORE_MODE" -eq 0 ]; then
  check_forward_mode_safety
fi

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

RESTORE_PAYLOAD=""
RESTORE_PUT_PAYLOAD=""
RESTORE_SIGNATURES_ENABLED=""
RESTORE_TARGET_CHECKS_STRICT=""
RESTORE_TARGET_CHECKS_CONTEXTS=""
RESTORE_TARGET_CHECKS_CONTEXTS_LOG=""
RESTORE_TARGET_ADMINS_ENABLED=""
RESTORE_TARGET_FORCE_PUSHES=""
RESTORE_TARGET_DELETIONS=""
RESTORE_CAUTION_LINES=()
RESTORE_CAUTION_LINES_BLOCK=""
FORWARD_CAUTION_LINES_BLOCK=""
if [ "$RESTORE_MODE" -eq 1 ]; then
  RESTORE_PAYLOAD="$(printf '%s' "$RESTORE_TARGET_JSON" | validate_restore_source_json)"
  RESTORE_PUT_PAYLOAD="$(printf '%s' "$RESTORE_PAYLOAD" | jq 'del(.required_signatures)')"
  RESTORE_TARGET_CHECKS_STRICT="$(printf '%s' "$RESTORE_TARGET_JSON" | jq -r '.required_status_checks.strict // false')"
  RESTORE_TARGET_CHECKS_CONTEXTS="$(printf '%s' "$RESTORE_TARGET_JSON" | jq -r '.required_status_checks.contexts // [] | join(",")')"
  RESTORE_TARGET_CHECKS_CONTEXTS_LOG="$(sanitize_context_for_log "$RESTORE_TARGET_CHECKS_CONTEXTS")"
  RESTORE_TARGET_ADMINS_ENABLED="$(printf '%s' "$RESTORE_PAYLOAD" | jq -r '.enforce_admins // false')"
  RESTORE_TARGET_FORCE_PUSHES="$(printf '%s' "$RESTORE_PAYLOAD" | jq -r '.allow_force_pushes // false')"
  RESTORE_TARGET_DELETIONS="$(printf '%s' "$RESTORE_PAYLOAD" | jq -r '.allow_deletions // false')"
  CURRENT_SIGNATURES_ENABLED="$(printf '%s' "$BEFORE_JSON" | jq -r '.required_signatures.enabled // false')"
  RESTORE_SIGNATURES_ENABLED="$(
    printf '%s' "$RESTORE_TARGET_JSON" | python3 -c 'import json, sys; data = json.load(sys.stdin); enabled = bool(((data.get("required_signatures") or {}).get("enabled", False))); print("true" if enabled else "false")'
  )"
  if [ "$CURRENT_SIGNATURES_ENABLED" = "true" ] && [ "$RESTORE_SIGNATURES_ENABLED" = "false" ] && [ "$ACK_RESTORE_SIGNATURES_REMOVAL" -ne 1 ]; then
    echo "error: restore target disables required signatures; pass --i-understand-restore-disables-required-signatures to continue" >&2
    exit 2
  fi
  if [ "$CURRENT_SIGNATURES_ENABLED" = "true" ] && [ "$RESTORE_SIGNATURES_ENABLED" = "false" ]; then
    log "CAUTION: restore target disables required_signatures; operator acknowledges posture change"
    RESTORE_CAUTION_LINES+=("- **CAUTION:** restore target disables required_signatures; operator acknowledges posture change.")
  fi
  if [ "$RESTORE_TARGET_FORCE_PUSHES" = "true" ]; then
    if [ "$ACK_RESTORE_FORCE_PUSHES" -ne 1 ]; then
      echo "error: restore target re-enables allow_force_pushes; pass --i-understand-restore-re-enables-force-pushes to continue" >&2
      exit 2
    fi
    log "CAUTION: restore target re-enables allow_force_pushes; operator acknowledges posture change"
    RESTORE_CAUTION_LINES+=("- **CAUTION:** restore target re-enables allow_force_pushes; operator acknowledges posture change.")
  fi
  if [ "$RESTORE_TARGET_DELETIONS" = "true" ]; then
    if [ "$ACK_RESTORE_DELETIONS" -ne 1 ]; then
      echo "error: restore target re-enables allow_deletions; pass --i-understand-restore-re-enables-deletions to continue" >&2
      exit 2
    fi
    log "CAUTION: restore target re-enables allow_deletions; operator acknowledges posture change"
    RESTORE_CAUTION_LINES+=("- **CAUTION:** restore target re-enables allow_deletions; operator acknowledges posture change.")
  fi
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

if [ "$RESTORE_MODE" -eq 1 ]; then
  if [ "$RESTORE_TARGET_ADMINS_ENABLED" = "false" ] && [ "$ACK_RESTORE_ADMIN_REMOVAL" -ne 1 ]; then
    echo "error: restore target removes admin enforcement; pass --i-understand-restore-removes-admin-enforcement to continue" >&2
    exit 2
  fi
  if [ "$RESTORE_TARGET_ADMINS_ENABLED" = "false" ]; then
    log "CAUTION: restore target removes admin enforcement; operator acknowledges posture change"
    RESTORE_CAUTION_LINES+=("- **CAUTION:** restore target removes admin enforcement; operator acknowledged via --i-understand-restore-removes-admin-enforcement.")
  fi
  restore_contexts="$(printf '%s' "$RESTORE_TARGET_JSON" | jq -r '.required_status_checks.contexts // [] | length')"
  restore_canonical_present=0
  if printf '%s' "$RESTORE_TARGET_JSON" | jq -e --arg ctx "$REQUIRED_CONTEXT" '(.required_status_checks // {}).contexts // [] | index($ctx) != null' >/dev/null 2>&1; then
    restore_canonical_present=1
  fi
  if [ "$restore_contexts" -eq 0 ]; then
    if [ "$ACK_RESTORE_REQUIRED_CHECKS_REMOVAL" -ne 1 ] && [ "$ACK_RESTORE_REPLACES_REQUIRED_CHECK_CONTEXT" -ne 1 ]; then
      echo "error: restore target removes required status checks; pass --i-understand-restore-removes-required-checks to continue" >&2
      exit 2
    fi
    log "CAUTION: restore target removes required status checks; operator acknowledges posture change"
    if [ "$ACK_RESTORE_REQUIRED_CHECKS_REMOVAL" -eq 1 ]; then
      RESTORE_CAUTION_LINES+=("- **CAUTION:** restore target removes required status checks; operator acknowledged via --i-understand-restore-removes-required-checks.")
    else
      RESTORE_CAUTION_LINES+=("- **CAUTION:** restore target removes required status checks; operator acknowledged via --i-understand-restore-replaces-required-check-context.")
    fi
  elif [ "$restore_canonical_present" -eq 0 ]; then
    if [ "$ACK_RESTORE_REQUIRED_CHECKS_REMOVAL" -ne 1 ] && [ "$ACK_RESTORE_REPLACES_REQUIRED_CHECK_CONTEXT" -ne 1 ]; then
      echo "error: restore target replaces canonical required status check context; pass --i-understand-restore-replaces-required-check-context to continue or use --i-understand-restore-removes-required-checks if intentional removal" >&2
      exit 2
    fi
    log "CAUTION: restore target replaces required_status_checks.contexts with a non-canonical set; operator acknowledges posture change"
    RESTORE_CAUTION_LINES+=("- **CAUTION:** restore target replaces required_status_checks.contexts with a non-canonical set; operator acknowledged via --i-understand-restore-replaces-required-check-context.")
  fi
  if [ "$RESTORE_TARGET_CHECKS_STRICT" = "false" ]; then
    if [ "$ACK_RESTORE_DISABLES_STRICT_MODE" -ne 1 ]; then
      echo "error: restore target disables strict mode; pass --i-understand-restore-disables-strict-mode to continue" >&2
      exit 2
    fi
    log "CAUTION: restore target disables strict mode; operator acknowledges posture change"
    RESTORE_CAUTION_LINES+=("- **CAUTION:** restore target disables strict mode; operator acknowledges posture change.")
  fi

  log "restoring branch protection (unified PUT)..."
  printf '%s' "$RESTORE_PUT_PAYLOAD" | gh api -X PUT "repos/${REPO}/branches/${BRANCH}/protection" \
    -H "Accept: application/vnd.github+json" \
    --input - >/dev/null || APPLY_FAIL=1

  if [ "$APPLY_FAIL" -ne 0 ]; then
    echo "ERROR: unified PUT failed; partial branch-protection state may exist on ${REPO}@${BRANCH}" >&2
    echo "       continuing to log emission so the failure is auditable, then exiting non-zero" >&2
    FAIL=1
  else
    restore_signatures_enabled="$RESTORE_SIGNATURES_ENABLED"
    if [ "$restore_signatures_enabled" = "true" ]; then
      log "restoring required_signatures (dedicated sub-resource: enable)..."
      restore_signatures_err="$(mktemp)"
      if ! gh api -X POST "repos/${REPO}/branches/${BRANCH}/protection/required_signatures" >/dev/null 2>"$restore_signatures_err"; then
        if grep -q '404' "$restore_signatures_err"; then
          log "required_signatures POST already in desired state (404 suppressed)"
        else
          echo "ERROR: required_signatures POST failed; status-checks/admins/reviews are set but signatures are NOT" >&2
          echo "       continuing to log emission so the partial-state failure is auditable, then exiting non-zero" >&2
          APPLY_FAIL=1
          FAIL=1
        fi
      fi
      rm -f "$restore_signatures_err"
    else
      log "restoring required_signatures (dedicated sub-resource: disable)..."
      restore_signatures_err="$(mktemp)"
      if ! gh api -X DELETE "repos/${REPO}/branches/${BRANCH}/protection/required_signatures" >/dev/null 2>"$restore_signatures_err"; then
        if grep -q '404' "$restore_signatures_err"; then
          log "required_signatures DELETE already in desired state (404 suppressed)"
        else
          echo "ERROR: required_signatures DELETE failed; status-checks/admins/reviews are set but signatures are NOT" >&2
          echo "       continuing to log emission so the partial-state failure is auditable, then exiting non-zero" >&2
          APPLY_FAIL=1
          FAIL=1
        fi
      fi
      rm -f "$restore_signatures_err"
    fi
  fi
else
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
fi

if [ "$RESTORE_MODE" -eq 1 ]; then
  if [ "${#RESTORE_CAUTION_LINES[@]}" -gt 0 ]; then
    RESTORE_CAUTION_LINES_BLOCK=$'\n'"$(printf '%s\n' "${RESTORE_CAUTION_LINES[@]}")"
  else
    RESTORE_CAUTION_LINES_BLOCK=""
  fi
fi

if [ -n "$GATE2_CAUTION_LINE" ]; then
  FORWARD_CAUTION_LINES_BLOCK+="${GATE2_CAUTION_LINE}"$'\n'
fi
if [ -n "$WRAPPER_INACCESSIBLE_CAUTION_LINE" ]; then
  FORWARD_CAUTION_LINES_BLOCK+="${WRAPPER_INACCESSIBLE_CAUTION_LINE}"$'\n'
fi
if [ -n "$WRAPPER_INACCESSIBLE_NOOP_LINE" ]; then
  FORWARD_CAUTION_LINES_BLOCK+="${WRAPPER_INACCESSIBLE_NOOP_LINE}"$'\n'
fi

# ---------- Verify ----------

log "verifying..."
if [ "$RESTORE_MODE" -eq 1 ]; then
  AFTER_RAW="$(gh api -X GET "repos/${REPO}/branches/${BRANCH}/protection" 2>&1)" || AFTER_STATUS=$?
  AFTER_STATUS="${AFTER_STATUS:-0}"
  if [ "$AFTER_STATUS" -eq 0 ]; then
    AFTER_JSON="$AFTER_RAW"
  else
    AFTER_JSON='{"_error":"restore after-state capture failed"}'
    echo "ERROR: post-restore GET branch-protection failed; continuing to log emission so the failure is auditable" >&2
    APPLY_FAIL=1
    FAIL=1
  fi
else
  if AFTER_JSON="$(gh api -X GET "repos/${REPO}/branches/${BRANCH}/protection")"; then
    :
  else
    AFTER_JSON='{"_error":"forward-mode verify GET failed"}'
    echo "ERROR: post-apply GET branch-protection failed; continuing to log emission so the failure is auditable" >&2
    APPLY_FAIL=1
    FAIL=1
  fi
fi

CHECKS_STRICT="$(printf '%s' "$AFTER_JSON" | jq -r '.required_status_checks.strict // false')"
CHECKS_CONTEXTS="$(printf '%s' "$AFTER_JSON" | jq -r '.required_status_checks.contexts // [] | join(",")')"
APPLIED_ADMINS="$(printf '%s' "$AFTER_JSON" | jq -r '.enforce_admins.enabled // false')"
SIGS_ENABLED="$(printf '%s' "$AFTER_JSON" | jq -r '.required_signatures.enabled // false')"

if [ "$RESTORE_MODE" -eq 1 ]; then
  EXPECTED_CHECKS_STRICT="$RESTORE_TARGET_CHECKS_STRICT"
  EXPECTED_CHECKS_CONTEXTS="$RESTORE_TARGET_CHECKS_CONTEXTS"
  EXPECTED_APPLIED_ADMINS="$RESTORE_TARGET_ADMINS_ENABLED"
  EXPECTED_SIGS_ENABLED="$RESTORE_SIGNATURES_ENABLED"
else
  EXPECTED_CHECKS_STRICT="true"
  EXPECTED_CHECKS_CONTEXTS="$REQUIRED_CONTEXT"
  EXPECTED_APPLIED_ADMINS="$ENFORCE_ADMINS"
  EXPECTED_SIGS_ENABLED="true"
fi

# Closes 020G R3 correctness CORR3-001 + safety SAF-R3-001:
# preserve any FAIL=1 set by the apply-phase trap. Initialising
# FAIL=0 unconditionally would launder an apply-failure into a
# false-success when the pre-existing state happens to satisfy
# the verify checks. Default to 0 only if not already set.
FAIL="${FAIL:-0}"
[ "$CHECKS_STRICT" = "$EXPECTED_CHECKS_STRICT" ] || { echo "verify FAIL: required_status_checks.strict=${CHECKS_STRICT} (expected ${EXPECTED_CHECKS_STRICT})" >&2; FAIL=1; }
if [ "$RESTORE_MODE" -eq 1 ]; then
  if ! printf '%s' "$AFTER_JSON" | jq -e --argjson expected_contexts "$(printf '%s' "$RESTORE_TARGET_JSON" | jq '.required_status_checks.contexts // []')" '(.required_status_checks.contexts // []) as $a | ($a | sort) == ($expected_contexts | sort)' >/dev/null 2>&1; then
    echo "verify FAIL: contexts order-equivalent comparison failed (expected: ${EXPECTED_CHECKS_CONTEXTS}; got: ${CHECKS_CONTEXTS})" >&2
    FAIL=1
  fi
else
  if [ -n "$EXPECTED_CHECKS_CONTEXTS" ]; then
    [ "$CHECKS_CONTEXTS" = "$EXPECTED_CHECKS_CONTEXTS" ] || { echo "verify FAIL: contexts missing ${EXPECTED_CHECKS_CONTEXTS} (got: ${CHECKS_CONTEXTS})" >&2; FAIL=1; }
  else
    [ -z "$CHECKS_CONTEXTS" ] || { echo "verify FAIL: contexts expected to be empty (got: ${CHECKS_CONTEXTS})" >&2; FAIL=1; }
  fi
fi
[ "$APPLIED_ADMINS" = "$EXPECTED_APPLIED_ADMINS" ] || { echo "verify FAIL: enforce_admins=${APPLIED_ADMINS} (expected ${EXPECTED_APPLIED_ADMINS})" >&2; FAIL=1; }
[ "$SIGS_ENABLED" = "$EXPECTED_SIGS_ENABLED" ] || { echo "verify FAIL: required_signatures=${SIGS_ENABLED} (expected ${EXPECTED_SIGS_ENABLED})" >&2; FAIL=1; }

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
TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

LOG_FILE="docs/reviews/WP-SCP-020/branch-protection-log.md"

# Emit the log block. Use ~~~~ outer fence so inner ``` JSON
# fences nest correctly (CommonMark requires the closing fence
# to match the opening fence character; fence types ~~~ and ```
# do not collide). Closes 020G R1 correctness CORR-001.

if [ "$RESTORE_MODE" -eq 1 ]; then
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
- **Required check:** \`${RESTORE_TARGET_CHECKS_CONTEXTS_LOG}\`
- **enforce_admins:** ${RESTORE_TARGET_ADMINS_ENABLED}
- **Plan-only:** no
- **Restore mode:** yes${RESTORE_CAUTION_LINES_BLOCK}
- **Restoring TO:**
\`\`\`json
$(printf '%s' "$RESTORE_TARGET_JSON" | python3 -m json.tool 2>/dev/null || printf '%s' "$RESTORE_TARGET_JSON")
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
else
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
${FORWARD_CAUTION_LINES_BLOCK}- **PUT payload applied:**
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
fi

# Closes 020G R1 safety SAF-010: the script exits non-zero on
# verification failure even though the log block IS emitted, so
# the operator's calling shell still sees a hard fail.
if [ "${FAIL:-0}" -ne 0 ]; then
  exit 1
fi
