# D-036 R1 — completeness_governance lens

**Reviewed:** D-036 v1 (commit `274d801`) + RULE-003 v1 (commit `274d801`).
**Lens scope:** SCP rule-RFC convention compliance, CT documentation gate, ADR cross-linkage, ASC discipline, governance-doc completeness, RULE-TEMPLATE compliance.

**Verdict:** APPROVED_WITH_FINDINGS.

---

## CRIT

None.

## MAJ

### CG-MAJ-001 — D-036 has hard forward-coupling to ACC ADR-024 (not yet authored)

D-036 Cross-references names `acc/docs/decisions/ADR-024-cross-repo-trust-boundary.md` as a peer ADR "to be authored by ACC EST-P WS-EST-P-3.0". This is a HARD-DEP on a document that does not yet exist. If ADR-024 lands with materially different shape than D-036 anticipates, D-036 may need amendment.

**Disposition:** Fix in v2 — add explicit TF-D036-NEW that tracks "ADR-024 (ACC side) landing with consistent shape"; if ADR-024 deviates, D-036 amendment is required.

### CG-MAJ-002 — RULE-003 §10 BLOCKING resolution mechanism non-standard

RULE-003 §10 question 1 is marked `[BLOCKING]` with a "Default proposal if no response: option (a) vendored snapshot via Renovate." Per RULE-TEMPLATE §10, a proposal with unresolved `[BLOCKING]` questions does NOT meet quorum, even with one CODEOWNER approval. The default-if-no-response mechanism is non-standard — RULE-TEMPLATE expects operator answer in PR conversation.

**Disposition:** Fix in v2 — either downgrade question 1 to `[deferrable]` (the default is sound + low-stakes; the long-term path is captured as TF-RULE-003-002), OR keep `[BLOCKING]` + explicitly state that the BLOCKING resolution mechanism is "operator answer-or-default-acceptance, with PR-merge ceremony recording explicit acceptance of the default in the merge commit message". The second is more explicit but heavier; recommend (a) downgrade.

### CG-MAJ-003 — D-036 Element 3 schema-version evolution discipline unsaid

Element 3 signed-manifest carries `schema_version: d-036-mcp-manifest-v1`. TF-D036-006 tracks "schema versioning evolution". But the workflow consumer's behaviour at schema-version mismatch is not specified: does the workflow accept multiple versions concurrently (JWKS-style rollover)? Refuse old versions? Refuse new versions? The discipline-at-evolution-time gap creates ambiguity at the first version bump.

**Disposition:** Fix in v2 — D-036 Element 3 adds short note: "The workflow consumer accepts the manifest if `schema_version` matches a known version in its compiled-in version-allowlist. Version-allowlist is bumped via standard SCP federation-primitive PR. New versions are additive; old versions are removed only when adopter cascade has migrated. Mirrors `policies/VERSIONING.md` discipline."

## MIN

### CG-MIN-001 — RULE-003 §2 should reference STATUS.md chain entries for D-036

RULE-003 §2 "Prior conversation" references D-036 + ESTATE-CONVERGENCE §43 + plan-doc + HOME §8.2 + D-050. Missing: `STATUS.md` chain entries. Even if no STATUS.md entry exists for D-036 yet (it lands at merge), referencing the discipline shows the proposer knows the chain.

**Disposition:** Optional cosmetic fix in v2 — add reference to "STATUS.md 2026-05-24 chain entry (to be appended at merge)".

### CG-MIN-002 — D-036 out-of-sequence numbering needs DECISIONS.md row consistency

D-036 is reserved out-of-sequence (D-049 + D-050 are already filed at higher numbers). The file naming is internally consistent (`D-036-...-2026-05-24.md`), but `docs/DECISIONS.md` is a single-table record — appending an out-of-sequence row may break monotonic-numbering expectations. The DECISIONS.md row should explicitly note "D-036 was reserved 2026-05-XX as the SCP rule-RFC vehicle per ESTATE-CONVERGENCE §43" so future readers understand the gap.

**Disposition:** Fix in v2 — D-036 §"Cross-references" notes the DECISIONS.md row will carry the reservation context. The DECISIONS.md amendment itself happens at the status-bookkeeping commit AFTER operator-attended merge (per the standard pattern).

### CG-MIN-003 — D-036 §"Open questions" defaults bypass RULE-TEMPLATE BLOCKING shape

D-036 §"Open questions" carries three questions each with "Preferred operator default if no response". Same concern as CG-MAJ-002 but for the ADR (which doesn't have the same `[BLOCKING]`/`[deferrable]` convention as the rule-RFC). The ADR's open questions are conventionally resolved at merge; the default-mechanism here is non-standard for D-NNN docs in SCP.

**Disposition:** Optional cosmetic fix in v2 — replace "Preferred operator default if no response" with "If unresolved at merge, the implicit acceptance is" — same semantics, more aligned with ADR convention.

### CG-MIN-004 — D-036 Status flip ceremony reminder for PR opener

D-036 §"Status flip ceremony" notes mechanical auto-merge is not authorised. The PR body needs to assert R1 evidence linkage per cardinal rule 11. This is a process-discipline reminder for me (the PR opener), not a doc fix.

**Disposition:** Carry forward to PR opening step — ensure PR body cross-links R1 evidence at `docs/reviews/D-036/R1/`.

## nit

### CG-NIT-001 — Section structure consistent with D-049 + D-050 precedents

Reviewed; no fix.

### CG-NIT-002 — Terminology ("EST-P", "ACC-as-cross-repo-caller") consistent across both docs

Reviewed; no fix.

### CG-NIT-003 — RULE-003 §6 (conflict-gate strategy) coverage adequate

Reviewed; 14 fixtures named, suppression paths covered per RULE-TEMPLATE §8. No fix.
