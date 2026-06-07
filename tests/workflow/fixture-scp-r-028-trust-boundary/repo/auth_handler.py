"""Trust-boundary fixture (WP-SCP-028 Phase 2 — FUP-VERIFIED-FLAG-TRUST-
BOUNDARY-001).

This adopter file deliberately ASSERTS that the canonicals are verified, to try
to fool the gate into trusting them. It must NOT work: the materialisation step
derives `auth_contract_verified` / `canonical_sdk_versions_verified` ONLY from
the workflow's own `cosign verify-blob` exit (here the harness drives a FAILED
verify via `simulate-auth-verified: false`), never from repo content. So the
rule still sees verified=false and fires its fail-closed signature finding
(deny-class, warn-rendered, gate GREEN). If the materialisation ever read the
flag from a repo file, this fixture's oracle would have NO finding — the test
would fail loudly.
"""

from ct_auth import jwks_client  # imports the SDK -> the import-fence applies

# Spoof attempt — these are read by NOTHING in the materialisation step; the
# `*_verified` flags come from cosign / the simulate input, not from here.
auth_contract_verified = True
canonical_sdk_versions_verified = True
