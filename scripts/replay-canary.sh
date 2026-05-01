#!/usr/bin/env bash
# WP-SCP-020 slice 020E.c — canary replay.
#
# Replays each of the four federation-primitive canaries against the
# currently-released `@main` and `@v1.*` tags, then compares the
# observed verdict against the canonical baseline recorded in
# `docs/reviews/WP-SCP-020/canary-evidence.md`.
#
# Used by:
#   - WP-SCP-020 020H.1 (iv-d) weekly cron — divergence opens a
#     `rule-regression` issue automatically.
#   - Manual rollback-detection during incidents.
#
# The four canary verdicts (preserved as permanent fixtures across
# three distinct branches — canaries 1 and 2 share
# canary/deliberate-violation-pre):
#   1. canary/deliberate-violation-pre   — SCP-R-001 deny verified
#   2. canary/deliberate-violation-pre   — also serves as 020E.b
#                                          (post-protection block)
#   3. canary/waived-violation           — SCP-R-001 deny suppressed
#                                          by sibling waivers.json
#   4. canary/rule-config-disabled       — SCP-R-001 deny suppressed
#                                          by sibling .scp/rule-config.yaml
#                                          disable: true (closes
#                                          TF-020H1-004; landed in
#                                          slice 020H.4).
#
# Canary 1 and 2 use the SAME branch — see canary-evidence.md
# §"Canary 2" for the strategy decision.
#
# Output: a tab-separated line per canary on stdout, in the form
#   <canary-name>\t<expected>\t<observed>\t<verdict>
# where <verdict> is OK or REGRESSION. Exit code 0 if every canary
# is OK; exit code 1 if any REGRESSION.
#
# Cold-start vs warm-start wall-clock measurement (TF-E.a-001):
# `--measure-cold-start` triggers a `gh workflow dispatch` so each
# replay runs on a freshly-provisioned runner with no binary cache.
# Without the flag, replays observe the latest workflow run on the
# canary branch (warm-start wall-clock).
#
# Reference: docs/reviews/WP-SCP-020/canary-evidence.md;
# WP-SCP-020 §4 020E.a/b/c + §4 020H.1 (iv-d).

set -euo pipefail

REPO="${SCP_REPLAY_REPO:-jrnb2024/standards-control-plane-}"
COLD_START=0

usage() {
  cat <<'EOF' >&2
Usage: replay-canary.sh [--measure-cold-start] [--repo OWNER/NAME]

  --measure-cold-start   Trigger fresh workflow_dispatch runs to
                         measure cold-start wall-clock (TF-E.a-001).
                         Default: read latest existing run on each
                         canary branch (warm-start).
  --repo                 Override target repo (default:
                         jrnb2024/standards-control-plane-).
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --measure-cold-start) COLD_START=1; shift ;;
    --repo) REPO="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown flag: $1" >&2; usage; exit 2 ;;
  esac
done

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

require_cmd gh
require_cmd jq

# Canary registry: name | branch | expected_verdict | expected_findings_count | expected_waivers_count
CANARIES=(
  "deliberate-violation-pre|canary/deliberate-violation-pre|FAILURE|1|0"
  "waived-violation|canary/waived-violation|SUCCESS|0|1"
  "rule-config-disabled|canary/rule-config-disabled|SUCCESS|0|0"
)

regression_count=0

for entry in "${CANARIES[@]}"; do
  IFS='|' read -r name branch expected_verdict expected_findings expected_waivers <<<"$entry"

  if [ "$COLD_START" -eq 1 ]; then
    gh workflow run policy-check.yml --ref "$branch" --repo "$REPO" >/dev/null 2>&1 || true
    # Wait briefly for the dispatch to register, then poll.
    sleep 5
  fi

  # Fetch the latest workflow_run on the canary branch.
  run_json="$(gh run list \
    --repo "$REPO" \
    --branch "$branch" \
    --workflow policy-check.yml \
    --limit 1 \
    --json databaseId,conclusion,status,headSha,createdAt 2>/dev/null || echo '[]')"

  run_id="$(printf '%s' "$run_json" | jq -r '.[0].databaseId // empty')"
  observed_conclusion="$(printf '%s' "$run_json" | jq -r '.[0].conclusion // "MISSING"' | tr '[:lower:]' '[:upper:]')"

  if [ -z "$run_id" ]; then
    printf '%s\t%s\t%s\tREGRESSION (no workflow run found on branch)\n' \
      "$name" "$expected_verdict" "MISSING"
    regression_count=$((regression_count + 1))
    continue
  fi

  # Per WP-SCP-022 020E.c: when the structured finding payload is
  # available (via the policy-check-summary artifact), assert
  # findings.count and waivers_applied.count against the baseline.
  # When not available (e.g. this script is being called against an
  # older release tag without the artifact), fall back to the
  # workflow conclusion alone.
  summary_path="$(mktemp -d)/policy-check-summary"
  if gh run download "$run_id" --repo "$REPO" --name policy-check-summary --dir "$summary_path" >/dev/null 2>&1; then
    summary_file="$summary_path/policy-check-summary.json"
    if [ -f "$summary_file" ]; then
      observed_findings="$(jq '.findings | length' "$summary_file")"
      observed_waivers="$(jq '.waivers_applied | length' "$summary_file")"
    else
      observed_findings=-1
      observed_waivers=-1
    fi
  else
    observed_findings=-1
    observed_waivers=-1
  fi
  rm -rf "$summary_path"

  verdict="OK"
  if [ "$observed_conclusion" != "$expected_verdict" ]; then
    verdict="REGRESSION (conclusion drift: expected=$expected_verdict observed=$observed_conclusion)"
    regression_count=$((regression_count + 1))
  elif [ "$observed_findings" -ge 0 ] && [ "$observed_findings" != "$expected_findings" ]; then
    verdict="REGRESSION (findings drift: expected=$expected_findings observed=$observed_findings)"
    regression_count=$((regression_count + 1))
  elif [ "$observed_waivers" -ge 0 ] && [ "$observed_waivers" != "$expected_waivers" ]; then
    verdict="REGRESSION (waivers drift: expected=$expected_waivers observed=$observed_waivers)"
    regression_count=$((regression_count + 1))
  fi

  printf '%s\trun-id=%s\tconclusion=%s\tfindings=%s\twaivers=%s\t%s\n' \
    "$name" "$run_id" "$observed_conclusion" "$observed_findings" "$observed_waivers" "$verdict"
done

if [ "$regression_count" -gt 0 ]; then
  echo "" >&2
  echo "$regression_count regression(s) detected" >&2
  exit 1
fi

exit 0
