# ARCH-SCP-ESTATE-AUTHORITY-001 — Signed selector bundle contract

## 1. Files and trust boundary

The contract is published under `schemas/estate-authority/v1/` and validated by
`standards_control_plane.estate_authority`. Inputs are data only. The validator performs
no filesystem lookup based on a selected path, no Git operation, no network request and
no state write.

The top-level `estate-authority-bundle/v1` object has exactly:

```text
schema_version
registry            estate-authority-selector-registry/v1 envelope
head                estate-authority-head/v1 envelope
selections[]        estate-authority-selection/v1 envelopes
```

Every signed envelope has the exact keys `schema_version`, `payload`, `signature`.
`signature` has exactly `algorithm`, `key_id`, `value`. The signed bytes are compact
UTF-8 JSON for `{schema_version,payload}` with object keys recursively sorted; arrays
retain order. `algorithm` is exactly `Ed25519`; `value` is unpadded base64url.

## 2. Selector registry and rotation

The registry payload declares registry ID, registry epoch/sequence, predecessor digest,
issuance/expiry, and one to eight keys. Each key binds ID, purpose, status, public key and
validity window. The same raw Ed25519 public-key material cannot appear under two IDs or
purposes. Purposes are `estate-authority-registry-root` and
`estate-document-authority-selection`; statuses are `active|next|revoked`.

The registry envelope is signed by an active registry-root key contained in the current
registry. The initial registry is accepted only when pinned by the caller's expected
registry digest. A later registry must increase sequence, bind the prior registry digest
as predecessor, and carry a `rotation` object. That object names the prior and introduced
root key IDs and contains signatures by both keys over the new registry's canonical
`{schema_version,payload}` bytes. The introduced key must be `active|next`, valid and
purpose-separated. The two rotation signatures cover
`{schema_version: estate-authority-registry-rotation/v1, payload}` where `payload` is
the new registry payload with the two rotation signature values omitted; the envelope
signature then covers the complete registry payload. Across accepted states, an ID's
purpose and public-key fingerprint are immutable, status transitions only move toward
revocation, and removal is allowed only after revocation. Removed IDs become durable
retirement tombstones and cannot be reused. A legacy high-water record is accepted while
the registry is unchanged, but it must be upgraded before any registry transition.

## 3. Selection envelope

The selection payload is deliberately byte-semantic with one doc-agent projection row:

```text
selection_id, project_id, repository_id, source_revision, path,
source_blob_sha256, lifecycle, authority, evidence_scope, selector_id,
sequence, predecessor_digest, review_ref, expires_at, supersedes
```

The selected timestamp is the signed head's `issued_at`; all rows in one projection are
reviewed under that head. A selection signature key must equal `selector_id`, be active,
carry purpose `estate-document-authority-selection`, and be valid both at head issuance
and validation time. The selection sequence equals the head sequence and predecessor
equals the head predecessor. Lifecycle/authority pairs are exact:

| lifecycle | authority |
|---|---|
| `canonical` | `canonical` |
| `active` | `active_noncanonical` |
| `superseded` | `superseded` |

Evidence scope is `repository_guidance|documentation`. Positive selection never changes
evidence class; doc-agent keeps that as an orthogonal corpus field.

## 4. Signed head, digests and revocation

The head payload includes `authority_epoch`, `sequence`, `head_digest`,
`predecessor_digest`, `selector_registry_digest`, `selection_digest`,
`revocation_digest`, active/revoked key IDs, revoked selection digests, issue/review
identity and issuance/expiry.

To avoid self-referential hashing, `head_digest` is SHA-256 over canonical head payload
with `head_digest` and the downstream `selection_digest` omitted. The included
`selection_envelopes_digest` still binds the complete signed selection set before the
head digest is computed. `revocation_digest` is SHA-256 over the canonical object
`{"revoked_key_ids": [...], "revoked_selection_digests": [...]}`. These are the signed
revocation deltas for that head; arrays are unique and sorted by UTF-8 bytes. A delta may
name an envelope included in the current bundle or one bound by the immediately previous
accepted high-water record. The validator unions accepted deltas into durable cumulative
tombstones. A later head therefore advances without repeating all historic revocations.

`selection_digest` is SHA-256 over the exact compact UTF-8 bytes of the projected object:

```json
{"schema_version":"estate-authority-selections/v1","authority_epoch":1,"sequence":1,"head_digest":"sha256:...","selections":[...]}
```

Rows are sorted by `(repository_id, path, selection_id)` and retain exactly doc-agent's
closed row keys. The complete canonical projection is capped at 4 MiB, matching the
consumer's bounded file reader. A selection envelope digest is SHA-256 over its complete
canonical envelope. Any envelope whose digest is in the cumulative revoked-selection set
is excluded. A current envelope may be carried specifically so its signed digest can be
revoked; it is validated cryptographically but is not projected.

The head is signed by an active selector key listed in `active_key_ids`. Revoked keys may
not remain active. Head expiry is no more than 24 hours after issuance; every selection
must outlive the head but is still rejected when expired at validation time.

## 5. Anti-rollback and epoch transition

The caller may pass a previously accepted high-water record containing authority/head
and registry sequence/digest fields plus cumulative revoked-key and revoked-selection
tombstones. The strengthened record also contains the current registry key bindings
(`key_id`, purpose, status and raw-public-key SHA-256), retired-key tombstones, and the
prior head's exact selection-envelope digests.

- lower epoch: reject;
- same epoch/lower sequence: reject;
- same epoch/same sequence/different head: reject as a fork;
- same epoch/higher sequence/wrong predecessor: reject;
- higher epoch: require an `epoch_transition` carrying prior epoch/head/registry, new
  epoch and signatures from both the prior active root key and a current active root key.

A changed registry must likewise increase its `(registry_epoch, registry_sequence)` and
its dual-signed rotation must name the exact previously accepted registry digest. Same-
or-lower registry sequence, registry rollback, wrong registry predecessor, material or
purpose replacement, status rollback, removal before revocation, and reuse of a retired
or revoked key ID fail closed. All sequence and epoch integers are bounded by JavaScript's
safe-integer maximum so Python and JavaScript consumers cannot disagree.

The validator proves the transition but does not persist it. The root-owned verifier is
responsible for fsynced high-water storage and local lease projection.

## 6. Supersession graph

Selection IDs and `(repository_id,path)` bindings are unique. Each `supersedes` target
must exist in the projected set and have lifecycle `superseded`. Depth-first validation
rejects every cycle, including self-cycles. A revoked target cannot satisfy a surviving
selection's supersession reference.

## 7. Compatibility with doc-agent

`validate_authority_bundle()` returns the exact `estate-authority-selections/v1`
projection plus authority epoch, sequence, head/selection/revocation/registry digests.
The projected row keys and value grammar match
`src/lib/source-authority-bundle.js` in mapp-doc-agent. SCP does not create the
host-local `estate-authority-projection/v1`: the root-owned verifier/poller signs that
short-lived host lease after accepting this upstream contract.

## 8. Failures and limits

Failures are stable `EstateAuthorityError.code` values and include schema, registry,
signature, digest, authorization, time, revocation, duplicate, supersession, rollback,
fork, predecessor and epoch-transition failures. The bundle is capped by schema at
10,000 selections, eight registry keys and 10,000 revocations. JSON Schema validation
precedes cryptographic work.
