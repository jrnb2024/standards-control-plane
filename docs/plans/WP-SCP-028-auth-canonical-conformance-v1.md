# WP-SCP-028 — Auth-canonical conformance Phase 1

**Version:** v1.0 (ACTIVE; ratified by D-058 2026-05-29)
**Plan-doc anchor:** `docs/decisions/D-058-scp-canonical-conformance-strategy-2026-05-29.md` §6
**Successor decision reservation:** D-059 — 4-week observation-window outcome (deny-promote / hold-at-warn / re-scope)
**Predecessor (architectural inheritance):** D-049 (LINKAGE not VALUES) + D-036/RULE-003 + SCP-R-006 (the prototype shape)
**Owner:** SCP (rule implementation) + CT (canonical authority — must publish prereqs)
**Operator-attended controls:** plan-stage 3-lens review at code-write time; D-040 single-operator-mode applies; D-031 bus-factor-1 acknowledged

---

## §1 Scope + invariants

### 1.1 Goal

Ship the first end-to-end realisation of D-058's canonical-conformance enforcement: **three warn-baseline Rego rules** that verify adopter conformance to CT's published auth canonical, propagated via the existing cohort-cascade required-check path, observed for 4 weeks, then deny-promoted on outcome ratification (D-059).

### 1.2 Hard invariants (load-bearing)

1. **LINKAGE not VALUES.** All three rules read CT's published manifest at evaluation time + check adopter linkage. No copy of the manifest content lives in SCP rule bodies. (Inherited from D-049 + D-058 §2.)
2. **CT is the sole auth canonical authority.** SCP does NOT author auth patterns; it gates conformance to CT's authorship.
3. **Warn-baseline first.** All three rules ship at `warn` per `policies/VERSIONING.md` deny/warn discipline; deny-promotion requires explicit D-059 ratification at the 4-week observation close.
4. **No MCP consult dependency.** WP-SCP-028 uses the merge-gate required-check path exclusively. The `scp.consult_rules` consult surface stays observation-mode (D-054 + 026F still open).
5. **Cohort cascade unchanged.** Rules propagate via the existing Renovate-cascade + required-check primitive; no new infrastructure.
6. **Reversibility.** Any rule can be flipped to `disabled` via `policies/rule-config.yaml` + propagated in next Renovate cycle (~24h max).

### 1.3 Anti-scope (what this WP explicitly does NOT do)

- **Does NOT modify CT.** The one hard CT prereq (adding the `protected_primitives` block + re-sign) is CT-side operator-attended work per the handoff prompt at `docs/coordination/2026-05-30-WP-SCP-028-CT-prereqs-handoff-prompt.md`, not WP-SCP-028 scope. SCP does not edit CT's canonical.
- **Does NOT install / require MCP consult invocation.** Adopters use the merge-gate path; consult is optional.
- **Does NOT change `.scp/rule-config.yaml` adopter schemas.** Adopter wrapper shape unchanged; rules consume their existing config surface.
- **Does NOT carry auth canonical content.** Rules read CT's signed manifest; SCP never duplicates issuer/audience/algorithm values.
- **Does NOT touch the federation primitive workflow.** `policy-check.yml` workflow shape unchanged; new rules slot into the existing rule library.
- **Does NOT cut a release.** v1.4.0 cut on rules merging is a separate operator-attended ceremony (mirrors v1.3.0 pattern; see `scripts/operator/cut-release.sh`).

---

## §2 Prereqs (gating)

WP-SCP-028 cannot fire until all of the following are true. Continuation prompt halts cleanly with operator-action message if any fail at pre-flight.

### 2.1 CT-side prereqs (operator-attended on CT)

