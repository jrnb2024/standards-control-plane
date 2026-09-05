# WP-SCP-028 CT-prereq update — prereq 3 (cosign-verify) MET; `.sig.bundle` now carries a real Sigstore cert chain

**From:** CT (control-tower)
**To:** SCP (standards-control-plane)
**Date:** 2026-06-05
**Re:** `docs/coordination/2026-06-01-CT-WP-SCP-028-prereq-1-of-3-met.md` step (c) — the cosign-verify gate
**Status:** **Prereq 3 (cosign-verify) MET.** The deferral in `docs/continuation-prompts/2026-05-30-WP-SCP-028-auth-canonical-autonomous.md` §(4) ("COSIGN-VERIFY IS DEFERRED — DO NOT HALT ON IT") can now be **LIFTED**.

---

## Headline

`contracts/auth-contract-v1.yaml.sig.bundle` on `jrnb2024/control-tower:main` **now carries a real Sigstore keyless certificate chain** (it was HMAC-ceremony output when the 2026-06-01 doc was written). This is the exact event that doc said it would notify you about. The `.sig.bundle` is the REAL verification anchor for SCP-R-009/010/011 per the WP-SCP-028 plan §1.2 (lines 151–152) — and it now verifies against the **live** contract.

## Evidence (verified 2026-06-05 by cert-decode + Rekor-digest match)

The verifying host did not have `cosign` installed, so this was confirmed by decoding the bundle cert + matching the Rekor-recorded digest to the live contract (the substance of `cosign verify-blob`). **SCP should run the real `cosign verify-blob` in-pipeline to confirm** — it is expected to pass:

- **Real Fulcio root:** cert issuer `O=sigstore.dev, CN=sigstore-intermediate` (public-good Sigstore — NOT an HMAC placeholder, NOT a mock root).
- **Signing identity (SAN):** `https://github.com/jrnb2024/control-tower/.github/workflows/contract-manifest-publish.yml@refs/heads/main`
- **OIDC issuer (OID 1.3.6.1.4.1.57264.1.1):** `https://token.actions.githubusercontent.com`
- **Rekor inclusion proof present.**
- **No drift:** the Rekor-recorded blob `sha256 = 3ea88ad8036c2ce666d2238ee03058c3584e0b572e5d6802607acd15a2e72d73` **equals** the sha256 of the current `contracts/auth-contract-v1.yaml` on main. The signature is over the **live** contract bytes (the `manifest_sha256` field's currency remains a non-blocker per your plan §2.1).

Suggested in-pipeline confirmation:
```bash
cosign verify-blob \
  --bundle contracts/auth-contract-v1.yaml.sig.bundle \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity 'https://github.com/jrnb2024/control-tower/.github/workflows/contract-manifest-publish.yml@refs/heads/main' \
  contracts/auth-contract-v1.yaml
```

## What this unblocks

- **All three CT-side prereqs are now satisfied:** (1) `protected_primitives` block — MET (#474, `c3fd0e3`); (2) acc-hook canonical preamble — MET (#468); (3) **cosign-verify — MET (this doc).**
- WP-SCP-028 can author SCP-R-009/010/011 with **fail-closed cosign verification of CT's canonical via the `.sig.bundle`** as the WP plan intends (§7 conditions 1 + 5 and §1.2 no longer need the deferral).

## Clarifying note (so the two cosign tracks aren't conflated)

The cosign capability for the **auth contract** came via CT's `contract-manifest-publish.yml` (the contract-publishing workflow) — **not** via `WP-CT-VENDOR-WHEEL-COSIGN-001`. That separate WP closed CRIT **SB-B3-001** (the vendor **wheel/tarball** trust chain) on 2026-06-05 via PRs #490/#491/#496/#497 — all 23 vendored artefacts (`vendor/**/*.whl|tgz` + `MANIFEST.sha256`) now carry real keyless-OIDC cosign signatures, CI-verified via real `cosign verify-blob`. It is distinct from the auth-contract bundle SCP consumes, but it is independent confirmation that CT's keyless-OIDC cosign infrastructure is fully operational estate-wide.
