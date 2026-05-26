# Standards Control Plane

**The policy layer for an agent-assisted software estate.** SCP authors the rules, ships them as a reusable workflow that gates every merge, and gives agents a signed consult surface to read those rules *before* they write code.

This page is the canonical introduction to what SCP is, why it exists, how it works, where it fits, and where it's going.

---

## 1. Why this exists

Building software with agents at estate scale changes the failure mode.

When a single team uses an agent to write a feature, the human reviewer is the gate. They read the diff, smell the structure, push back, merge. The agent is fast; the human is the brake. The estate stays coherent because every change still passes through a person who carries the architectural intent in their head.

That breaks down when:

- **There are five or ten repos in the estate** and the agents-per-repo ratio climbs faster than the humans-per-repo ratio.
- **The agent in repo A doesn't know what repo B decided last week.** Decisions don't propagate. The same architectural question gets re-answered differently every time it's asked.
- **Conventions are written down but not enforced.** A `CONVENTIONS.md` that says "all services must expose `/health` returning the SVC-002 shape" works until somebody (human or agent) doesn't read it. Then there's drift, and the drift compounds across the estate.
- **Review velocity drops below merge velocity.** Agents author faster than humans can adversarially review. Either reviewers become rubber stamps, or merges queue up and the agent's speed advantage evaporates.

The temptation is to write more conventions. Longer style guides. More CLAUDE.md files. Bigger PR templates. None of that helps — convention is *a thing humans agree to follow*; it has no machine teeth. Once the agent is the primary author and the human is the reviewer, the agent needs to be reading the rules and the merge gate needs to be enforcing them. Documents alone don't get you there.

**SCP exists to put teeth on the rules.** It does three things, layered:

1. It is the **source of truth for policy** — declarative rules with stable IDs, evaluated by OPA against repo state, plus an architectural decision record (D-001 through D-048 and counting).
2. It ships those rules as a **reusable GitHub Actions workflow** that adopter repos consume by SHA-pinned wrapper. The workflow runs on every PR; its result becomes a required status check; the merge button greys out if the workflow fails. Convention becomes machinery.
3. It exposes the same rules as an **MCP server** so agents can call `scp.consult_rules(domain="auth")` before authoring code under `src/auth/`. The agent gets back plain JSON (`ConsultRulesResponse`). Receipt-signing + adopter PreCommit-hook validation were retracted to §6.3 future-scope per D-054 + D-055 (2026-05-25 / 2026-05-26); WP-SCP-027 will ship that capability on operator-attended demand signal. Today, enforcement is rooted at the merge gate, not pre-commit.

The federation primitive (point 2) is the load-bearing part. Everything else either feeds it, or sits beside it on the same trust chain. If you only remember one thing about SCP it should be: **adopters install a thin wrapper that calls a SCP-owned workflow, SCP cuts releases, Renovate cascades the version bumps, and merge is gated on the workflow passing.**

## 2. What it actually is

A single GitHub repository — `github.com/jrnb2024/standards-control-plane-` — that contains:

- A library of OPA Rego rules and their prose documentation
- A reusable GitHub Actions workflow that evaluates those rules against any caller repo
- A Python package providing a CLI, an HTTP service, and an MCP server
- A scaffolder that emits the integration files for new adopter repos
- An operator-side branch-protection helper that turns on the required-check on adopter repos
- An invocation log recording every branch-protection mutation across the estate
- A complete decision record (`docs/DECISIONS.md`) explaining why every architectural choice was made

