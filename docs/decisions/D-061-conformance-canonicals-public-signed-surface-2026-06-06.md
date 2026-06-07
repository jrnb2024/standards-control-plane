# D-061 — Conformance canonicals are published to a public, signed surface

**Date:** 2026-06-06 · **Status:** ACCEPTED · **Extends:** D-058 (canonical-conformance strategy) · **Reserves nothing; consumes nothing.**

> Numbered D-061 to avoid the reserved D-059 (WP-SCP-028 deny-promote outcome) and D-060 (WP-SCP-030 observation outcome). Renumber on merge if the reservations differ.

## Context

WP-SCP-028 Phase 2 (the companion that makes SCP-R-009/010/011 *fire*) halted at pre-flight on a real access gap: the materialisation must, at **unattended adopter CI time** (PIM, mapp-doc-agent, SCP-self — every cohort repo), fetch CT's signed canonical (`auth-contract-v1.yaml` + `.sig.bundle`, `canonical-sdk-versions.yaml` + sig) and verify it. But `control-tower` is **private** — `raw.githubusercontent.com/.../control-tower/...` 404s unauthenticated, and the SCP policy-check App is scoped to SCP only. There is no CT-read credential in adopter CI (and putting one there would be a per-adopter credential sprawl). D-058 said authorities "publish" their canonical but under-specified **where / accessible-how**.

## Decision

**A domain authority's conformance canonical MUST be published to a public, signed surface. SCP rules and adopters fetch it from that surface and cryptographically verify it — they never depend on read access to the authority's (private) source repo.**

- The published artefacts are **non-secret** (forbidden-symbol names, JWT claim shape, OIDC issuer patterns, SemVer floors) — they are *specs meant for estate-wide consumption*. The authority repo's privacy protects code, not the canonical.
- **The cryptographic signature — not repo privacy — is the trust anchor.** Artefacts are cosign-keyless-signed + Rekor-logged — **both** `auth-contract-v1.yaml` and `canonical-sdk-versions.yaml` (per Decision A, 2026-06-07: unified on one trust mechanism — no Ed25519/static key). The public surface is therefore **availability, not trust**: a tampered public copy fails verification → fail-closed. The consumer's `*_verified` flag is derived ONLY from its own verify run (the WP-SCP-028 trust boundary), never from the fetched/adopter content.

## Consequences

- **CT (authority):** ships `WP-CT-PUBLISH-CANONICAL-PUBLIC-SURFACE` — extend `contract-manifest-publish.yml` to push the signed artefacts to a public surface (recommended: a public `estate-canonicals` repo) in the same run that signs them.
- **SCP (consumer):** the WP-SCP-028 Phase-2 materialisation fetches the **public** surface (unauthenticated, works in any adopter's CI) + **cosign-verifies both canonicals** (same identity `…/contract-manifest-publish.yml@refs/heads/main`). **The CT publish WP has LANDED (#501 + #502); the surface is LIVE + verified (2026-06-07** — both canonicals 200 + cosign Verified OK via `verify-public-canonical-surface.sh`). Phase 2's gate is therefore satisfied.
- **Program-wide:** this is the standard substrate for *every* conformance domain, not a WP-SCP-028 one-off. Future authority canonicals follow the same publish-public-signed pattern.

## Alternatives rejected

- **Vendor a cosign-verified copy into each consumer** — bounded staleness window vs the authority's main + a per-consumer substrate + refresh mechanism. Acceptable at warn-baseline, but a snapshot-per-consumer, not one source of truth; rejected in favour of the read-through public surface.
- **Grant the consumer CI a read credential to the private authority repo** — puts an authority-read credential into every adopter's CI run; security sprawl; touches App config + secrets. Rejected.

## Cross-references

- D-058 (strategy) · WP-SCP-028 (first auth-domain rules) · `control-tower` WP-CT-PUBLISH-CANONICAL-PUBLIC-SURFACE (the authority-side publish) · the cosign trust anchor (WP-CT-VENDOR-WHEEL-COSIGN-001 + `contract-manifest-publish.yml`).
