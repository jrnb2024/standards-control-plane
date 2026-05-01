# WP-SCP-022 slice 020H.3.1 — release-gate auto-issue (dispatch note)

**Date:** 2026-05-01
**Tier:** orchestrator-applied (Tier 1 only)
**Closes:** WP-SCP-022 020H.3 R1 SAFE-CRIT-001 follow-up — TF-020H3rg-003 (auto-open `release-gate-violation` issue on push:tags failure).

**Slice naming.** "020H.3.1" follows the `<slice>.<patch>` reconciliation pattern established by 020D2.1 (the post-USER-GATE-A reconciliation that landed D-033). 020H.3 itself is post-Threshold-A (.N convention); the trailing `.1` on this slice signals "follow-up to 020H.3 closing one of its tracked-forward items in-place rather than opening a new dot-N slice." Dispatches dir: `020h3-1-auto-issue` (avoids collision with the existing `020h3` and `020h3-release-gate`).

## Justification for not invoking Codex executor

Per `feedback_four_tier_dispatch.md` in-line escalation guidance.
The slice's surface is **one new step in an existing workflow + 3
small doc updates**:

- `.github/workflows/release-gate.yml` — `permissions: { issues: write }`
  added; new "Open release-gate-violation issue" step gated on
  `if: failure() && github.event_name == 'push'`. Pattern is a
  near-mechanical port of the canary-replay.yml gh-issue-create
  block (which itself reached fixpoint at 020H.1 fix-round-1 +
  fix-round-2).
- `policies/VERSIONING.md` "Machine enforcement (2)" subsection —
  remove the `(per TF-020H3rg-003)` qualifier since the auto-issue
  is now live.
- `docs/adoption/ADOPT-001-project-onboarding.md` §12.7.7 — same
  qualifier removal in the `SCP-EREL-001` row.
- `STATUS.md` — TF-020H3rg-003 marked closed; 020H.3 marked landed
  (carrier-slice obligation backfill, mirroring the 020H.1→020H.3
  transition); 020H.3.1 IN FLIGHT row.

Codex Tier 3 dispatch overhead would exceed the marginal benefit;
orchestrator-applied + R1 × 3 is the right posture (symmetric with
020H.3 + the established pattern for follow-up slices).

## Slice acceptance

- [x] **(i) `permissions: { issues: write }` added** to release-gate.yml
  with comment explaining the bounded threat surface (per-repo
  GITHUB_TOKEN privilege; only fires on push:tags failure).
- [x] **(ii) "Open release-gate-violation issue" step.** Gated on
  `failure() && github.event_name == 'push'` so workflow_dispatch
  dry-runs never reach it. Fields:
  - `assignees="${SCP_RELEASE_GATE_ASSIGNEES:-jrnb2024}"` — forward-compat
    env for 2nd-maintainer escalation, symmetric with canary-replay.yml.
  - De-dup by candidate tag: `gh issue list --search "in:title \"<title>\""`
    → if exists, append a `Re-detected in workflow run <URL>` comment;
    else create a new issue.
  - Issue body composed via Python heredoc (`python3 - <<'PY'`) with
    explicit `.replace()` placeholder substitution — matches the
    canary-replay.yml fix-round-1 SAFE-MIN-004 pattern (no
    shell-injection surface from CANDIDATE_TAG / RUN_URL).
  - Labels: `release-gate-violation`, `needs-triage`, `auto-opened`.
- [x] **(iii) De-dup scope.** Tag-keyed (NOT week-of-year as in
  canary-replay.yml — a tag is a single event, not a recurring
  detection class). An existing open issue for the same tag gets
  a comment update; a new tag opens a new issue.
- [x] **(iv) Body content.** Lists the bad tag, the workflow-run URL,
  references VERSIONING.md "Bad-tag recovery procedure" (don't
  delete; cut corrected v<X>.<Y+1>.0; release note on bad tag's
  page; emergency ruleset-disable path). Includes a triage
  checklist matching the rule-regression.md template's pattern.
- [x] **(v) Empty CANDIDATE_TAG fallback.** If the Resolve-tag step
  itself failed before assigning the output (malformed tag ref),
  the issue title falls back to `${GITHUB_REF##refs/tags/}` so
  the alert isn't lost.
- [x] **(vi) Doc updates.** workflow header + VERSIONING.md "Machine
  enforcement (2)" + ADOPT-001 §12.7.7 SCP-EREL-001 row all updated
  to reflect that the auto-issue is now live (the `(per TF-020H3rg-003)`
  qualifier removed).
- [x] **(vii) STATUS.md updates.** TF-020H3rg-003 strikethrough'd +
  closed annotation; 020H.3 IN FLIGHT row marked landed at PR #79
  commit `42f49db` (carrier-slice backfill from 020H.3); 020H.3.1
  IN FLIGHT row added; "Last updated" bumped.

## Out of scope / forward-looking

- **Issue auto-close on corrective tag-cut.** When the operator
  cuts the corrected v<X>.<Y+1>.0, the open `release-gate-violation`
  issue isn't auto-closed. Operator closes manually after the
  triage checklist is complete. Forward-compat: a future workflow
  could auto-close on the next clean run that targets the same
  tag-series. Not in scope; would file as TF-020H3rg-004 if needed.
- **Estate-cascade adopter alerting.** When SCP cuts a bad tag,
  Renovate-using adopters see the corrected-tag bump within hours;
  manually SHA-pinning adopters see SCP-FRESH-001 only after 3+
  MINOR releases (per the existing freshness-threshold default).
  This slice doesn't change that latency. Cross-references
  ADOPT-001 §12.7.11 + VERSIONING.md "Bad-tag recovery procedure"
  for the existing detection chain.

## R1 review

3× parallel Sonnet R1 review (correctness / safety_bypass /
completeness_governance). Recurse to fixpoint per
`feedback_recursive_adversarial_review.md`.

## Files

- `.github/workflows/release-gate.yml` — `permissions` extended; new
  "Open release-gate-violation issue (post-tag observer only)" step;
  workflow header updated.
- `policies/VERSIONING.md` — Machine enforcement (2) subsection text
  qualifier removal.
- `docs/adoption/ADOPT-001-project-onboarding.md` — §12.7.7 SCP-EREL-001
  row text qualifier removal + auto-issue mention.
- `STATUS.md` — TF-020H3rg-003 closed + 020H.3 landed mark + 020H.3.1
  IN FLIGHT row + Last-updated bump.
- `docs/reviews/WP-SCP-022/dispatches/020h3-1-auto-issue/DISPATCH-NOTE.md` — this file.
