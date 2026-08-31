# REQ-SCP-ECCC-001 — Native standards-audit interface

Expose a checked-in, machine-readable contract for the already implemented
`standards-control-plane audit --request <json> [--overlay <path>] [--write-output]`
boundary. It must bind the existing audit request/result schemas, supported flags,
stdout JSON result, side-effect opt-in and exit semantics. It must not describe
`audit-changed`, `consult`, HTTP service behaviour or functionality not exercised by
the current CLI. A conformance test must compare the contract with the real parser,
schemas and command result. There is no command, output, endpoint or service change;
the sole production behaviour change is the intentional fail-closed tightening of
unsafe `scope.subsystem` validation before optional persistence.

Validation closure: `scope.subsystem` is a safe identifier, matching
`^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`. It starts with an alphanumeric character,
is at most 128 characters, and excludes slash, backslash, dot-segment values,
whitespace, and absolute paths before any optional output persistence is reached.
The focused conformance test records malformed-request exit 1, argparse misuse exit
2, traversal rejection without filesystem escape, read-only default behaviour, and
isolated `--write-output` delegation.
