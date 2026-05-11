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
  local data_dir
  local output_dir
  local policy_dir
  local rule_config_path
  local waivers_path
  local -a conftest_args
  # Closes WP-SCP-022 slice 020D1/020H.1 CI fixpoint #1 (2026-04-30):
  # `local -a targets` (without initialiser) declares the array but
  # leaves it unset. Under `set -u`, `${#targets[@]}` then trips
  # 'unbound variable' if the loop's case statement never runs the
  # `targets+=("$target")` branch — which happens when every file in
  # the changed-files manifest has an extension conftest cannot parse
  # (.md, .py, .rego, .sh, ...). The 020D1 PR diff was workflow-yaml-
  # only so the bug was masked; 020H.1's diff is .md-only and
  # tripped it. Initialising to empty fixes the cold-start case.
  local -a targets=()
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

  # WP-SCP-022 020C.1 selftest exposed: conftest can't parse .md /
  # other-text files; passing them in the target list crashes the
  # whole evaluation with `unknown parser: md`. Filter to file
  # extensions conftest can natively load. Manifest files
  # (package.json, pyproject.toml, go.mod) are already rewritten
  # into yaml surrogates by the workflow's "Prepare manifest
  # evaluation targets" step, so they enter this loop as `.yaml`.
  #
  # WP-SCP-022 slice 020Q (closes TF-006): also skip
  # `tests/conflict_gate/fixtures/**` paths — those fixtures exist
  # to be audited BY the conflict-gate test framework
  # (`tests/conflict_gate/test_conflict_gate.py`), which loads sibling
  # `waivers.json` / `.scp/rule-config.yaml` and passes them to OPA via
  # `--data`. Auditing them here from the production policy-check
  # workflow would fire raw rule denies (e.g. SCP-R-001 on a fixture
  # `services.yml` with an unapproved mode) without the suppression
  # context the fixture is designed to exercise. The fixture-corpus
  # invariant is enforced by the conflict-gate pytest layer; the
  # production policy-check should not re-audit these files.
  local target_basename
  local target_ext
  while IFS= read -r target; do
    if [ -z "$target" ]; then
      continue
    fi
    case "$target" in
      tests/conflict_gate/fixtures/*)
        if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
          printf '::debug::skipping %s: conflict-gate fixture (audited by pytest layer, closes 020Q)\n' "$target"
        fi
        continue
        ;;
      docs/reviews/*)
        if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
          printf '::debug::skipping %s: governance review artifact (Claude SDK output / dispatch package), not policy input\n' "$target"
        fi
        continue
        ;;
    esac
    target_basename="$(basename "$target")"
    target_ext="${target_basename##*.}"
    case "$target_ext" in
      yml|yaml|json|toml|hcl|ini|properties|cue|edn|xml)
        targets+=("$target")
        ;;
      *)
        # Conftest cannot parse this file type; skip silently.
        # Document via debug for diagnosability.
        if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
          printf '::debug::skipping %s: conftest has no parser for .%s\n' "$target" "$target_ext"
        fi
        ;;
    esac
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

  # WP-SCP-022 slice 020C.1: wrap caller-side waivers + rule-config so
  # they land at predictable namespaces in the Rego data document
  # (data.waivers / data.rule_config) regardless of conftest's
  # filename-derived merge semantics. See policies/scp_common.rego.
  data_dir="$(mktemp -d "${TMPDIR:-/tmp}/scp-data.XXXXXX")"

  if [ -f "$waivers_path" ]; then
    if ! python3 - "$waivers_path" "${data_dir}/waivers.json" <<'PY'
import json
import sys

source = sys.argv[1]
dest = sys.argv[2]
try:
    with open(source, "r", encoding="utf-8") as handle:
        content = json.load(handle)
except Exception:
    # Defensive: malformed waivers.json should not crash the policy run;
    # SCP-R-002 will deny it as part of the regular evaluation.
    content = []
with open(dest, "w", encoding="utf-8") as handle:
    json.dump({"waivers": content}, handle)
PY
    then
      rm -rf "$data_dir"
      rm -f "$conftest_json"
      scp_policy_check_emit_error "SCP-E002" "$waivers_path" "waivers data wrapper failed to write"
      return 1
    fi
    conftest_args+=(--data "${data_dir}/waivers.json")
  fi

  if [ -f "$rule_config_path" ]; then
    if ! python3 - "$rule_config_path" "${data_dir}/rule_config.json" <<'PY'
import json
import sys

try:
    import yaml  # type: ignore
except ImportError:
    sys.stderr.write("pyyaml not installed; skipping rule-config wrap (rule-config disables will not apply)\n")
    raise SystemExit(0)

source = sys.argv[1]
dest = sys.argv[2]
try:
    with open(source, "r", encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}
except Exception as exc:
    sys.stderr.write(f"rule-config parse failed: {exc}\n")
    raise SystemExit(1)
if not isinstance(content, dict):
    content = {}
with open(dest, "w", encoding="utf-8") as handle:
    json.dump({"rule_config": content}, handle)
PY
    then
      rm -rf "$data_dir"
      rm -f "$conftest_json"
      scp_policy_check_emit_error "SCP-E002" "$rule_config_path" "rule-config data wrapper failed to write"
      return 1
    fi
    if [ -f "${data_dir}/rule_config.json" ]; then
      conftest_args+=(--data "${data_dir}/rule_config.json")
    fi
  fi

  if ! conftest "${conftest_args[@]}" "${targets[@]}" > "$conftest_json"; then
    rm -rf "$data_dir"
    rm -f "$conftest_json"
    scp_policy_check_emit_error "SCP-E002" "$policy_dir" "Conftest invocation failed while loading the policy bundle or evaluating the changed-file set"
    return 1
  fi

  python3 - "$conftest_json" "${output_dir}/policy-findings.json" "${output_dir}/waivers-applied.json" "${output_dir}/disabled-rules.json" <<'PY'
import json
import sys
from pathlib import Path

source_path = Path(sys.argv[1])
findings_target = Path(sys.argv[2])
waivers_target = Path(sys.argv[3])
disabled_target = Path(sys.argv[4])

payload = json.loads(source_path.read_text())
findings: list[dict[str, str]] = []
waivers_applied: list[dict[str, str]] = []
disabled_rules: list[dict[str, str]] = []

# WP-SCP-022 slice 020C.1: existing disabled-rules.json may already hold
# system-applied entries (e.g. SCP-R-003 no-manifest-applicable) written
# by other workflow steps. Preserve those, then append rule-config /
# waiver entries derived from this conftest run.
if disabled_target.exists():
    try:
        existing_disabled = json.loads(disabled_target.read_text())
        if isinstance(existing_disabled, list):
            disabled_rules = [item for item in existing_disabled if isinstance(item, dict)]
    except json.JSONDecodeError:
        disabled_rules = []

if waivers_target.exists():
    try:
        existing_waivers = json.loads(waivers_target.read_text())
        if isinstance(existing_waivers, list):
            waivers_applied = [item for item in existing_waivers if isinstance(item, dict)]
    except json.JSONDecodeError:
        waivers_applied = []

# Deduplication keyed on the observable identity. For waivers, the
# (rule_id, finding_id, expires_at) triple. For disabled_rules, the
# (rule_id, reason) pair — the run only ever emits one expires_at per
# (rule, reason), so the pair is sufficient.
waivers_seen = {(w.get("rule_id", ""), w.get("finding_id", ""), w.get("expires_at", "")) for w in waivers_applied}
disabled_seen = {(d.get("rule_id", ""), d.get("reason", "")) for d in disabled_rules}

for result in payload if isinstance(payload, list) else []:
    filename = str(result.get("filename", ""))
    failures = result.get("failures", [])
    if isinstance(failures, list):
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

    warnings = result.get("warnings", [])
    if not isinstance(warnings, list):
        continue
    for warning in warnings:
        if not isinstance(warning, dict):
            continue
        kind = warning.get("kind", "")
        if not kind:
            metadata = warning.get("metadata", {})
            kind = metadata.get("kind", "") if isinstance(metadata, dict) else ""
        rule_id = warning.get("rule_id", "")
        if not rule_id:
            metadata = warning.get("metadata", {})
            rule_id = metadata.get("rule_id", "") if isinstance(metadata, dict) else ""
        if kind == "waiver":
            entry = {
                "expires_at": str(warning.get("expires_at", "")),
            }
            if rule_id:
                entry["rule_id"] = str(rule_id)
            finding_id = warning.get("finding_id", "")
            if finding_id:
                entry["finding_id"] = str(finding_id)
            file_value = warning.get("file", "")
            if file_value:
                entry["file"] = str(file_value)
            key = (entry.get("rule_id", ""), entry.get("finding_id", ""), entry.get("expires_at", ""))
            if key in waivers_seen:
                continue
            waivers_seen.add(key)
            waivers_applied.append(entry)
        elif kind == "rule_config":
            entry = {
                "rule_id": str(rule_id),
                "reason": str(warning.get("reason", "rule-config override")),
                "expires_at": str(warning.get("expires_at", "")),
            }
            key = (entry["rule_id"], entry["reason"])
            if key in disabled_seen:
                continue
            disabled_seen.add(key)
            disabled_rules.append(entry)

findings_target.write_text(json.dumps(findings, indent=2) + "\n")
waivers_target.write_text(json.dumps(waivers_applied, indent=2) + "\n")
disabled_target.write_text(json.dumps(disabled_rules, indent=2) + "\n")
PY

  rm -rf "$data_dir"
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
