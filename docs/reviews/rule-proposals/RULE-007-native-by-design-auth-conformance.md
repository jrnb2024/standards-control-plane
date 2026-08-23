# RULE-007 — Native-by-design auth as a first-class conformance state (retire the per-repo C1a waiver)

**Status:** DRAFT
**Author:** filed from the mapp-pim auth-foundation close-out (FUP-SCP-NATIVE-BY-DESIGN)
**Filed:** 2026-06-19
**Target release:** v1.7.0 (federation primitive) — sequenced with/after D-059.
**Type:** rule-add (extends SCP-R-009 with a positive-attestation PASS path + a recognised scorecard state)
**Quorum required:** 1 (single-operator mode per D-031)
**Review window:** 48h wall-clock from PR open — **non-waivable** (§5 is non-empty).
**Bypass-surface non-empty:** `true` *(adds a new `.scp/rule-config.yaml` key `auth-native-by-design`)*

---

## 1. Summary

An estate repo can be auth-conformant either by **pinning** the published `ct-auth-{py,ts,go}` SDK (gated today by SCP-R-009) or by a **native-by-design** implementation that links no published SDK because the SDK lacks a required symbol (decision B1; PIM Go auth, `MapClaimsToIdentity`). Today the native path is represented as a **per-repo waiver** (PIM's C1a waiver), which reads as "a finding we ignore" rather than "a conformant state." This proposal makes native-by-design a **first-class PASS**: the adopter makes a positive attestation in `.scp/rule-config.yaml` plus a machine-checked binding to the canonical's current `claim_shape_version`, SCP-R-009 emits a `native-by-design-conformant` observability record, the scorecard shows a PASS row, and the per-repo waiver is retired. LINKAGE-not-VALUES is preserved: SCP gates the *declaration + evidence presence*, never the native code's behaviour.

## 2. Motivation

- **Concrete finding:** `mapp-pim/docs/governance/decisions/2026-06-06-C1a-go-fork-native-by-design-waiver.md`. ESTATE-CONVERGENCE C1a ("pin ct-auth-go 1.0.1") is satisfied only via a waiver because PIM's Go auth is native (the published `ct-auth-go` lacks `MapClaimsToIdentity`). The waiver text itself asks SCP to "make native-by-design first-class in the Phase-2 materialisation (an explicit PASS for SCP-R-009/010/011, not a per-repo waiver)." This proposal is that materialisation.
- **Governance concern:** at **D-059** (SCP-R-009 deny-promote), the conformance model should represent native-by-design positively. Today SCP-R-009 **vacuously passes** native repos (it iterates `input.adopter_ct_auth_deps`; a native repo pins none → empty → no finding) and SCP-R-010 vacuously passes (no `imports_ct_auth`). So native-by-design is indistinguishable from "never evaluated." A waiver is the wrong primitive for a state that is genuinely conformant. The B2 alternative (hollow-pin the unused SDK to satisfy the letter of R-009) was explicitly rejected by C1a as a values-coupling false signal — so a positive native-by-design PASS is the only honest representation.
- **Prior context:** D-058 (canonical-conformance strategy), D-059 reserved for the SCP-R-009/010/011 deny-promote outcome, and the D-058 §7 roadmap slot **WP-SCP-032 (ct-auth py/ts/go parity)**. This proposal is the auth-domain piece of that parity.

## 3. Rule specification

### 3.1 Match conditions

Extends SCP-R-009. For a language family `<lang>` the adopter is **native-by-design-conformant** (a positive PASS record) when ALL hold:
1. `input.rule_config.auth-native-by-design.<lang>.attested == true`, AND
2. the adopter pins **no** `ct-auth-<lang>` dep (`input.adopter_ct_auth_deps` has no entry for that package family — the same dep list SCP-R-009 already materialises), AND
3. the declared `input.rule_config.auth-native-by-design.<lang>.contract_conformance_evidence` path is present in `input.adopter_source_files` (the workflow already enumerates adopter files), AND
4. *(optional, when the canonical manifest is verified)* the evidence file's pinned `claim_shape_version` is **not behind** CT's signed `auth-contract-v1.yaml::claim_shape_version` read at eval time (LINKAGE-not-VALUES: SCP reads the canonical version, never copies it).

When (1)+(2)+(3) hold but a `ct-auth-<lang>` dep IS also present → that is a contradiction (declared native yet pins the SDK) → a `warn` finding ("native-by-design declared but SDK pinned; choose one").

### 3.2 Severity & threshold

- The positive `native-by-design-conformant` record is an **observability record** (no severity; renders as a scorecard PASS row), mirroring the existing suppression-observability `warn` records in SCP-R-009.
- The contradiction case (declared native + SDK pinned) lands at **`warn` baseline** per `policies/VERSIONING.md`.
- The stale-evidence case (3.1 condition 4 fails) lands at **`warn`** (correctness drift — the adopter's pin is behind CT's current contract), parallel to SCP-R-009's existing stale-pin warn.
- Adopter override unchanged: `.scp/rule-config.yaml disable: true` + `justification` + `expires_at` still suppress per `schemas/rule-config.schema.json`.

### 3.3 Annotation contract

- Infrastructure code: reuse `SCP-E006` (disabled/observability record) for the positive `native-by-design-conformant` record; `SCP-E003`-class for the contradiction/stale `warn` (rendered `::warning::` at warn-baseline). No new `SCP-EXXX` code (that would be a separate workflow change).
- Rule-specific annotation: `SCP-R-009` durable identifier (this is an R-009 extension, not a new rule ID — keeps the auth-version-pin contract under one rule). Message e.g. `SCP-R-009: <repo> Go auth is native-by-design-conformant (attested; evidence=<path>; claim_shape_version=<v> in sync with CT <v>).`
- `scp/policy-check-readback` line stays within the ~80-char budget.

### 3.4 Implementation sketch

Reuses SCP-R-009's existing `scp_r_009_*` helpers (`scp_r_009_adopter_deps`, `scp_r_009_manifest`, `scp_r_009_semver/lt`) + estate suppression helpers. PoC:

```rego
# positive PASS: native-by-design attested, no SDK dep, evidence present
scp_r_009_native_conformant contains rec if {
    nbd := object.get(object.get(input, "rule_config", {}), "auth-native-by-design", {})
    some lang, decl in nbd
    object.get(decl, "attested", false) == true
    not scp_r_009_has_dep_for_lang(lang)            # no ct-auth-<lang> pin
    ev := object.get(decl, "contract_conformance_evidence", "")
    scp_r_009_evidence_present(ev)                   # ev in adopter_source_files
    rec := {"kind": "native-by-design-conformant", "rule_id": scp_r_009_rule_id,
            "lang": lang, "evidence": ev,
            "msg": sprintf("SCP-R-009: %s auth is native-by-design-conformant (evidence=%s)", [lang, ev])}
}
# surfaced as a `warn`-channel observability record (no deny), like the existing
# waiver/disable suppression records; the scorecard projects it as a PASS row.
```

The stale-evidence check reuses `scp_r_009_lt(evidence_claim_shape_version, manifest_claim_shape_version)` against the verified manifest.

## 4. False-positive surface

- **Repo declares native-by-design but its native impl is actually wrong.** SCP cannot and must not detect this (VALUES). Mitigation: the attestation REQUIRES a `contract_conformance_evidence` file, and the adopter's own CI must keep that evidence green (PIM's `scripts/check_auth_contract_sync.py` fails CI if CT's `claim_shape_version` advances past the pin). SCP gates the *presence + declaration + version-freshness*, exactly as it gates a version pin for SDK consumers. Estimated FP: ~0 per 100 PRs (the record is informational; a wrong native impl is the adopter's + the contract-test's responsibility, identical to a wrong SDK being CT's).
- **Evidence path renamed without updating the attestation.** Condition (3) then fails → no positive record (reverts to today's vacuous pass), not a false deny. Recommended response: update `.scp/rule-config.yaml`.

## 5. Bypass surface

**Non-empty.** New `.scp/rule-config.yaml` key: `auth-native-by-design.<lang>.{attested, contract_conformance_evidence, waiver_ref}`.

- This is a **positive attestation**, semantically distinct from the existing `auth-canonical-version-pin-disabled` opt-out: opt-out = "do not gate me" (suppression); native-by-design = "gate me on the native contract, here is my evidence" (conformance). It does NOT suppress any deny — it only produces a positive record + (in the deny-promoted future) lets R-009's "no dep" case be a recognised PASS rather than relying on a waiver.
- **Implicit exclusion set:** the positive record is emitted ONLY when `attested == true` AND no SDK dep AND evidence present. Absence of the key = today's behaviour unchanged (vacuous pass). It cannot be used to bypass a downgrade finding: a repo that pins an SDK below the secure floor still trips SCP-R-009's downgrade deny regardless of any `auth-native-by-design` key (condition (2) "no dep" is false there).
- **Residual known bypass:** SCP gates the *declaration + evidence-file presence + version-freshness*, not the native code's semantic correctness. The gap (a repo could attest native-by-design, carry a green-but-meaningless evidence file, and ship a broken native impl) is the same residual SCP accepts for SDK consumers (it gates the pin, not CT's SDK correctness). Closure path: the adopter's contract-conformance test is the semantic gate; SCP gating it exists + is fresh is the LINKAGE assertion. Honest-actor posture per D-049/D-058.

