"""Non-conformant adopter (WP-SCP-028 Phase 2 LOAD-BEARING selftest fixture).

Imports the ct-auth SDK yet re-implements `validate_token`, a `tier_deny`
canonical primitive (security-class). SCP-R-010 therefore emits a DENY-class
finding. Because SCP-R-010 is in WARN_BASELINE_RULES (the coupling guard), the
finding is rendered ::warning:: and EXCLUDED from the merge-gate threshold — so
the reusable workflow runs with `threshold: deny` and STILL exits 0 (gate
GREEN). If SCP-R-010 were materialised but NOT added to the warn-baseline set,
this job would deny-BLOCK; `result == success` proves the two landed together.
"""

from ct_auth import jwks_client  # imports the SDK -> the import-fence applies


def validate_token(token):
    # tier_deny shadow: re-implementing the canonical primitive instead of
    # calling the SDK's. This is the security-class drift SCP-R-010 catches.
    return token is not None
