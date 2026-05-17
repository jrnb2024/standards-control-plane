# Branch-protection invocation log

This log captures every invocation of `scripts/enable-required-check.sh`
against an adopter repo. The log commit is part of the invocation
procedure per WP-SCP-020 §4 020G(iii); without the log entry the
apply is unrecorded.

## Format

Each invocation appends a new section under "## Invocations" with:
- Timestamp (ISO 8601 UTC).
- Target repo + branch.
- Operator handle.
- Script SHA at invocation time (so a future audit can correlate
  the apply with the script source as it stood that day).
- The exact PUT payload applied.
- Before-state and after-state of the GitHub branch-protection
  configuration.
- `preserve-existing-contexts: {true|false}` — added in WP-SCP-024
  024C fix-round-4. Indicates whether the invocation merged the
  canonical context into the target branch's pre-existing
  required_status_checks.contexts (`true`, brownfield) or REPLACED
  them with a single-element list (`false`, greenfield default).
  Audit-grep this field to enumerate brownfield-adopter invocations.
- `skip-required-signatures: {true|false}` — added in WP-SCP-024
  024C fix-round-4. Indicates whether the invocation skipped the
  dedicated POST to `.../required_signatures`. When `true`, the
  adopter MUST have an open `FUP-<ADOPTER>-COMMIT-SIGNING` row in
  their governance tracker (per ADOPT-001 §12.7.3); audit-grep
  this field to enumerate adopters with deferred commit-signing
  enforcement.
- Optional CAUTION lines — emitted by the script when a posture-
  degrading flag was used (`--no-enforce-admins`,
  `--skip-required-signatures`, or the destructive context-
  replacement default detected with pre-existing non-canonical
  contexts). CAUTION lines render directly into the entry above
  the PUT-payload block so they are visible in the committed log.

## Why log on the SCP repo

The federation primitive is owned by SCP. Adopter-side branch
protection is a downstream effect of pinning the SCP wrapper —
the audit trail belongs at the federation source, not at the
adopter. This is symmetric with `docs/security/branch-protection.md`
(which documents SCP-self's own protections) and `docs/DECISIONS.md`
(which carries the federation-primitive decisions).

## Invocations

<!-- new entries appended below this line by `enable-required-check.sh` operators -->

_(no invocations recorded yet — this slice ships the log file
alongside the script; first real invocation against an adopter
will populate the first entry. Estate cascade rollout = WP-SCP-024.)_
