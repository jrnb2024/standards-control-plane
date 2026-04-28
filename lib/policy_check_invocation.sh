#!/usr/bin/env bash
set -euo pipefail

scp_policy_check_emit_error() {
  local code="$1"
  local file="$2"
  local message="$3"

  if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
    printf '::error file=%s,title=%s::%s\n' "$file" "$code" "$message"
    return
  fi

  printf '%s %s: %s\n' "$code" "$file" "$message" >&2
}

scp_policy_check_output_dir() {
  printf '%s\n' "${SCP_POLICY_CHECK_OUTPUT_DIR:-output/findings}"
}

scp_policy_check_policy_dir() {
  local policy_root="${SCP_POLICY_CHECK_POLICY_ROOT:-policies}"
  local rule_set="${SCP_RULE_SET:-starter}"
  if [ "$rule_set" = "starter" ]; then
    printf '%s\n' "$policy_root"
    return
  fi
  printf '%s/%s\n' "$policy_root" "$rule_set"
}

scp_policy_check_sha256_file() {
  local path="$1"

  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$path" | awk '{print $1}'
    return
  fi

  sha256sum "$path" | awk '{print $1}'
}

scp_policy_check_verify_runtime_binary() {
  local label="$1"
  local path="$2"
  local expected="$3"
  local actual

  if [ -z "$path" ] || [ -z "$expected" ]; then
    scp_policy_check_emit_error "SCP-E001" "${path:-<unset>}" "${label} runtime binary verification refused: empty path or expected SHA256 (caller must set both)"
    return 1
  fi

  if [ ! -f "$path" ]; then
    scp_policy_check_emit_error "SCP-E001" "$path" "${label} runtime binary is missing at the configured path"
    return 1
  fi

  actual="$(scp_policy_check_sha256_file "$path")"
  if [ "$actual" != "$expected" ]; then
    scp_policy_check_emit_error "SCP-E001" "$path" "${label} runtime binary failed SHA256 verification immediately before execution"
    return 1
  fi
}

