# D-036 R1 — safety_bypass lens

**Reviewed:** D-036 v1 (commit `274d801`) + RULE-003 v1 (commit `274d801`).
**Lens scope:** Active attack surfaces — env-strip bypass, JWT replay, HMAC key compromise, signed-manifest tamper, lateral-movement under per-repo compromise, fail-open vs fail-closed defaults.

**Verdict:** CHANGES_REQUESTED.

---

## CRIT

### SB-CRIT-001 — Shared-secret lateral-movement: compromise of any per-repo MCP server breaks the entire estate

D-036 Element 4 + Element 5 together propagate a credential set to per-repo MCP server subprocesses that includes:
- `CT_AUTH_TOKEN` — the ACC-as-caller JWT (per Element 4)
- `SERVICE_AUTH_SECRET` — estate-shared HMAC secret (per Element 4)
- `ACC_COSIGNAL_TOKEN` — HMAC-signed cosignal token (per Element 5)
- `ACC_COSIGNAL_HMAC_KEY` — the SHARED 32-byte HMAC key file at `<target>/.acc/credentials/cosignal-hmac-key` (per Element 5)

The HMAC key being SHARED across all 9 estate repos creates a **lateral-movement vector**: compromise of ANY single repo (root access to read `<target>/.acc/credentials/cosignal-hmac-key`) grants the attacker the ability to mint valid `ACC_COSIGNAL_TOKEN` values for ANY other repo. Combined with the propagated `SERVICE_AUTH_SECRET` (also shared) + a token (which the attacker can re-mint if they obtain ACC's SA UUID, which is public per estate_repos.yaml), a single-repo compromise = full estate ACC-impersonation capability.

The recovery story ("rotate the key across all 9 repos") is sound but is **post-compromise damage limitation**, not prevention. Element 5's "operationally tractable for the 9-repo estate at bus-factor-1" rationale is true for operational simplicity but accepts a significant threat-model regression vs per-target-derived ephemeral tokens.

**Disposition:** Fix in v2 — surface this as a load-bearing residual in D-036 Element 5 explicitly. Either:
(a) downgrade the HMAC shared-key shape to per-target HKDF-derived subkeys from a master key (master stays kernel-protected on ACC side only; subkeys derived per-dispatch with HKDF + per-target context); OR
(b) keep the shared-key shape and add an EXPLICIT threat-model paragraph acknowledging single-repo-compromise = estate-wide ACC-impersonation, with operator authorisation for accepting the risk under D-031 single-operator-mode bus-factor-1 (analogous to D-050's "key custody is bus-factor-1" acceptance).

Option (b) is the bounded-reversal-friendly choice; (a) is the strictly-better security posture but requires per-language HKDF implementation in the ct-auth verifiers. **Recommend (b) for v1.4.0 ship + (a) as TF-D036-NEW for v1.5.0+.**

## MAJ

### SB-MAJ-001 — JWT replay defence is purely time-window, no `jti` cache

Element 2 specifies dynamic TTL with 6h ceiling; Element 5 specifies `jti` is recorded in the audit log. But the runtime verifier (target-repo's `ct-auth` library + acc-hook HMAC verification) is NOT specified to maintain a `jti` cache for replay defence. A captured valid token can be replayed within its TTL window (up to 6h) AND the cosignal HMAC for that token can be replayed within ±15min (per Element 5 timestamp window). Combined: up to 30min replay window per captured token; potentially up to 6h if HMAC ts can be replayed via clock manipulation.

**Disposition:** Fix in v2 — D-036 Element 2 (or new sibling Element 6) must specify the target-repo verifier maintains a `jti` cache for the duration of the token TTL with eviction on `exp`. Or: explicitly accept replay-within-window as residual + TF for `jti`-cache hardening.

### SB-MAJ-002 — CT manifest signing-key custody not documented in D-036

Element 3's signed manifest is signed with an Ed25519 key whose custody is described as "CT-side" without further specification. Single-operator-mode (D-031) means: if CT's signing key is on `@jrnb2024`'s machine alongside ACC's HMAC key + per-target credentials, the entire trust chain collapses to single-machine compromise. D-036 cannot trust the manifest if the manifest signing key's custody is not at least as protected as ACC's HMAC key custody.

**Disposition:** Fix in v2 — D-036 Element 3 must either:
(a) reference an existing CT key-custody SOP (verify one exists at `control-tower/docs/security/`);
(b) require CT to author one as a precondition of D-036 acceptance (file as `[BLOCKING]` open question);
(c) explicitly inherit D-031 bus-factor-1 custody for the CT signing key and acknowledge the single-machine-compromise risk symmetrically.

### SB-MAJ-003 — Inv-C should ramp to deny faster than other invariants

RULE-003 §3.2 ramps SCP-R-006 from warn → deny via per-adopter `threshold-overrides`, treating all four invariants uniformly. But Inv-C (MCP server SHA-pin against signed manifest) is a TAMPER-DETECTION invariant — a warn-baseline tamper detection is operationally meaningless because tamper is not a "rare false-positive ramp-up problem" but a "binary security event". The other three invariants (Inv-A, B, D) are reasonable warn-baseline → deny-ramp; Inv-C should be deny on first adopter who opts in.

**Disposition:** Fix in v2 — RULE-003 §3.2 differentiates Inv-C: when `acc-cross-repo-caller-scoped: true`, Inv-C fires at DENY immediately (not warn-baseline). Other invariants ramp per the existing pattern. Add to the rule's Rego: `deny contains output if { ... finding.invariant == "Inv-C" ... }` regardless of `threshold-overrides`.

### SB-MAJ-004 — D-036 Element 1 silently assumes ct-auth verifier extension

D-036 Element 1 says "only services whose `sub` claim ... matches an entry in `allowed_callers` are authorised." This is a NEW verification step. The existing `ct-auth` (Python + TS) libraries verify `iss`/`aud`/`exp`/`sub` per the JWT spec but do NOT consult an `allowed_callers` list. Without explicit extension to ct-auth (per-language), the `allowed_callers` declaration is purely ADVISORY at runtime — the target accepts ANY valid token whose `aud` matches the service. SCP-R-006 enforces the declaration is correct, but runtime enforcement of "this caller is in the allowed set" is not in place until ct-auth is extended.

**Disposition:** Fix in v2 — D-036 Element 1 adds explicit subsection "Implementation contract on ct-auth": per-language ct-auth (Python + TS + Go) MUST be extended to consult `allowed_callers` when verifying tokens, with verification failure when `sub` not in the list. Cross-reference: this is a hard-dep on CT WP-AUTH-007 (or sibling WP) shipping the verifier extension.

### SB-MAJ-005 — Element 4 env-propagation doesn't sanitise inherited env

Element 4 lists env vars that MUST propagate. But the allowlist mechanism in `CrossRepoDispatcher` (per CRIT-SB-002 fix in EST-P plan-doc) starts from ACC's own environment and strips down. If ACC's environment was contaminated by an upstream attacker (operator opened a tainted shell, env-file injection), `SSL_CERT_FILE`/`PYTHONPATH`/`LANG` propagation carries the contamination forward. The right discipline: ACC sanitises before copy (validates each env var's value against a known-shape regex before propagation).

**Disposition:** Fix in v2 — D-036 Element 4 adds note that ACC's allowlist mechanism additionally validates each env var's value against a known-shape regex (for `PATH`/`HOME`/`PYTHONPATH`: existing directories; for `SSL_CERT_FILE`: existing file in a CA bundle directory; for `LANG`: known-locale enum). Sanitise before copy.

## MIN

### SB-MIN-001 — Element 5 `ts` window asymmetric replay

Element 5 timestamp window is ±15min (30min total). Adversary with captured `ACC_COSIGNAL_TOKEN` has 30min to replay. ±15min tolerates NTP skew but is generous. ±2min would tighten to 4min replay window; combined with `jti` cache (SB-MAJ-001 fix) the replay window collapses to "until `jti` cache observes first use".

**Disposition:** Fix in v2 — tighten to ±2min OR document that ±15min is operator-decision and acceptable given the in-place `CT_AUTH_TOKEN` 6h TTL ceiling (which dominates the threat).

### SB-MIN-002 — `jti` UUID v4 entropy sufficient

Reviewed; no fix.

### SB-MIN-003 — RULE-003 §5 Residual known bypass enumeration accurate

Reviewed; no fix.

## nit

### SB-NIT-001 — Element 5 weekly rotation is the operator-default; event-triggered is additive

Reviewed; well-specified.
