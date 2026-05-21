# TF-PIM-001 impl WP — R1 synthesis (v0.2)

**Reviewed:** 2026-05-21 PM (impl WP plan-doc v0.2 at `ef5312e`)
**Lenses dispatched:** sec / arch-skeptic / pragmatist (Plan agents; read-only; DO-NOT-EDIT mandate per `feedback_subagent_review_only_scope_must_be_enforced`; sample-size-3 incident citation: CT c565fd0 + Recommender V14 INT #2 + docs/ESTATE-CONVERGENCE.md; isolated worktrees; Sonnet model)
**Lens evidence files:**
- `sec-lens-r1.md`
- `arch-skeptic-lens-r1.md`
- `pragmatist-lens-r1.md`

---

## R1 convergence — ACCEPT-WITH-AMENDMENT (all three lenses)

| Lens | Verdict | Convergence signal | Findings count |
|---|---|---|---|
| sec | ACCEPT-WITH-AMENDMENT | ITERATE-EXPECTED | 2 MIN + 1 NIT |
| arch-skeptic | ACCEPT-WITH-AMENDMENT | ITERATE-EXPECTED | 2 MAJ + 3 MIN + 1 NIT |
| pragmatist | ACCEPT-WITH-AMENDMENT | ITERATE-EXPECTED | 2 MIN + 1 NIT |

**Total: 2 MAJ + 7 MIN + 3 NIT = 12 findings.** No STRUCTURAL-BLOCK from any lens; consistent direction toward v0.3 fold + R2 verification.

## Findings classification

### 2 MAJ (arch-skeptic; block-on-amendment)

- **ARCH-MAJ-001** — §7.5a Wave D rollback step 3: `enable-required-check.sh --restore` requires a pre-state JSON that does not exist for SCP-self (SCP main's branch protection was installed via WP-SCP-020 020D2, not via `enable-required-check.sh` forward-mode). Rollback step is not executable as written using the documented tool.
- **ARCH-MAJ-002** — §7.6 Wave G Branch 4 + AC #1 ambiguity: "all 12 policy-check steps green" conflates infrastructure-health (the federation-primitive runs) with denial-free policy evaluation (no SCP-R-NNN rule fires). Branch 4 allows AC #1 satisfaction even with `SCP-E003` denials; this is structurally wrong.

### 7 MIN

- **SEC-MIN-001** — Wave A step 7 + §7.1 mitigation: `gh api .../actions/secrets` is paginated; needs `--paginate` flag.
- **SEC-MIN-002** — §6.4 invariant verification: `gh search code` has indexing lag + auth-scope caveat; needs local-grep secondary verification.
- **ARCH-MIN-001** — §4 Wave E parallelism: env-var injection in policy-check.yml must be same-PR-coupled with Wave D (mandatory, not optional).
- **ARCH-MIN-002** — §3.2 scaffolder FUP: Wave G evidence URL is the validation evidence for the scaffolder fix.
- **ARCH-MIN-003** — §9 follow-ups: TF-PIM-001-ARCH-002 real-API selftest coverage missing from explicit §9 follow-up list.
- **PRAG-MIN-001** — §9 SCAFFOLDER FUP unblock signal lacks close condition (Wave G evidence URL).
- **PRAG-MIN-002** — §9 WP-SCP-024 §5.2 amendment requirement at first 024D dispatch + Recommender first-test-of-same-namespace-install flag missing.

### 3 NIT

- **SEC-NIT-001** — Wave A: add step 10 to author App-key rotation SOP as a committed .md file.
- **ARCH-NIT-001** — §6.4: SCP-self wrapper missing from `gh search code` scope.
- **PRAG-NIT-001** — Operator-attended gate batching observation: Waves A+B and Waves G+H could be batched per session for ergonomics.

## Cross-cutting strengthening since path-ratification R1

All 3 lenses noted v0.2 measurably strengthens the impl WP relative to v0.1 + the path-ratification baseline:

- 4-step `.pem` discipline (sec): exceeds TF-PIM-001-SEC-001's original mitigation; macOS `srm -P` callout is a meaningful platform-specific hardening
- Fallback decision rule (sec): tighter than TF-PIM-001-SEC-003 required; named PRIMARY + FALLBACK + engagement criterion + documentation requirement
- Wave G failure tree + Wave D rollback strategy (sec + arch-skeptic): neither existed in v0.1; both are load-bearing additions
- Reversibility under each wave is well-bounded (arch-skeptic): all 8 waves have explicit reversal mechanisms; no irreversibility
- §3.2 out-of-scope discipline (arch-skeptic): SCAFFOLDER FUP correctly deferred; not over-coupled
- D-049 §Sequencing impact (pragmatist): items 1 and 2 supported by v0.2 wave structure; no conflict
- Cohort-of-5 in-namespace replication (pragmatist): §12.7.16 ceremony is sufficient to replicate per-adopter in @jrnb2024 namespace

## Pareto-frontier check (arch-skeptic, unprompted)

Considered: collapse Waves A+B+C+D into a single ADR-PLUS-IMPL slice. Verdict: NOT recommended. ADR-first discipline (Wave B before Wave D) is architecturally intentional; coupling ADR to Codex Tier 2 dispatch would force an ADR through code-change R-cycle protocol. Wave C/D same-PR coupling IS recommended (ADOPT-001 updates as docs-change in same commit as workflow change) — surfaced as observation, not finding.

8-wave structure is operational-debt-minimal given the estate's dispatch + review protocol.

## v0.3 fold scope

All 12 findings fold into v0.3 on the same branch (`chore/tf-pim-001-impl-plan-doc-v01`):

1. ARCH-MAJ-001: §7.5a step 3 rewrite — name `gh api PATCH` direct invocation; remove `enable-required-check.sh --restore` reference for SCP-self
2. ARCH-MAJ-002: AC #1 clarification ("all 12 steps complete with PASS verdict") + Wave G Action step 3 constraint (canary PR MUST be denial-free by design) + §7.6 Branch 4 rewording
3. SEC-MIN-001: Wave A step 7 + §7.1 — add `--paginate` flag
4. SEC-MIN-002: §6.4 — add local-grep secondary verification + auth-scope callout
5. ARCH-MIN-001: §4 Wave E parallelism — mandate same-PR coupling for env-var injection
6. ARCH-MIN-002: §3.2 — note Wave G evidence URL as scaffolder fix validation
7. ARCH-MIN-003: §9 — add real-API selftest TF
8. PRAG-MIN-001: §9 — explicit SCAFFOLDER FUP close condition
9. PRAG-MIN-002: §9 — WP-SCP-024 §5.2 amendment + Recommender first-test flag
10. SEC-NIT-001: Wave A — step 10 (authoring SOP file)
11. ARCH-NIT-001: §6.4 — SCP-self wrapper in grep scope
12. PRAG-NIT-001: §4 or §5 — Recommended-batching note

R2 dispatched against v0.3 must verify all 12 closures. R-fixpoint MET if R2 returns ACCEPT (no new significant findings) on all three lenses. Option A R4 mechanical override available at R3 if diminishing-returns trajectory matches `feedback_asymptotic_trajectory_split.md`.

## Cross-lens agreement (load-bearing for v0.3 fold)

All 3 lenses agree:
- v0.2 is materially stronger than v0.1
- No STRUCTURAL-BLOCK
- 12 findings fold into v0.3 prose-only (no wave resequencing; no new acceptance criteria; no architectural change)
- R-fixpoint via R2 is reasonable expectation

The plan-doc is on the right shape; v0.3 closes 12 specific gaps but does not require redirection.
