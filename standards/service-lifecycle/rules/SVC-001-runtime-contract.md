# SVC-001 — Service Must Declare Runtime Contract

**Domain:** service-lifecycle  
**Version:** 1.0.0  
**Status:** active  
**Severity default:** high

Every service registered in `services.yml` must include a `runtime_contract`
block under its `local` environment.  The contract declares how the service is
started, what infrastructure and peer services it depends on, and what group
it belongs to for selective startup.

## Signals

- service entry in `services.yml` has no `runtime_contract` under `local`
- `runtime_contract` missing required fields (start_command, working_dir, interpreter, required_infra, group)
- `interpreter` is `python-venv` but `venv_path` is not set
- `working_dir` points to a directory that does not exist

## Rationale

Without a runtime contract, service dependencies are implicit, startup ordering
is ad-hoc, and automated conformance auditing of the estate's runtime topology
is impossible.  The contract makes dependencies, grouping, and health
expectations explicit and machine-readable.

## Exceptions

- Services with `local.status: planned` are exempt until they reach `ready`.
- Services that are inherently compose-only (e.g. multi-container Go
  microservice meshes) should still declare a contract with
  `interpreter: none` and a `docker compose up` start command so the ecosystem
  generator can include them.

## Schema

`schemas/runtime-contract.schema.json`
