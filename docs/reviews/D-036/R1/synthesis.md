# D-036 R1 synthesis + fix-round dispositions

**R1 conducted:** 2026-05-24
**Lens count:** 3 (correctness / safety_bypass / completeness_governance) — author-side inline review (single-process), NOT 3 parallel sub-agents. Disclosed transparently; mitigation = adversarial per-lens disciplined writing (each lens written in a separate disciplined pass with its own scope).
**Reviewed surface:** D-036 v1 (`docs/decisions/D-036-acc-cross-repo-caller-pair-2026-05-24.md`) + RULE-003 v1 (`docs/reviews/rule-proposals/RULE-003-acc-cross-repo-caller.md`); commit `274d801`.
**R1 evidence:** `correctness-lens.md`, `safety-bypass-lens.md`, `completeness-governance-lens.md` (this directory).

## Finding tally

| Lens | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|
| correctness | 0 | 3 | 3 | 2 |
| safety_bypass | 1 | 5 | 3 | 1 |
| completeness_governance | 0 | 3 | 4 | 3 |
| **Total** | **1** | **11** | **10** | **6** |

## CRIT — must close in fix-round

### SB-CRIT-001 — Shared-secret lateral-movement under single-repo compromise

**Closure for v2:** Option (b) selected — keep shared-key shape + add explicit threat-model paragraph acknowledging single-repo-compromise = estate-wide ACC-impersonation risk; operator-authorised under D-031 single-operator-mode bus-factor-1 (analogous to D-050's "key custody is bus-factor-1" acceptance). Per-target HKDF-derived subkeys captured as TF-D036-008 for v1.5.0+. Element 5 gets a new "Threat-model acknowledgement" subsection.

## MAJ — must close in fix-round (8 of 11)

### CORR-MAJ-001 — `iss` shape under-specified

**Closure for v2:** Mark D-036 Element 2 `iss` value as "subject to WP-AUTH-007 final shape; v2 specifies `https://control-tower.brokapps.ai` as the canonical hostname-form; WP-AUTH-007's eventual issuer URI is what ct-auth verifiers actually check." Add explicit cross-reference + TF if WP-AUTH-007 lands with different shape.

### CORR-MAJ-002 — Inv-C fails-OPEN on missing manifest entry

**Closure for v2:** Add explicit fail-CLOSED Rego rule in RULE-003 §3.4: missing-manifest-entry-with-on-disk-source fires Inv-C finding (severity warn baseline; deny when threshold-overrides set OR Inv-C unconditionally per SB-MAJ-003 below).

### CORR-MAJ-003 — Rego dict iteration shape

**Closure for v2:** Refactor RULE-003 §3.4 Rego snippet to use explicit dict iteration (`some service_name, service in input.services_yml.services`).

### SB-MAJ-001 — JWT replay defence: no `jti` cache

**Closure for v2:** D-036 Element 2 adds subsection: target-repo `ct-auth` verifier maintains an in-memory `jti` cache for the duration of each token's TTL; replay detection on `jti` re-presentation. Implementation contract on ct-auth (per SB-MAJ-004 closure). Cache eviction on `exp` reached.

### SB-MAJ-002 — CT manifest signing-key custody not documented

**Closure for v2:** D-036 Element 3 amended with explicit subsection: CT manifest signing key inherits D-031 single-operator-mode bus-factor-1 custody (symmetric with D-050 + Element 5 acknowledgement). File `control-tower/docs/security/manifest-signing-key-custody.md` as TF-D036-NEW (operator-authorisation gate to author).

### SB-MAJ-003 — Inv-C must ramp to deny faster than other invariants

**Closure for v2:** RULE-003 §3.2 differentiated: Inv-C fires at DENY whenever the rule fires (no warn-baseline for tamper detection). Other invariants ramp via `threshold-overrides` per existing pattern. Rego deny body adds `... finding.invariant == "Inv-C"` short-circuit.

### SB-MAJ-004 — Element 1 silently assumes ct-auth verifier extension

**Closure for v2:** D-036 Element 1 adds explicit "Implementation contract on ct-auth" subsection: per-language ct-auth (Python + TS + Go) MUST be extended to consume `allowed_callers` at token-verify time; verification failure when `sub` not in declared list. Cross-reference WP-AUTH-007 (or sibling) hard-dep.

### SB-MAJ-005 — Element 4 env-propagation needs sanitisation pre-copy

**Closure for v2:** D-036 Element 4 adds note: ACC's allowlist mechanism additionally validates each propagated env var's value against a known-shape regex before copy. Explicit regex shapes for `PATH`/`HOME`/`PYTHONPATH`/`SSL_CERT_FILE`/`LANG`.

### CG-MAJ-001 — Hard forward-coupling to ACC ADR-024

**Closure for v2:** Add TF-D036-009 tracking "ADR-024 (ACC side) landing with consistent shape"; D-036 amendment required if ADR-024 deviates materially.

### CG-MAJ-002 — RULE-003 §10 BLOCKING resolution non-standard

**Closure for v2:** Downgrade RULE-003 §10 question 1 from `[BLOCKING]` to `[deferrable]` — the default (vendored snapshot via Renovate) is sound + low-stakes + the long-term build-artefact path is captured as TF-RULE-003-002. Defensible downgrade.

### CG-MAJ-003 — D-036 Element 3 schema-version evolution discipline unsaid

**Closure for v2:** D-036 Element 3 adds short note on workflow consumer's version-allowlist mechanism (JWKS-style rollover; bumped via standard SCP federation-primitive PR; mirrors `policies/VERSIONING.md`).

## MIN — close best-effort in fix-round (5 of 10)

### CORR-MIN-001 — `CT_AUTH_TOKEN` env propagation contradicts in-band JWT

**Closure for v2:** Remove `CT_AUTH_TOKEN` from D-036 Element 4 env allowlist; add note that JWT is presented per-RPC-call as Authorization header on JSON-RPC, not via env.

### CORR-MIN-002 — Pipe-delimited HMAC payload future-ambiguity risk

**Closure for v2:** Switch D-036 Element 5 HMAC payload to canonical JSON (RFC 8785 JCS).

### CORR-MIN-003 — Rego set-union `|` syntax ambiguity

**Closure for v2:** Refactor RULE-003 §3.4 Rego to single `scp_r_006_all_findings` partial rule.

### SB-MIN-001 — Element 5 ts window asymmetric replay

**Closure for v2:** Document ±15min as operator-decision rationale (acceptable given 6h TTL ceiling dominates); tighten to ±2min in TF when `jti` cache lands.

### CG-MIN-003 — D-036 §"Open questions" default-mechanism non-standard

**Closure for v2:** Replace "Preferred operator default if no response" with "If unresolved at merge, the implicit acceptance is" — minor wording shift.

## MIN — deferred to v2 not closing (5 of 10)

- SB-MIN-002 — `jti` UUID v4 entropy: no-fix (sufficient).
- SB-MIN-003 — RULE-003 §5 Residual known bypass: no-fix (accurate).
- CG-MIN-001 — STATUS.md chain reference: optional cosmetic; defer.
- CG-MIN-002 — DECISIONS.md row consistency: handled at status-bookkeeping commit post-merge, not in D-036 file itself; no-fix in v2.
- CG-MIN-004 — PR opener reminder: process-discipline, not doc fix; carry forward to PR open.

## nit — no fixes

CORR-NIT-001/002, SB-NIT-001, CG-NIT-001/002/003 — all confirm-no-action.

## R1 → R-fixpoint disposition

- 1 CRIT to close (SB-CRIT-001)
- 8 MAJ to close (3 correctness + 4 safety_bypass + 3 completeness_governance; one safety_bypass MAJ counted under CG section above misalignment — net 11 total MAJ, 8 closing in v2)
- 5 MIN closing in v2 best-effort
- 3 MAJ deferred OR captured as TF:
  - (None deferred; all 11 MAJ have closure paths.)

**R1 fixpoint plan:** v2 closes 1 CRIT + 11 MAJ + 5 MIN = 17 findings. v3 R2 regression-only review (single pass) verifies CRIT + MAJ closure + no new findings from the v2 edits. If R2 surfaces new CRIT/MAJ, run R3 fix-round; if R2 surfaces only MIN, ship at R2-FIXPOINT-MET (zero CRIT + zero MAJ).

**Diminishing-returns exit clause:** if R2 surfaces ≥2 new CRIT/MAJ on the v2 edits AND those findings are in the same "shape class" as R1 (auth-surface invariants, Rego shape bugs, ct-auth verifier coupling), apply Option A R4 mechanical override at R3 with diminishing-returns signal — ship v3 with open TFs + PR-body disclosure rather than diverging into a multi-round fix sprint. The auth-surface 3-lens-default per `feedback_orchestrator_auth_surface_plan_review_default.md` is the floor; diminishing-returns is the ceiling.
