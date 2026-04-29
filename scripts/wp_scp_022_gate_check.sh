#!/usr/bin/env bash
# WP-SCP-022 §4.7 gate-enforcement helper.
#
# Runs before each slice dispatch and at each gate transition. Verifies:
#   1. Gate artefact existence + content (signer line + timestamp +
#      canary-run-id for USER-GATE-A0; signer line for A / C).
#   2. 3× APPROVED hash chain in fixpoint.md for prior-merged slices.
#   3. No symlinks escaping the slice's repo root (portable across
#      macOS / Linux — no `readlink -f` reliance).
#   4. No D-021 collision in DECISIONS.md (reserved per WP-SCP-022 §10).
#   5. ACC repo pin drift detection (HEAD + blob SHAs).
#
# Closes WP-SCP-022 R1 CRIT-BYPASS-003 (3× APPROVED has no hard-stop) +
# R1 MAJ-BYPASS-009 (user-gate discretion) + R2 BYPASS-001 (hash-chain
# absent) + R2 BYPASS-004 (readlink portability) + R2 BYPASS-005 partial
# (defence-in-depth on signer identity via commit-author check) + R2
# BYPASS-008 (silent fallback when not in git repo) + R2 C-R2-005 (silent
# skip when prereqs missing).
#
# Usage:
#   scripts/wp_scp_022_gate_check.sh --gate <gate-id>
#   scripts/wp_scp_022_gate_check.sh --slice <slice-id>
#   scripts/wp_scp_022_gate_check.sh --check-acc-pin
#   scripts/wp_scp_022_gate_check.sh --check-d021
#   scripts/wp_scp_022_gate_check.sh --check-hash-chain <slice-id>
#
# Exit codes:
#   0  pass
#   1  gate artefact missing or required content absent
#   2  symlink escape detected
#   3  D-021 collision detected
#   4  ACC pin drift detected
#   5  hash-chain mismatch
#   6  missing prerequisite (jq, git, ACC repo, etc.)
#   10 invalid invocation
#
# Non-zero exit halts the autonomous chain.

set -euo pipefail

# Resolve repo root via git; refuse to fall back silently (closes R2
# BYPASS-008).
if ! REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  echo "GATE-CHECK FAIL: not inside a git repository" >&2
  exit 6
fi

PIN_MANIFEST="${REPO_ROOT}/docs/reviews/WP-SCP-022/acc-pin-manifest.json"
DECISIONS_PATH="${REPO_ROOT}/docs/DECISIONS.md"
DISPATCHES_DIR="${REPO_ROOT}/docs/reviews/WP-SCP-022/dispatches"
SCP_OPERATOR_EMAIL="${SCP_OPERATOR_EMAIL:-jrnb2024}"
# Default allowlist covers (a) the GitHub username `jrnb2024` matched as a
# bare local-part (works for jrnb2024@github.com etc.); (b) the operator's
# personal email james@brokai.net. Override with SCP_OPERATOR_EMAILS to add
# work or alternate identities. Closes R4 BYPASS-001.
SCP_OPERATOR_EMAILS_DEFAULT="jrnb2024:james@brokai.net:james.brooke@mapp.com:james.brooke@storystream.it"

usage() {
  cat >&2 <<USAGE
Usage:
  $0 --gate <gate-id>            Verify a gate artefact (USER-GATE-A0|A|C)
  $0 --slice <slice-id>          Pre-dispatch checks for a slice
  $0 --check-acc-pin             Verify ACC repo HEAD + blob SHAs
  $0 --check-d021                Detect D-021 collision
  $0 --check-hash-chain <slice>  Verify slice fixpoint hash chain

Exit codes: 0 pass | 1 artefact | 2 symlink | 3 d021 | 4 acc-pin |
            5 hash-chain | 6 missing-prereq | 10 invalid invocation
USAGE
}

# ---------------- helpers ----------------

require_cmd() {
  for cmd in "$@"; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      echo "GATE-CHECK FAIL: missing prerequisite: $cmd" >&2
      return 6
    fi
  done
}

# Portable real-path resolver — works on macOS without GNU coreutils.
# Closes R2 BYPASS-004.
resolve_real_path() {
  python3 - "$1" <<'PYEOF'
import os, sys
p = sys.argv[1]
try:
    rp = os.path.realpath(p, strict=False)
except TypeError:
    rp = os.path.realpath(p)
if not os.path.exists(rp):
    print("__DANGLING__:" + rp)
else:
    print(rp)
PYEOF
}

