# STRAT-SCP-ESTATE-AUTHORITY-001 — Select authority outside the source repository

## Approach

Create one versioned authority bundle containing three independently checkable layers:

1. a root-authorized selector-key registry with purpose-separated Ed25519 public keys;
2. a selector-signed, sequenced and expiring authority head with revocation state; and
3. selector-signed commit/path/blob-bound selection envelopes that project exactly into
   doc-agent's `estate-authority-selections/v1` consumer format.

An offline SCP validator enforces the closed shapes, canonical signature bytes,
purpose/status/time authorization, digest relationships, revocation, supersession and
anti-rollback rules. Fixtures demonstrate positive and revoked states without publishing
any private key or live authority.

## Why this shape

Repository metadata is useful lifecycle evidence but is not independent authority. A
selector signature prevents a source repository from promoting its own prose, while
commit/path/blob binding prevents a valid selection from drifting to changed bytes. A
signed head makes the whole selected set revocable and gives a durable verifier a
monotonic state to ratchet. Projecting into the already implemented doc-agent selection
manifest avoids a second consumer vocabulary.

## Rejected alternatives

- Trust `.doc-lifecycle.json`, frontmatter or repository-side signatures. The source
  would still ratify itself.
- Infer authority from recency, file name or branch. None proves reviewed selection.
- Put a private signing key in SCP, doc-agent or a fixture. Key custody is an
  operator-owned deployment concern and is deliberately absent from this dark slice.
- Let doc-agent fetch SCP or validate arbitrary repository files directly. The runtime
  consumes only independently distributed, digest-bound projection bytes.
- Reset monotonic state on an epoch change. Epoch transition is itself authorized; it is
  not a bypass around the high-water mark.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Canonicalization differs across Python and Node | Restrict values to JSON primitives and implement sorted-key compact UTF-8 canonicalization matching doc-agent; pin canonical-byte tests. |
| A key is reused for another purpose | Every registry row carries an exact signing purpose and the validator checks it before signature verification. |
| Rotation silently installs an attacker key | Registry transition needs old-and-new signatures; higher authority epoch needs prior-and-new root signatures. |
| Revocation is represented but ignored | Projection construction removes revoked digests and rejects selected/revoked overlap; tests prove changed projected digest. |
| A signed selection points at different bytes | Repository, commit, normalized path and raw source-blob SHA are covered by the signature and projected unchanged. |
| Fixture success is mistaken for live activation | Governance metadata explicitly reports `dark_contract`; no key, systemd unit, config change, merge or deployment is part of this slice. |