| Prereq | Current state (2026-05-30) | Closure path |
|---|---|---|
| **CT publishes `contracts/auth-contract-v1.yaml` with a `protected_primitives` block** | **NOT PRESENT** (the only HARD prereq) — contract has `claim_shape_version: 1.1.0` + `issuers` + `key_rotation_policy` but no `protected_primitives` declaration; SCP-R-010 reads this block | CT adds the block + re-signs. Handoff prompt at `docs/coordination/2026-05-30-WP-SCP-028-CT-prereqs-handoff-prompt.md`. CT ratifies the deny/warn tiering + symbol set. |
| **CT's `auth-contract-v1.yaml.sig.bundle` verifies via cosign** | SHIPPED (Sigstore bundle present + verifying; this is the REAL verification anchor) | n/a — done. **SCP-R-009/011 verify CT's canonical via this `.sig.bundle`, NOT via the `manifest_sha256` field.** |
| **CT publishes `contracts/auth-contract-v1.yaml`** with current `claim_shape_version` | SHIPPED (claim_shape_version 1.1.0 live; bumps to 1.2.0 when the protected_primitives block lands) | n/a — done |
| **ct-auth-{python,ts,go} package versions declared in canonical-sdk-versions.yaml** | SHIPPED (ts 1.1.0 / py 1.0.0 / go 1.0.1 per CT canonical-sdk-versions.yaml 2026-05-30) | n/a — done |
| **`manifest_sha256` field current** | Drift OPEN (`386b4097…` recorded vs current contract hash) but **NOT a SCP blocker** — it is a caching/freshness hint, not the verification anchor (estate consumers verify via `.sig.bundle`). Clears as a side effect of the protected_primitives re-sign ceremony OR on CT's own FUP-CT-MANIFEST-CRON-REFRESH-001 roadmap. | No SCP-side action; no CT one-off needed. SCP does NOT gate on this field's currency. |

### 2.2 SCP-side prereqs (operator-attended on SCP)

| Prereq | Closure path |
|---|---|
| **D-058 ADR ratified (this PR)** | Operator merges this PR |
| **`docs/coordination/2026-05-29-estate-canonicals-cheap-shape.md` filed** | Filed in this PR; CT operator-attended landing of authoritative `ESTATE-CANONICALS.md` is separate work |
| **`policies/VERSIONING.md` updated to enumerate the new R-009/R-010/R-011 in WARN_BASELINE_RULES** | Done at rule-author time during WP-SCP-028 autonomous run |

### 2.3 Cohort prereqs

| Adopter | State 2026-05-29 | Action |
|---|---|---|
| PIM | LIVE | None — receives rules via cohort cascade after WP-SCP-028 merges + adopter wrapper pin advances |
| CT | LIVE | None — same |
| mapp-doc-agent | LIVE | None — same |
| Recommender | DEFERRED (`ErrManifestStale`) | Out of scope — separate CT-side workstream |
| shopify-app | QUEUED | Out of scope — WP-SCP-024 cohort cascade finalization, not this WP |

---

## §3 Rules to ship

### 3.1 SCP-R-009 — auth-canonical-version-pin

**Baseline:** warn (deny-promote candidate at D-059)
**Intent:** Adopter manifests must reference ct-auth-{language} package versions **greater-than-or-equal-to** the versions declared in CT's published `canonical-sdk-versions.yaml`. Deny on downgrade; warn on stale (>30d behind).

**Input surface (rule reads):**
- Adopter's `pyproject.toml` / `package.json` / `go.mod` (whichever languages they consume)
- CT's `canonical-sdk-versions.yaml` (materialised via SCP workflow input — same pattern as SCP-R-006's planned input materialisation)
- CT's `canonical-sdk-versions.yaml.sig.bundle` (Ed25519 signature verification)

**Deny conditions:**
1. Adopter pins a ct-auth-{py,ts,go} version strictly less than CT's published minimum
2. Adopter pins via SHA when CT canonical declares a tagged-version constraint (or vice versa where allowed)
3. Manifest signature verification fails (fail-closed)

**Warn conditions:**
1. Adopter pinned version is >30 days behind CT's published current

**Vacuous-pass when:**
- Adopter doesn't consume ct-auth (no matching import detected) — Inv-A short-circuits