The package is small and deliberately unambitious in surface area. SCP does policy and gates merge. It does not orchestrate dispatch (that's [ACC](#43-acc-the-agent-orchestrator)), it does not own governance dashboards (that's [Control Tower](#44-control-tower-governance-and-estate-operations)), it does not retrieve historical context (that's mapp-doc-agent). The boundary is intentional: SCP is the policy layer, not the platform.

## 3. How SCP solves the problem

Three primitives, composed:

### 3.1 Policy as code

Policy lives in three deterministic artefact classes:

| Class | Lives in | Example |
|---|---|---|
| **Rules** | `policies/*.rego` + `docs/standards/*.md` | `SCP-R-001` — every reusable workflow with a `permissions:` block must enumerate scopes explicitly |
| **Decisions** | `docs/DECISIONS.md` (single table) + `docs/decisions/*.md` (standalone ADRs) | `D-022` — adopt the federation-primitive shape (workflow_call + SHA-pinned wrapper). `D-033` — single-operator mode for the SCP self-dogfood. `D-048` — depth-defense surface for break-glass |
| **Adoption** | `docs/adoption/ADOPT-001-project-onboarding.md` | The repo-onboarding brief: how to write your wrapper, configure branch protection, run break-glass, file FUPs |

Rules are short, machine-evaluable, and individually versionable. They get IDs (`SCP-R-NNN`), thresholds (`warn` or `deny`), and Rego implementations. New rules go through a `rule-RFC` process (D-036) with a 48h ceiling and adversarial review before they ship.

Decisions are the *why*. They're prose — multi-paragraph, with rationale and trade-offs. They get IDs (`D-NNN`), dates, status (`ACCEPTED` / `REVISED` / `RETIRED`), and a cross-link to the work-package that produced them.

### 3.2 The federation primitive

`.github/workflows/policy-check.yml` is a `workflow_call`-shaped reusable workflow. Adopter repos consume it via a four-line wrapper:

```yaml
# adopter repo: .github/workflows/policy-check-wrapper.yml
jobs:
  policy-check:
    uses: jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<v1.0.0 SHA>
    with:
      rule-set: starter
      threshold: deny
```

The wrapper SHA-pins the workflow to a specific SCP release tag (canonical: `v1.0.0 @ 41a5299`). Renovate watches SCP for new versions and opens auto-PRs against each adopter to bump the pin within ~24h of a SCP release.

When a developer pushes a commit to a PR branch on an adopter repo, the wrapper fires. It calls SCP's workflow, which checks out the adopter repo, downloads SHA256-verified OPA/Conftest/Regal binaries, evaluates the rules against the adopter's file tree, applies waiver overlays if any, and emits a structured summary plus a check-run conclusion. That conclusion shows up as `policy-check / scp/policy-check` on the PR. If it's red, merge is blocked.

Adopters that want stricter posture set their branch protection to require the check via `scripts/enable-required-check.sh`. This is the load-bearing operator step — it turns *advisory* (workflow runs, result visible) into *enforcing* (workflow result blocks merge). It's deliberately operator-attended; the script refuses to run when `CI=true`.

### 3.3 Pre-code consult surface

`src/standards_control_plane/mcp_server/` is an MCP (Model Context Protocol) server. Agents — Claude Code in adopter repos, ACC orchestrators, Codex executors — call it before they write code in governed domains.

```
agent: scp.consult_rules(domain="auth")
       (via scp-cli consult --domain auth, WP-SCP-026 026B)
SCP:   returns matched rules as plain JSON (ConsultRulesResponse)
agent: writes code with rules in context
gate:  the federation primitive's required check at merge time
       (policy-check / scp/policy-check) is the load-bearing
       enforcement boundary
```

Per D-054 + D-055 (2026-05-25 / 2026-05-26), receipt-signing + adopter PreCommit-hook validation were retracted to `docs/OVERVIEW.md` §6.3 future-scope. Today's consult responses are unsigned JSON; enforcement is rooted at the federation-primitive merge gate, not at pre-commit. The receipt-signing capability — Ed25519 signature scoped to `base_sha + head_sha + changed_files_hash` with TTL ≤ 2h + adopter PreCommit-validator + `SCP_MCP_ALLOW_OFFLINE=true` break-glass + `SCP-MCP-E010` finding on bypass — moves to **WP-SCP-027** with an operator-attended demand-signal trigger. See OVERVIEW.md §6.3 for the full forward-scope.

---

## 4. Architecture

### 4.1 The three-layer estate model

SCP is the **policy** layer of a three-layer architecture the estate runs on:

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
│     shopify-app, FLA (pilot), …                                 │
│   • .github/workflows/policy-check-wrapper.yml (calls SCP)      │
│   • .claude/ hook chain (calls ACC kernel)                      │
│   • CI gate blocks merge on policy-check fail                   │
└─────────────────────────────────────────────────────────────────┘
```

SCP doesn't execute agent work and doesn't orchestrate dispatch — it provides authoritative policy and gates merge. ACC orchestrates; adopter repos execute. The boundaries are clean by design: SCP changes only when policy changes; ACC changes when orchestration changes; adopter repos change when application code changes.

### 4.2 Where SCP itself lives

| Surface | Address |
|---|---|
| Source repo | `github.com/jrnb2024/standards-control-plane-` |
| Working tree | `~/Projects/standards-control-plane` |
| Service (shared) | `https://scp.brokapps.ai` (port 3787 backend) |
| Service (dev tunnel) | `https://scp-dev.brokapps.ai` |
| MCP server | `scp-mcp-server` CLI; **stdio transport only** (zero adopter consumers as of 2026-05-26). HTTP transport + `acc.brokapps.ai` MCP-hosting claim retracted per D-054 + D-055; deferred to WP-SCP-027 future-scope. `acc.brokapps.ai` is ACC's orchestrator UI, not SCP's MCP. |
| Branch protection on `main` | `policy-check / scp/policy-check` + `check-invocation-log-entry` required; `enforce_admins=true`; required-signed-commits; tag-protection on `v*` + `renovate/v*` |
| Release cadence | semver per `policies/VERSIONING.md` (D-036). Cuts at v1.0.0 (2026-04-30), v1.0.1 (2026-05-01), v1.1.0 (2026-05-02), v1.2.0 (2026-05-03) |

### 4.3 Top-level directories

| Directory | What lives there |
|---|---|
| `.github/workflows/` | `policy-check.yml` (the federation primitive) + 5 sibling workflows: conflict-gate, release-gate, check-invocation-log-entry, r1-evidence-check, scorecard-aggregator |
| `policies/` | OPA Rego rules + `VERSIONING.md` (semver contract) + `deprecations.yaml` |
| `scripts/` | `enable-required-check.sh` (branch-protection helper) + `scaffold-downstream.sh` (cascade scaffolder) + `check-invocation-log-entry.sh` (CI enforcer) + ~30 utilities |
| `src/standards_control_plane/` | Python package: evaluator, audit CLI, MCP server, FastAPI service, schemas |
| `schemas/` | JSON schemas for policy-check-summary, rule-config, scorecard-emit, scorecard-index |
| `templates/` | `adopter-wrapper.yml.tmpl` — canonical wrapper template the scaffolder fills in |
| `renovate/` | Renovate shared preset adopters extend via `github>jrnb2024/standards-control-plane-//renovate/default#renovate/v1.0.0` |
| `docs/plans/WP-SCP-NNN-*.md` | Per-work-package implementation plans (source of truth for what each WP delivers) |
| `docs/architecture/WP-SCP-NNN-*.md` | Per-WP technical architecture notes |
| `docs/adoption/ADOPT-001-project-onboarding.md` | The repo-onboarding brief (deep integration guide) |
| `docs/DECISIONS.md` | The decision record — every architectural choice in one table |
| `docs/reviews/WP-SCP-NNN/` | Adversarial review evidence: per-slice 3-lens R1+R2 JSONs + fix-round audit logs + DISPATCH-NOTEs |
| `docs/reviews/WP-SCP-020/branch-protection-log.md` | Adopter-side branch-protection mutation log (operator-pasted invocation log blocks) |
| `docs/security/` | Branch-protection spec + MCP signing keys public ring |
| `docs/standards/` | Rule documentation prose (one `.md` per rule + matrices) |
| `STATUS.md` | Always-current operational state. Today's chain at the bottom |
| `tests/` | pytest + bash test suites (pytest for evaluator/MCP/scorecards; bash for shell scripts) |

---

## 5. How it works — the four logical flows

Most of what SCP does happens at one of four flow boundaries. Tracing each end-to-end is the fastest way to understand the system.

### 5.1 The merge-gate flow

A developer opens a PR on an onboarded adopter repo. What happens:

```
1. Developer pushes commit to PR branch
2. GitHub Actions starts the adopter's policy-check-wrapper.yml
3. Wrapper invokes SCP's policy-check.yml@<pinned-SHA>
4. SCP workflow:
   a. checkout adopter repo at PR head
   b. install Python deps via hash-pinned requirements
   c. download OPA + Conftest + Regal binaries
      (SHA256-verified per scripts/scp-policy-check.lock)
   d. evaluate Rego rules against adopter file tree
   e. apply waiver overlay (docs/waivers/*.yaml on adopter, if any)
   f. emit summary JSON conforming to
      schemas/policy-check-summary.schema.json
   g. emit OPTIONAL scorecard-emit.json artefact
      (if wrapper sets scorecard-emit: true)
   h. post scp/policy-check-readback commit status with summary
5. GitHub merge gate: policy-check check-run conclusion = pass/fail
6. If fail: PR can't merge (required status check + enforce_admins=true)
7. If pass: developer self-approves (single-operator mode per D-033)
            OR non-author CODEOWNER reviewer approves (multi-maintainer mode)
8. Merge → squash to main
```

The wrapper job's permissions are deliberately minimal: `contents:read + statuses:write`. Least-privilege per D-029 — even if the workflow were compromised, the blast radius is bounded.

### 5.2 The bootstrap flow

How an operator onboards a new adopter repo:

```
1. Operator runs the scaffolder from the SCP repo:
   scripts/scaffold-downstream.sh \
     --adopter-repo OWNER/REPO --default-branch main \
     --scp-sha <v1.0.0 SHA> --scorecard-emit false \
     --output-dir ~/Projects/scp-scaffolds/<slice-name>
   → Emits policy-check-wrapper.yml + CODEOWNERS snippet
     + CASCADE-PR-BODY.md + MANIFEST.json (SHA256 audit)

2. Operator opens adopter PR on the adopter repo with the scaffolded
   artefacts. Wrapper SHA-pins to the SCP release tag.

3. After adopter PR merges, operator runs:
   scripts/enable-required-check.sh --repo OWNER/REPO --branch main --plan
   → dry-run; prints PUT payload + current branch-protection state.
     Operator reviews.

4. Operator re-runs without --plan (brownfield adopters add
   --preserve-existing-contexts):
   scripts/enable-required-check.sh --repo OWNER/REPO --branch main \
     --preserve-existing-contexts
   → applies required-check + enforce_admins + required-signatures
   → emits invocation log block (operator name, timestamp,
     script SHA256, before/after API JSON, structured flag values)

5. Operator pastes the log block into
   docs/reviews/WP-SCP-020/branch-protection-log.md,
   commits to the SCP-side cascade slice branch.

6. Operator runs the post-merge live-state verification
   (per 024C R1 SAF-001 closure):
   gh api repos/OWNER/REPO/branches/main/protection
   → Confirms canonical context present + enforce_admins=true
     + required_signatures=true.
   Pastes the JSON into the cascade-slice DISPATCH-NOTE.

7. Bake observation begins: ≥1 calendar week + ≥1 Renovate-issued
   SHA pin bump cycle merged + observed clean on adopter main.

8. After bake-clean: operator declares cascade-status: onboarded in
   the SCP-side DISPATCH-NOTE, ratifies the per-slice D-NNN row, the
   slice PR self-merges per D-040.
```

Bootstrap-only at every step. `enable-required-check.sh` refuses `CI=true`. No automation writes to adopter repos — every mutation is operator-attended and logged.

### 5.3 The break-glass flow

What you do when something goes wrong — a bad SCP release ships, an adopter's CI is broken, a deploy needs to happen *now*. Per ADOPT-001 §12.8 + D-047 + D-048, three gates with a <30-minute SLO:

```
Gate 1 — DISABLE
  scripts/enable-required-check.sh --restore <pre-state.json>
  (pre-state.json = the "Before" JSON captured in the prior
   invocation log entry — i.e. the audit trail's own evidence
   becomes the restore input.)
  → Transforms GET-shape API response into PUT-shape payload, strips
    envelope fields, restores required_signatures via the dedicated
    sub-resource.
  → Posture-degradation acknowledgement flags required if the restore
    removes admin enforcement / required-checks / signatures / re-enables
    force-pushes or deletions / disables strict mode / replaces the
    canonical required-check context.
  → Validator (TOP_LEVEL_TOGGLE_KEYS hardening from 024B-extras-3)
    rejects malformed pre-state JSONs at parse time rather than
    silently dropping fields.

Gate 2 — FIX
  Pin adopter wrapper to a known-good release-tag SHA (operator-chosen
  or Renovate-bumped). Per D-048, --expected-wrapper-sha automated
  verification + annotated-tag dereferencing.

Gate 3 — RE-ENABLE
  scripts/enable-required-check.sh --repo OWNER/REPO --branch BRANCH \
    --expected-wrapper-sha <release-tag-SHA>
  → Validates the supplied SHA against actual git tag refs
    (annotated-tag dereferencing handles single-level indirection).
  → Verifies the adopter wrapper file pins to the same SHA.
  → Re-applies branch protection per the Gate 1 inverse.
  → Logs invocation per D-035.
```

Permanence: after any break-glass cycle, `prior_restore_evidence_present` is true forever for that adopter. All subsequent forward-mode invocations permanently require `--expected-wrapper-sha` (or an audited bypass via `--i-understand-no-gate-2-verification`). The audit trail can't be cleared; the safety constraint can only escalate, never relax.

### 5.4 The MCP consult flow

How an agent reads policy before authoring code. Per D-024 + D-025 + D-054 + D-055:

```
1. Agent (Claude Code in an adopter repo, or an ACC orchestrator) is
   about to author code under e.g. src/auth/.
2. Agent invokes `scp-cli consult --domain auth` (WP-SCP-026 026B) or
   calls `scp.consult_rules` directly over stdio MCP if the per-repo
   MCP server proxies the tool.
3. SCP MCP server:
   a. resolves matching rules from docs/standards/ + policies/
   b. constructs ConsultRulesResponse payload: rule IDs + thresholds +
      rationale + applicable_rules / approved_patterns / open_findings /
      historical_reviews / guidance / risks / confidence /
      confidence_class / schema_version
   c. returns plain JSON to the caller. No signature today.
4. Agent authors code with rules in context.
5. Commit proceeds; PR opens; merge gate runs (flow 5.1) — the
   federation primitive's required check is the load-bearing
   enforcement boundary, not pre-commit receipt validation.
```

**Receipt-signing + PreCommit-hook validation status:** retracted to §6.3 future-scope per D-054 + D-055. The receipt-signing capability — Ed25519 signature scoped to `base_sha + head_sha + changed_files_hash` with TTL ≤ 2h + adopter PreCommit-validator + `SCP_MCP_ALLOW_OFFLINE=true` break-glass + `SCP-MCP-E010` finding on bypass — moves to WP-SCP-027 with an operator-attended demand-signal trigger. See OVERVIEW.md §6.3.

Two enforcement gates today:

- Skip-consult agents are NOT gated at commit time today (no receipt validation). If WP-SCP-027 ships, PreCommit will enforce. WP-SCP-027 fires only on explicit operator-attended demand signal at WP-SCP-026 026F close-out per D-054; absence of a signal is a valid outcome and WP-SCP-027 may be held indefinitely.
- Drift-from-consulted-rules agents fail at merge time (rules consulted, rules violated). The break-glass for that is the `scp_bypass: true` three-gate model — CODEOWNER review + sibling `D-NNN` row + matching waiver entry, all in the same PR.

---

## 6. How it integrates

SCP only matters in proportion to what it's wired into. The integration surfaces fall into five buckets.

### 6.1 GitHub Actions — execution substrate

The federation primitive *is* a reusable GitHub Actions workflow. Three integration surfaces:

| Surface | What it does |
|---|---|
| `workflow_call` | Primary integration shape. Adopters wrap; SCP's workflow validates and signals via commit status |
| Artifact Attestation (OIDC) | Per D-041/D-042, opt-in scorecard-emit uses `actions/attest-build-provenance@v4.1.0` (Sigstore/Fulcio) to sign emit artefacts. SCP aggregator verifies via `gh attestation verify --signer-workflow` |
| Branch protection API | `enable-required-check.sh` calls `repos/OWNER/NAME/branches/BRANCH/protection` via `gh api` per the D-035 invocation procedure |

### 6.2 Renovate — version-skew tolerance + cascade propagation

Renovate is the GitHub app that handles version cascades:

- **Shared preset.** The `renovate/v*` tag series carries SCP's shared Renovate preset (`renovate/default`). Adopters extend it via `github>jrnb2024/standards-control-plane-//renovate/default#renovate/v1.0.0`. When SCP cuts a new version, Renovate auto-PRs each adopter within ~24h.
- **Tag protection.** D-030 (`v*`) + D-034 (`renovate/v*`) prevent tag force-push. The trust chain is rooted in immutable tag SHAs.
- **Cascade propagation.** WP-SCP-024 invariant 8: bake observation requires ≥1 Renovate-issued SHA pin bump cycle merged + observed clean per adopter before Threshold A credit. The R-024-07 fallback (operator-driven bump) unblocks but does NOT count toward Threshold A — the cascade has to demonstrate the push-based propagation actually works.

### 6.3 ACC — the agent orchestrator

ACC (`~/Projects/acc`, deployed at `acc.brokapps.ai`) is the multi-agent orchestrator. It connects to SCP at three layers:

- **At plan-decompose:** ACC calls `scp.consult_rules` for each work-package slice before dispatching agents. The returned rules feed into the slice's DISPATCH-NOTE scope.
- **At PreToolUse:** ACC's kernel hook intercepts every code-author tool call. The hook routes through SCP MCP for pre-code consult (plain JSON; no receipt validation per D-054 + D-055).
- **At dispatcher-init:** ACC's `install_acc_hook.sh --target-repo PATH` installs the kernel hook into adopter repos (FUP-ACC-INSTALL-TARGET-REPO-001 closed 2026-05-15 via ACC PRs #199 + #202).

Cross-repo notifications between SCP and ACC are filed at `~/Projects/control-tower/governance/docs/notifications/SCP-*.md`. CT's governance log is the canonical cross-repo conversation venue.

### 6.4 Control Tower — governance and estate operations

CT (`~/Projects/control-tower`, deployed at `control-tower.brokapps.ai`) is the governance and dashboarding layer. SCP connects:

| Surface | Notes |
|---|---|
| Governance notifications | CT hosts the cross-repo conversation log at `governance/docs/notifications/`. SCP files cascade-start + Threshold-A announcements there |
| Decision coordination | D-019/D-020/D-021 (Service Auth Contract) used cross-repo `D-NNN` prefixing per `project_d_nnn_prefixing.md`. SCP prefixes its decisions `SCP D-NNN`; CT prefixes `CT D-NNN` |
| Federation primitive | CT itself is one of the 5 cohort adopters (slice 024D). Once 024C PIM bake-clean closes, CT onboards next |
| Auth | SCP-the-service uses CT's OIDC for browser auth (`CT_APP_ID=scp` for shared, `scp-dev` for the dev tunnel) |

### 6.5 The cohort adopters

Five repos are sequenced for cascade onboarding per WP-SCP-024 §5.1 canary-first ordering:

1. **PIM** (`jrnb2024/mapp-pim`) — canary, smallest blast radius (onboarded 2026-05-17 at ceremony level; bake observation pending)
2. **Control Tower** (`jrnb2024/control-tower`) — high-traffic flagship; queued for 024D after PIM bake-clean
3. **mapp-doc-agent** + **recommender** (paired) — 024E
4. **shopify-app** — 024F
5. (FLA pilot runs separately on its own track per invariant 4 — `WP-SCP-020.1`. FLA pilot safety findings get reviewed in every cascade slice's DISPATCH-NOTE but the pilot doesn't gate the cascade.)

Each adopter, once onboarded, has:

- A wrapper file at `.github/workflows/policy-check-wrapper.yml` (SHA-pinned, Renovate-bumped)
- The `policy-check / scp/policy-check` required status check on the default branch
- An invocation log entry in SCP's `docs/reviews/WP-SCP-020/branch-protection-log.md`
- A per-slice DISPATCH-NOTE with `cascade-status:` declared at close

---

## 7. Where we are

Two trajectories, both live.

### 7.1 SCP-self — Threshold A reached 2026-04-30

The first-order question — *does SCP gate itself on its own merges?* — was answered yes on 2026-04-30 when **USER-GATE-A signed**. The current operational state on SCP's own `main`:

```
enforce_admins:           true   (admin override OFF)
required_status_checks:   ["policy-check / scp/policy-check",
                           "check-invocation-log-entry"]  (strict)
required_signatures:      true   (every commit verified-signed)
required_pull_request_reviews:  count=0, codeowner=false
                                (single-operator mode per D-033)
tag-protection:           v* + renovate/v* (deletion / force-push / update blocked)
```

The federation primitive shipped at v1.0.0 on 2026-04-30 and has cut three patch/minor releases since (v1.0.1 — Python hash-pinning; v1.1.0 — SCP-R-004 promotion; v1.2.0 — opt-in scorecard-emit).

| Programme | State |
|---|---|
| WP-SCP-019 (Service Auth Contract) | ✅ closed 2026-04-20 |
| WP-SCP-020 (Policy Federation Primitive) | ✅ **closed 2026-04-30 at v1.0.0 (Threshold A)** |
| WP-SCP-021 (MCP Server) | ✅ landed 2026-04-29 (USER-GATE-C signed) |
| WP-SCP-022 (Implementation Programme) | ✅ **closed 2026-04-30** (USER-GATE-A signed) |
| WP-SCP-023 (Cross-repo Scorecards) | ✅ closed Threshold A scaffolding 2026-05-03 |

### 7.2 Estate cascade — at canary-start

The second-order question — *does SCP gate the wider estate?* — is in progress.

| Cohort slice | Adopter | State |
|---|---|---|
| 024C | PIM (`jrnb2024/mapp-pim`) | **CEREMONY COMPLETE 2026-05-17.** 5 required contexts live; `required_signatures.enabled=true`; bake observation pending (≥1 calendar week + ≥1 Renovate cycle clean) |
| 024D | Control Tower | DEFERRED — opens after 024C bake-clean |
| 024E | mapp-doc-agent + recommender paired | DEFERRED — opens after 024D bake-clean |
| 024F | shopify-app | DEFERRED — opens after 024E bake-clean |
| 024G | Threshold A + USER-GATE-E + D-046 | ≥3 of 5 cohort adopters onboarded + each survived ≥1 Renovate cycle |

"Operationally usable across the estate" = Threshold A signed at 024G. Calendar estimate: 4–8 weeks from 024C bake-clean. Most of the time is bake observation by design; engineering is days, not weeks.

### 7.3 Open follow-up items

Each cascade slice surfaces its own tracked-forward items. The currently-open ones inherited from 024C close-out:

- **TF-024C-R5-001-SIGNING-DEFERRAL-AUDIT** — estate-side audit detecting adopters with `skip-required-signatures: true` AND live `required_signatures.enabled=false`. Out of in-slice scope (touches CI workflows + scorecard-aggregator). Revisit when first adopter actually uses `--skip` — PIM does not.
- **TF-024C-R5-002-CT-NOTIFICATION-AMENDMENT** — amend CT cascade-start notification with R4 + R5 brownfield-adopter flags erratum. Cross-repo write — operator-mediated per Pattern 4.
- **FUP-024C-STEP3-CASCADE-STATUS-FORMAT-001** + **FUP-024C-STEP3-POLL-RACE-001** — two defects in the pre-authored operator step3 script, surfaced during operator queue execution; both should be folded into a script-hardening sub-slice.
- **D-045 row** — the 024C ratification text exists in the slice DISPATCH-NOTE but the actual row hasn't yet been transcribed into `docs/DECISIONS.md`.

---

## 8. Where we're going

Threshold A is the floor, not the ceiling. Five directions of travel beyond it.

### 8.1 Cohort completion + maintenance

After Threshold A (024G + USER-GATE-E + D-046):

- Recurring Renovate-driven SHA pin bumps; each version cut auto-cascades within ~24h
- Departing-adopter procedure (rare; covered by invariant 7 rollback)
- Opportunistic onboarding of additional non-cohort adopters
- Bus-factor-1 quarterly review (2026-07-21 named; 2026-10-21 next)

### 8.2 Policy expansion

The federation primitive can carry any policy expressible as OPA Rego against repo state. Candidates being staged:

- **Architecture conformance.** Extend WP-SCP-008 evaluator to assert ports/adapters discipline, dependency-direction invariants, layered-architecture rules.
- **Service-contract conformance.** Every service exports an OpenAPI / Avro / Proto contract committed to the repo; SCP rule asserts that contract changes are versioned and deprecation-ramped.
- **Test-coverage thresholds.** Per-domain coverage floors; deny PRs that drop coverage below baseline without a waiver.
- **Dependency hygiene.** Deny PRs adding deps from non-allowlisted registries; require SBOM attestation.
- **Secret-scope discipline.** Workflow `permissions:` blocks must follow least-privilege; deny `permissions: write-all`.
- **Authentication-claim conformance.** Services consuming SVC-003 must declare their mode + the auth-contract version they implement.
- **DPBM (Design Parity Build Method).** D-048/ADR-016 estate doctrine for designed visual output; SCP rule enforces presence of design-artefact references in PRs touching frontend code.

Each new rule follows the rule-RFC process (D-036): `docs/reviews/rule-proposals/PROP-NNN.md` + quorum review + 48h ceiling.

### 8.3 Tighter agent integration

The MCP surface is at v0.3 today. The forward direction:

- **WP-SCP-025** (proposal queue) — a formal `propose()` MCP method + adjudication workflow per D-023. Multi-agent coordination via a structured queue, not free-form chat.
- **Pre-code consult mandatory in more domains.** Current `domain-map` covers auth, schemas, governance. Extend to architecture, contracts, deployment manifests.
- **Live-policy injection.** Agents called with up-to-date rule context at dispatch-time (currently consulted on-demand).
- **Receipt validation on more tools.** Currently `PreCommit`; extend to `PrePush`, `PrePR`, `PreDeploy`.

### 8.4 Estate observability

WP-SCP-023 (scorecards) is at Threshold A scaffolding. The forward direction:

- **Real-time scorecard dashboard.** Current aggregator runs on a weekly cron; the ambition is continuous (event-driven on adopter `workflow_run` completion).
- **Drift-detection alerts.** When an adopter's posture deviates (waivers expiring, rules disabled, SHA pin stuck) the operator gets pinged via CT governance log.
- **Quarterly compliance reports.** Auto-generated markdown + executive summary across cohort.
- **Adopter contribution surface.** Adopters propose rules via PR; SCP runs them in `warn` mode for ≥1 release before flipping to `deny`.

### 8.5 Estate-wide architectural governance

The bigger ambition — beyond Threshold A — is for SCP to become the place where **estate-wide architectural decisions are codified and enforced.** Examples of the kind of work that becomes possible once the federation primitive is universally adopted:

- **Layered architecture invariants.** Services must respect dependency direction (e.g., domain layer can't import from infra layer).
- **Cross-service contract gates.** Breaking changes to public service contracts require synchronised PRs across consumers + producers.
- **Estate version coordination.** When a shared dependency (CT-AUTH, ACC kernel, MCP SDK) version-bumps, SCP gates the rollout across the cohort.
- **Compliance attestation.** For regulated work (data residency, retention, audit), the federation primitive's required check at merge time is the binding attestation that PRs comply with relevant standards. A signed-receipt class of attestation (pre-commit receipts validating consult-time rule context) is future-scope; see §6.3 + WP-SCP-027.
- **New-domain onboarding.** Beyond the current 5 cohort + FLA, a formal procedure for new adopters joining the federation (cost estimate, technical fit, governance acceptance).

These are direction-of-travel notes, not implementation commitments. Each becomes a future WP-SCP-NNN with its own plan-doc, slice plan, and Threshold criteria. The federation primitive enables them; the rule-RFC process gates them; the cohort adopters consume them.

The longer-horizon view: as agents take on more of the SDLC — design, planning, code authoring, review, testing, release — the rules they're operating against need to be *both* machine-readable (so the agents can consult them) *and* machine-enforced (so violations get caught at the gate, not in production). SCP is the layer where those rules live, and the federation primitive is the mechanism by which they reach every repo in the estate without anybody having to remember to copy them in.

---

## 9. Reference

### 9.1 Service endpoints

When `standards-control-plane serve` is running:

| Endpoint | Purpose |
|---|---|
| `GET /` | This page (the integrated docs) |
| `GET /docs/adoption` | ADOPT-001 onboarding guide rendered as text |
| `GET /health` | Liveness — returns SVC-002 shape `{status, version, checks}` |
| `GET /status-app/health` | Status-integration health (auth mode, artefact freshness) |
| `GET /registry` | Standards registry snapshot |
| `POST /consult` | Consult guidance via the deployed FastAPI HTTP service (distinct from MCP — MCP transport is stdio-only per D-054 + D-055) |
| `POST /audit` | Audit execution via the deployed FastAPI HTTP service (distinct from MCP — MCP transport is stdio-only per D-054 + D-055) |
| `GET /auth/me` | Current authenticated user claims |
| `GET /api/auth/me` | SDK BFF claims endpoint |

### 9.2 Key documents

| Topic | Path |
|---|---|
| Integrated system overview | `docs/OVERVIEW.md` |
| Adoption brief (operator runbook) | `docs/adoption/ADOPT-001-project-onboarding.md` |
| Decision record (single table) | `docs/DECISIONS.md` |
| Standalone ADRs | `docs/decisions/*.md` |
| Per-WP plans | `docs/plans/WP-SCP-NNN-*.md` |
| Per-WP architecture notes | `docs/architecture/WP-SCP-NNN-technical-architecture.md` |
| Operational state (always current) | `STATUS.md` |
| Adversarial review evidence | `docs/reviews/WP-SCP-NNN/<slice>/r{1,2,…}-*.json` |
| Adopter branch-protection mutation log | `docs/reviews/WP-SCP-020/branch-protection-log.md` |
| Deployment runbook | `docs/deployment.md` |

### 9.3 Source repo

```
github.com/jrnb2024/standards-control-plane-
```

Branch protection on `main` requires `policy-check / scp/policy-check` + `check-invocation-log-entry`, `enforce_admins=true`, signed commits, tag-protection on `v*` and `renovate/v*`. Self-dogfooded — SCP gates itself on the same primitive it ships.
