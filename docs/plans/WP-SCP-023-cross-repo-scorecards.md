# ProgrammePlan — WP-SCP-023 Cross-repo Scorecards

**Work Package:** `WP-SCP-023`
**Version:** 0.1
**Status:** Draft — ready for plan-PR review
**Date:** 2026-05-03
**Branch:** `feature/wp-scp-023-cross-repo-scorecards-plan`
**Programme Ref:** to be filed at slice 023A close-out (proposed `SCP-101` cross-repo scorecards backlog row)
**Decisions reserved (do not assign in any slice before the named target slice — see `docs/DECISIONS.md` header reservation note):**
- **D-041** — reserved for slice 023B: cross-repo scorecard data shape (`schemas/scorecard-emit.schema.json`) + opt-in adopter participation model.
- **D-042** — reserved for slice 023C: aggregator pipeline trust model + GitHub Actions Artifact Attestation (OIDC-based) for adopter emits + SCP-side Ed25519 key registry for the central index (extends WP-SCP-021's `docs/security/mcp-signing-keys.pub` infrastructure).
- **D-043** — reserved for slice 023D: MCP method shape (`scp.consult_scorecard`) + read-only contract + signed-output envelope.

**Predecessors:**
- `WP-SCP-019` (Service Auth Contract) — closed 2026-04-20.
- `WP-SCP-020` (Policy Federation Primitive) — closed 2026-04-30 at v1.0.0; v1.1.0 cut 2026-05-02.
- `WP-SCP-021` (MCP Server) — landed 2026-04-29 (USER-GATE-C signed).
- `WP-SCP-022` (Implementation Programme) — closed 2026-04-30 at Threshold A; post-Threshold-A backlog cleared 2026-05-02 / 03 (slices 020M / 020N / 020L / 020P / TF-020P-005 / 020Q).
- **TF-006 closed in slice 020Q** (PR #96, commit `974a173`, 2026-05-03). The conflict-gate Python evaluator now mirrors `policies/scp_common.rego`'s suppression semantics 1:1 — necessary for cross-repo aggregation to apply waivers consistently.

## 1. Purpose

WP-SCP-020 + WP-SCP-021 give SCP **per-PR authority** over each adopter repo:
- WP-SCP-020 (federation primitive): every adopter PR runs the SCP reusable workflow + Conftest evaluation against the SCP-R-NNN rule library + emits `policy-check-summary.json` (findings, waivers applied, verdict, version pin).
- WP-SCP-021 (MCP server): agents working in adopter repos can consult `scp.consult_rules` / `scp.audit_changed` for pre-code guidance + Ed25519-signed receipts.

Neither WP gives SCP **estate-wide observability** — the ability to answer "which repos in the estate currently meet which standards at which level, and which are drifting?" Today this question requires manually visiting each adopter's PR history to aggregate verdicts.

`WP-SCP-023` ratifies a **cross-repo scorecard surface** that aggregates per-repo conformance signals into a unified, queryable index. It:

1. Defines a per-repo **scorecard emit contract** that adopter wrappers OPTIONALLY add to their SCP federation-primitive invocation. Emits a `scorecard-emit.json` per PR alongside the existing `policy-check-summary.json`.
2. Defines a **central aggregator** that consumes per-repo scorecard emits (cron-driven from a known set of opt-in adopter repos) into a single signed index at `output/scorecards/index.json` in the SCP source repo.
3. Defines an **exposure surface** at two levels: (a) an auto-generated markdown report at `docs/scorecards/<YYYY-MM-DD>.md` checked into the SCP repo (operator + auditor consumption); (b) a new MCP method `scp.consult_scorecard` (agent + tooling consumption).
4. Defines a **Threshold A criterion** for WP-SCP-023: at least 3 estate adopters opted in, at least 1 weekly aggregator run completed cleanly, exposure surface live in both forms.

This is **move #5** of the 5-move MVCP — estate-wide observability for the federation primitive. Canonical move numbering per individual plan-docs: move #1 = WP-SCP-020 federation primitive (per WP-SCP-020 §1); move #3 = WP-SCP-021 MCP server (per WP-SCP-021 §1); move #4 = WP-SCP-022-proposal-queue (per WP-SCP-022 §12); move #5 = WP-SCP-023 scorecards (per WP-SCP-022 §12). **Move #2 is conflicted in the corpus** — WP-SCP-020 §1's enumeration "Moves #2–#5 (MCP server; proposal queue; scorecards; estate rollout)" implicitly numbers MCP server as move #2, while WP-SCP-021 §1 and WP-SCP-020 §3 both explicitly assign move #3 to the MCP server. This plan adopts per-plan-doc explicit self-declaration (WP-SCP-021 §1 = move #3), leaving move #2 with no plan-doc self-declaring it. Resolving the WP-SCP-020 internal §1-vs-§3 inconsistency is out of scope for WP-SCP-023. WP-SCP-020 made SCP authoritative per-PR; WP-SCP-021 made SCP consultable pre-code; WP-SCP-023 makes SCP **observable estate-wide**. **WP-SCP-024 (estate cascade) follows as the natural successor beyond the 5-move MVCP** — once SCP can observe drift, the next step is to drive it down via coordinated cascade (FLA pilot → PIM/recommender/etc.).

This plan is a **process artefact + spec artefact** — it does not ship code in this slice. Implementation lands in 023B/023C/023D/023E.

## 2. Invariants and what this is NOT

### Invariants

1. **Aggregator output is informational; the federation primitive is per-PR authoritative.** A scorecard reading "compliant" does NOT bypass any per-PR `policy-check / scp/policy-check` required check. A scorecard reading "non-compliant" does NOT block any merge. The federation primitive (WP-SCP-020) remains the only enforcement surface; scorecards add observation. **Positively: the aggregator MUST faithfully report verified emit content** — it does not transform, smooth, or "best-interpret" verdicts; rule_counts and waiver counts are passed through as-emitted from each adopter's signed emit. A divergence between the aggregator's reported state and an adopter's actual `output/findings/policy-check-summary.json` is a verification failure, not a smoothing artefact.
2. **Waiver content is NEVER aggregated outside the source repo's CODEOWNERS scope.** Per-repo emitter publishes aggregated counts (`waivers_applied_count`, `waivers_active_count`) and rule_ids — **not** the waiver `reason` text, `approved_by` identities, or `waiver_id` strings. Centralising those would cross a privacy boundary (waiver reasons may carry incident details, vendor names, decision-context that's bounded to the source-repo audience).
3. **Rule-id-only matching, mirroring `policies/scp_common.rego`.** Per the documented note in `scp_common.rego` lines 31-44 (the "Spec note" comment block on `scp_active_waiver_for`), finding-id-level matching is deferred to WP-SCP-023. This plan keeps it deferred — finding-id correlation would require a per-finding-id index that grows with PR throughput; rule-id aggregation is bounded by the rule library cardinality (~5-10 rules at v1.x). Finding-id can land as a v2.0+ extension.
4. **Opt-in adopter participation.** Adopters MUST explicitly add the scorecard-emit step to their wrapper to participate. Non-participating adopters appear in the index as `participation_status: "opt-out"` (or are absent entirely if no record was ever attempted). The index NEVER lists non-participants as "non-compliant" or "unknown" in a way that creates social pressure to opt in.
5. **MCP exposure is read-only.** `scp.consult_scorecard` returns aggregated metrics + version pins + verdicts. It does NOT mutate the index, and it does NOT expose raw waiver content. Mirrors WP-SCP-021's read-only consult posture.
6. **Aggregator output is Ed25519-signed.** Each emit + the central index carry an Ed25519 signature using the same key infrastructure WP-SCP-021 established for MCP receipts. A tampered index can be detected by signature-verification at consumption time. Closes the bypass-surface concern that a compromised aggregator could mis-report estate state.
7. **Bus-factor-1 acknowledged.** In single-operator mode (D-031), the aggregator runs as a GitHub Action on the SCP source repo with the same operator identity that owns the federation primitive. The 2026-07-21 quarterly review (per WP-SCP-020 §8 + STATUS.md) covers this exposure.
8. **No cross-repo write surface.** The aggregator pulls from adopter repos via public read paths only (artifact downloads from finished workflow runs, or direct repo file reads via the GitHub API). No write back to adopter repos at any point.

### What this is NOT

- **NOT a per-PR gate.** The federation primitive is the gate; scorecards observe.
- **NOT a per-finding tracking system.** Per-finding correlation is deferred to v2.0+.
- **NOT a cross-repo decision-record aggregator.** That's `SCP-075-crossrepo`, a separate WP.
- **NOT a vendor SLA dashboard.** Scorecards measure adopter conformance to SCP rules; they do not measure SCP vendor responsiveness.
- **NOT a replacement for the per-PR `output/findings/` artifacts.** Each adopter still owns their finding history; scorecards add an estate-wide rollup.
- **NOT mandatory for adopters.** Opt-in invariant.
- **NOT a privacy-relaxation surface.** The plan tightens what crosses repo boundaries; it does not loosen.

## 3. Programme protocol position

Follows `PROG-SCP-001` and `WP-SCP-022` programme protocol: every implementation slice flows through four-tier dispatch (Opus orchestrator + Codex executor + 3× Sonnet R1 + recursive fix-rounds to fixpoint). Plan-doc slice 023A is orchestrator-applied per `feedback_four_tier_dispatch.md` (estate-doctrine specification); subsequent implementation slices may dispatch Codex executors.

### Slice ordering

| Slice | Title | Tier | Branch suffix | Dependency |
|---|---|---|---|---|
| 023A | Plan-doc (this slice) | orchestrator-applied | `feature/wp-scp-023-cross-repo-scorecards-plan` | TF-006 closed |
| 023B | Per-repo scorecard emitter + schema (`scorecard-emit.json`) | Codex executor (Tier 3) | `feature/wp-scp-023-023b-emitter` | 023A merged |
| 023C | Central aggregator + signed index (`output/scorecards/index.json`) | Codex executor (Tier 3) | `feature/wp-scp-023-023c-aggregator` | 023B merged |
| 023D | Exposure surface — markdown report + MCP method `scp.consult_scorecard` | Codex executor (Tier 3) | `feature/wp-scp-023-023d-exposure` | 023C merged |
| 023E | Threshold A sign-off + 3-adopter onboarding + USER-GATE-D | orchestrator-applied + USER-GATE | `feature/wp-scp-023-023e-threshold` | 023D merged + ≥3 adopters opted in |

### Plan-PR semantics

The plan-doc is itself a PR that goes through CI + R1+R2 fixpoint (this slice). On merge, slice 023B opens against the new plan-doc as its reference. Each implementation slice cites this plan-doc + DISPATCH-NOTE when dispatched.

## 4. Threat model

The cross-repo scorecard surface introduces three new data-flow boundaries:

1. **Adopter PR → adopter repo Actions artifact.** The scorecard emit lives alongside `policy-check-summary.json` in the adopter's CI workflow artifact. Trust boundary: adopter's GitHub Actions runner. Threat: a malicious adopter PR could craft a fake scorecard emit. **Mitigation:** the emit is generated by the SCP reusable workflow (D-022 SHA-pinned), not the adopter's wrapper; the adopter cannot tamper with the emit content. The aggregator validates the emit's signature against the SCP-side known key.

2. **Adopter repo artifact → SCP aggregator (cron run).** The aggregator pulls per-repo emits via the GitHub API. Trust boundary: GitHub artifact-download API + the SCP repo's `GITHUB_TOKEN`. Threat: a compromised SCP-side runner could substitute a fabricated emit. **Mitigation:** every emit carries an Ed25519 signature from the per-PR run; the aggregator verifies the signature before accepting the emit into the index. Drift alarms fire if a known-opt-in adopter's emit suddenly becomes unverifiable.

3. **Aggregator index → consumer (markdown / MCP).** The central index is read by operators (markdown), agents (MCP), and external auditors (signed JSON). Trust boundary: the SCP source repo + the MCP server. Threat: a tampered index could mis-report estate state. **Mitigation:** the index itself carries an Ed25519 signature over its full content; consumers verify before trusting.

The threat model explicitly excludes:
- **Active adversary against the GitHub Actions OIDC trust chain** — outside the federation primitive's scope; depends on GitHub's security posture.
- **Operator-side trojan attack on the SCP repo** — bus-factor-1 cost acknowledged in invariant 7; mitigated by the 2026-07-21 quarterly review + CODEOWNERS coverage on `output/scorecards/**` (added in 023C).
- **Long-term key rotation** — the Ed25519 keys reuse WP-SCP-021's MCP signing key; rotation is governed by D-024/D-025; key rotation procedures are outside this WP's scope.

## 5. Architecture

### Per-repo scorecard emitter (lands in 023B)

The SCP reusable workflow gains a new **opt-in** step `Emit scorecard summary`. Adopter wrappers enable it via:

```yaml
jobs:
  policy-check:
    uses: jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<sha>
    with:
      scorecard-emit: true   # <-- opt-in, default false
```

The emit step writes `output/scorecards/scorecard-emit.json` with the `scorecard-emit.schema.json` shape:

```jsonc
{
  "schema_version": "0.1",
  "emitted_at": "<RFC3339>",
  "scp_version": "<scp federation primitive version pin from version-manifest.json>",
  "repo": "<owner/name>",
  "ref": "<branch / tag>",
  "commit": "<head sha>",
  "verdict": "allow" | "deny" | "warn",
  "rule_counts": {
    "SCP-R-001": { "raw_findings": <int>, "denies": <int>, "waived": <int>, "rule_config_disabled": <bool> },
    "SCP-R-002": { ... },
    ...
  },
  "waivers_aggregate": {
    "active_count": <int>,
    "by_rule_id": { "SCP-R-001": <int>, ... },
    "expiring_within_30d": <int>
  },
  "rule_config_aggregate": {
    "disabled_rules": ["SCP-R-NNN", ...],
    "expiring_within_30d": <int>
  },
  "signature": "<ed25519 signature over the canonicalised payload above, base64>"
}
```

**No waiver content** crosses the boundary — only counts + rule_id keys.

### Central aggregator (lands in 023C)

A new `.github/workflows/scorecard-aggregator.yml` cron workflow runs **weekly** on the SCP source repo (default cadence per §10 Q3 resolution; operator may manual-trigger via `gh workflow run scorecard-aggregator.yml` for ad-hoc runs). It uses **two-job permission scoping** (mirroring the WP-SCP-022 D-037 release-gate-violation pattern):

**Job 1 — `aggregate` (read-only):**
Permissions: `contents: read`, `actions: read`, `attestations: read` (for `gh attestation verify` calls against GitHub's Artifact Attestation API to verify adopter emit OIDC attestations). **Note:** `id-token: write` is intentionally NOT granted — that permission is for the job to REQUEST a GitHub OIDC token (which the aggregator does not need); reading + verifying existing artifact attestations only requires `attestations: read`.

1. Reads a registry of opt-in adopter repos at `docs/scorecards/opt-in-registry.yaml` (CODEOWNERS-protected; updated by adopters via PR).
2. For each adopter, fetches the latest `scorecard-emit.json` artifact from the most recent green policy-check run on the adopter's default branch via `gh run download`.
3. Verifies each emit's signature against the SCP-side **key registry** at `docs/security/mcp-signing-keys.pub` (the WP-SCP-021-established path; CODEOWNERS-covered via `docs/security/**`). The registry carries a list of `(key_id, public_key, valid_from, valid_until)` entries; each emit carries its signing `key_id`. The aggregator verifies each emit against the key that was current at `emitted_at` time. This bounded extension of WP-SCP-021's existing key infrastructure handles key rotation without invalidating historical emits (closes 023A R1 MAJ-SAFE-002).

   **Signing mechanism (per D-042 to be filed at 023C):** the SCP reusable workflow uses **GitHub Actions Artifact Attestation** (OIDC-based) — the per-PR run signs the emit with the GitHub Actions OIDC token at upload time; the aggregator verifies via `gh attestation verify` against GitHub's Artifact Attestation API (Sigstore/Fulcio-backed). **No private signing key is ever distributed to adopter runners** — this closes the SCP-private-key-in-adopter-runner contradiction (closes 023A R1 MAJ-SAFE-001). The MCP-signing-keys.pub registry covers the SCP-side aggregator-emitted index signature; adopter emits use OIDC attestation for per-emit verification.

   **Non-negotiable verification constraint (per D-042 + closes 023A R2 MAJ-SAFE-R2-001):** the aggregator MUST verify the **`job_workflow_ref` OIDC claim** in each artifact attestation against the expected SCP reusable workflow path AND the SHA pin the adopter's caller wrapper specifies. JWKS signature verification alone proves GitHub issued the token but does NOT prove the SCP reusable workflow produced the artifact — without the `job_workflow_ref` check, any workflow in an opted-in adopter's repo could fabricate an emit and pass aggregator verification. The 023C `gh attestation verify` invocation MUST use the **`--signer-workflow`** flag (binding to the specific signing workflow path; closes 023A R3 COR-R3-MAJ-001 / MIN-SAFE-R3-001 — the earlier draft cited a non-existent `--source-path-prefix` flag) — for example: `gh attestation verify <artifact> --signer-workflow jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<sha>` — bound to the SCP reusable workflow path AND the SHA pin the adopter's caller wrapper specifies. An attestation produced by any other workflow (custom or third-party) MUST be rejected with `verification_failure: untrusted_workflow_source`.
4. Aggregates verified emits into `output/scorecards/index.json` with the `scorecard-index.schema.json` shape.

**Job 2 — `commit` (write-scoped, gated):**
Permissions: `contents: write`, `pull-requests: write`. Fires only on `needs.aggregate.result == 'success'`.

5. Signs the index itself with the SCP-side aggregator key (from `docs/security/mcp-signing-keys.pub`).
6. Commits the new index + an auto-generated markdown report at `docs/scorecards/<YYYY-MM-DD>.md` to a `scorecards/<YYYY-MM-DD>` branch.
7. Opens a PR for operator review (single-operator self-merge per D-040 once R1+R2 fixpoint reached on the diff).

Failure modes:
- Emit signature invalid → adopter row marked `verification_failure` in the index; aggregator does not silently drop.
- Adopter repo unreachable (rate-limit, deletion) → adopter row marked `unreachable_at: <ts>`; row from the prior index is retained.
- Aggregator-side error → the cron run fails loudly; no partial-index commit lands.

### Exposure surface (lands in 023D)

Two surfaces:

**Markdown report** (`docs/scorecards/<YYYY-MM-DD>.md`):
- Adopter table: repo | scp_version | verdict | rule denies | active waivers | expiring waivers | rule-config disabled.
- Drift section: deltas vs prior index (verdict flips, version drift).
- Generated automatically by the aggregator; checked into the SCP repo for auditability.

**MCP method `scp.consult_scorecard`** (extends WP-SCP-021's MCP server):
- Input: optional `repo_filter` (single-repo or `*` for all); optional `since_ts` (return only emits newer than).
- Output: aggregated metrics matching the markdown report's content + the index signature.
- Read-only; no mutation; no exposure of raw waiver content.

### Slice 023E: Threshold A sign-off

Mirrors WP-SCP-020's USER-GATE-A pattern:
- Threshold A criterion: ≥3 estate adopters opted in (FLA + 2 of {PIM, recommender, mapp-doc-agent, control-tower}); ≥1 weekly aggregator run committed a fully-verified index; markdown report + MCP method both queryable; CODEOWNERS coverage on `docs/scorecards/**` + `output/scorecards/**` confirmed.
- USER-GATE-D artefact: `docs/gates/USER-GATE-D.md` signed by `@jrnb2024` (single-operator) ratifying that scorecard surface is operationally trusted for estate observability.

## 6. Slice plan

| Slice | Deliverable | Acceptance criteria | Tier | Dispatch contract |
|---|---|---|---|---|
| 023A (this) | `docs/plans/WP-SCP-023-cross-repo-scorecards.md` v0.1 | Plan-doc R2 fixpoint reached + merged | orchestrator | DISPATCH-NOTE + 3-lens R1 |
| 023B | Per-repo emitter + `schemas/scorecard-emit.schema.json` + reusable-workflow `scorecard-emit` step (opt-in, default false) | Schema validates against ≥3 hand-crafted fixture emits; reusable workflow opt-in step lands hash-pinned + CODEOWNERS-covered; D-041 filed | Codex executor | Per WP-SCP-022 dispatch contract |
| 023C | `.github/workflows/scorecard-aggregator.yml` cron + `docs/scorecards/opt-in-registry.yaml` (empty initial state) + `output/scorecards/index.json` schema + Ed25519 verification path | Aggregator runs on the SCP repo against an empty registry without error; aggregator opens a draft PR template; D-042 filed | Codex executor | Per WP-SCP-022 dispatch contract |
| 023D | Markdown report generator + MCP method `scp.consult_scorecard` (read-only, signed-output) + ADOPT-001 §13 onboarding section | Markdown report rendered against an empty index produces a valid placeholder; MCP method returns aggregated-only data + verifiable signature; D-043 filed | Codex executor | Per WP-SCP-022 dispatch contract |
| 023E | Threshold A onboarding (FLA + 2 estate adopters opted in via PR to `opt-in-registry.yaml`); USER-GATE-D ratification artefact | ≥3 adopter rows present + verified in the live index; weekly aggregator run committed cleanly; USER-GATE-D signed | orchestrator + USER-GATE | Per WP-SCP-022 USER-GATE pattern |

## 7. Risk surface

| ID | Risk | Mitigation | Owner |
|---|---|---|---|
| **R-023-01** | Centralising waiver counts may indirectly leak waiver patterns (a sudden spike in `expiring_within_30d` for a specific rule_id correlates with known incidents). | The aggregated counts are bounded — they reveal *that* an adopter has waivers, not *what* the waivers say. Forward-compat: if leakage proves material, slice 024 introduces aggregator-side k-anonymity (group adopters into buckets) before exposure. | 023C / 023D |
| **R-023-02** | Aggregator pipeline compromise could mis-report estate state. | Ed25519 signature on each emit + the central index. Consumers verify before trusting. | 023C / 023D |
| **R-023-03** | Adopter opt-in skew creates social pressure to participate. | Invariant 4: non-participants appear as `opt-out` or absent, never as "unknown" or "non-compliant". Documented in the markdown report header. | 023D |
| **R-023-04** | MCP method abuse: a hostile agent could enumerate adopter waivers across the estate. | MCP method returns aggregated metrics only; rate-limited via the existing MCP server's per-client limits (WP-SCP-021); auditable via MCP receipt. | 023D |
| **R-023-05** | Cron-based aggregator falls behind reality (last-week's index doesn't reflect today's PRs). | Markdown report headers carry `aggregated_at` timestamp + the operator can manually trigger via `gh workflow run`. The cron is a default cadence, not a hard guarantee. | 023C |
| **R-023-06** | Aggregator's GitHub Actions runner is the same identity that owns the federation primitive — bus-factor-1 cost. | Acknowledged in invariant 7; covered by 2026-07-21 quarterly review (WP-SCP-020 §8). | 023E |
| **R-023-07** | Schema drift (`scorecard-emit.schema.json` v0.1 → v1.0) could invalidate prior emits. | Schema version field carried in every emit; aggregator handles known versions; drops unknown with a warning. v1.0 cut after Threshold A. | 023B → 023E |
| **R-023-08** | Plan-doc commits to an architecture before any adopter has implemented an emitter. | Plan-doc is v0.1; the schema lands at v0.x in 023B; v1.0 is reserved until at least one real adopter validates the shape (FLA pilot canary). | 023A → 023B |
| **R-023-09** | Waiver-content invariant could be subverted by a future schema extension that adds a `waiver_excerpts` field. | Invariant 2 is non-negotiable per this plan; any future schema field that includes waiver content requires an amending D-NNN row + plan-doc amendment. | All slices |

## 8. Acceptance criteria + Threshold A

**Plan-doc (slice 023A) acceptance:**
- v0.1 plan-doc lands with §1–§10 populated.
- 3-lens R1+R2 fixpoint reached (0 CRIT + 0 MAJ on a complete cycle).
- D-041 / D-042 / D-043 reserved (not assigned in this slice).

**Threshold A (slice 023E gate):**
- ≥3 estate adopters listed in `docs/scorecards/opt-in-registry.yaml` (FLA + 2 of {PIM, recommender, mapp-doc-agent, control-tower}).
- ≥1 weekly aggregator run has produced a `output/scorecards/index.json` with verified signatures across all opted-in adopters.
- `docs/scorecards/<YYYY-MM-DD>.md` markdown report generated + checked in.
- `scp.consult_scorecard` MCP method live on the deployed MCP server + returns valid responses against the live index.
- CODEOWNERS coverage confirmed on `docs/scorecards/**` + `output/scorecards/**` + `docs/security/mcp-signing-keys.pub` (via existing `docs/security/** @jrnb2024`) + `.github/workflows/scorecard-aggregator.yml` (via existing `.github/** @jrnb2024`) + `schemas/scorecard-*.schema.json` (via existing `schemas/** @jrnb2024`).
- USER-GATE-D artefact (`docs/gates/USER-GATE-D.md`) signed by @jrnb2024.

**Closure metric:**
WP-SCP-023 closes when Threshold A is reached. Post-Threshold-A backlog is opportunistic (e.g. add per-rule trend graphs to the markdown report; expand to include workflow-selftest results).

## 9. Decisions reserved

| ID | Slice | Topic |
|---|---|---|
| **D-041** | 023B | Cross-repo scorecard data shape (`schemas/scorecard-emit.schema.json` at v0.1) + opt-in adopter participation model. Ratifies invariants 1–4 in code form. |
| **D-042** | 023C | Aggregator pipeline trust model: GitHub Actions Artifact Attestation (OIDC-based) for adopter emits + **mandatory `job_workflow_ref` OIDC claim verification via `gh attestation verify --signer-workflow` bound to the SCP reusable workflow path + SHA pin** (per §5 step 3 non-negotiable constraint; closes 023A R2 MAJ-SAFE-R2-001) + SCP-side Ed25519 key registry for the aggregator-emitted central index (extends WP-SCP-021's `docs/security/mcp-signing-keys.pub`). Ratifies invariants 6–8 in workflow form. |
| **D-043** | 023D | MCP method shape (`scp.consult_scorecard`) + read-only contract + signed-output envelope. Ratifies invariant 5 in MCP-method form. |

**Codex-executor reservation guard.** Per the `docs/DECISIONS.md` header reservation block, Codex executors dispatched for any WP-SCP-023 implementation slice must NOT assign D-041, D-042, or D-043 to any other decision filed during that slice. The reservation pattern mirrors WP-SCP-022's D-021 reservation guard.

## 10. Forward-looking + open questions

These are explicitly OPEN at v0.1 and will be revisited at each implementation slice:

1. **Schema versioning posture for `scorecard-emit.schema.json`** — Resolved at plan-doc level: **MAJOR-pinned per `policies/VERSIONING.md` (D-036)**. Schema breaking changes require a new MAJOR version + one-release deprecation ramp; minor additive fields are MINOR-bump. Codified in D-041's scope.
2. **Per-repo emit cadence** — emit on every PR (proposed in §5 emitter framing) vs only on default-branch pushes? Resolved at plan-doc level: **emit on every PR + default-branch pushes; aggregator reads only the latest-default-branch-run** (per §5 step 2). Slice 023B's D-041 ratifies the implementation shape.
3. **Aggregator scheduling** — Resolved at plan-doc level: **weekly default** (per §5 + §8 Threshold A "≥1 weekly aggregator run"). Operator can manual-trigger ad-hoc via `gh workflow run scorecard-aggregator.yml`. Daily-vs-other-cadences are revisitable in D-042 if estate scale demands.
4. **Markdown report retention** — keep all weekly snapshots in-repo or compact monthly? Likely keep last 90 days + compact older. Resolve at 023D.
5. **MCP method auth posture** — same as WP-SCP-021's other consult methods (Ed25519 receipts) or adjusted? Likely identical. Resolve at 023D.
6. **Threshold A adopter set** — FLA is the canary; the other 2 of 3 should be the most cooperative adopters at the time of 023E. Likely PIM + control-tower. Reaffirm at 023E.
7. **WP-SCP-024 estate-cascade hand-off** — once scorecards exist, WP-SCP-024 (cascade) gains a target metric. Surface this in WP-SCP-024 plan-doc cross-reference.
8. **FLA pilot stability gate** — per `reference_fla_gold_standard.md`, FLA is "still maturing, don't freeze template yet". Slice 023B should NOT freeze any FLA-derived scorecard shape; the schema is data-driven not template-driven. Confirm at 023B kickoff.

---

**Status:** Draft v0.1 — awaiting plan-PR R1+R2 fixpoint + merge.
**Next:** R1 dispatch (3× parallel Sonnet) per DISPATCH-NOTE.
