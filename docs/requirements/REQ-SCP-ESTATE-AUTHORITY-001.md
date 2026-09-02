# REQ-SCP-ESTATE-AUTHORITY-001 — Independent document-authority selection

## Objective

Publish a dark, independently verifiable Standards Control Plane contract for selecting
the exact repository documents that may carry positive `repository_guidance` or
`documentation` authority in Documentation Intelligence. Repository content cannot
self-certify. Every positive selection is selector-signed and bound to one repository,
commit, normalized path and source-blob digest; the signed head is sequenced, expiring,
revocable and resistant to rollback.

This slice publishes contracts and an offline validator only. It creates no signing
key, signs no live selection, changes no runtime flag and deploys nothing.

## Acceptance criteria

| ID | Requirement |
|---|---|
| SCP-EA-01 | The bundle, selector registry, signed head and signed selection envelopes use closed JSON schemas; unknown fields and malformed nested values fail validation. |
| SCP-EA-02 | A selection binds `selection_id`, project/repository identity, 40-hex source commit, normalized relative path, 64-hex source blob SHA-256, lifecycle/authority pair, evidence scope, selector ID, sequence/predecessor, review reference, expiry and exact supersession IDs. |
| SCP-EA-03 | Only a selector key whose purpose is `estate-document-authority-selection`, whose status is `active`, and whose validity window covers validation time may authorize a selection. Repository-originated keys or self-asserted authority are not accepted. |
| SCP-EA-04 | Ed25519 signatures cover RFC-8785-compatible canonical UTF-8 JSON bytes of `{schema_version,payload}`. Signature, payload, key, registry and digest tampering fail closed. |
| SCP-EA-05 | The head binds authority epoch, monotonically increasing sequence, head/predecessor digest, selector-registry digest, exact projected selection-file digest, revocation-delta digest, active/revoked key IDs, newly revoked selection digests, review reference and issuance/expiry. |
| SCP-EA-06 | A previous accepted state rejects lower authority/registry epochs, lower sequences, same-sequence forks and missing head/registry predecessor linkage. It also binds every current key ID to purpose, status, public-key fingerprint and validity window, retains retired-key IDs and their public-key fingerprints plus revoked-selection tombstones, and retains the prior head's exact selection-envelope digests. A higher authority epoch requires an explicit `epoch_transition` signed by a root that was active and valid in the prior accepted binding through transition validation, plus the valid new active root. |
| SCP-EA-07 | Registry rotation requires a closed transition signed by a root that was active in the prior accepted binding and by a genuinely new next/active root ID. The prior root may become revoked in the transition it signs but cannot authorize a later transition. Public-key material cannot be reused under another ID or purpose; retained IDs cannot change purpose, material or validity window; keys must be revoked before removal; retired or revoked IDs and retired or previously bound public-key material cannot be resurrected under any ID or purpose. Revoked keys cannot sign a later registry, head or selection. |
| SCP-EA-08 | Expired registry, head or selection records fail closed. A selection must strictly outlive its head. A head may revoke an envelope in its own set or the immediately preceding accepted set; cumulative tombstones remain in high-water state without forcing every later head to repeat them. Revoked selections are absent from the projected selection set. |
| SCP-EA-09 | Supersession targets exist, are selected as `superseded`, and form an acyclic graph. Duplicated selection IDs or repository/path bindings fail. |
| SCP-EA-10 | Successful validation emits an in-memory projection whose `estate-authority-selections/v1` keys, field names and digest semantics match doc-agent's `source-authority-bundle.js` consumer exactly. |
| SCP-EA-11 | Checked-in valid and revoked fixtures have a closed public contract shape and contain no private-key, seed, bearer-token or credential-bearing fields. This repository-level check does not claim to classify arbitrary secret values. |
| SCP-EA-12 | A governance linkage manifest identifies SCP as selector-contract owner, doc-agent as consumer and the exact schemas/validator/tests without claiming live enforcement. |
| SCP-EA-13 | Successful validation emits a closed `estate-authority-high-water/v1` envelope with a canonical state digest. Its exact serialized bytes are accepted unchanged after restart, are capped at 4 MiB, and never exceed the 8,000-entry bound of any cumulative ID, fingerprint or digest collection accepted by the next validation. Capacity exhaustion fails before acceptance; tombstones are not discarded or reset. |

## Constraints

- SCP owns selector authorization and contract validation, not repository content.
- The selector and registry signing purposes are separated.
- Digests are lowercase `sha256:` plus 64 lowercase hexadecimal characters, except
  doc-agent's existing `source_blob_sha256`, which remains 64 lowercase hex without a
  prefix.
- Repository IDs follow doc-agent's closed lowercase hyphen grammar. Paths are relative,
  slash-normalized, at most 512 UTF-8 bytes, contain no dot/empty components, controls or
  backslashes, and are never resolved by this validator.
- Validation performs no network access, writes no state and never mutates input.
- Anti-rollback enforcement is expressed against caller-supplied previously accepted
  state; durable root-owned high-water persistence remains the verifier/poller owner's
  responsibility.
- The high-water state digest detects corruption of the persisted representation. It is
  not a MAC and does not replace root ownership, atomic durable writes, or restoration
  from authenticated backup.

## Global programme mapping

This owner slice advances DA-ESTATE-CONTEXT-CLOSURE-001 AC-10, AC-20, AC-21, AC-22,
AC-25 and AC-36. Live key custody, root-owned distribution, poller operation and
authority activation remain Gate-D work and are not implied by fixture success.
