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
