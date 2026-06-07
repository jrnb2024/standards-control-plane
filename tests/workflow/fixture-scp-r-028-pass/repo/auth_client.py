"""Conformant adopter auth client (WP-SCP-028 Phase 2 selftest fixture).

Imports the ct-auth SDK and USES its canonical primitives — it does not
shadow/re-implement any protected primitive (SCP-R-010), hardcodes only a
canonical issuer (SCP-R-011), and declares no old-shape Claims type. With the
canonicals cosign-verified (simulate-auth-verified=true) all three auth rules
evaluate against real inputs and produce NO finding: the conformant path.
"""

from ct_auth import verify_request  # canonical SDK primitive (used, not shadowed)


def build_session(request):
    # Reads the Authorization header and delegates verification to the SDK.
    token = request.headers.get("Authorization", "")
    issuer = "https://ct.brokapps.ai"  # a canonical issuer (in CT's issuers set)
    return verify_request(token, issuer=issuer)
