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

if [ -z "${base_ref}" ]; then
  echo "SCP_DIFF_BASE is required" >&2
  exit 1
fi

changed_files="$(git diff --name-only "${base_ref}..${head_ref}")"

if ! grep -Fxq "docs/DECISIONS.md" <<<"${changed_files}"; then
  echo "docs/DECISIONS.md must be part of the bypass diff" >&2
  exit 1
fi

if ! grep -Fxq "${waivers_path}" <<<"${changed_files}"; then
  echo "${waivers_path} must be part of the bypass diff" >&2
  exit 1
fi

if ! git diff --unified=0 "${base_ref}..${head_ref}" -- docs/DECISIONS.md | grep -Eq '^\+\|\s*D-0[0-9]{3}\s*\|\s*20[0-9]{2}-[0-9]{2}-[0-9]{2}\s*\|'; then
  echo "bypass diff must add a DECISIONS.md D-NNN table row" >&2
  exit 1
fi

if [ ! -f "${waivers_path}" ]; then
  echo "${waivers_path} does not exist at HEAD" >&2
  exit 1
fi

if ! jq -e --arg rule_id "${rule_id}" 'any(.[]?; .rule_id? == $rule_id)' "${waivers_path}" >/dev/null; then
  echo "waivers file is missing rule_id=${rule_id}" >&2
  exit 1
fi

if ! git diff --unified=20 "${base_ref}..${head_ref}" -- "${waivers_path}" | grep -Eq "^\+.*\"rule_id\"[[:space:]]*:[[:space:]]*\"${rule_id}\""; then
  echo "bypass diff must add a waivers entry for rule_id=${rule_id}" >&2
  exit 1
fi
