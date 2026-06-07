# fixture-scp-r-028-pass — conformant adopter (WP-SCP-028 Phase 2)

Proves the **opted-in + conformant** row of the auth-canonical companion
materialisation: with the canonicals present and cosign-verified
(`simulate-auth-verified: true`), SCP-R-009/010/011 all evaluate against real
inputs and emit **no finding**; the merge gate is GREEN.

- `repo/auth_client.py` — imports the ct-auth SDK and USES `verify_request`; it
  does not shadow a protected primitive (SCP-R-010), hardcodes only the
  canonical issuer `https://ct.brokapps.ai` (SCP-R-011), declares no old-shape
  Claims type, and carries no manifest (SCP-R-009 has no dep to compare, so it
  is active-but-vacuous here; its version path is covered by
  `policies/tests/scp_r_009_test.rego` and by `fixture-scp-r-028-import-fence`'s
  sibling materialisation). It is a `.py` file, which conftest does not parse,
  so the per-file pass (SCP-R-001..008) sees zero targets — the oracle is just
  the SCP-R-003 `no-manifest-applicable` observability record.
- `canonicals/` — frozen fixture canonicals (NOT the live CT artefacts), read by
  the materialisation step because the harness passes
  `auth-canonical-source: tests/workflow/fixture-scp-r-028-pass/canonicals`.
  They live OUTSIDE `repo/` so conftest never enumerates them.

The harness invokes this with `threshold: deny`; `result == success` is asserted
by the orchestrator, and the summary is compared byte-for-byte to
`expected-annotations.json`.