**Schema additions:**
- `schemas/canonical-sdk-versions.schema.json` (NEW; validates CT's published manifest shape)

### 3.2 SCP-R-010 — auth-canonical-import-fence

**Baseline:** warn (deny-promote candidate at D-059)
**Intent:** Adopter source files that import the ct-auth SDK must NOT shadow or re-implement the canonical's protected primitives (`verify_token` / `sign_token` / `decode_jwt` / `validate_audience` / `extract_claims` and their language equivalents). Detection via canonical-declared forbidden-symbol set.

**Input surface (rule reads):**
- Adopter's source files matching `**/*.py` `**/*.ts` `**/*.tsx` `**/*.go` (changed-files set arithmetic)
- CT's `contracts/auth-contract-v1.yaml` for the forbidden-symbol declaration block (NEW key needed in CT's manifest: `protected_primitives: { python: […], typescript: […], go: […] }`)

**Deny conditions:**
1. Adopter defines a function/method named in the forbidden-symbol set within a file that also imports ct-auth (shadow risk)
2. Adopter re-exports a ct-auth primitive under a different name (rename risk; detected via re-export AST pattern)

**Warn conditions:**
1. Adopter imports a ct-auth primitive then defines a function in the same file with `_legacy` / `_internal` / `_v1` suffix (potential parallel implementation)

**Vacuous-pass when:**
- No file in the PR's changed-set imports from ct-auth/`@control-tower/auth`/ctauth-go

**Schema additions:**
- `schemas/auth-contract-v1.schema.json` (NEW; declares `protected_primitives` block shape)
- **CT-side prereq amendment:** CT's `contracts/auth-contract-v1.yaml` must add the `protected_primitives` block. This is a small additive change CT operator-attended ship; tracked as a sibling FUP from this WP.

### 3.3 SCP-R-011 — auth-contract-claim-shape

**Baseline:** warn (deny-promote candidate at D-059)
**Intent:** Adopter code that handles `Authorization` headers must declare it accepts the current `claim_shape_version`. Deny old issuers-of-1 schema patterns as drift.

**Input surface (rule reads):**
- Adopter source matching `**/*.py` `**/*.ts` `**/*.go` (changed-files arithmetic)
- CT's `contracts/auth-contract-v1.yaml` for current `claim_shape_version`

**Deny conditions:**
1. Adopter code parses `Authorization` header AND defines a `Claims` / `JwtPayload` / equivalent type with old-shape fields (e.g. `iss` as string array instead of single string per claim_shape_version 1.1.0; `aud` missing audience-list support)
2. Adopter code uses a hardcoded JWT issuer string that doesn't match CT's `canonical_issuer_pattern` (regex)

**Warn conditions:**
1. Adopter code declares `claim_shape_version` constant that lags CT's current by ≥1 MAJOR

**Vacuous-pass when:**
- No file in the PR changed-set touches Authorization handling (substring + AST detection)

**Schema additions:** none beyond §3.1 + §3.2

---

## §4 Workflow + input materialisation

Same pattern SCP-R-006 set up — workflow extension materialises CT's published artefacts as Rego inputs at evaluation time:

