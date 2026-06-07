# fixture-scp-r-028-import-fence — LOAD-BEARING coupling guard (WP-SCP-028 Phase 2)

The keystone of the auth-canonical companion activation (mirrors
`fixture-scp-r-030-marker-absent`). `repo/auth_shim.py` imports the ct-auth SDK
and re-implements `validate_token`, a `tier_deny` canonical primitive, so
SCP-R-010 emits a **deny-class** finding. The reusable workflow runs with
`threshold: deny` and MUST still exit 0 (`result == success`): SCP-R-010's
membership in BOTH `WARN_BASELINE_RULES` sites demotes the finding to
`::warning::` and excludes it from the threshold. This proves the §4.1 coupling
guard — the materialisation step and the warn-baseline membership landed in the
SAME PR, so an adopter with a shadowed primitive WARNS instead of being BLOCKED.

`canonicals/` is read via `auth-canonical-source`; `simulate-auth-verified: true`
stands in for a successful `cosign verify-blob` so the rule's version/import/
claim logic (not its fail-closed branch) is exercised. `.py` is conftest-unparsed,
so the only non-auth oracle entry is the SCP-R-003 `no-manifest-applicable` record.