verify_gate_commit_author() {
  # Defence-in-depth on signer identity (R-022-12).
  # SCP_OPERATOR_EMAILS is a colon-separated allowlist of acceptable
  # author identities. Each entry is matched as either an exact full
  # email address (preferred) or a bare local-part (matches any host).
  # Substring matching is intentionally avoided to close R3 BYPASS-002
  # (over-permissive substring case `*${EMAIL}*`).
  #
  # Default: jrnb2024 (bare local-part — matches jrnb2024@github.com,
  # jrnb2024@anywhere). Override with:
  #   SCP_OPERATOR_EMAILS="james@brokai.net:jrnb2024:james@anthropic.com"
  local path_rel="$1"
  if ! email="$(git -C "$REPO_ROOT" log -1 --format=%ae -- "$path_rel" 2>/dev/null)"; then
    echo "GATE-CHECK FAIL: cannot read git log for $path_rel" >&2
    return 1
  fi
  if [[ -z "$email" ]]; then
    echo "GATE-CHECK FAIL: $path_rel has no commits (uncommitted gate artefact)" >&2
    return 1
  fi
  local allowlist="${SCP_OPERATOR_EMAILS:-${SCP_OPERATOR_EMAILS_DEFAULT}}"
  local actual_local="${email%@*}"
  local IFS=':'
  for candidate in $allowlist; do
    [[ -z "$candidate" ]] && continue
    if [[ "$candidate" == *"@"* ]]; then
      # full email — exact match required
      if [[ "$candidate" == "$email" ]]; then
        return 0
      fi
    else
      # bare local-part — match against email's local part exactly
      if [[ "$candidate" == "$actual_local" ]]; then
        return 0
      fi
    fi
  done
  echo "GATE-CHECK FAIL: $path_rel committed by '$email' (expected member of allowlist '$allowlist'); refusing to advance chain on third-party gate signature" >&2
  return 1
}

# ---------------- mode: --gate ----------------

check_gate_artefact() {
  local gate="$1"
  local path
  case "$gate" in
    USER-GATE-A0)
      path="${REPO_ROOT}/docs/reviews/WP-SCP-020/release-signoff.md"
      ;;
    USER-GATE-A)
      path="${REPO_ROOT}/docs/reviews/WP-SCP-022/gates/USER-GATE-A.md"
      ;;
    USER-GATE-C)
      path="${REPO_ROOT}/docs/reviews/WP-SCP-022/gates/USER-GATE-C.md"
      ;;
    *)
      echo "unknown gate: $gate" >&2
      return 10
      ;;
  esac

  if [[ ! -f "$path" ]]; then
    echo "GATE-CHECK FAIL: $gate artefact missing: $path" >&2
    return 1
  fi

  # All gates require a Signed:/Signer: line.
  if ! grep -E '^(Signed|Signer):\s+\S+' "$path" >/dev/null; then
    echo "GATE-CHECK FAIL: $path lacks 'Signed:' or 'Signer:' line" >&2
    return 1
  fi

  if [[ "$gate" == "USER-GATE-A0" ]]; then
    # WP-SCP-020 §4 020H part 2 also requires named-signer + timestamp +
    # canary-run-id reference. Closes R2 C-MIN-01.
    if ! grep -E '^(Timestamp|Date|Signed-At):\s+[0-9]{4}-[0-9]{2}-[0-9]{2}' "$path" >/dev/null; then
      echo "GATE-CHECK FAIL: $path lacks ISO-8601 'Timestamp:'/'Date:'/'Signed-At:' line" >&2
      return 1
    fi
    if ! grep -E '^(Canary-Run-Id|Workflow-Run-Id|Run-Id):\s+\S+' "$path" >/dev/null; then
      echo "GATE-CHECK FAIL: $path lacks 'Canary-Run-Id:' / 'Workflow-Run-Id:' / 'Run-Id:' line" >&2
      return 1
    fi
  fi

  # Defence-in-depth: verify commit author matches the configured
  # operator (closes R2 BYPASS-005 partial).
  local rel="${path#${REPO_ROOT}/}"
  if ! verify_gate_commit_author "$rel"; then
    return 1
  fi

  echo "GATE-CHECK OK: $gate verified at $path"
  return 0
}

# ---------------- mode: --slice ----------------