scp_policy_check_verify_runtime_binaries() {
  local missing=()
  [ -z "${SCP_POLICY_CHECK_OPA_BIN:-}" ] && missing+=("SCP_POLICY_CHECK_OPA_BIN")
  [ -z "${SCP_POLICY_CHECK_OPA_SHA256:-}" ] && missing+=("SCP_POLICY_CHECK_OPA_SHA256")
  [ -z "${SCP_POLICY_CHECK_CONFTEST_BIN:-}" ] && missing+=("SCP_POLICY_CHECK_CONFTEST_BIN")
  [ -z "${SCP_POLICY_CHECK_CONFTEST_SHA256:-}" ] && missing+=("SCP_POLICY_CHECK_CONFTEST_SHA256")
  if [ ${#missing[@]} -gt 0 ]; then
    scp_policy_check_emit_error "SCP-E001" "<env>" "runtime binary verification refused: required env vars unset: ${missing[*]}"
    return 1
  fi

  scp_policy_check_verify_runtime_binary \
    "OPA" \
    "$SCP_POLICY_CHECK_OPA_BIN" \
    "$SCP_POLICY_CHECK_OPA_SHA256" || return 1

  scp_policy_check_verify_runtime_binary \
    "Conftest" \
    "$SCP_POLICY_CHECK_CONFTEST_BIN" \
    "$SCP_POLICY_CHECK_CONFTEST_SHA256" || return 1
}

scp_policy_check_init_outputs() {
  local output_dir
  local policy_dir
  local rule_config_path

  output_dir="$(scp_policy_check_output_dir)"
  policy_dir="$(scp_policy_check_policy_dir)"
  rule_config_path="${SCP_RULE_CONFIG_PATH:-.scp/rule-config.yaml}"

  if [ -e "$rule_config_path" ] && [ ! -f "$rule_config_path" ]; then
    scp_policy_check_emit_error "SCP-E002" "$rule_config_path" "rule-config-path must point to a regular file when present"
    return 1
  fi

  if [ -e "$policy_dir" ] && [ ! -d "$policy_dir" ]; then
    scp_policy_check_emit_error "SCP-E002" "$policy_dir" "policy bundle path must be a directory when present"
    return 1
  fi

  mkdir -p "$output_dir"
  printf '[]\n' > "${output_dir}/policy-findings.json"
  printf '[]\n' > "${output_dir}/disabled-rules.json"
  printf '[]\n' > "${output_dir}/waivers-applied.json"
  printf '{"run": false, "disagreements": []}\n' > "${output_dir}/conflict-gate.json"
}

scp_policy_check_run() {
  local changed_files_path
  local conftest_json
  local output_dir
  local policy_dir
  local rule_config_path
  local waivers_path
  local -a conftest_args
  local -a targets
  local target

  scp_policy_check_init_outputs || return 1

  changed_files_path="${SCP_CHANGED_FILES_PATH:-changed-files.txt}"
  output_dir="$(scp_policy_check_output_dir)"
  policy_dir="$(scp_policy_check_policy_dir)"
  rule_config_path="${SCP_RULE_CONFIG_PATH:-.scp/rule-config.yaml}"
  waivers_path="${SCP_WAIVERS_PATH:-output/findings/waivers.json}"

  if [ ! -f "$changed_files_path" ]; then
    scp_policy_check_emit_error "SCP-E002" "$changed_files_path" "changed-files manifest is required before invoking Conftest"
    return 1
  fi

  if [ ! -d "$policy_dir" ]; then
    if [ "${SCP_RULE_SET:-starter}" = "starter" ] && [ "$policy_dir" = "policies" ]; then
      return 0
    fi

    scp_policy_check_emit_error "SCP-E002" "$policy_dir" "policy bundle path does not exist for the selected rule-set"
    return 1
  fi

  if ! find "$policy_dir" -type f -name '*.rego' -print -quit | grep -q .; then
    return 0
  fi

  while IFS= read -r target; do
    if [ -n "$target" ]; then
      targets+=("$target")
    fi
  done < "$changed_files_path"

  if [ "${#targets[@]}" -eq 0 ]; then
    return 0
  fi

  scp_policy_check_verify_runtime_binaries || return 1

  if ! command -v conftest >/dev/null 2>&1; then
    scp_policy_check_emit_error "SCP-E001" "conftest" "Conftest must be on PATH before invoking the shared policy-check library"
    return 1
  fi

  conftest_json="$(mktemp "${TMPDIR:-/tmp}/scp-conftest.XXXXXX.json")"
  conftest_args=(test --no-fail --output json --policy "$policy_dir")

  if [ -f "$waivers_path" ]; then
    conftest_args+=(--data "$waivers_path")
  fi

  if [ -f "$rule_config_path" ]; then
    conftest_args+=(--data "$rule_config_path")
  fi

  if ! conftest "${conftest_args[@]}" "${targets[@]}" > "$conftest_json"; then
    rm -f "$conftest_json"
    scp_policy_check_emit_error "SCP-E002" "$policy_dir" "Conftest invocation failed while loading the policy bundle or evaluating the changed-file set"
    return 1
  fi

  python3 - "$conftest_json" "${output_dir}/policy-findings.json" <<'PY'
import json
import sys
from pathlib import Path

source_path = Path(sys.argv[1])
target_path = Path(sys.argv[2])
payload = json.loads(source_path.read_text())
findings: list[dict[str, str]] = []

for result in payload if isinstance(payload, list) else []:
    filename = str(result.get("filename", ""))
    failures = result.get("failures", [])
    if not isinstance(failures, list):
        continue
    for failure in failures:
        finding = {
            "verdict": "deny",
            "rule_id": "",
            "file": filename,
            "path": filename,
            "message": "",
            "remediation_url": "",
        }
        if isinstance(failure, dict):
            metadata = failure.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            rule_id = failure.get("rule_id") or metadata.get("rule_id") or failure.get("code") or ""
            remediation_url = failure.get("remediation_url") or metadata.get("remediation_url") or ""
            file_value = failure.get("file") or failure.get("path") or filename
            message = (
                failure.get("message")
                or failure.get("msg")
                or failure.get("deny")
                or json.dumps(failure, sort_keys=True)
            )
            finding.update(
                {
                    "rule_id": str(rule_id),
                    "file": str(file_value),
                    "path": str(file_value),
                    "message": str(message),
                    "remediation_url": str(remediation_url),
                }
            )
        else:
            finding["message"] = str(failure)
        findings.append(finding)

target_path.write_text(json.dumps(findings, indent=2) + "\n")
PY

  rm -f "$conftest_json"
}

scp_policy_check_print_effective_denies() {
  local output_dir

  output_dir="$(scp_policy_check_output_dir)"
  python3 - "${output_dir}/policy-findings.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    raise SystemExit(0)

payload = json.loads(path.read_text())
for finding in payload:
    if finding.get("verdict") != "deny":
        continue
    print(json.dumps(finding, separators=(",", ":")), file=sys.stderr)
PY
}

scp_policy_check_threshold_ok() {
  local output_dir

  output_dir="$(scp_policy_check_output_dir)"
  python3 - "${output_dir}/policy-findings.json" "${SCP_THRESHOLD:-deny}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
threshold = sys.argv[2]
if not path.exists():
    raise SystemExit(0)

payload = json.loads(path.read_text())
denies = [item for item in payload if item.get("verdict") == "deny"]
raise SystemExit(1 if threshold == "deny" and denies else 0)
PY
}
