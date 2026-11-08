# REQ-SCP-ECCC-001 — Native standards-audit interface

Expose a checked-in, machine-readable contract for the already implemented
`standards-control-plane audit --request <json> [--overlay <path>] [--write-output]`
boundary. It must bind the existing audit request/result schemas, supported flags,
stdout JSON result, side-effect opt-in and exit semantics. It must not describe
`audit-changed`, `consult`, HTTP service behaviour or functionality not exercised by
the current CLI. A conformance test must compare the contract with the real parser,
schemas and command result. No production behaviour changes.
