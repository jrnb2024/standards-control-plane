# Estate-canonicals cheap-shape — Phase A of D-058 (CT-prerequisites memo)

**Filed:** 2026-05-29 (concurrent with D-058 ratification)
**Authority chain:** D-058 §5 (Phase A — Estate-canonicals index, cheap text shape)
**Owner:** CT (authoritative file lands operator-attended on CT main)
**Coordinated by:** SCP (this memo describes the contract)
**Status:** AWAITING CT-side operator action

This memo is the SCP-side coordination doc for **Phase A** of D-058's two-phase strategic rollout: ship the cheap text-index shape FIRST, then the mechanical Rego enforcement layer second (Phase B = WP-SCP-028). The text-index alone captures ~80% of canonical-awareness value at ~10% of the implementation cost.

---

## §1 What CT publishes

A single markdown file at `control-tower/docs/ESTATE-CANONICALS.md` with the shape below. CT-owned; operator-attended commit; CODEOWNERS-protected.

### 1.1 File header

```markdown
# Estate canonical architecture index

**Authority:** Control Tower (CT) maintains this index.
**Purpose:** Single source of truth for "what's the canonical pattern for X across the estate, at what version, owned by which authority."
**Scope:** Cross-cutting concerns that span ≥2 estate repos.
**Discipline:** This file IS the index. Canonical content lives in the owning-authority's repo at the path declared here. Adopters reference this index by section number + version.
**Bound rule:** SCP enforces LINKAGE (does your code reference these canonicals correctly?), not VALUES (does your code match canonical content byte-for-byte?). See SCP D-049 + D-058.
```

### 1.2 Domain entry shape

For each cross-cutting domain, one row in a table of this shape:

| Domain | Authority | Canonical doc path | Current version | Signed manifest | Last updated |
|---|---|---|---|---|---|
| Auth | CT | `control-tower/contracts/auth-contract-v1.yaml` | `claim_shape_version 1.1.0` | `control-tower/policies/canonical-sdk-versions.yaml` + `.sig.bundle` | 2026-05-29 |
| SDK pinning | CT | `control-tower/policies/canonical-sdk-versions.yaml` | (see file header) | `.sig.bundle` adjacent | 2026-05-29 |
| Orchestrator / dispatcher | ACC | `acc/docs/plans/PLAN-EST-P-cross-repo-orchestration-v3.md` | Gate-A draft | NOT YET PUBLISHED | NOT YET PUBLISHED |
| Kafka event shape | (TBD — RI proposes? CT?) | (TBD — `mapp-returns-intelligence/contracts/events/return.scored.json`?) | (TBD) | NOT YET PUBLISHED | NOT YET PUBLISHED |
| Governance documentation | SCP | `standards-control-plane/docs/` (taxonomy: requirements/strategy/architecture/design/plan separation per `feedback_documentation_standards.md`) | n/a (process not artefact) | n/a | 2026-05-29 |
| Observability (`/health` shape + OTel) | (TBD — CT?) | (TBD) | (TBD) | NOT YET PUBLISHED | NOT YET PUBLISHED |
| Tenancy / cross-tenant prevention | (TBD — CT?) | (TBD) | (TBD) | NOT YET PUBLISHED | NOT YET PUBLISHED |
| FastAPI conventions | (TBD — informal) | (TBD) | (TBD) | NOT YET PUBLISHED | NOT YET PUBLISHED |
| Frontend (Next.js + Tailwind + Zustand) | (TBD — ACC FE?) | (TBD) | (TBD) | NOT YET PUBLISHED | NOT YET PUBLISHED |
| Postgres (migration tool + naming + RLS) | (TBD) | (TBD) | (TBD) | NOT YET PUBLISHED | NOT YET PUBLISHED |

### 1.3 Per-domain notes

Each row carries a one-paragraph note describing:
- What the canonical PRESCRIBES (the "thou shalt" pattern; high-level — link to the canonical doc for detail)
- What it EXCLUDES (the "thou shalt not" — the anti-patterns)
- The CONFORMANCE check shape (LINKAGE: "reference this manifest"; or VALUES: "byte-equal to this — currently no rules in this shape per D-049")
- The OWNING-team contact + escalation path

### 1.4 Versioning + change policy

- Domain authorities update their entry when their canonical changes
- Each row carries a `Last updated` date; rows >90 days stale flag for owner review
- Changes to this index are PR-reviewed by CT CODEOWNERS
- Major canonical version bumps (e.g. ct-auth-py 1.x → 2.x) require a 30-day deprecation announcement in this file's `Deprecation log` section before adopter-breaking deny rules can ship

### 1.5 Initial publication scope

CT operator-attended ship covers ONLY domains that have published artefacts today:
- **Auth** (canonical-sdk-versions.yaml + auth-contract-v1.yaml — close manifest_sha256 drift first)
- **SDK pinning** (canonical-sdk-versions.yaml)
- **Governance documentation** (SCP-owned process)

All other rows ship as `(TBD — authority unassigned)` placeholders. Each gets filled when its owning authority publishes the 4-artefact tuple per D-058 §3.

---

## §2 What each adopter does (PR template change)

Each adopter repo adds the following block to `.github/pull_request_template.md` (or extends if exists):

