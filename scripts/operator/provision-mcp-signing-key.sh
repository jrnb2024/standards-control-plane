#!/usr/bin/env bash
# Provision the SCP MCP signing-key ring so `propose()` works (clears SCP-MCP-E021).
#
# WHAT THIS DOES (all on YOUR machine; the operator holds the private key):
#   1. Generates an Ed25519 keypair via the SCP's own `scp-mcp-server keygen`.
#      - PRIVATE key  -> ~/.config/scp/mcp-signing-key      (mode 600, NEVER committed)
#      - PUBLIC  key  -> ~/.config/scp/mcp-signing-key.pub   (OpenSSH ssh-ed25519 line)
#      - prints the KEY_ID (derived from the raw public key bytes)
#   2. Appends the trust-anchor line to docs/security/mcp-signing-keys.pub in the
#      exact format the server parses:
#        ssh-ed25519 <pub> key_id=<KEY_ID> current=true retain_until=<+90d>
#   3. STOPS. It does NOT git-commit anything — you review, then commit ONLY the
#      committed trust file (docs/security/mcp-signing-keys.pub). The private key
#      stays in ~/.config/scp and is gitignored; do not move/commit it.
#
# After committing the trust file + reconnecting the scp-standards MCP server,
# `propose()` will record signing_key_id and stop returning SCP-MCP-E021.
#
#   ./scripts/operator/provision-mcp-signing-key.sh           # first provision
#   ./scripts/operator/provision-mcp-signing-key.sh --rotate  # add a new current key (rotation)
set -euo pipefail
cd "$(dirname "$0")/../.."   # repo root (standards-control-plane)

REPO_ROOT="$(pwd)"
TRUST_FILE="$REPO_ROOT/docs/security/mcp-signing-keys.pub"
PRIV="$HOME/.config/scp/mcp-signing-key"
PUB="$PRIV.pub"
BIN="$REPO_ROOT/.venv-mcp/bin/scp-mcp-server"
ROTATE="${1:-}"

bold(){ printf '\033[1m%s\033[0m\n' "$*"; }
ok(){ printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn(){ printf '  \033[33m!\033[0m %s\n' "$*"; }
fail(){ printf '  \033[31m✗\033[0m %s\n' "$*" >&2; exit 1; }

bold "1/4  Preflight"
[ -x "$BIN" ] || fail "scp-mcp-server not found at $BIN (the .venv-mcp the MCP server runs from). Activate/create that venv with the [mcp] extra first."
[ -f "$TRUST_FILE" ] || fail "trust file missing: $TRUST_FILE"
mkdir -p "$HOME/.config/scp"
if [ -f "$PRIV" ] && [ "$ROTATE" != "--rotate" ]; then
  fail "A private key already exists at $PRIV. Re-run with --rotate to add a NEW current key (90-day overlap), or remove the old one deliberately."
fi
ok "scp-mcp-server present; trust file present"

bold "2/4  Generate Ed25519 keypair (private key stays on this machine)"
KEYGEN_OUT="$PRIV"
[ "$ROTATE" = "--rotate" ] && KEYGEN_OUT="$PRIV.$(date +%Y%m%d)"
KEY_ID="$("$BIN" keygen --out "$KEYGEN_OUT")" || fail "keygen failed"
PUBLINE="$(cat "$KEYGEN_OUT.pub")"
# strip any trailing OpenSSH comment so only 'ssh-ed25519 <base64>' remains
PUBLINE="$(printf '%s' "$PUBLINE" | awk '{print $1" "$2}')"
ok "key_id = $KEY_ID"
ok "private key: $KEYGEN_OUT (mode 600 — DO NOT commit or move)"

bold "3/4  Assemble + append the trust-anchor line"
RETAIN_UNTIL="$(date -v +90d +%Y-%m-%d 2>/dev/null || date -d '+90 days' +%Y-%m-%d)"
# demote any existing current=true lines (only one key may be current at a time)
if grep -qE '^ssh-ed25519 .*current=(true|1|yes)' "$TRUST_FILE" 2>/dev/null; then
  warn "demoting previous current key(s) to current=false (rotation overlap)"
  sed -i.bak -E 's/(current=)(true|1|yes)/\1false/g' "$TRUST_FILE" && rm -f "$TRUST_FILE.bak"
fi
ENTRY="$PUBLINE key_id=$KEY_ID current=true retain_until=$RETAIN_UNTIL"
printf '%s\n' "$ENTRY" >> "$TRUST_FILE"
ok "appended to $TRUST_FILE:"
printf '      %s\n' "$ENTRY"

bold "4/4  Next steps (operator — NOT automated)"
cat <<EOF
  Review the change, then commit ONLY the trust file:
    git -C "$REPO_ROOT" add docs/security/mcp-signing-keys.pub
    git -C "$REPO_ROOT" diff --cached docs/security/mcp-signing-keys.pub   # eyeball it
    git -C "$REPO_ROOT" commit -m "security: provision MCP signing key \$KEY_ID (current)"
    git -C "$REPO_ROOT" push        # the committed-at-a-known-SHA file is the trust anchor

  The PRIVATE key ($KEYGEN_OUT) must NEVER be committed (it is gitignored). Back it up
  securely (e.g. your password manager) — losing it means rotating to a new key.

  Then reconnect the scp-standards MCP server (restart Claude Code / re-handshake) so it
  re-reads the populated key ring. propose() will then record signing_key_id and stop
  returning SCP-MCP-E021.
EOF
ok "done"
