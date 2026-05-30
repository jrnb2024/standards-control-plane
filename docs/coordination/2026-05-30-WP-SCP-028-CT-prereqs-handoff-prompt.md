# CT handoff prompt — auth-canonical prereqs for SCP WP-SCP-028

**From:** Standards Control Plane (SCP), per D-058 + WP-SCP-028
**To:** Control Tower (CT) team / a CT Claude Code session
**Filed:** 2026-05-30
**Nature:** Self-contained work brief. Drop the **"PROMPT"** section below into a fresh Claude Code session rooted at `~/Projects/control-tower`, OR hand it to the CT operator. The surrounding context is for the requester's record (SCP).

---

## Why SCP is asking (context — not part of the droppable prompt)

D-058 (2026-05-29, SCP) ratified canonical-architecture conformance enforcement as SCP's strategic direction, **auth first**. WP-SCP-028 will ship 3 warn-baseline Rego rules that gate adopter conformance to CT's published auth canonical — CT remains the sole auth authority; SCP only gates LINKAGE (does adopter code reference CT's canonical correctly?), never VALUES.

Two of those rules need a CT-side artefact that doesn't exist yet:

- **SCP-R-010 (auth-canonical-import-fence)** reads a `protected_primitives` declaration from `contracts/auth-contract-v1.yaml` — the set of ct-auth SDK symbols adopters must not shadow / re-implement. **This block does not exist today.** Without it, SCP-R-010 cannot be authored.
- **SCP-R-009 (auth-canonical-version-pin)** + **SCP-R-011 (auth-contract-claim-shape)** read CT's already-published `canonical-sdk-versions.yaml` + `auth-contract-v1.yaml`. These exist. **SCP verifies them via the `.sig.bundle` (Sigstore/cosign) — the real verification anchor — NOT the `manifest_sha256` field.** So SCP does NOT need CT to do any one-off `manifest_sha256` fix.

## In-flight safety (verified 2026-05-30 — for the requester's record)

A full survey of CT's in-flight state found **no collision risk**:
- 3 open CT PRs (#455 dispatch-isolation / #437 PIM C.2 / #406 audit) — none touch `contracts/auth-contract-v1.yaml` or `policies/canonical-sdk-versions.yaml`.
- The §C.1 prep branch (`chore/ws-auth-cascade-c1-prep`) *narrows* the cron-refresh trigger; it does not add schema surface.
- The 4 staged §C.1 Codex WPs (audience-dynamic + ct-auth-{py,ts} 1.0.1) are SDK + behaviour changes, not schema changes. `protected_primitives` is a schema-additive change, orthogonal to all of them.
- **Elegant consequence:** adding `protected_primitives` forces a contract re-sign + manifest refresh, which **clears the existing `manifest_sha256` drift (`386b4097…` → current) as a natural side effect** of the same ceremony. CT does NOT need a separate one-off manifest fix; the drift-clear that was on CT's FUP-CT-MANIFEST-CRON-REFRESH-001 roadmap happens here instead (or remains on that roadmap — either is fine, SCP verifies via `.sig.bundle`).

**Do NOT** treat this as urgent or let it pre-empt the §C.1 cascade. It is additive and can land whenever CT has a maintenance window. SCP's WP-SCP-028 is gated on it but not time-pressured.

---

## ═══════════════ PROMPT (drop into a CT Claude Code session) ═══════════════

You are working in the Control Tower (CT) repo at `~/Projects/control-tower`. The Standards Control Plane (SCP) project needs CT to publish two auth-canonical artefacts so SCP's WP-SCP-028 conformance rules can gate the estate against CT's auth canonical. **CT is the auth authority** — you ratify what the canonical IS; SCP only gates conformance to it. This work is **additive, not urgent**, and must not disrupt the in-flight §C.1 auth cascade.

### Deliverable 1 — `protected_primitives` block in `contracts/auth-contract-v1.yaml`

Add a top-level `protected_primitives:` block (peer to `key_rotation_policy:`) declaring the ct-auth SDK symbols that adopters MUST NOT shadow or re-implement in their own code. This is the canonical "thou shalt not re-implement the auth verification path" surface.

**Proposed block (SCP's draft — YOU ratify the actual symbol set + tiering; this is a starting point derived from the current SDK exports, not a decision SCP gets to make):**

```yaml
protected_primitives:
  # Symbols adopters MUST NOT shadow or re-implement. SCP-R-010 gates this.
  # Tier "deny": re-implementing these is a security hole (token verification /
  #   signing / JWKS path). A shadow here means an adopter is doing its own auth
  #   verification instead of CT's — exactly the divergence the canonical exists to prevent.
  # Tier "warn": re-implementing these is a correctness/drift risk, not a direct
  #   security hole (permission-query helpers). Adopters occasionally have
  #   legitimate reasons to wrap these; warn + review rather than hard-deny.
  tier_deny:
    python:        [validate_token, decode_token_unverified, JWKSClient, StatefulJWKSClient]
    typescript:    [validateToken, decodeTokenUnsafe, verify, JWKSClient]
    go:            [WithCTJWT, WithServiceJWT, BuildMiddleware, NewHTTPJWKSCache, ClaimsFromContext]
  tier_warn:
    python:        [has_permission, has_app_permission, has_role, is_platform_admin, get_permissions, clear_permissions_cache]
    typescript:    [hasPermission, hasAppPermission, hasRole, isPlatformAdmin, getPermissions, clearPermissionsCache]
    go:            [VerifiedClaims]
```

**Your ratification decisions (CT's call, not SCP's):**
1. Is the deny/warn tiering right? The principle SCP proposes: **deny** = the token-verification + JWKS + middleware path (re-implementing it is a security hole); **warn** = permission-query helpers (wrapping them is sometimes legitimate). Adjust per CT's actual threat model.
2. Are the symbol names accurate + complete against the *current* SDK exports? Verify against `packages/ct-auth-{python,ts,go}/` — SCP derived these from the exports as of 2026-05-30 but the SDKs evolve (e.g. §C.1 ct-auth-{py,ts} 1.0.1 may add/rename symbols; reconcile if those land first).
3. Should the block carry a `since_version:` per symbol (so SCP-R-010 only fences a symbol once the SDK that exports it is the adopter's declared minimum)? Recommended but optional.

### Deliverable 2 — re-sign + manifest refresh (clears the existing drift)

Adding Deliverable 1 changes `auth-contract-v1.yaml`, which:
- Requires a `claim_shape_version` bump: **1.1.0 → 1.2.0** (schema-additive ⇒ MINOR per your SemVer discipline). Confirm this is the right bump per CT's manifest-version policy.
- Requires re-running the signing ceremony: `scripts/contracts/build-signed-manifest.sh` (regenerates `.hmac` + `.sig` + `.sig.bundle`) + updating `policies/canonical-sdk-versions.yaml::auth_contract.manifest_sha256` to the new content hash.
- **This clears the pre-existing `manifest_sha256` drift as a side effect** — the refresh recomputes against the new contract content. No separate one-off fix needed; this folds the FUP-CT-MANIFEST-CRON-REFRESH-001 drift-clear step (ii) into this ceremony (or coordinate with that WP if it's mid-flight — check `docs/BACKLOG.md` for WP-CT-VENDOR-WHEEL-COSIGN-001 status, since Axis 2 OIDC bot-signing was folded there).

**Signing-path note:** if WP-CT-VENDOR-WHEEL-COSIGN-001 (OIDC bot signing) hasn't landed yet, this is an **operator-attended** signing (manual `workflow_dispatch` of `contract-manifest-publish.yml`, or local signing per the existing ceremony). Do not bypass `required_signatures` with a branch-pattern exemption — that was explicitly rejected per the §C-kickoff Axis-2 decision.

### Deliverable 3 — publish `docs/ESTATE-CANONICALS.md` (Phase A of D-058)

Author the estate-canonicals index per the SCP-side coordination memo (read it first: `~/Projects/standards-control-plane/docs/coordination/2026-05-29-estate-canonicals-cheap-shape.md` §1). This is a CT-owned text index: each cross-cutting domain → owning authority → canonical doc path → current version. Initial publication scope is ONLY the domains with published artefacts today (auth, SDK-pinning, governance-docs); everything else ships as `(TBD — authority unassigned)` placeholders. No Rego, no automation — just the markdown index + a one-paragraph note per domain.

### Pre-flight (do this first)

1. `git -C ~/Projects/control-tower fetch origin && git -C ~/Projects/control-tower status` — confirm clean tree on main.
2. Read `contracts/auth-contract-v1.yaml` (current shape; 40 lines; `claim_shape_version: 1.1.0`).
3. Read `policies/canonical-sdk-versions.yaml` (current `auth_contract.manifest_sha256`).
4. Check `docs/BACKLOG.md` for WP-CT-VENDOR-WHEEL-COSIGN-001 + FUP-CT-MANIFEST-CRON-REFRESH-001 status — confirm you're not racing a manifest-refresh that's already mid-flight. If one is OPEN, coordinate (don't double-refresh).
5. Confirm the §C.1 staged Codex WPs (audience-dynamic + ct-auth 1.0.1) haven't changed the SDK export surface since 2026-05-30 — if they have, reconcile the `protected_primitives` symbol list against the new exports.

### Acceptance criteria

- [ ] `contracts/auth-contract-v1.yaml` has a ratified `protected_primitives` block (tiering + symbols confirmed against actual SDK exports).
- [ ] `claim_shape_version` bumped (1.1.0 → 1.2.0 or per CT policy).
- [ ] Re-sign ceremony run: `.hmac` + `.sig` + `.sig.bundle` regenerated; `.sig.bundle` verifies via cosign.
- [ ] `policies/canonical-sdk-versions.yaml::auth_contract.manifest_sha256` matches the new contract content (drift cleared).
- [ ] `docs/ESTATE-CANONICALS.md` published (initial scope: auth + SDK-pinning + governance-docs; rest as TBD placeholders).
- [ ] PR opened with CT's standard `## R1 evidence` block (3 lens lines — CT's `validate PR body` + `r1-evidence-check` gates require it).
- [ ] No change to any file touched by the in-flight §C.1 cascade beyond the contract + policy + new docs.

### What NOT to do

- Do NOT do a standalone one-off `manifest_sha256` edit divorced from a content change — the drift clears via the Deliverable-2 re-sign ceremony, or stays on the FUP-CT-MANIFEST-CRON-REFRESH-001 roadmap. SCP verifies via `.sig.bundle`, so a stale `manifest_sha256` does not block SCP.
- Do NOT pre-empt or reorder the §C.1 cascade for this. It's additive + not time-pressured.
- Do NOT decide the canonical on SCP's behalf beyond ratifying the proposed block — but equally, do NOT under-scope: if CT's threat model says more symbols are protected than SCP proposed, add them.
- Do NOT bypass `required_signatures` via branch-pattern exemption (Axis-2 decision).

### When done

Notify SCP (or update `~/Projects/standards-control-plane/docs/coordination/2026-05-29-estate-canonicals-cheap-shape.md` §6 sequencing table) that Deliverables 1-3 are landed. SCP's WP-SCP-028 autonomous run then unblocks (its pre-flight verifies `protected_primitives` present + `.sig.bundle` verifies — it does NOT gate on `manifest_sha256` currency).

## ═══════════════ END PROMPT ═══════════════

---

## Notes for the SCP requester (not part of the droppable prompt)

- **WP-SCP-028 prereq framing corrected (this PR).** The plan-doc + autonomous-run prompt originally gated on "manifest_sha256 drift closed." Per this investigation, the real anchor is `.sig.bundle` (cosign). Both are corrected in this same PR so the CT ask + the SCP-side gate agree: SCP verifies via `.sig.bundle`; the only hard CT prereq is the `protected_primitives` block.
- **The drift is not SCP's blocker.** It closes on CT's roadmap OR as a side effect of the `protected_primitives` ceremony. SCP should not have asked CT to fix it as a discrete task.
- **Real SDK symbol surface captured** in the proposed block above (verified against `packages/ct-auth-{python,ts,go}/` exports 2026-05-30) so CT reacts to a concrete draft, not a blank page.
