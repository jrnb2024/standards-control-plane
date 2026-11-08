# ARCH-SCP-ECCC-001 — Audit CLI contract

The contract is immutable JSON under `contracts/interfaces/` and names the executable,
subcommand, arguments, request/result schema paths, stdout media type, exit codes and
optional persistence side effect. A focused pytest loads the real parser and schemas,
runs a representative read-only audit request, and proves the emitted result satisfies
the declared result schema. The contract is catalogue evidence; runtime output is not.
