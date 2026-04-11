# ARCH-001 — Service Boundaries Must Be Respected

**Domain:** architecture  
**Version:** 1.0.0  
**Status:** active  
**Severity default:** high

Code should stay within the declared service or module boundary unless an
explicit integration seam is defined and documented.

## Signals

- direct imports across bounded service layers
- hidden dependency on another service's private implementation
- repo-local shortcuts that bypass documented integration contracts
