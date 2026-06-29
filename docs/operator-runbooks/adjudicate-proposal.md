# Runbook: adjudicate a queued SCP proposal (interim, until WP-SCP-022 ships)

The MCP `propose()` intake is live and stages proposals as
`docs/reviews/proposals/PROP-NNN.md` with `adjudication_status: queued_no_adjudicator`.
**The automated adjudication workflow is NOT yet built** (WP-SCP-022 §12 —
"proposals queue until adjudication ships"). This runbook is the interim, manual
path to turn a queued proposal into a live rule that `consult_rules` serves.

> Rule-authoring is SCP self-work → it is **Pattern-3** (D-057). Declare scope for a
> Claude Code session FIRST, from a normal terminal (not inside the session):
> `scripts/operator/scp-pattern3-dispatch.sh "standards/**" "docs/reviews/proposals/**" "docs/DECISIONS.md"`

## Queue status
All three opening proposals are **ACCEPTED and live** (adjudicated 2026-06-28, #220; `consult_rules` serves them):
- **PROP-001 → SVC-004** — dev/staging deploy recipe (service-lifecycle). *(SVC-004 deploy-script `applies_to` globs added in #222.)*
- **PROP-002 → GOV-004** — four-tier orchestrator build method, TDD + adversarial reviews (governance).
- **PROP-003 → GOV-005** — operating stance: dev-only / no prod / no ceremony / cost-not-a-gate (governance).

Each proposal's full text is in `docs/reviews/proposals/PROP-NNN.md` (now `adjudication_status: accepted`). No proposals are currently queued; this runbook applies to the next `propose()` intake.

> 🔑 Merge gotcha (from #220): `main` enforces `required_signatures`. The COMMITTER email must match a verified signing key on the GitHub account (`james.brooke@mapp.com`), or GitHub marks the commit *Unverified* and the merge blocks even after the gated-merge drops the invocation-log check. Commit with `-c user.email=james.brooke@mapp.com`.

## To ACCEPT a proposal (make it a live rule)

1. **Decide.** Read the proposal. Resolve its "Open reconciliation" notes (e.g. PROP-001:
   confirm `DEC-PIM-017` wording + staging hostname convention). Accept / amend / reject is
   the governance call.

2. **Author the rule prose** at `standards/<domain>/rules/<RULE-ID>-<slug>.md`, matching the
   existing format (see `standards/governance/rules/GOV-001-scope-boundaries.md`):
   `# <RULE-ID> — <Title>` · **Domain / Version / Status: active / Severity default** · summary ·
   `## Signals` · `## Rationale`.

3. **Add the registry entry** to `standards/<domain>/index.json` (the per-domain index the
   loader reads — top index `standards/standards-index.json` maps domain → `<domain>/index.json`).
   Validate against `schemas/standards-rule.schema.json`: `rule_id`, `domain`, `title`, `summary`,
   `path` (the .md), `severity_default`, `scope`, `signals`, `applies_to` (globs that decide which
   changed files the rule fires on). Bump the domain `version`.

4. **Record the decision** in `docs/DECISIONS.md` (`D-NNN`: accept PROP-NNN as <RULE-ID>, date,
   rationale, ACCEPTED).

5. **Retire the queue entry** — set the proposal file's `adjudication_status: accepted` (+ the
   `<RULE-ID>` and decision ref), or move it under an `accepted/` subfolder.

6. **Open a PR.** The body MUST carry a `## R1 evidence` block (correctness / safety_bypass /
   completeness_governance) or a `## Protocol deviation` block — the `validate PR body` check
   enforces this. `policy-check` must be green.

7. **Merge.** Either the full WP-SCP-024 DISPATCH-NOTE flow (if you treat it as a work package),
   or the non-WP escape hatch:
   `scripts/operator/scp-gated-merge.sh <PR_NUMBER>`
   (temporarily drops ONLY `check-invocation-log-entry`, merges, and always restores branch
   protection exactly; refuses unless `policy-check` is already green).

8. **Verify.** Reconnect the scp-standards MCP server, then
   `consult_rules({domain:"<domain>"})` — the new rule is now served.

## To REJECT or AMEND
Set the proposal file's `adjudication_status: rejected|amended` with a one-line reason + decision
ref, and (if amended) open a follow-up `propose()` with the revised text.

## Notes
- This whole interim path is replaced once the WP-SCP-022 proposal-queue adjudication workflow
  ships (then `adjudicate` becomes a first-class operation).
- `scp-gated-merge.sh` is the reusable "get a non-WP governed change past `enforce_admins` +
  the invocation-log gate" operator step — use it for adjudication, key-ring rotation, runbook
  edits, etc.
