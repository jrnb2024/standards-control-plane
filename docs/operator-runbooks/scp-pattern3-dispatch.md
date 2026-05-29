# Operator runbook — Pattern-3 session-start ACC dispatch ceremony

**Status:** ACTIVE (D-057 ratified 2026-05-29).
**Audience:** the SCP operator running a Claude Code autonomous session against `~/Projects/standards-control-plane` as the project root.
**Companion script:** `scripts/operator/scp-pattern3-dispatch.sh`.
**Authority:** `docs/decisions/D-057-scp-self-orchestrate-pattern-2026-05-29.md`.

---

## When to use this

You're about to kick off a **Claude Code autonomous session in the SCP repo** (project root = `~/Projects/standards-control-plane`) that will need to write **source** files — `src/**`, `tests/**`, `policies/**`, `scripts/**`, `pyproject.toml`, root-level `STATUS.md`, or `.claude/**`.

If the session will only touch `docs/**`, `CLAUDE.md`, `AGENTS.md`, or memory files: **no dispatch needed.** The acc-hook's `alwaysAllowed()` permits those unconditionally.

This ceremony does NOT apply to a Claude Code session whose project root is some *other* directory (e.g. the parent `/Users/amplience/Projects`) — the SCP hook is loaded from the SCP repo's `.claude/settings.json` and is only in effect when the SCP repo is the project root.

---

## The ceremony (one command, two endpoints)

### 1. **Before** you kick off the session — bootstrap the dispatch

From a normal terminal (not inside the Claude Code session):

```bash
cd ~/Projects/standards-control-plane
scripts/operator/scp-pattern3-dispatch.sh \
    "src/<specific-file>.py" \
    "tests/<specific-test>.py" \
    "STATUS.md"
```

The script writes `.acc/active-dispatch.json` with your enumerated `scope_boundary`, a unique `dispatch_id`, and `started_at` stamped to **now**. The acc-hook (`hook/internal/policy/freshness.go`) denies the dispatch once `started_at` is older than **4 hours** (`active_dispatch_ttl_seconds = 14400` in `acc.kernel.config`), so the bootstrap must be reasonably close to session kickoff.

### 2. Run the session

The acc-hook permits writes inside your declared `scope_boundary` (and inside `alwaysAllowed()`). Writes outside both are denied + logged to `.acc/hook-audit-log/YYYY-MM-DD.jsonl` with an HMAC signature.

### 3. **After** the session ends — tear down

```bash
scripts/operator/scp-pattern3-dispatch.sh --teardown
```

Removes `.acc/active-dispatch.json`. This prevents a later, unrelated session inheriting a still-within-TTL dispatch.

---

## `scope_boundary` discipline (acceptance criteria)

The script enforces — and you MUST observe — the following invariants. They are not stylistic; the self-escalation guard depends on them.

### A1 — Enumerate specific paths, not blanket globs

The script REJECTS:

- `**`, `/`, `.`, `./`, `*` — blanket scopes that defeat the guard.
- Absolute paths (`/abs/path`).
- Parent-traversal entries containing `..`.

Pass concrete repo-relative paths or narrowly-scoped globs.

**Smoke test:**
```bash
$ scripts/operator/scp-pattern3-dispatch.sh "**"
scp-pattern3-dispatch: ERROR: forbidden scope '**': blanket globs and any glob covering .acc/active-dispatch.json are refused (D-057 self-escalation guard)
```

### A2 — Never cover `.acc/active-dispatch.json` (the self-escalation guard)

The script REJECTS any of: `.acc`, `.acc/`, `.acc/**`, `.acc/*`, `.acc/active-dispatch.json`.

**Why this is load-bearing:** `.acc/active-dispatch.json` is NOT in the hook's `alwaysAllowed()` set. If a session's `scope_boundary` covered it, the session could overwrite its own dispatch mid-run to widen scope to `src/**`. Forbidding self-covering scopes at write time closes that path.

**Smoke test:**
```bash
$ scripts/operator/scp-pattern3-dispatch.sh ".acc/**"
scp-pattern3-dispatch: ERROR: forbidden scope '.acc/**': ...
$ scripts/operator/scp-pattern3-dispatch.sh ".acc/active-dispatch.json"
scp-pattern3-dispatch: ERROR: forbidden scope '.acc/active-dispatch.json': ...
```

A complementary hook-side deny is filed forward as `FUP-ACC-HOOK-DENY-ACTIVE-DISPATCH-PATH-001` for defence-in-depth.

### A3 — Never run under CI

The script REJECTS `CI=true` and `GITHUB_ACTIONS=true` — operator-attended ceremony only.

**Smoke test:**
```bash
$ CI=true scripts/operator/scp-pattern3-dispatch.sh "src/x.py"
scp-pattern3-dispatch: ERROR: refusing to run under CI (operator-attended ceremony only)
```

### A4 — `started_at` is stamped to now

The script always sets `started_at` to the current UTC timestamp on every write. You cannot accidentally extend a stale dispatch by re-running it without realising — each run is a fresh 4h window.

---

## Fail-closed semantics (what happens if you get it wrong)

| Scenario | Hook behaviour |
|---|---|
| No `.acc/active-dispatch.json` exists | Source writes denied (only `alwaysAllowed()` paths permitted). |
| Dispatch JSON malformed (parse error) | Treated as no dispatch → source writes denied. **Fail-closed.** |
| Dispatch `started_at` > 4h old | Denied as stale (freshness gate). |
| Dispatch `started_at` missing/future | Denied (fail-closed). |
| Write target is in `scope_boundary` | Allowed + logged with HMAC signature. |
| Write target is OUTSIDE `scope_boundary` AND not in `alwaysAllowed()` | Denied + logged. |
| Bash with redirection (`>`, `2>&1`, pipes) | **Denied regardless of dispatch** — `bash.Decide()` doesn't consult scope. Use the Write tool or rewrite the command. |

Recovery from a denial in-session: stop, exit the session, re-run the bootstrap with the correct scope, restart the session. **Do not** disable the hook to unblock — D-057 forbids that pattern.

---

## When you should NOT use this ceremony

- The session will only touch `docs/**` / `CLAUDE.md` / `AGENTS.md` / memory — those are always-allowed, no dispatch needed.
- The repo is not SCP — this runbook is SCP-specific per D-057's gating predicate. Other repos must record their own ADR.
- You're not at the operator console — never delegate the bootstrap to an unattended automation; the trust anchor is the operator running the script knowingly.

---

## Reference

- **D-057** — `docs/decisions/D-057-scp-self-orchestrate-pattern-2026-05-29.md`
- **Hook source** — `~/Projects/acc/hook/cmd/acc-hook/main.go` (`alwaysAllowed()` at L277-290; `bash.Decide()`; `freshness.go DefaultActiveDispatchTTLSeconds=14400`)
- **ACC ADR-019** — supervisor-rip: hook is the estate's sole mechanical write-scope enforcement
- **Companion script** — `scripts/operator/scp-pattern3-dispatch.sh`
- **Forensic audit log** — `.acc/hook-audit-log/YYYY-MM-DD.jsonl`