| Rego input key | Source | Mechanism |
|---|---|---|
| `input.canonical_sdk_versions` | `https://raw.githubusercontent.com/jrnb2024/control-tower/main/policies/canonical-sdk-versions.yaml` | fetched at policy-check-time; the FILE CONTENT (canonical versions) is the LINKAGE source. The `manifest_sha256` field within is NOT used as the verification anchor (it's a freshness hint that may drift). |
| `input.auth_contract` | `https://raw.githubusercontent.com/jrnb2024/control-tower/main/contracts/auth-contract-v1.yaml` | fetched + **verified via the sibling `.sig.bundle` (Sigstore/cosign) — the REAL verification anchor**. The contract carries `protected_primitives` (for SCP-R-010) + `claim_shape_version` + `canonical_issuer_pattern` (for SCP-R-011). |
| `input.auth_contract_sig_bundle` | Sibling `auth-contract-v1.yaml.sig.bundle` | fetched same way; cosign-verified (keyless Sigstore OIDC; X.509 cert chain self-verifying via Rekor transparency log). This is what proves the contract is authentic, NOT the `manifest_sha256` field. |
| `input.adopter_changed_files` | already materialised (existing workflow surface) | unchanged |
| `input.adopter_manifests` | adopter's checked-out `pyproject.toml` / `package.json` / `go.mod` | existing workflow surface; rule reads from checked-out tree |

Until the workflow extension lands (sibling Codex Tier 2 PR, operator-attended first-fire per four-tier dispatch — same pattern as SCP-R-006), the rules load but vacuously pass (all guard checks fail closed; rule emits zero findings). This is the **safe failure mode** inherited from SCP-R-006 and is explicitly OK — adopters see no behavioural change until both the rules + the workflow input materialisation are landed.

---

## §5 Cohort cascade

After rules merge into SCP main + a new release tag is cut (operator-attended; mirrors v1.3.0 ceremony):

1. **PIM** wrapper pin advances to v1.4.0 SHA via `scripts/operator/scp-wrapper-bump-sweep.sh` next monthly cycle (or sooner if operator runs it manually). Wrapper picks up SCP-R-009/010/011 automatically at next PR.
2. **CT** same.
3. **mapp-doc-agent** same.

**Recommender** + **shopify-app** are out of scope per §2.3.

**4-week observation window** opens at the date all 3 LIVE adopters have advanced their wrapper pin past v1.4.0. Observation criteria:

- Rule firing rate (allow + warn + deny per adopter per week)
- False-positive count (PRs flagged that the operator subsequently labels `false_positive`)
- Adopter-friction tickets (any operator-attended override events)
- Real-deny events (PRs the rules genuinely block; ideally >0 to prove value)

**Close criteria (D-059 decides):**
- **DENY-PROMOTE** if: ≥3 real-deny events across the cohort during the window + zero or one false positives + no adopter-friction tickets requiring rule disable
- **HOLD-AT-WARN** if: 0 real-deny events but 0 false positives — the rules are well-shaped but not yet exercised; extend observation 4 more weeks
- **RE-SCOPE** if: ≥3 false-positive events OR ≥1 adopter-friction-ticket requiring rule disable — the rule shape itself needs revision before deny-promotion

---

## §6 Implementation phases (for the autonomous run)

### Phase 0 — Pre-flight (deterministic) [10 min]

- Verify D-058 merged + this plan-doc landed
- Verify CT `protected_primitives` block present in `contracts/auth-contract-v1.yaml` (HALT with operator-action note if not — this is the ONE hard CT prereq; handoff prompt at `docs/coordination/2026-05-30-WP-SCP-028-CT-prereqs-handoff-prompt.md`)
- Verify CT's `auth-contract-v1.yaml.sig.bundle` verifies via cosign (HALT if signature invalid — fail-closed; this is the verification anchor, NOT `manifest_sha256`)
- Do NOT gate on `manifest_sha256` currency — it is a freshness hint, not the anchor; a drifted value does not block WP-SCP-028
- Verify acc-hook is live (D-057 cardinal pre-flight)
- Verify session-start `.acc/active-dispatch.json` exists with scope covering the WP-SCP-028 file set (D-057 ceremony)

### Phase 1 — Schema authoring [1-2h]

- Author `schemas/canonical-sdk-versions.schema.json`
- Author `schemas/auth-contract-v1.schema.json`
- Extend `schemas/rule-config.schema.json` with new `auth-canonical-version-pin-disabled` / `auth-canonical-import-fence-disabled` / `auth-contract-claim-shape-disabled` opt-out keys
- 3-lens R1 review on schemas

### Phase 2 — Rule authoring [3-4h]

- Author `policies/SCP-R-009.rego` (auth-canonical-version-pin)
- Author `policies/SCP-R-010.rego` (auth-canonical-import-fence)
- Author `policies/SCP-R-011.rego` (auth-contract-claim-shape)
- Extend `policies/scp_common.rego` with auth-canonical helper functions if needed
- 3-lens R1 review on each rule (correctness / safety_bypass / completeness_governance — mandatory per `feedback_orchestrator_auth_surface_plan_review_default.md`)

### Phase 3 — Tests + fixtures [2-3h]

- Test fixtures for SCP-R-009 (downgrade / stale / exact-match / vacuous-pass)
- Test fixtures for SCP-R-010 (shadow / re-export / vacuous-pass / legitimate-extension)
- Test fixtures for SCP-R-011 (old-claim-shape / current-claim-shape / hardcoded-issuer / vacuous-pass)
- Coverage: each rule ≥90% per existing SCP discipline
- regal lint + opa fmt clean

### Phase 4 — Bookkeeping [1h]

- `policies/VERSIONING.md` extend `WARN_BASELINE_RULES` to `{"SCP-R-004", "SCP-R-008", "SCP-R-009", "SCP-R-010", "SCP-R-011"}`
- `version-manifest.json` bump from v1.3.0 → v1.4.0 (MINOR per VERSIONING.md additive-rule guarantee)
- `docs/DECISIONS.md` row + Last Updated bump (this plan-doc + D-058 already filed)
- `docs/BACKLOG.md` flip WP-SCP-028 from OPEN → SHIPPED
- `STATUS.md` chain row (triggers check-invocation-log-entry)

### Phase 5 — Operator handoff [10 min]

- Halt with operator-action message:
  - "v1.4.0 ready to cut via `scripts/operator/cut-release.sh --version v1.4.0 --sha <merge-sha>`"
  - "After tag pushed: `scripts/operator/scp-wrapper-bump-sweep.sh --emit-commands` to propagate to PIM/CT/mapp-doc-agent"
  - "After all 3 bumps merged: 4-week observation window opens; D-059 decision date estimated <close-date>"

---

## §7 Halting conditions (autonomous-run discipline)

The autonomous-run continuation prompt halts cleanly with operator-action message on any of:

1. **Phase 0.2 prereq miss** — `contracts/auth-contract-v1.yaml protected_primitives` block missing (the ONE hard CT prereq), OR `auth-contract-v1.yaml.sig.bundle` doesn't cosign-verify. (NOT manifest_sha256 currency — that is not a blocker.)
2. **3-lens review hits REJECT** on any of the 3 rules (auth-surface = mandatory safety lens; REJECT is hard stop)
3. **Cure-worse R2 trigger** per the per-WP scope (a fix-round introducing a worse-than-original failure mode)
4. **Context-budget split** (>8h elapsed; split-point after Phase 2 or Phase 3 per the established autonomous-run discipline)
5. **Fail-closed signature verification** — CT's `auth-contract-v1.yaml.sig.bundle` (or canonical-sdk-versions sig) doesn't cosign-verify; rules can't ship in good faith

---

## §8 Success criteria

- 3 new Rego rules at `policies/SCP-R-009..R-011.rego`, each with ≥90% coverage, regal lint + opa fmt clean
- 2 new JSON schemas (`canonical-sdk-versions.schema.json` + `auth-contract-v1.schema.json`)
- 1 extended schema (`rule-config.schema.json` with 3 new opt-out keys)
- `VERSIONING.md` `WARN_BASELINE_RULES` extended
- `version-manifest.json` bumped to v1.4.0
- `BACKLOG.md` WP-SCP-028 row flipped SHIPPED
- `DECISIONS.md` row + Last Updated bumped
- `STATUS.md` chain row landed (triggers check-invocation-log-entry)
- 3-lens R1 review evidence at `docs/reviews/WP-SCP-028/per-rule-r1-dispositions.md`
- CI green on all required checks
- Operator handoff message at the close
- Halt-cleanly behaviour on the named conditions

---

## §9 D-059 reservation

D-059 is RESERVED for the 4-week observation-window outcome ratification (deny-promote / hold-at-warn / re-scope). Codex executors dispatched for any WP-SCP-028 implementation slice MUST NOT assign D-059 to any decision filed during that slice. The reservation pattern mirrors D-021 / D-041-043 / D-044-046 / D-047-048 / D-055-056.

---

**Identified at:** D-058 §6 (this PR).

**Filed:** 2026-05-29 (this PR).

**Closes when:** Phase 0-5 complete + 4-week observation window opens + D-059 ratifies outcome.
