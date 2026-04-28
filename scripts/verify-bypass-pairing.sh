#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <bypass-rule-id>" >&2
  exit 1
fi

rule_id="$1"
base_ref="${SCP_DIFF_BASE:-}"
head_ref="${SCP_DIFF_HEAD:-HEAD}"
waivers_path="${SCP_WAIVERS_PATH:-output/findings/waivers.json}"
waivers_path="${waivers_path#./}"

if [ -z "${base_ref}" ]; then
  echo "SCP_DIFF_BASE is required" >&2
  exit 1
fi

changed_files="$(git diff --name-only "${base_ref}..${head_ref}")"
decisions_diff="$(git diff --unified=0 "${base_ref}..${head_ref}" -- docs/DECISIONS.md)"

if ! grep -Fxq "docs/DECISIONS.md" <<<"${changed_files}"; then
  echo "docs/DECISIONS.md must be part of the bypass diff" >&2
  exit 1
fi

if ! grep -Fxq "${waivers_path}" <<<"${changed_files}"; then
  echo "${waivers_path} must be part of the bypass diff" >&2
  exit 1
fi

decision_row="$(printf '%s\n' "${decisions_diff}" | grep -E '^\+\|\s*D-[0-9]{3}\s*\|\s*20[0-9]{2}-[0-9]{2}-[0-9]{2}\s*\|' | grep -F -- "${rule_id}" | head -n 1 || true)"
if [ -z "${decision_row}" ]; then
  echo "bypass diff must add a DECISIONS.md D-NNN table row" >&2
  exit 1
fi

if [ ! -f "${waivers_path}" ]; then
  echo "${waivers_path} does not exist at HEAD" >&2
  exit 1
fi

base_waivers_file="$(mktemp)"
trap 'rm -f "${base_waivers_file}"' EXIT

if ! git show "${base_ref}:${waivers_path}" >"${base_waivers_file}" 2>/dev/null; then
  printf '[]\n' >"${base_waivers_file}"
fi

matching_waiver="$(
  jq -c --arg rule_id "${rule_id}" --slurpfile base "${base_waivers_file}" '
    first(
      .[]?
      | select(.rule_id? == $rule_id)
      | select((. as $entry | any($base[0][]?; . == $entry)) | not)
    ) // empty
  ' "${waivers_path}"
)"

if [ -z "${matching_waiver}" ]; then
  echo "bypass diff must add a waivers entry for rule_id=${rule_id}" >&2
  exit 1
fi

expires_at="$(jq -r '.expires_at // empty' <<<"${matching_waiver}")"
if [ -z "${expires_at}" ]; then
  echo "waivers entry for rule_id=${rule_id} must define expires_at" >&2
  exit 1
fi

normalized_expires_at="$(python3 - "${expires_at}" <<'PY'
from datetime import date, datetime, time, timezone
import sys

raw = sys.argv[1]

try:
    if "T" in raw:
        expiry = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
        valid = expiry > datetime.now(timezone.utc)
        normalized = expiry.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    else:
        expiry = date.fromisoformat(raw)
        valid = expiry > datetime.now(timezone.utc).date()
        normalized = datetime.combine(expiry, time.min, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
except ValueError:
    sys.exit(2)

if not valid:
    sys.exit(1)

print(normalized)
PY
)" || {
  status=$?
  if [ "${status}" -eq 2 ]; then
    echo "waivers entry for rule_id=${rule_id} has an invalid expires_at value: ${expires_at}" >&2
  else
    echo "waivers entry for rule_id=${rule_id} is expired: ${expires_at}" >&2
  fi
  exit 1
}

decision_id="$(grep -oE 'D-[0-9]{3}' <<<"${decision_row}" | head -n 1)"
printf 'decision_id=%s\n' "${decision_id}"
printf 'expires_at=%s\n' "${expires_at}"
printf 'waiver_expires_at=%s\n' "${normalized_expires_at}"