```markdown
## Canonical conformance declaration

If this PR touches one or more cross-cutting domain(s) listed in `control-tower/docs/ESTATE-CANONICALS.md`:

- [ ] **Auth** — conforms to `ESTATE-CANONICALS.md §Auth` version `<v>`
- [ ] **SDK pinning** — conforms to `ESTATE-CANONICALS.md §SDK pinning` version `<v>`
- [ ] **Orchestrator / dispatcher** — conforms to `ESTATE-CANONICALS.md §Orchestrator` version `<v>`
- [ ] **Other (specify):** `____________________________________`

Check applicable boxes. If unchecked and your PR touches a listed domain, the merge gate will warn (Phase A) or deny (Phase B post-deny-promote).
```

Estate-wide adopter PR-template propagation is operator-attended; each repo's PR is small (1 file change).

---

## §3 What SCP does (Phase A enforcement; minimal)

SCP ships **zero new rules** for Phase A. The validation is via the existing `r1-evidence-check.yml` pattern: a thin workflow that greps adopter PR bodies for the declaration block + warns if absent. Same pattern as the existing R1-evidence gate; trivially extensible.

The workflow extension lives in **each adopter's `.github/workflows/`** (not SCP's federation primitive — that stays Rego-only). One-line shell check: "if PR diff touches `<domain-paths>` AND PR body lacks `## Canonical conformance declaration` block, fail." Adopter-specific tuning of which paths trigger which domain check.

This is genuinely Phase A's full mechanical surface — markdown + PR-template + grep. No Rego, no MCP, no schemas. Days of effort, not weeks.

---

## §4 What Phase B (WP-SCP-028) adds on top

Phase B layers mechanical Rego enforcement over the Phase A text index for the **auth domain specifically**:

- Rules read CT's canonical artefacts (signed manifest + auth contract)
- LINKAGE checks: adopter pins are correct + adopter doesn't shadow protected primitives + adopter declares current claim_shape_version
- Cohort cascade via existing required-check path

Phase B does NOT replace Phase A — it complements it. The PR template still applies; the Rego rules add merge-gate teeth for the specific auth-canonical conformance properties that are machine-verifiable.

---

## §5 CT-side action items

Per D-058 §5 + this memo, CT operator-attended ship:

1. **Close `FUP-CT-MANIFEST-CRON-REFRESH-001`** — resolve `manifest_sha256` drift (`386b4097` recorded vs `eddcd053` actual); add bot-signing axis to manifest cron-refresh.
2. **Add `protected_primitives` block to `contracts/auth-contract-v1.yaml`** — declares the language-specific protected symbol sets (python: [verify_token, sign_token, …]; typescript: […]; go: […]). Needed for SCP-R-010 (auth-canonical-import-fence) at WP-SCP-028 fire time.
3. **Author + publish `control-tower/docs/ESTATE-CANONICALS.md`** per §1 shape above. Initial publication scope per §1.5.
4. **Estate-wide PR-template propagation** — operator-attended PR per repo (PIM, mapp-doc-agent, SCP-self, RI, SA, ACC, mapp-visual-shopping, Recommender, FLA). Each PR is the small block from §2.
5. **Adopter-side workflow extension** per §3 (a thin grep job in each adopter's `.github/workflows/` — operator-attended; small).

Estimated total operator effort: 1-2 days CT-side + 0.5 day per adopter for PR-template propagation + workflow ship.

---

## §6 Sequencing relative to WP-SCP-028

| Order | Item | Owner | State |
|---|---|---|---|
| 1 | D-058 ADR ratified | SCP operator | THIS PR |
| 2 | WP-SCP-028 plan-doc filed | SCP operator | THIS PR |
| 3 | This coordination memo filed | SCP operator | THIS PR |
| 4 | CT closes `FUP-CT-MANIFEST-CRON-REFRESH-001` (manifest_sha256 drift) | CT operator | OPEN |
| 5 | CT adds `protected_primitives` block to `auth-contract-v1.yaml` | CT operator | OPEN |
| 6 | CT publishes `ESTATE-CANONICALS.md` initial version | CT operator | OPEN |
| 7 | Adopter PR-template propagation (estate-wide) | Operator per repo | OPEN |
| 8 | WP-SCP-028 autonomous run fires | SCP autonomous session | GATED on 4+5 |
| 9 | v1.4.0 cut + cohort cascade propagation | SCP operator | GATED on 8 |
| 10 | 4-week observation window opens | n/a | GATED on 9 |
| 11 | D-059 ratifies outcome | SCP operator | GATED on 10 |

Steps 4, 5, 6, 7 are independent of each other and can proceed in any order. Steps 4 + 5 are the hard prereqs for WP-SCP-028; 6 + 7 unblock Phase A's full enforcement surface but don't block Phase B's start.

---

## §7 Reversibility

If Phase A surfaces that the PR-template declaration is unhelpful (high false-positive checkbox-fatigue, adopters checking boxes without reading), reversal:
- Remove the block from PR templates (estate-wide PRs)
- Disable the grep job in adopter workflows
- Total reversal: ~1 day operator-attended; no production impact

If Phase B surfaces deeper issues post-deny-promote, D-059 + the rule-config disable mechanism handles reversibility (per WP-SCP-028 §1.2 invariant 6).

---

**Filed:** 2026-05-29 (this PR; ratified by D-058).

**Closes when:** all 11 sequencing items above complete OR D-058 is amended to retire Phase A (e.g. if CT operator finds the cheap shape doesn't earn its keep at the estate's current scale).
