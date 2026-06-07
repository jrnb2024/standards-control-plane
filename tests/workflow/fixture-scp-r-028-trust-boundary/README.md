# fixture-scp-r-028-trust-boundary — the verified-flag trust boundary (WP-SCP-028 Phase 2)

Closes + TESTS **FUP-WP-SCP-028-VERIFIED-FLAG-TRUST-BOUNDARY-001**: an adopter
cannot spoof `auth_contract_verified` / `canonical_sdk_versions_verified` by
asserting them in its own repo. `repo/auth_handler.py` imports the ct-auth SDK
and sets `auth_contract_verified = True` / `canonical_sdk_versions_verified =
True` — a deliberate spoof. The harness drives a FAILED verification with
`simulate-auth-verified: false` (standing in for a `cosign verify-blob` that did
not pass). Because the materialisation step derives `*_verified` ONLY from that
cosign exit / simulate input — NEVER from repo content — the rule still sees
`verified=false` and emits SCP-R-010's fail-closed signature finding
(`file: auth-contract-v1.yaml`), warn-rendered, gate GREEN.

If the materialisation ever read the flag from repo content, the spoof would
flip it to true and the fail-closed finding would vanish — so the presence of
the finding in the oracle IS the proof the trust boundary holds.

`canonical_sdk_versions_verified` is set by the identical code path (one
assignment from the same source), so proving the boundary for
`auth_contract_verified` proves it for both. `.py` is conftest-unparsed, so the
only non-auth oracle entry is the SCP-R-003 `no-manifest-applicable` record.
