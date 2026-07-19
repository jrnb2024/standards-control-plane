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

scp_policy_check_prepare_manifest_targets() {
  # Rewrites the changed-files manifest in place: each changed file that a
  # content rule declares an interest in (policies/rule-inputs.yaml — the
  # rule input contract) is replaced by a YAML surrogate (written under
  # RUNNER_TEMP) that conftest can parse, and SCP_R003_MANIFEST_APPLICABLE
  # is exported via GITHUB_ENV so the downstream SCP-R-003 manifest step
  # knows whether any vendoring manifest was in scope. Inputs (env):
  # SCP_CHANGED_FILES_PATH (default changed-files.txt), RUNNER_TEMP
  # (surrogate root parent), GITHUB_ENV (flag sink; the write is skipped
  # when GITHUB_ENV is unset, e.g. a non-CI/local invocation),
  # SCP_RULE_INPUTS_PATH (contract override; defaults to the
  # policies/rule-inputs.yaml sibling of this lib file).
  #
  # WP-SCP-025 v2: the feed used to hardcode the three vendoring-manifest
  # basenames, which silently starved every OTHER content rule of input —
  # SCP-R-008 (.env secrets) and SCP-R-012 (schema migrations) could never
  # fire on a real PR. The set is now declared per-rule in the contract and
  # the feed surrogates the union; a missing/malformed contract HARD-FAILS
  # in CI (SCP-E002) rather than degrading to a narrower feed. Outside CI
  # (local/unit-test invocations without the repo checkout) it falls back
  # to the built-in SCP-R-003 manifest set with a stderr warning — the
  # pre-contract behaviour, never less.
  #
  # Extracted from the former inline "Prepare manifest evaluation targets"
  # workflow step (plus the deleted-manifest fix below) so the logic is
  # directly unit-testable with a synthetic changed-files.txt — see
  # tests/workflow/test_prepare_manifest_targets.py. lib/ is an
  # internal-only surface per policies/VERSIONING.md §Scope (refactored
  # without notice).
  local scp_lib_dir
  scp_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  SCP_RULE_INPUTS_RESOLVED="${SCP_RULE_INPUTS_PATH:-${scp_lib_dir}/../policies/rule-inputs.yaml}" \
    python3 - <<'PY'
import json
import os
import re
import sys
from pathlib import Path

changed_files_path = Path(os.environ.get("SCP_CHANGED_FILES_PATH", "changed-files.txt"))
transformed_root = Path(os.environ["RUNNER_TEMP"]) / "scp-policy-manifest-surrogates"
transformed_root.mkdir(parents=True, exist_ok=True)

contract_path = Path(os.environ["SCP_RULE_INPUTS_RESOLVED"])
in_ci = os.environ.get("GITHUB_ACTIONS") == "true"

# Pre-contract behaviour: the SCP-R-003 vendoring-manifest set. Used ONLY as
# the non-CI fallback — in CI a missing contract is a hard SCP-E002 (a broken
# contract must never silently re-narrow the feed; that is the exact failure
# mode the contract exists to kill).
FALLBACK_ENTRIES = [
    ("SCP-R-003", "basename_regex", re.compile(r"^(package\.json|pyproject\.toml|go\.mod)$")),
]


def fail(message: str) -> None:
    print(f"::error file={contract_path},title=SCP-E002::{message}")
    raise SystemExit(1)


def fallback(reason: str):
    if in_ci:
        fail(f"{reason} — refusing to degrade to the narrower built-in feed in CI")
    sys.stderr.write(
        f"{reason}; falling back to the built-in SCP-R-003 manifest feed "
        "(content rules beyond SCP-R-003 will not be fed)\n"
    )
    return FALLBACK_ENTRIES


def parse_contract_text(text: str):
    """Strict stdlib parser for the rule-inputs contract.

    Deliberately NOT PyYAML: this function must run identically in every
    context that sources the lib — including the stdlib-only
    prepare-manifest-targets-unit CI job and bare local shells — and a
    parser dependency that is present in some contexts but not others is
    exactly the kind of environment-dependent feed divergence the contract
    exists to kill. The contract grammar is a rigid, repo-controlled YAML
    subset (documented in policies/rule-inputs.yaml): full-line comments
    and blank lines anywhere; `schema_version: 1`; `rules:`; entries of
    `- rule_id: <token>` / `  match:` / `    <kind>: '<regex>'` at exact
    2/4/6-space indents. ANYTHING else is a hard parse error — fail-closed,
    never a guess."""
    schema_seen = False
    rules_seen = False
    entries: list[tuple[str, str, str]] = []  # (rule_id, kind, raw_pattern)
    pending_rule_id = None
    pending_match_open = False

    def unquote(value: str, what: str) -> str:
        value = value.strip()
        if len(value) >= 2 and value[0] == "'" and value[-1] == "'":
            return value[1:-1].replace("''", "'")
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            fail(f"{what}: use single-quoted patterns (double-quoted YAML escapes are not part of the contract subset)")
        return value

    for lineno, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        where = f"line {lineno}"
        if raw.startswith("schema_version:"):
            if raw.split(":", 1)[1].strip() != "1":
                fail(f"{where}: schema_version must be 1")
            schema_seen = True
        elif raw == "rules:":
            rules_seen = True
        elif raw.startswith("  - rule_id:"):
            if not rules_seen:
                fail(f"{where}: rule entry before rules:")
            if pending_rule_id is not None:
                fail(f"{where}: previous rule entry ({pending_rule_id}) has no completed match block")
            pending_rule_id = raw.split(":", 1)[1].strip()
            if not pending_rule_id:
                fail(f"{where}: rule_id must be a non-empty token")
            pending_match_open = False
        elif raw == "    match:":
            if pending_rule_id is None:
                fail(f"{where}: match: outside a rule entry")
            if pending_match_open:
                fail(f"{where}: duplicate match: in rule entry ({pending_rule_id})")
            pending_match_open = True
        elif raw.startswith("      ") and ":" in raw:
            if not pending_match_open:
                fail(f"{where}: pattern line outside a match: block (each rule declares exactly one of basename_regex | path_regex)")
            kind, _, value = raw.strip().partition(":")
            if kind not in ("basename_regex", "path_regex"):
                fail(f"{where}: unknown match kind {kind!r} (exactly one of basename_regex | path_regex)")
            pattern = unquote(value, f"{where} ({pending_rule_id})")
            if not pattern:
                fail(f"{where}: {kind} must be a non-empty pattern")
            entries.append((pending_rule_id, kind, pattern))
            pending_rule_id = None
            pending_match_open = False
        else:
            fail(f"{where}: unrecognised contract line {raw!r} (strict subset; see policies/rule-inputs.yaml header)")

    if not schema_seen:
        fail("rule-inputs contract must declare schema_version: 1")
    if pending_rule_id is not None:
        fail(f"rule entry ({pending_rule_id}) has no completed match block (exactly one of basename_regex | path_regex)")
    if not entries:
        fail("rule-inputs contract must declare a non-empty rules: list")
    return entries


def load_contract():
    if not contract_path.is_file():
        return fallback(f"rule-inputs contract not found at {contract_path}")
    parsed = parse_contract_text(contract_path.read_text(encoding="utf-8"))
    entries = []
    for rule_id, kind, pattern in parsed:
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            fail(f"({rule_id}) {kind} does not compile: {exc}")
        entries.append((rule_id, kind, compiled))
    return entries


contract_entries = load_contract()


def matched_rule_ids(path: str) -> list[str]:
    basename = Path(path).name
    matched = []
    for rule_id, kind, regex in contract_entries:
        subject = basename if kind == "basename_regex" else path
        # .search() (not .match()) for BOTH kinds: contract patterns carry
        # their own anchors. basename patterns are ^…$-anchored so search
        # degenerates to full-match; path patterns like (^|/)versions/…
        # MUST be able to hit mid-path — .match() would silently unfeed
        # nested paths (alembic/versions/…) and recreate the P0.
        if regex.search(subject):
            matched.append(rule_id)
    return matched


rewritten: list[str] = []
manifest_count = 0

for index, raw_line in enumerate(changed_files_path.read_text().splitlines()):
    path = raw_line.strip()
    if not path:
        continue

    name = Path(path).name
    rule_ids = matched_rule_ids(path)
    if not rule_ids:
        rewritten.append(path)
        continue

    source = Path(path)
    if not source.is_file():
        # No regular file at HEAD for this manifest path = nothing to
        # evaluate, so skip it. The common case is a manifest DELETED in the
        # PR diff: the adopter-mode enumeration (`git diff --name-only
        # BASE..HEAD`) INCLUDES deletions. is_file() is also False for a path
        # that is a directory or a broken symlink — equally no regular-file
        # content to attest, so the skip is correct for all of them (a
        # symlink pointing at a real regular file resolves True and IS
        # evaluated). A deletion/absence carries no vendoring-attestation
        # surface to hide, so skipping cannot mask an evasion. The previous
        # `sys.exit(1)` here (SCP-E002) was
        # over-broad: it blocked the required gate on any adopter PR that
        # retired a vendored module's go.mod (e.g. mapp-pim #403). The
        # manifest_count bump now lives AFTER this skip so a pure deletion
        # cannot flip SCP_R003_MANIFEST_APPLICABLE true for a no-op.
        continue

    if "SCP-R-003" in rule_ids:
        manifest_count += 1
    content = source.read_text(encoding="utf-8")
    surrogate = transformed_root / f"{index:04d}-{name}.yaml"
    yaml_payload = [
        f"source_file: {json.dumps(path)}",
        "content: |-",
    ]
    for line in content.splitlines():
        yaml_payload.append(f"  {line}")
    if content.endswith("\n"):
        yaml_payload.append("  ")
    surrogate.write_text("\n".join(yaml_payload) + "\n", encoding="utf-8")
    rewritten.append(str(surrogate))

changed_files_path.write_text("".join(f"{entry}\n" for entry in rewritten), encoding="utf-8")

github_env = os.environ.get("GITHUB_ENV")
if github_env:
    with Path(github_env).open("a", encoding="utf-8") as handle:
        handle.write(f"SCP_R003_MANIFEST_APPLICABLE={'true' if manifest_count else 'false'}\n")
PY
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
  #
  # 024B-extras-1 fix-round-24 (narrows fix-round-23 over-broad
  # `docs/reviews/*`):
  # exclude only audit-artifact JSON files generated by Sonnet R1 lens,
  # Codex executor, and dispatch packages. The original fix-round-23
  # pattern `docs/reviews/*` was too broad — it would have silently
  # bypassed policy evaluation of rule-RFC files at
  # `docs/reviews/rule-proposals/` (R23 SAFE-R23-002 closure). Markdown
  # files under `docs/reviews/` are already filtered by the extension-
  # based filter below; only parseable JSON in audit paths needs
  # explicit path-glob exclusion. Rule-RFC YAML or JSON files under
  # `docs/reviews/rule-proposals/` remain policy-evaluable.
  # References: TF-006 / WP-SCP-022 020Q precedent; R23 SAFE-R23-001/002
  # + CG-001/002 closures.
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
      docs/reviews/*/r1-*.json|\
      docs/reviews/*/r*-archive/*.json|\
      docs/reviews/*/dispatches/*/*.json|\
      docs/reviews/*/dispatches/*.json|\
      docs/reviews/*/r23-fix23/*.json|\
      docs/reviews/*/r24-*/*.json)
        if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
          printf '::debug::skipping %s: Sonnet R1 / Codex / dispatch audit artifact, not policy input (closes R23 SAFE-R23-001/002)\n' "$target"
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

  # No .json suffix: BSD/macOS mktemp only substitutes trailing X's, so a
  # suffixed template creates the literal file and every later run fails.
  conftest_json="$(mktemp "${TMPDIR:-/tmp}/scp-conftest-out.XXXXXX")"
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