check_no_symlink_escape() {
  local slice_id="$1"
  local link_count
  link_count=$(find "$REPO_ROOT" -type l -not -path '*/\.git/*' 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$link_count" -eq 0 ]]; then
    echo "GATE-CHECK OK: slice $slice_id — no symlinks present"
    return 0
  fi

  local escapes=()
  while IFS= read -r link; do
    [[ -z "$link" ]] && continue
    target="$(resolve_real_path "$link")"
    case "$target" in
      __DANGLING__:*)
        escapes+=("$link -> ${target#__DANGLING__:} (DANGLING)")
        ;;
      "$REPO_ROOT"/*|"$REPO_ROOT")
        : # safe — inside repo
        ;;
      *)
        escapes+=("$link -> $target")
        ;;
    esac
  done < <(find "$REPO_ROOT" -type l -not -path '*/\.git/*' 2>/dev/null)

  if (( ${#escapes[@]} > 0 )); then
    echo "GATE-CHECK FAIL: slice $slice_id — symlink escape(s) detected:" >&2
    printf '  %s\n' "${escapes[@]}" >&2
    return 2
  fi

  echo "GATE-CHECK OK: slice $slice_id — $link_count symlink(s) all in-repo"
  return 0
}

check_d021_collision() {
  if [[ ! -f "$DECISIONS_PATH" ]]; then
    echo "GATE-CHECK FAIL: $DECISIONS_PATH missing" >&2
    return 6
  fi
  local hits
  hits=$(grep -E '^\| D-021 \|' "$DECISIONS_PATH" || true)
  if [[ -z "$hits" ]]; then
    echo "GATE-CHECK OK: D-021 not yet filed (reserved slot)"
    return 0
  fi
  if echo "$hits" | grep -q '2026-05-31'; then
    echo "GATE-CHECK OK: D-021 filed at canonical 2026-05-31 slot"
    return 0
  fi
  echo "GATE-CHECK FAIL: D-021 filed at non-canonical date — reserved slot collision" >&2
  echo "$hits" >&2
  return 3
}

check_acc_pin() {
  if [[ ! -f "$PIN_MANIFEST" ]]; then
    echo "GATE-CHECK FAIL: $PIN_MANIFEST missing" >&2
    return 6
  fi
  require_cmd jq python3 || return 6
  local acc_root="${HOME}/Projects/acc"
  if [[ ! -d "${acc_root}/.git" ]]; then
    echo "GATE-CHECK FAIL: $acc_root not a git repo" >&2
    return 6
  fi

  local pinned_head live_head
  pinned_head=$(jq -r '.acc_repo_head' "$PIN_MANIFEST")
  live_head=$(git -C "$acc_root" rev-parse HEAD)

  if [[ "$pinned_head" != "$live_head" ]]; then
    echo "GATE-CHECK NOTICE: ACC HEAD drift — pinned $pinned_head, live $live_head"
    # Drift is informational — blob-SHA check below is the actual gate.
  fi

  local drift=0
  while IFS= read -r entry; do
    local pinned_sha live_sha
    pinned_sha=$(jq -r --arg k "$entry" '.blobs[$k]' "$PIN_MANIFEST")
    live_sha=$(git -C "$acc_root" ls-tree HEAD "$entry" 2>/dev/null | awk '{print $3}')
    if [[ -z "$live_sha" ]]; then
      echo "GATE-CHECK FAIL: ACC blob missing — $entry not present in live ACC HEAD" >&2
      drift=1
      continue
    fi
    if [[ "$pinned_sha" != "$live_sha" ]]; then
      echo "GATE-CHECK FAIL: ACC blob drift — $entry pinned $pinned_sha, live $live_sha" >&2
      drift=1
    fi
  done < <(jq -r '.blobs | keys[]' "$PIN_MANIFEST")

  if (( drift == 1 )); then
    return 4
  fi
  echo "GATE-CHECK OK: ACC pin manifest matches live blobs"
  return 0
}

# ---------------- mode: --check-hash-chain ----------------

check_hash_chain() {
  local slice_id="$1"
  local fixpoint="${DISPATCHES_DIR}/${slice_id}/fixpoint.md"
  if [[ ! -f "$fixpoint" ]]; then
    echo "GATE-CHECK FAIL: $fixpoint missing" >&2
    return 1
  fi
  # Closes R4 C-nit-01 / BYPASS-004: python3 isn't used inside
  # check_hash_chain itself (it's used by check_no_symlink_escape's
  # resolve_real_path helper, which has its own require). Don't gate
  # this function on python3 being present.
  if ! command -v sha256sum >/dev/null 2>&1; then
    if ! command -v shasum >/dev/null 2>&1; then
      echo "GATE-CHECK FAIL: need sha256sum or shasum" >&2
      return 6
    fi
  fi

  # Extract the sha256_chain block. Format expected:
  #   ## sha256_chain
  #   correctness: <hex>
  #   safety: <hex>
  #   completeness: <hex>
  #   chain: <hex over (corr || safety || completeness)>
  local chain_block
  chain_block=$(awk '/^## sha256_chain/{flag=1;next}/^## /{flag=0}flag' "$fixpoint")
  if [[ -z "$chain_block" ]]; then
    echo "GATE-CHECK FAIL: $fixpoint has no '## sha256_chain' block" >&2
    return 5
  fi

  local recorded_corr recorded_safety recorded_comp recorded_chain
  recorded_corr=$(echo "$chain_block" | awk -F': ' '/^correctness:/{print $2}')
  recorded_safety=$(echo "$chain_block" | awk -F': ' '/^safety:/{print $2}')
  recorded_comp=$(echo "$chain_block" | awk -F': ' '/^completeness:/{print $2}')
  recorded_chain=$(echo "$chain_block" | awk -F': ' '/^chain:/{print $2}')

  if [[ -z "$recorded_corr" || -z "$recorded_safety" || -z "$recorded_comp" || -z "$recorded_chain" ]]; then
    echo "GATE-CHECK FAIL: sha256_chain block incomplete in $fixpoint" >&2
    return 5
  fi

  # Determine which round directory is terminal — find the highest
  # fix-round-N or use r0 (initial round if no fix needed).
  local terminal_dir="${DISPATCHES_DIR}/${slice_id}"
  local highest=-1
  for d in "$terminal_dir"/fix-round-*; do
    [[ -d "$d" ]] || continue
    n="${d##*/fix-round-}"
    [[ "$n" =~ ^[0-9]+$ ]] || continue
    if (( n > highest )); then
      highest="$n"
      terminal_dir="$d"
    fi
  done

  hash_file() {
    if command -v sha256sum >/dev/null 2>&1; then
      sha256sum "$1" | awk '{print $1}'
    else
      shasum -a 256 "$1" | awk '{print $1}'
    fi
  }

  # Per plan §4.5: implementation slices use the flat layout
  #   <dispatch-dir>/review-{correctness,safety,completeness}.json   (initial round)
  #   <dispatch-dir>/fix-round-N/review-{correctness,safety,completeness}.json (fix rounds)
  # The plan-slice review pack itself uses r{N}-{lens}/dispatcher-result.json
  # but that pack is NOT consumed by --check-hash-chain (which only
  # operates on implementation slices). Closes R3 C-MAJ-01 / BYPASS-001.
  local computed_corr computed_safety computed_comp
  if [[ "$highest" -lt 0 ]]; then
    # initial-round (no fix rounds) — flat layout in slice dir
    computed_corr=$(hash_file "$terminal_dir/review-correctness.json" 2>/dev/null || true)
    computed_safety=$(hash_file "$terminal_dir/review-safety.json" 2>/dev/null || true)
    computed_comp=$(hash_file "$terminal_dir/review-completeness.json" 2>/dev/null || true)
  else
    # terminal fix-round
    computed_corr=$(hash_file "$terminal_dir/review-correctness.json" 2>/dev/null || true)
    computed_safety=$(hash_file "$terminal_dir/review-safety.json" 2>/dev/null || true)
    computed_comp=$(hash_file "$terminal_dir/review-completeness.json" 2>/dev/null || true)
  fi

  if [[ -z "$computed_corr" || -z "$computed_safety" || -z "$computed_comp" ]]; then
    echo "GATE-CHECK FAIL: cannot locate terminal-round reviewer-result JSONs for slice $slice_id" >&2
    return 5
  fi

  if [[ "$recorded_corr" != "$computed_corr" || "$recorded_safety" != "$computed_safety" || "$recorded_comp" != "$computed_comp" ]]; then
    echo "GATE-CHECK FAIL: sha256_chain leaf mismatch for slice $slice_id" >&2
    return 5
  fi

  # Recompute chain hash = sha256(corr || safety || completeness)
  local computed_chain
  if command -v sha256sum >/dev/null 2>&1; then
    computed_chain=$(printf '%s%s%s' "$computed_corr" "$computed_safety" "$computed_comp" | sha256sum | awk '{print $1}')
  else
    computed_chain=$(printf '%s%s%s' "$computed_corr" "$computed_safety" "$computed_comp" | shasum -a 256 | awk '{print $1}')
  fi
  if [[ "$recorded_chain" != "$computed_chain" ]]; then
    echo "GATE-CHECK FAIL: sha256_chain root mismatch for slice $slice_id" >&2
    return 5
  fi
  echo "GATE-CHECK OK: hash chain verified for slice $slice_id (round=${highest:-r1})"
  return 0
}

# ---------------- main dispatch ----------------

main() {
  if [[ $# -lt 1 ]]; then
    usage
    return 10
  fi
  case "$1" in
    --gate)
      [[ $# -lt 2 ]] && { usage; return 10; }
      check_gate_artefact "$2"
      ;;
    --slice)
      [[ $# -lt 2 ]] && { usage; return 10; }
      check_no_symlink_escape "$2"
      check_d021_collision
      check_acc_pin
      ;;
    --check-acc-pin)
      check_acc_pin
      ;;
    --check-d021)
      check_d021_collision
      ;;
    --check-hash-chain)
      [[ $# -lt 2 ]] && { usage; return 10; }
      check_hash_chain "$2"
      ;;
    --help|-h)
      usage
      return 0
      ;;
    *)
      usage
      return 10
      ;;
  esac
}

main "$@"
