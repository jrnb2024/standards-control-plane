# PLAN-SCP-ESTATE-AUTHORITY-001 — Dark authority-selector contract

## Scope and review tier

This is the Standards Control Plane owner slice of
DA-ESTATE-CONTEXT-CLOSURE-001. It is a HEAVY contract/security change under GOV-009.
Gate C therefore requires the programme's three independent review lenses before merge.

## Gate A

1. Load SCP local governance and the global requirements, strategy, architecture and
   programme plan.
2. Compare the proposed projection byte-for-byte with doc-agent's
   `source-authority-bundle.js` and runtime fail-closed behaviour.
3. Publish this requirement, strategy, architecture and plan before gated writes.
4. Use the operator-created Pattern 3 dispatch only for its exact scoped paths; do not
   widen or self-modify it.

## Gate B build sequence

1. Write RED tests for schema closure, signature tamper, purpose/status/time failures,
   registry and key rotation, sequence rollback, same-sequence fork, predecessor
   mismatch, epoch transition, revocation, duplicates, expiry and supersession cycles.
2. Add closed Draft 2020-12 bundle and registry schemas.
3. Implement the read-only Python validator and exact doc-agent selection projection.
4. Add public-only valid and revoked fixtures; assert no private material is present.
5. Add a governance linkage manifest naming owner, consumer, contract state and exact
   evidence paths without claiming activation.
6. Run focused pytest, Ruff, schema validation, secret scan and `git diff --check`.

## Gate C

The programme orchestrator will run independent data-integrity, security/bypass and
architecture/completeness reviews on the integrated final diff. Every P0/P1/P2 finding
must enter RED/GREEN closure. This executor does not merge, sign or activate.

## Gate D and dependency order

1. Merge/deploy the dark Control Tower identity contract.
2. Merge this SCP contract through PR and required policy checks.
3. Operator provisions purpose-separated keys out of band and publishes the first
   reviewed registry/head/selection set; no agent-generated private key is accepted.
4. The docker-host root verifier validates this upstream contract, persists high-water
   state and writes the short-lived host projection consumed by doc-agent.
5. Doc-agent shadow mode proves registry/head/projection digests and revocation/lease
   behaviour before authority enforcement can be enabled.

## Rollback

This slice is dark and additive. Before activation, rollback is removal/revert of the
contract PR. After future activation, consumers first set `SOURCE_AUTHORITY_ENABLED=false`
and read back the prior config digest; the signed registry/head remain available until
every consumer is off. Revocation and high-water evidence are retained, never reset.

## Explicit exclusions

- no private/secret key creation or storage;
- no live authority claim or selection population;
- no systemd/poller installation;
- no change to doc-agent, Control Tower, ACC or client configuration;
- no commit, push, PR, merge, deployment or feature activation by this executor.

## Local Gate-B evidence

- Authority contract suite: `42 passed`.
- Adjacent registry/examples/audit-contract regression: `27 passed`.
- Full repository snapshot: `477 passed, 6 failed`; the six failures reproduce the
  checkout baseline outside this change set (three scorecard golden URL drifts, the
  existing repository secret-scan pair, external-repo MCP subprocess import setup and
  the stale governance-rule-count assertion).
- Ruff on changed Python: passed.
- Strict mypy on the validator: passed.
- Draft-2020-12 meta-schema checks, JSON parsing, changed-file secret scan and trailing-
  whitespace/diff checks: passed.
- Gate C, commit/PR/merge, live key custody, publication, poller projection and activation
  remain open and are not claimed by this evidence.
