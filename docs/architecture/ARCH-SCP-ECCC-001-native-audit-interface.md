# ARCH-SCP-ECCC-001 — Audit CLI contract

The contract is immutable JSON under `contracts/interfaces/` and names the executable,
subcommand, arguments, request/result schema paths, stdout media type, exit codes and
optional persistence side effect. A focused pytest loads the real parser and schemas,
runs a representative read-only audit request, and proves the emitted result satisfies
the declared result schema. The request schema constrains `scope.subsystem` to the
safe identifier grammar `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$` so a value interpolated
by output writers cannot contain path separators, whitespace, absolute-path prefixes,
or dot-segment values. The contract is catalogue evidence; runtime output is not.

The default audit mode makes no persistence calls. `--write-output` opts into the
existing findings, report, CI, and Control Tower writer sequence; those production
writers own their concrete output paths, so this contract intentionally makes no
unverifiable fixed-path claim. The focused test binds that sequence with monkeypatched
production functions while all filesystem assertions use temporary isolation.
