# Standards Control Plane — System Overview

**Status as of:** 2026-05-25 PM (TF-PIM-001 FINAL CLOSED 2026-05-24 via Path C v2; **PIM (024C) + CT (024D) both LIVE** as cohort adopters #1 + #2; **v1.3.0 CUT 2026-05-25** with SCP-R-007 + SCP-R-008 live + Renovate cascade triggered to PIM + CT; **2 of 5 cohort adopters onboarded**; cascade Threshold A still requires ≥3 of 5 + Renovate cycles + USER-GATE-E)
**Audience:** operators, agent-assisted developers, estate-side maintainers, future-self
**Purpose:** the holistic "what / how / why / where-it's-going" doc. Per-WP architecture notes live alongside this file at `docs/architecture/WP-SCP-NNN-technical-architecture.md`; this is the integrated overview.

---

## 1. What SCP does (in detail)

SCP — **Standards Control Plane** — is the estate's source-of-truth for policy + the mechanism that *enforces* that policy at the only point where enforcement isn't theatre: **the merge gate**.

Concretely it does five things, layered:

### 1.1 Authors policy as code

Three deterministic artefact classes live in this repo:

- **Rules** (`docs/standards/*.md` + `policies/*.rego`) — declarative policy statements like "every reusable workflow with `permissions:` block must enumerate scopes explicitly" (`SCP-R-001`) or "waiver reasons must cite an issue/PR URL" (`SCP-R-004`). Each rule has a stable ID, a baseline threshold (`warn` or `deny`), and a Rego implementation that evaluates against repo state.
- **Decisions** (`docs/DECISIONS.md`, the `D-NNN` table) — non-fungible record of architectural decisions with full rationale prose. D-022 (federation primitive shape), D-035 (adopter-helper invocation procedure), D-044 (cascade scaffolder contract), D-047 (--restore break-glass contract), D-048 (depth-defense surface), etc.
- **Adoption** (`docs/adoption/ADOPT-001-project-onboarding.md`) — operator runbook for onboarding an adopter to the federation primitive, including the §12.8 break-glass procedure (Gate 1 disable / Gate 2 fix / Gate 3 re-enable).

### 1.2 Ships policy as a reusable GitHub Actions workflow

`.github/workflows/policy-check.yml` is the canonical SCP federation primitive — a `workflow_call`-shaped reusable workflow that adopters consume via a thin wrapper:

```yaml
# adopter repo: .github/workflows/policy-check-wrapper.yml
jobs:
  policy-check:
    uses: jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<v1.0.0 SHA>
```

The wrapper SHA-pins to a specific SCP release tag (canonical pin: v1.0.0 @41a5299 per scaffolder constant + STATUS.md TF-023E-002 — v1.0.0 remains the recommended pin until TF-023E-002 closes by restructuring `attest-scorecard` into a separate workflow file). Renovate auto-PRs adopters when SCP cuts a new version, so the cascade is push-based (SCP cuts → Renovate fans out → adopter PR opens automatically → CI verifies the new version doesn't break the adopter).

### 1.3 Enforces policy at the merge gate

Two enforcement primitives compose:

- **Required status check** on the adopter's default branch — `policy-check / scp/policy-check` must pass before merge. Set via `scripts/enable-required-check.sh --repo OWNER/NAME --branch BRANCH`. Operator-bootstrap-only (script refuses `CI=true` / `GITHUB_ACTIONS=true` per D-035).
- **Branch protection** with `enforce_admins=true`, `required-signed-commits`, `tag-protection` on `v*` + `renovate/v*` patterns. The PR can't merge without policy-check green; admins can't bypass; tags can't be force-pushed.

### 1.4 Provides the consult surface for agents

`src/standards_control_plane/mcp_server/` exposes SCP's rules + decisions + scorecards as MCP (Model Context Protocol) tools that agents (Claude Code, ACC orchestrators, Codex executors) call BEFORE writing code:

- `scp.consult_rules(domain)` — agent asks "what rules apply if I'm changing files under X?" before authoring; returns matched rules + Ed25519-signed receipt.
- `scp.consult_scorecard(repo_filter, since)` — agent asks "what's the policy compliance posture across the estate?"; aggregator data via WP-SCP-023.

Receipts are signed with SCP's private Ed25519 key (per D-024); adopter `PreCommit` hooks refuse commit without a valid receipt for any changes in governed domains. **Receipts are short-lived** (TTL ≤ 2h) + scoped to the specific commit (`base_sha + head_sha + changed_files_hash`), so replay across PRs fails.

### 1.5 Aggregates compliance posture across the estate

`scripts/scorecard-aggregator.py` (run via `.github/workflows/scorecard-aggregator.yml` weekly + `workflow_dispatch`) pulls each opt-in adopter's latest `scorecard-emit.json` artefact, verifies the GitHub Actions Artifact Attestation, schema-validates, aggregates into `output/scorecards/index.json`, and opens an operator-review PR. The MCP method `scp.consult_scorecard` exposes this index to agents.

---

## 2. Architecture

### 2.1 Three-layer estate model

SCP is the policy layer of a three-layer model the estate runs on (per `project_scp_control_plane_architecture.md` memory):

```
┌─────────────────────────────────────────────────────────────────┐
│ SCP — policy layer                                              │
│   • Rules + Decisions + Adoption procedures                     │
│   • Reusable workflow (federation primitive)                    │
│   • Required-check enforcement helper                           │
│   • MCP consult surface for agents                              │
│   • Cross-repo scorecards aggregator                            │
└────────────────┬────────────────────────────────────────────────┘
                 │ MCP (stdio + HTTP) — consult tools
                 │ GitHub Actions reusable workflow — gate enforcement
                 │ Renovate preset — adopter pin bumps
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ ACC — orchestration layer                                       │
│   • Multi-agent orchestrator (LangGraph + Claude Agent SDK)     │
│   • Kernel hook (PreToolUse) intercepting code-author tools     │
│   • Dispatcher routing agents through SCP consult before code   │
│   • Live Watch UI (acc.brokapps.ai)                             │
└────────────────┬────────────────────────────────────────────────┘
                 │ ACC kernel hook on adopter repo
                 │ Calls SCP MCP for pre-code consult
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Adopter repos — execution layer                                 │
│   • mapp-pim, control-tower, recommender, mapp-doc-agent,       │
│     shopify-app, FLA (pilot), ...                               │
│   • .github/workflows/policy-check-wrapper.yml (calls SCP)      │
│   • .claude/ hook chain (calls ACC kernel)                      │
│   • CI gate blocks merge on policy-check fail                   │
└─────────────────────────────────────────────────────────────────┘
```

SCP doesn't execute agent work and doesn't orchestrate dispatch — it just provides authoritative policy and gates merge. ACC orchestrates; adopter repos execute.

### 2.2 Where SCP itself lives

- **Repo:** `github.com/jrnb2024/standards-control-plane-` (single GitHub user namespace; bus-factor-1 mode per D-031).
- **Local working tree:** `~/Projects/standards-control-plane`.
- **Branch protection on main:** `policy-check / scp/policy-check` + `check-invocation-log-entry` required; `enforce_admins=true`; required-signed-commits; tag-protection on `v*` + `renovate/v*`.
- **MCP server deployment:** `acc.brokapps.ai` (ACC-hosted; stdio + HTTP transports per D-024).
- **Release cadence:** semver per `policies/VERSIONING.md` (D-036). Cuts at v1.0.0 (2026-04-30), v1.0.1 (2026-05-01 — Python hash-pinning), v1.1.0 (2026-05-02 — SCP-R-004 promotion), v1.2.0 (2026-05-03 — opt-in scorecard-emit).

### 2.3 Per-component homes (top-level dirs)

| Dir | What lives here |
|---|---|
| `.github/workflows/` | `policy-check.yml` (the federation primitive) + 5 sibling workflows (conflict-gate, release-gate, check-invocation-log-entry, r1-evidence-check, scorecard-aggregator) |
| `policies/` | OPA Rego rules + VERSIONING.md (semver contract) + deprecations.yaml |
| `scripts/` | `enable-required-check.sh` (operator-bootstrap branch protection helper) + `scaffold-downstream.sh` (cascade scaffolder) + `check-invocation-log-entry.sh` (CI enforcer) + 30+ sibling utilities |
| `src/standards_control_plane/` | Python package: evaluator, audit CLI, MCP server, schemas |
| `schemas/` | JSON-schemas for policy-check-summary, rule-config, scorecard-emit, scorecard-index |
| `templates/` | `adopter-wrapper.yml.tmpl` (canonical wrapper template) |
| `renovate/` | Renovate shared preset that adopters extend |
| `docs/plans/` | Per-WP implementation programme plans (the source-of-truth for what each WP delivers) |
| `docs/architecture/` | Per-WP technical architecture notes + this overview |
| `docs/adoption/` | `ADOPT-001-project-onboarding.md` operator runbook + break-glass procedure |
| `docs/DECISIONS.md` | Single-table D-NNN decision record (D-001 → D-048) |
| `docs/decisions/` | ADR-style stand-alone decision docs (e.g., `D-SCP-024B-SCOPE-SPLIT-2026-05-09.md`) |
| `docs/reviews/WP-SCP-NNN/` | Adversarial review evidence: per-slice 3-lens R1+R2 JSONs + fix-round audit logs + DISPATCH-NOTEs |
| `docs/reviews/WP-SCP-020/branch-protection-log.md` | Adopter-side branch-protection mutation log (operator-pasted invocation log blocks from `enable-required-check.sh`) |
| `docs/scorecards/` | Cross-repo scorecard reports (markdown + opt-in-registry.yaml) |
| `docs/security/` | Branch-protection spec + MCP signing keys public ring |
| `docs/standards/` | Rule documentation prose (one .md per rule + matrices) |
| `docs/gates/` | USER-GATE-* operator sign-off artefacts |
| `STATUS.md` | Operational state-of-the-world. Always current. Today's chain at the bottom. |
| `tests/` | Python pytest + bash test suites (pytest for evaluator/MCP/scorecards; bash for shell scripts under check_invocation_log/ + scaffolder/) |

---

## 3. How it does its thing — logical flow

Four core flows, traced end-to-end.

### 3.1 PR-on-adopter-repo flow (the merge gate)

When a developer opens a PR on `mapp-pim/mapp-pim` after PIM onboards:

```
1. Developer pushes commit to PR branch
2. GitHub Actions starts the adopter's policy-check-wrapper.yml
3. Wrapper invokes SCP's policy-check.yml@<pinned-SHA>
4. SCP workflow:
   a. checkout adopter repo
   b. install Python deps via hash-pinned requirements
   c. download OPA + Conftest + Regal binaries (SHA256-verified per scp-policy-check.lock)
   d. evaluate Rego rules against adopter file tree
   e. apply waiver overlay (docs/waivers/*.yaml on adopter repo, if any)
   f. emit summary JSON conforming to schemas/policy-check-summary.schema.json
   g. emit OPTIONAL scorecard-emit.json artefact (if wrapper sets scorecard-emit: true)
   h. post scp/policy-check-readback commit status with summary
5. GitHub merge gate: policy-check check-run conclusion = pass/fail
6. If fail: PR can't merge (required status check + enforce_admins=true)
7. If pass: developer self-approves (single-operator) or non-author reviewer approves
8. Merge → squash to main
```

The wrapper job's permissions are `contents:read + statuses:write` only — least-privilege per D-029.

### 3.2 Operator-bootstrap flow (onboarding an adopter)

When the operator onboards a new adopter (e.g., PIM in 024C):

```
1. Operator runs scripts/scaffold-downstream.sh --adopter-repo mapp-pim/mapp-pim \
     --default-branch main --scp-sha <v1.0.0 SHA> --scorecard-emit false \
     --output-dir ~/Projects/scp-scaffolds/024c-pim
   → Emits .github/workflows/policy-check-wrapper.yml + CODEOWNERS snippet
     + CASCADE-PR-BODY.md + MANIFEST.json (SHA256 audit)

2. Operator opens adopter PR on mapp-pim/mapp-pim with the scaffolded artefacts.
   Wrapper SHA-pins to SCP v1.0.0 release tag.

3. Operator (after adopter PR merges) runs:
   scripts/enable-required-check.sh --repo mapp-pim/mapp-pim --branch main --plan
   → dry-run; prints PUT payload + current state. Operator reviews.

4. Operator re-runs without --plan:
   scripts/enable-required-check.sh --repo mapp-pim/mapp-pim --branch main
   → Applies: required-check + enforce_admins + required-PR-reviews + required-signatures
   → Emits invocation log block (operator name, timestamp, script SHA256,
     before/after API JSON)

5. Operator pastes log block into docs/reviews/WP-SCP-020/branch-protection-log.md,
   commits to the SCP-side cascade slice branch.

6. Operator runs the post-merge live-state verification (per 024C R1 SAF-001 closure):
   gh api repos/mapp-pim/mapp-pim/branches/main/protection
   → Confirms canonical context present + enforce_admins=true.
   Pastes the JSON into the cascade-slice DISPATCH-NOTE.

7. Bake observation begins: ≥1 calendar week + ≥1 Renovate-issued SHA pin
   bump cycle merged + observed clean on PIM main.

8. After bake-clean: operator declares cascade-status: onboarded in the
   SCP-side DISPATCH-NOTE, ratifies D-045 (first cascade slice does this),
   SCP-side cascade slice PR moves out of draft + self-merges per D-040.
```

Bootstrap-only at every step: `enable-required-check.sh` refuses `CI=true` / `GITHUB_ACTIONS=true`. No automation writes to adopter repos.

### 3.3 Break-glass flow (rolling back when something goes wrong)

Per ADOPT-001 §12.8 + D-047 + D-048, 3-gate procedure with <30-min SLO (invariant 7):

```
Gate 1 — DISABLE
  scripts/enable-required-check.sh --restore <pre-state.json>
  (pre-state.json = the "Before" JSON captured in the prior invocation log entry)
  → Transforms GET-shape API response into PUT-shape payload, strips envelope
    fields, restores required_signatures via dedicated sub-resource.
  → Posture-degradation acknowledgement flags required if restore removes
    admin enforcement / required-checks / signatures / re-enables force-pushes
    or deletions / disables strict mode / replaces canonical required-check context.
  → Validator (TOP_LEVEL_TOGGLE_KEYS hardening from 024B-extras-3) rejects
    malformed pre-state JSONs at parse time rather than silently dropping fields.

Gate 2 — FIX
  Pin adopter wrapper to a known-good release-tag SHA (operator-chosen or
  Renovate-bumped). Per D-048, --expected-wrapper-sha automated verification
  + annotated-tag dereferencing.

Gate 3 — RE-ENABLE
  scripts/enable-required-check.sh --repo OWNER/NAME --branch BRANCH \
    --expected-wrapper-sha <release-tag-SHA>
  → Validates the supplied SHA against actual git tag refs (annotated-tag
    dereferencing handles single-level indirection).
  → Verifies the adopter wrapper file pins to the same SHA.
  → Re-applies branch protection per the Gate 1 inverse.
  → Logs invocation per D-035.

Permanence: after any break-glass cycle, prior_restore_evidence_present is
true forever for that adopter; all subsequent forward-mode invocations
permanently require --expected-wrapper-sha (or an audited bypass via
--i-understand-no-gate-2-verification).
```

### 3.4 Agent pre-code consult flow (MCP)

Per D-024 + D-025, agents call SCP via MCP **before** authoring code in governed domains:

```
1. Agent (Claude Code in adopter repo, or ACC orchestrator) is about to
   author code under e.g. src/auth/.
2. PreToolUse hook intercepts. Hook reads .claude/scp-config.yaml to resolve
   the agent's MCP transport (stdio vs HTTP).
3. Agent calls scp.consult_rules(domain="auth") via MCP.
4. SCP MCP server:
   a. resolves matching rules from docs/standards/ + policies/
   b. constructs response with rule IDs + thresholds + rationale
   c. constructs receipt envelope (key_id, repo, head_sha, base_sha,
      changed_files_hash, domains_covered, issued_at, expires_at ≤ 2h)
   d. signs receipt with private Ed25519 key
   e. returns rules + signed receipt
5. Agent authors code with rules in context.
6. PreCommit hook validates receipt:
   a. checks signature against public key from docs/security/mcp-signing-keys.pub
   b. checks expires_at not exceeded
   c. checks head_sha matches HEAD
   d. checks changed_files_hash matches actual file changes
   e. if any check fails: refuses commit
7. If valid: commit proceeds; PR opens; merge gate runs (flow 3.1).
```

Break-glass: `SCP_MCP_ALLOW_OFFLINE=true` env var bypasses receipt validation but requires a committed `docs/overrides/OVERRIDE-NNN.md` artefact with schema-validated expiry ≤ 14d. Bypass emits tracked finding `SCP-MCP-E010` so audit shows it.

---

## 4. How SCP interacts with other platform services

### 4.1 ACC (Agent Control Centre) — orchestration runtime

ACC at `~/Projects/acc`, deployed at `acc.brokapps.ai`, is the multi-agent orchestrator (LangGraph + Claude Agent SDK). The interaction is layered:

- **At plan-decompose:** ACC calls `scp.consult_rules` for each work-package slice before dispatching agents. The returned rules feed into the slice's DISPATCH-NOTE scope.
- **At PreToolUse:** ACC's kernel hook (per `feedback_four_tier_dispatch.md` + Phase X work) intercepts every code-author tool call. Hook routes through SCP MCP for receipt validation.
- **At dispatcher-init:** ACC's `install_acc_hook.sh --target-repo PATH` (FUP-ACC-INSTALL-TARGET-REPO-001, closed 2026-05-15) installs the kernel hook into adopter repos. Without per-repo install support, cascade onboarding was blocked — closed via PRs #199 + #202.
- **Cross-repo notification:** SCP cascade slices file announcements at `~/Projects/control-tower/governance/docs/notifications/SCP-*.md` (CT governance log is the cross-repo conversation venue per memory).

### 4.2 Control Tower (CT) — governance + estate operations dashboard

CT at `~/Projects/control-tower`, deployed at `control-tower.brokapps.ai`. Interaction:

- **Governance notifications:** CT hosts the canonical cross-repo conversation log at `governance/docs/notifications/`. SCP files cascade-start + Threshold-A announcements there.
- **Decision coordination:** D-019/D-020/D-021 (Service Auth Contract) used cross-repo `D-NNN` prefixing per `project_d_nnn_prefixing.md`. SCP prefixes its decisions with `SCP D-NNN`; CT prefixes with `CT D-NNN`.
- **Federation primitive:** CT itself is one of the 5 cohort adopters (slice 024D). Once 024C PIM bake-clean closes, CT onboards next.
- **Estate-regression coordination:** `mapp-estate-regression` repo coordinates with both SCP + CT via the same notifications path.

### 4.3 Renovate — version-skew tolerance + cascade propagation

Renovate at the GitHub-app level. Interaction:

- **Shared preset:** `renovate/v*` tag series carries SCP's Renovate shared preset (`renovate/default`). Adopters extend it via `github>jrnb2024/standards-control-plane-//renovate/default#renovate/v1.0.0`. SCP cuts new versions → Renovate auto-PRs adopters within ~24h.
- **Tag protection:** D-030 (v*) + D-034 (renovate/v*) prevent tag force-push, so the trust chain is rooted in immutable tag SHAs.
- **Cascade propagation:** invariant 8 bake observation requires ≥1 Renovate-issued SHA pin bump cycle merged + observed clean per adopter before Threshold A credit. R-024-07 fallback path (operator-driven bump) is acceptable as TEMPORARY unblock but does NOT count toward Threshold A.

### 4.4 GitHub Actions — execution substrate

The federation primitive IS a GitHub Actions reusable workflow. Interaction surfaces:

- **`workflow_call`:** primary integration shape. Adopters wrap; SCP's workflow validates and signals via commit status.
- **Artifact Attestation (OIDC):** per D-041/D-042, opt-in scorecard-emit uses `actions/attest-build-provenance@v4.1.0` (Sigstore/Fulcio) to sign emit artefacts. SCP aggregator verifies via `gh attestation verify --signer-workflow`.
- **Branch protection API:** `enable-required-check.sh` calls `repos/OWNER/NAME/branches/BRANCH/protection` via `gh api`. Per D-035 invocation procedure.

### 4.5 FLA (fashion-labelling-agent) — pilot reference implementation

FLA at `~/Projects/fashion-labelling-agent` is the executable gold-standard reference for the cascade pattern. Per invariant 4: cascade slices are **FLA-independent** — FLA pilot continues on its own track (`WP-SCP-020.1`). FLA pilot safety findings are reviewed per-cascade-slice DISPATCH-NOTE (plan-doc §5.2 item 5).

### 4.6 PIM / recommender / shopify-app / mapp-doc-agent — cohort adopters

The 5 cohort adopters per D-035 enumeration. Sequenced canary-first per §5.1 (PIM → CT → mapp-doc-agent + recommender paired → shopify-app). Each adopter:

- Wrapper file at `.github/workflows/policy-check-wrapper.yml` (SHA-pinned to SCP release tag, Renovate-bumped)
- Required status check `policy-check / scp/policy-check` on default branch
- Invocation log entry under SCP's `docs/reviews/WP-SCP-020/branch-protection-log.md`
- Per-slice DISPATCH-NOTE with `cascade-status:` declared at close

---

## 5. Current scope

### 5.1 Shipped + dogfooded (✅)

| Work-package | Delivered | Notes |
|---|---|---|
| WP-SCP-001 → 018 | Foundation: evaluator, audit CLI, schemas, rule catalogue, finding lifecycle, waivers, scorecards (Phase 1) | Closed pre-2026-04-18 |
| WP-SCP-019 (Service Auth Contract) | SVC-003 closed-mode-set authentication (user_oidc / service_rs256 / api_key / bearer_legacy) | Closed 2026-04-20 |
| WP-SCP-020 (Policy Federation Primitive) | Reusable workflow + OPA/Conftest + Renovate preset + required status check, GA v1.0.0 | Closed 2026-04-30 |
| WP-SCP-020.1 (FLA pilot) | First real-repo adopter (separate track per invariant 4) | Ongoing canary |
| WP-SCP-021 (MCP Server) | Ed25519-signed receipts + scoped pre-code consult; stdio + HTTP transports | v0.3 fixpoint 2026-04-29 |
| WP-SCP-022 (Implementation Programme) | Four-tier dispatch + R-cycle + Threshold A | Closed 2026-04-30 |
| WP-SCP-023 (Cross-repo Scorecards) | Aggregator pipeline + per-emit verification + MCP exposure | Closed Threshold A 2026-05-03 |
| WP-SCP-024 024A | Estate cascade plan-doc v0.1 | Merged PR #102 2026-05-04 |
| WP-SCP-024 024B-core | Scaffolder + adopter wrapper template + cascade-status CI enforcement | Merged 2026-05-09 |
| WP-SCP-024 024B-extras-1 | --restore mode + ADOPT-001 §12.8 break-glass + CI workflow wiring | Merged PR #113 2026-05-12 |
| WP-SCP-024 024B-extras-2 | Depth-defense surface (wrapper-SHA verification + canonical-context guard + set-equality verify + transform inclusion lists + audited bypass flags) | Merged PR #114 2026-05-13 |
| WP-SCP-024 024B-extras-3 | TOP_LEVEL_TOGGLE_KEYS validator hardening + workflow base-branch pin | Merged PR #116 2026-05-14 |
| TF-PIM-001 (cross-repo checkout auth — Path C v2) | GitHub App credential surface (App ID 3795720); D-050 ACCEPTED; ADOPT-001 §12.7.5/§12.7.10/§12.7.13/§12.7.16 amended; `actions/create-github-app-token` PRIMARY + `tibdex/github-app-token` FALLBACK; adopter wrapper `secrets: inherit` axis G Option α; `inputs.scp-sha` REQUIRED axis I; `selftest-mode` input cleanup-2 | **CLOSED 2026-05-24** (Path C v2 ratified PR #143; Waves D'.1/D'.2/G v2/H shipped PRs #145/#146/#280/#147; cleanup-1/2 PRs #149/#150) |
| WP-SCP-024 024C (PIM canary cascade) | PIM `policy-check / scp/policy-check` LIVE on PIM main (required-check restored via `--preserve-existing-contexts` alongside 4 pre-existing checks); first-try GREEN on cross-repo App-token-exchange | **CLOSED 2026-05-24** PR #147 |

### 5.2 In flight

| Slice | State |
|---|---|
| **WP-SCP-025 Phase 1 (2 domain rules)** | plan-doc + rule-RFC authoring + Rego impl; halt at first Codex-Tier-2 fire (if any) per four-tier dispatch pattern |
| **SCP-self wrapper bump (FUP-CLEANUP-2-001)** | pin to post-Wave-D'.1 SHA; add `selftest-mode: true` + caller-job `attestations: write + id-token: write` (post axis F closure) |
| **PR #148 (D-036 + RULE-003 ACC-as-cross-repo-caller)** | rule-RFC + ADR; HARD DEP for ACC EST-P WS-EST-P-2; PR body invites operator-requested R3 multi-agent review before merge |

### 5.3 Pending downstream

| Slice | Blocker |
|---|---|
| 024D (control-tower) | Operator-attended branch-protection mutation on `mapp/control-tower`; scaffolder output can be authored autonomously |
| 024E (mapp-doc-agent + recommender paired) | 024D bake-clean |
| 024F (shopify-app) | 024E bake-clean |
| 024G (Threshold A + USER-GATE-E + D-046) | ≥3 of 5 cohort adopters onboarded + each survived ≥1 Renovate cycle |

### 5.4 What "operationally usable across estate" means

Currently: SCP-self + **PIM** (cohort adopter #1, LIVE since 2026-05-24). Operationally usable across estate = Threshold A signed (≥3 of 5 + Renovate cycles clean + USER-GATE-E). Calendar estimate: ~3-6 weeks from CT onboarding kickoff (multi-week per slice by design, mostly bake observation; engineering is days, not weeks).

### 5.5 What the gate actually catches today (honest)

Across the 4 live rules (`SCP-R-001`/`002`/`003`/`004`), most adopter PRs touch none of the governed surfaces, so the gate runs in ~25-33s and resolves to GREEN-by-default. The 4 rules:

- `SCP-R-001` (services.yml auth-mode enumeration) — fires only on `services.yml` changes
- `SCP-R-002` (waiver schema completeness) — fires only on waiver-file changes
- `SCP-R-003` (dep manifest attestation marker) — fires on `package.json`/`pyproject.toml`/`go.mod` changes
- `SCP-R-004` (waiver `reason` must cite URL) — **warn baseline only; never blocks merge**

The 6 SDK-discipline rules originally framed as Wave-1 CT gates were **retired 2026-05-09** (parked under WP-SCP-025; see STATUS.md `Today's chain (2026-05-09 — D-035-rules retired + WP-SCP-025 parked)`). RULE-002 (D-049 design-system policy-layer adoption / proposed `SCP-R-005`) is filed as proposal docs but the Rego file does not exist yet — implementation slice deferred. RULE-003 (D-036 ACC-as-cross-repo-caller / proposed `SCP-R-006`) is open as PR #148 awaiting operator-merge ceremony.

Translation: the federation primitive plumbing is **mature and working**, but the **policy substance is thin**. The next inflection point is WP-SCP-025 Phase 1 — pick + ship 2 domain rules that actually catch real defects on representative adopter PRs.

---

## 6. Future scope

Five categories of work beyond Threshold A.

### 6.1 Cohort completion + maintenance

After Threshold A (24G + USER-GATE-E), maintenance posture per D-046:

- Recurring Renovate-driven SHA pin bumps; each version cut auto-cascades within ~24h
- Departing-adopter procedure (rare; covered by invariant 7 rollback)
- Opportunistic onboarding of additional non-cohort adopters as they emerge
- Bus-factor-1 quarterly review (2026-07-21 named; 2026-10-21 next)

### 6.2 Policy expansion

The federation primitive carries any policy expressible in OPA Rego against repo state. Real candidates beyond current rules:

- **Architecture conformance** — extend WP-SCP-008 evaluator to assert ports/adapters discipline, dependency-direction invariants, layered-architecture rules
- **Service-contract conformance** — every service exports an OpenAPI / Avro / Proto contract committed to the repo; SCP rule asserts that contract changes are versioned + deprecation-ramped
- **Test-coverage thresholds** — per-domain coverage floors; deny PRs that drop coverage below baseline without a waiver
- **Dependency hygiene** — deny PRs adding deps from non-allowlisted registries; require SBOM attestation
- **Secret-scope discipline** — workflow `permissions:` blocks must follow least-privilege; deny `permissions: write-all`
- **Authentication-claim conformance** — services consuming SVC-003 must declare their mode + the auth-contract version they implement
- **DPBM (Design Parity Build Method)** — D-028 / ADR-016 estate doctrine for designed visual output; SCP rule enforces presence of design-artefact references in PRs touching frontend code

Each new rule follows the rule-RFC process (D-036): `docs/reviews/rule-proposals/PROP-NNN.md` + quorum review + 48h ceiling.

### 6.3 Tighter agent integration

- **WP-SCP-025** (proposal queue) — formal `propose()` MCP method + adjudication workflow per D-023 (multi-agent coordination via structured queue, not free-form chat)
- **Pre-code consult mandatory in more domains** — current `domain-map` covers auth, schemas, governance. Extend to architecture, contracts, deployment manifests
- **Live-policy injection** — agents called with up-to-date rule context at dispatch-time (currently consulted on-demand)
- **Receipt validation on more tools** — currently `PreCommit`; extend to `PrePush`, `PrePR`, `PreDeploy`

### 6.4 Estate observability

- **Real-time scorecard dashboard** — current aggregator runs weekly cron; future ambition is continuous (event-driven on adopter `workflow_run` completion)
- **Drift-detection alerts** — when an adopter's posture deviates (waivers expiring, rules disabled, SHA pin stuck) operator gets pinged via CT governance log
- **Quarterly compliance reports** — auto-generated markdown + executive summary across cohort
- **Adopter contribution surface** — adopters can propose rules via PR; SCP runs them in `warn` mode for ≥1 release before flipping to `deny`

### 6.5 Estate-wide architectural governance

The bigger ambition (beyond Threshold A) is for SCP to become the place where **estate-wide architectural decisions are codified + enforced**. Examples:

- **Layered architecture invariants** — services must respect dependency direction (e.g., domain layer can't import from infra layer)
- **Cross-service contract gates** — breaking changes to public service contracts require synchronised PRs across consumers + producers
- **Estate version coordination** — when a shared dependency (CT-AUTH, ACC kernel, MCP SDK) version-bumps, SCP gates the rollout across the cohort
- **Compliance attestation** — for regulated work (data residency, retention, audit), SCP attests via signed receipts that PRs comply with relevant standards
- **Onboarding new estate domains** — beyond the current 5 cohort + FLA, formal procedure for "new adopter joining the federation" (cost estimate, technical fit, governance acceptance)

These are not implementation commitments — they're the direction-of-travel that the federation primitive enables. Each becomes a future WP-SCP-NNN with plan-doc + slice plan + Threshold criteria.

---

## 7. Pointers for further reading

| Topic | Primary source |
|---|---|
| Per-WP architecture details | `docs/architecture/WP-SCP-NNN-technical-architecture.md` (one per WP) |
| Per-WP implementation plan | `docs/plans/WP-SCP-NNN-*.md` |
| Decision history | `docs/DECISIONS.md` (single-table) + `docs/decisions/D-*.md` (standalone ADRs) |
| Adoption procedure | `docs/adoption/ADOPT-001-project-onboarding.md` |
| Operational state | `STATUS.md` (header `Last updated:` + bottom chain entries) |
| Adversarial review evidence | `docs/reviews/WP-SCP-NNN/<slice>/r{1,2,...}-*.json` |
| Adopter-side branch protection mutations | `docs/reviews/WP-SCP-020/branch-protection-log.md` |
| Cross-repo notifications (cascade announcements) | `~/Projects/control-tower/governance/docs/notifications/SCP-*.md` |
| Estate-wide architecture (3-layer model) | this file §2 |

---

## Maintenance

This doc is the integrated overview; the per-WP architecture/plan/decision docs remain source-of-truth for their subjects. Update this file when:

- A new top-level WP closes (add to §5.1; update the three-layer diagram if architecture shifts)
- A new integration surface lands (add to §4)
- The 3-layer model amends (rare; rewrite §2)
- Cascade Threshold A is reached (update §5.4 + §6 priorities shift)
