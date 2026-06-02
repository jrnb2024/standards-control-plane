<!-- canonical:acc-hook-onboarding v1 -->
# ⚠️ This repo runs the acc-hook (PreToolUse enforcement) — read before any write

This repo has the **ACC kernel hook live**. It **HARD-BLOCKS** source writes that
aren't covered by an active dispatch. This is not optional guidance.

## Always-allowed — write these freely, no ceremony

`docs/**` · `CLAUDE.md` · `AGENTS.md` · `.acc/work-packages/**`

These are in the hook's always-allowed set; documentation + memory writes never trip it.

## Source writes are GATED — satisfy the hook first

Before a session that will write source, the operator seeds a session-start
dispatch via `scripts/operator/scp-pattern3-dispatch.sh "<path>"` (D-057). Writes
inside the declared scope pass + are HMAC-logged.

## If you trip the hook

**STOP. Tell the operator the one ceremony step above.** Do **NOT** disable the
acc-hook to get unblocked — disabling enforcement is **forbidden estate-wide**
(D-057): sessions declare scope, they do not disable enforcement. Never `cp`/`mv`
the hook aside.
