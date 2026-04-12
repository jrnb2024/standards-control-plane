# Strategy — WP-SCP-012 Product-Coherence Evaluator Shell

**Work Package:** `WP-SCP-012`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Strategy

Keep the product shell explicitly advisory:

- low- or medium-confidence only
- bounded to enhancement-spec and UI-language signals
- no attempt to infer roadmap or prioritisation intent

## 2. Why this slice now

After UX and design shells, the last core advisory domain is product coherence.
It is also the highest-risk domain for false confidence, so this first slice
must stay narrow and clearly non-authoritative.

## 3. Delivery shape

- registry scaffolding first
- one product-drift fixture using internal language
- one stable product fixture using user-facing language
- no scoring special cases yet beyond the shared score model