Because §5 is non-empty, the 48h window is **non-waivable**; the PR description will carry the bypass-surface enumeration paragraph.

## 6. Conflict-gate strategy

- Match conditions (object lookups in `input.rule_config` + membership in the existing `adopter_ct_auth_deps` / `adopter_source_files`) are expressible in the Python evaluator (no AST, no new extraction — all inputs already materialised by the WP-SCP-028 Phase-2 companion).
- Fixtures: `tests/conflict_gate/scp-r-009/{allow,deny}/` gains a native-by-design-attested `allow` case + a declared-native-but-SDK-pinned `deny`/`warn` case, through the existing `adapter.py` contract.
- Confirm no self-dogfood flap (SCP-self pins no ct-auth and declares nothing → unaffected).

## 7. Estate-cascade considerations

- **PIM** opts in immediately (Go; the motivating case) — its `.scp/rule-config.yaml` gains `auth-native-by-design.go` pointing at `api/contracts/auth-canonical-pin.json`, and its C1a waiver is retired.
- **Recommender** (vendored ctauth) is the likely second adopter once it retires its vendored copy natively (WP-CT-E-501 territory).
- **Forward-looking decision:** this should be filed in coordination with **D-059** (SCP-R-009 deny-promote) — native-by-design first-class is the precondition that lets R-009 deny-promote without forcing native repos onto the rejected B2 hollow-pin. Roadmap home: **WP-SCP-032**.

