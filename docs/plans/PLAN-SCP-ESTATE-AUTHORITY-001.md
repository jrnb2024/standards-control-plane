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
2. Add closed Draft 2020-12 bundle, registry and durable high-water schemas.
3. Implement the read-only Python validator and exact doc-agent selection projection.
4. Add valid and revoked public-contract fixtures; assert their exact closed shape and
   reject credential-bearing key names without claiming arbitrary-value secret proof.
5. Add a governance linkage manifest naming owner, consumer, contract state and exact
   evidence paths without claiming activation.
6. Run focused pytest, Ruff, schema validation, secret scan and `git diff --check`.
7. Exercise real chained registry revoke/remove/retire transitions, prior-root eligibility,
   genuinely new rotation IDs, exact serialized restart state and collection-capacity
   boundaries. No injected legacy tombstone is accepted as proof of compaction.
8. Persist retired material fingerprints and prove that removal-plus-fresh-ID reuse and
   later reuse after canonical serialization both fail. Legacy state with unrecoverable
   retired material requires an authenticated-history migration rather than inference.

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
every consumer is off. Revocation and high-water evidence are retained, never reset. A
versioned capacity limit fails before mutation; raising or migrating that limit requires
a separately reviewed contract migration with authenticated backup continuity.

## Explicit exclusions

- no private/secret key creation or storage;
- no live authority claim or selection population;
- no systemd/poller installation;
- no change to doc-agent, Control Tower, ACC or client configuration;
- no commit, push, PR, merge, deployment or feature activation by this executor.

## Local Gate-B evidence

- Authority contract suite: `67 passed` on Python 3.14.
- Full dependency-complete repository snapshot: `512 passed, 6 failed` on Python 3.14.
  The six failures are unchanged, out-of-scope repository-baseline failures: three stale
  scorecard golden URLs, two known secret-scan fixture false positives, one external-repo
  subprocess import setup failure, and one stale governance-rule count (the two secret
  fixture paths form one pytest failure, so these causes total six tests).
- Ruff on changed Python, strict mypy on the validator, Draft-2020-12 meta-schema checks,
  JSON parsing and `git diff --check`: passed.
- The complete environment was installed into an untracked local `.venv`; no generated
  environment content is part of this candidate.
- Gate C, commit/PR/merge, live key custody, publication, poller projection and activation
  remain open and are not claimed by this evidence.
