# 024C ↔ TF-PIM-001 Wave F cross-reference

**Filed:** 2026-05-22 (Wave F dogfood verify PR #140)
**Related WP:** TF-PIM-001 Wave F (SCP-self dogfood verify)
**Related slice:** WP-SCP-024 024C PIM canary cascade

## Purpose

Cross-link document recording that TF-PIM-001 Wave F (SCP-self dogfood verify) is a precursor to WP-SCP-024 024C's PIM canary path. Wave F proves the new policy-check.yml workflow (Wave D + E impl, merged via PR #139 at `7acc661` on 2026-05-21) is SCP-self-green; Wave G (PIM canary cross-repo verify) is the operator-attended next step that exercises the same workflow from PIM's adopter context.

## Sequencing

| Step | Outcome | Status |
|------|---------|--------|
| TF-PIM-001 Waves A-E | App credential + token-exchange + selftest mock | ✅ Discharged via PRs #133-#139 |
| TF-PIM-001 Wave F | SCP-self dogfood verify (THIS PR #140) | 🔄 In CI |
| TF-PIM-001 Wave G | PIM canary cross-repo verify | ⏳ Operator-attended next |
| TF-PIM-001 Wave H | PIM main required-check restoration + TF-PIM-001 closure | ⏳ Operator-attended after Wave G |

## Why this file lives under 024C

The 024C PIM canary cascade slice is gated on TF-PIM-001 closure (Wave H restores PIM main's `policy-check / scp/policy-check` required-check). This cross-ref documents the dependency for future readers tracing 024C's pre-conditions.

## CI invocation log gate

This file is a **non-DISPATCH-NOTE artefact** under `docs/reviews/WP-SCP-024/024C/`. Per `.github/workflows/check-invocation-log-entry.yml`'s resolve-dispatch step: when no `DISPATCH-NOTE.md` is modified in the PR diff (only this cross-ref file is added under 024C), the workflow short-circuits to "nothing to enforce" and exits SUCCESS. No branch-protection-log entry is required (none was modified).

## No 024C dispatch-note modification

The 024C DISPATCH-NOTE.md is NOT modified by this PR. The slice's invocation-log enforcement (D-047) is not triggered.