## 8. Test plan

- `policies/tests/scp_r_009_test.rego` gains: native-attested-no-dep-evidence-present → positive record; native-attested-but-SDK-pinned → warn; native-attested-evidence-missing → no record (vacuous); native-attested-evidence-stale-vs-manifest → warn.
- Conflict-gate raw + suppression paths under `tests/conflict_gate/scp-r-009/` (incl. `rule-config-disabled` sibling).
- Workflow-selftest: extend a `fixture-scp-r-028-*` harness with a native-by-design adopter fixture.

## 9. Migration / rollout

- New positive PASS path + warn cases on SCP-R-009 → **MINOR** bump (target **v1.7.0**) per `policies/VERSIONING.md`.
- Sequenced with/after **D-059**. Until merged, PIM's C1a waiver stays in force; on merge, PIM adds the `auth-native-by-design.go` attestation and the waiver is allowed to expire.
- Adopter migration: add the `.scp/rule-config.yaml` block + ensure the evidence file (a contract pin) exists and is kept fresh in adopter CI. PIM already ships both (`api/contracts/auth-canonical-pin.json` + `scripts/check_auth_contract_sync.py` in lint CI).

## 10. Open questions

- **[BLOCKING]** Should the positive record live as an SCP-R-009 observability record (this proposal) or a new rule ID SCP-R-013? Recommendation: extend R-009 — native-by-design is an alternative satisfaction of the *same* version-pin contract, and one rule keeps the auth-version conformance under one durable ID. A reviewer preferring a distinct ID changes §3.3 only.
- **[BLOCKING]** Does `contract_conformance_evidence` need to be a structured, SCP-validated shape, or is "file exists + (optional) pins a non-stale claim_shape_version" sufficient? Recommendation: the latter (LINKAGE-faithful; the evidence's *content* is the adopter's contract-test responsibility, not SCP's).
- **[deferrable]** Whether to require the `waiver_ref` provenance field permanently or drop it once the originating waiver expires.
- **[deferrable]** ts/py native-by-design (unlikely — those SDKs are complete) vs Go-only scoping for v1.7.0.

## 11. References

- mapp-pim C1a waiver: `mapp-pim/docs/governance/decisions/2026-06-06-C1a-go-fork-native-by-design-waiver.md`.
- mapp-pim auth close-out verification (HIGH-A false-positive; native mapper live; `make test-contract` green): `mapp-pim/docs/governance/reviews/2026-06-19-auth-foundation-closeout-verification.md`.
- mapp-pim drift guard (the evidence an adopter surfaces): `mapp-pim/scripts/check_auth_contract_sync.py` + `mapp-pim/api/contracts/auth-canonical-pin.json`.
- Rules: `policies/SCP-R-009.rego` (version-pin, extended here), `SCP-R-010.rego` (import-fence), `SCP-R-011.rego` (claim-shape).
- Decisions: D-058 (canonical-conformance strategy), D-059 (reserved — deny-promote), D-058 §7 roadmap WP-SCP-032 (py/ts/go parity), WP-SCP-031 (vendored-SDK pinning).
