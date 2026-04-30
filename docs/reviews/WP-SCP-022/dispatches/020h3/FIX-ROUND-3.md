# 020h3 fix-round-3 (post-r2-correctness, post-r2-safety, pre-r2-completeness)

**Date:** 2026-04-30 (evening)

## Triggers

R2 dispatch returned (commits 6907a8b/f2c0c79 reviewed):

- **R2 correctness** (`review-correctness-r2.json`, ~8 min, APPROVED_WITH_FINDINGS): 4 MIN + 1 nit. None blocking.
- **R2 safety** (`review-safety-r2.json`, ~7.5 min, BLOCKED): 1 MAJ (SAFE-R2-001) + 3 MIN + 1 nit.
- **R2 completeness**: still running at fix-round-3 authoring time; findings will fold into fix-round-4 if any surface.

## Closures applied

| Finding | Severity | Closure |
|---|---|---|
| SAFE-R2-001 | MAJ | §12.7.4 multi-maintainer mode now requires `dismiss_stale_reviews: true` with rationale: without it, an attacker can obtain a CODEOWNER review on initial commit, then push subsequent malicious commits (rule-config disable, scp_bypass=true, fork-PR `if:` removal) without re-review. The `enable-required-check.sh` helper preserves existing review-shape verbatim and does not set this for adopters; the appendix instructs explicit configuration via the GitHub UI/API. |
| SAFE-R2-002 | MIN | §11.10 CODEOWNERS language upgraded from "recommendation" to "requirement (MUST)" with rationale: rule-config is a bypass-surface equivalent to scp_bypass without the three-gate check. Removes the §12.7.4 ↔ §11.10 normative mismatch. |
| SAFE-R2-003 | MIN | §12.7.13 supply-chain disclosure now receives forward-references from §12.7.1 (after the wrapper YAML — "Before deploying: review §12.7.13") and §12.7.9 (after the SHA-locked binary mention — "the CI workflow's Regal binary is NOT yet SHA256-verified"). Adopters following any natural setup path encounter the disclosure. |
| SAFE-R2-004 | MIN | TF-020H3-001 closure deadline made concrete in DISPATCH-NOTE + STATUS.md: **before v1.0.1 release OR within 14 calendar days of 020H part 3 merge (whichever first); for 2026-04-30 merge → 2026-05-14**. Includes user-review escalation if missed. |
| SAFE-R2-005 | nit | D-031 item (c) extended with a D-033 forward-reference annotation matching D-032's pattern. Eliminates the cross-document inconsistency where D-031 and D-033 named different live values (count=1 vs count=0) without a linking note. |
| CORR-MIN-R2-001 | MIN | DISPATCH-NOTE acceptance checklist row (xi) updated from "~2,400 PR runs/month" to "~2,000 PR runs/month" matching the §12.7.12 fix-round-1 correction. |
| CORR-MIN-R2-002 | MIN | §12.7.4 multi-maintainer mode no longer lists `require_review_from_non_author: true` as a REST API field. Replaced with: GitHub enforces non-self-approval at the platform level — there is no separate API field; the WP-SCP-020 plan corpus uses the term as shorthand for the platform behaviour. |
| CORR-MIN-R2-003 | MIN | §12.7.13 + DISPATCH-NOTE + STATUS.md all clarify that "020H.2" is a NEW post-Threshold-A slice in the dot-N naming series (mirroring 020H.1), distinct from the already-merged "020H part 2" (promote-to-v1.0.0). Removes the ambiguity between the two notations. |
| CORR-MIN-R2-004 | MIN | §12.7.4 expired-rule-config grace ramp text rewritten to clearly separate (a) the v1.0.0-shipped runtime warning (`policy-check.yml` "Emit expired-rule-config one-release warning" step — confirmed present at lines 698, 755, 758) from (b) the deferred release-tag-time refusal (TF-005 → 020D2 / future release-cut workflow). The conflated wording is gone. |
| CORR-nit-R2-001 | nit | §12.7.3 `administration:write` description corrected: GitHub fine-grained PAT environment management is `environments: write` (separate scope), not part of `administration:write`. Boundary noted in-line. |

## Closures NOT applied (deferred)

None this round; all R2 correctness + R2 safety findings closed.

## Re-review

R2 completeness still in flight. R3 dispatch will follow once R2 completeness lands — recursing per `feedback_recursive_adversarial_review.md`. Fixpoint criteria: zero new BLOCKING (CRIT/MAJ) findings on a full lens cycle.
