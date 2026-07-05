# SCP MCP Error Codes

The Standards Control Plane MCP server uses the `SCP-MCP-E0NN` error taxonomy for structured tool responses.

## Ranges

- `SCP-MCP-E001` through `SCP-MCP-E009`: protocol, handshake, or transport errors
- `SCP-MCP-E010` through `SCP-MCP-E019`: gating and circuit-breaker errors
- `SCP-MCP-E020` through `SCP-MCP-E029`: business-logic errors
- `SCP-MCP-E030` through `SCP-MCP-E099`: reserved

## SCP-MCP-E010

Reserved in 021C for the offline break-glass path populated by slice 021I.

## SCP-MCP-E011

`audit_changed` exceeded the 120 second wall-clock timeout.

Remediation: reduce the audit scope, retry with narrower refs, or run the heavier audit path outside MCP.

## SCP-MCP-E012

`audit_changed` refused to run because the diff exceeded the 500 changed-file cap.

Remediation: split the change set, narrow the refs, or use the non-MCP audit path for the larger review.

## SCP-MCP-E020

`propose` rejected a proposal on anti-spam grounds: either the caller exceeded the 10 submissions per rolling hour limit, or the body matched a normalised-text hash already queued within 24 hours. For stdio callers, the hourly limit is advisory because the caller key is `pid + executable path`; the branch-not-main invariant remains the hard safety boundary across process restarts.

Remediation: wait for the rolling-hour window to clear before retrying, or update the proposal body materially and inspect the existing `PROP-NNN.md` submission instead of resubmitting.

## SCP-MCP-E021

The request was invalid for the selected tool, the signing key ring required by `propose` was not configured, or the underlying SCP data source could not be parsed for that request.

Remediation: correct the request shape or inspect the referenced SCP artifact before retrying.

For `audit_changed` specifically, this is the code surfaced when `area_id` cannot
be inferred from the changed files (no `ENH-NNN-*.md` spec and no
`frontend/app/<route>/page.tsx` route in the diff). It is **recoverable**: pass
`area_hint` (the explicit area id), and optionally `subsystem`. `audit_changed`
audits `repo_root`, which **defaults to the MCP server's current working
directory** (mirroring the CLI) — set it explicitly when the server does not run
inside the repository you intend to audit. A `repo_root` that is not a git work
tree, or a base/head ref absent from that tree, fails loudly rather than silently
auditing the wrong repo. (The cwd-vs-`repo_root` mismatch guard is a CLI/library
check; the MCP tool runs its subprocess with `cwd = repo_root`, so it audits the
`repo_root` you pass.)

## SCP-MCP-E022

The requested SCP entity was not found in the current committed-state data set.

Remediation: verify the identifier and retry against the current findings, waiver, or decision corpus.
