"""Stub that mimics SCP's evaluator source containing marker strings.

Simulates what happens when SCP is audited against its own repo. The real
evaluator skips files at this path suffix so these literals don't
self-poison the code-pattern scan.
"""

MODE_CODE_MARKERS = {
    "mode.user_oidc": ("ControlTowerAuth", "ct_auth.", "create_bff_routes", "CT_JWKS_URL"),
    "mode.service_rs256": ('algorithms=["RS256"]', "algorithms=['RS256']"),
    "mode.api_key": ("X-API-Key", "x-api-key"),
    "mode.bearer_legacy": ("secrets.compare_digest",),
}
