# SCP REACH plan v2 — scoping for approval (2026-06-29)

Scopes the three reach workstreams from `SCP-REACH-CONTINUATION-2026-06-29.md`, grounded in
three read-only data probes + a plan-stage 3-lens adversarial review (correctness, D-058/scope
safety, completeness), with every contested claim verified against code. **Plan for approval —
no build work started.** Guardrails: D-058 (gate LINKAGE not VALUES; domain authorities author
canonicals, SCP only gates), D-049 (anti-scope: static repo state only — file presence, path
match, content substring, changed-file set arithmetic; no semantic interpretation beyond
signed-manifest/linkage), D-057 (SCP self-work is Pattern-3, operator-seeded dispatch), and
James's rules (cross-repo + branch-protection = operator-attended; sequential not batched;
dev/staging-only; **never touch kg-studio** — other fork's workspace).

## Plan-stage review outcome (verified)

Three Explore reviewers ran; I verified each blocker against code. **Verified TRUE:** ADOPT-001
stale dashed-repo URLs are real and pervasive (~20 lines, not 4); R-009/R-010 Rego are genuinely
language-agnostic (read input schema; `canonical-sdk-versions.schema.json` + `auth-contract-v1.schema.json`
already list `go`) so the Go gap is the workflow extraction layer, not the Rego; R3.0's advisory-only
characterization is correct; `scripts/scaffold-downstream.sh` exists (reuse it); `enable-required-check.sh`
has `--preserve-existing-contexts` + `--restore`/`--plan`. **Corrected:** the `UserPromptSubmit`
precedent is NOT in control-tower — it's `governance_context_injector.sh`, a deployed UserPromptSubmit
context-injector in Recommender / fashion-labelling-agent / fractal-inquiry-os / living-canvas (it
injects *local* governance context and does **not** consult SCP). **Refuted:** SCP-R-030 exists
(`policies/SCP-R-030.rego` + test) — R2.1's gating is valid. mapp-doc-agent is gated-but-not-acc-hooked
(expected; gating ≠ acc-hook).

## Ground truth from the probes

- **Adoption:** 25 repos. **4 gated** (SCP, control-tower, mapp-pim, mapp-doc-agent). 16 not-gated-with-CI, 5 no-CI. ADOPT-001 onboarding is heavy (~12 steps). Day-1 is **warn (workflow-side config), then flip the required check (script-side)** — two distinct levers. Blockers: admin PAT scope, brownfield `--preserve-existing-contexts` (default silently drops existing checks), commit-signing posture, `secrets: inherit`.
- **Consult:** global `~/.claude/CLAUDE.md` routes every interactive session on this machine. ACC owns hooks; SCP gates via SCP-R-030 (exists). A UserPromptSubmit context-injection mechanism is already deployed (`governance_context_injector.sh`) but does not call SCP. MCP is stdio; adopters consult via `scp-cli consult` or per-repo `.acc/mcp_server.py`.
- **Go:** ~970 Go files invisible. architecture globs are `.py/.ts/.tsx`. Auth rules R-009/010/011 are dormant + language-agnostic; gap = workflow extraction (parse go.mod, extract imports). 5 canonical Go SDKs live (ct-auth-go/http/rbac/tenant/webhooks); ct-events-go planned, unauthored.

---

## REACH-1 — Adoption cascade

Tier by real-operational-service + readiness; gate where it matters (not all 25); warn-first; sequential; operator-attended.

- **Tier A (pilot + first cascade):** mapp-returns-intelligence (Kafka producer), mapp-size-allocation, acc (dogfoods the hook authority). All acc-hooked + operational (verified).
- **Tier B:** brand-dna-spectrogram (only working Kafka consumer), fashion-labelling-agent, living-canvas, agentic_commerce_pac, mapp-visual-shopping (lower — STL-superseded). **Confirm currency at R1.2 start.**
- **Skip:** market-feed (deprecated D-038), demos/scratch (adaptive-labelling-demo, ms-stl-demo, kg-demo-framework, fashion-catalogue, labs-trends, fractal-inquiry-os, mapp-estate-regression, fashion-ontology-service). **kg-studio: NEVER (fork) — enforced by an explicit guard in the cascade helper, not operator memory.**

**Work packages**
- **R1.0 (docs, quick):** sweep ALL stale `standards-control-plane-` references in `docs/` (ADOPT-001 has ~20: pip-install, `uses:`, Renovate, `gh api` snippets). One docs PR, gated-merge. Acceptance: `grep -rn 'standards-control-plane-' docs/` returns nothing.
- **R1.1 (pilot, operator-attended):** onboard **mapp-returns-intelligence** end-to-end, reusing `scripts/scaffold-downstream.sh`. Sequence: (1) admin-PAT pre-flight (`gh api ...branches/main/protection` — fail fast on 403); (2) signing-posture check (`git log --pretty=%G? main | sort | uniq -c` → decide `--skip-required-signatures`); (3) scaffold caller workflow + overlay + CLAUDE.md consult line in **warn mode** (workflow `policy_check_warn_mode` / `.scp/rule-config.yaml`); (4) run the PR, verify clean warn output; (5) promote to enforce (workflow config), then `enable-required-check.sh --preserve-existing-contexts` to add the required check. Rollback: `enable-required-check.sh --restore`. Acceptance: policy-check green on RI; all ADOPT-001 steps done; branch-protection snapshot logged. Deliverable: `docs/adoption/REACH-1-tracker.md`.
- **R1.2 (cascade):** remaining Tier A then Tier B, **one repo at a time**, each with the R1.1 pre-flights, warn→required, tracked. No bulk PRs. Per-repo: re-check signing + existing required checks; the cascade helper hard-skips kg-studio.

## REACH-2 — Consult consumption (+ make adoption measurable)

SCP proposes content; **ACC authors the hook** (D-058); SCP gates via SCP-R-030 (exists). Build on the deployed UserPromptSubmit injector pattern, don't invent SessionStart.

**Work packages**
- **R2.1 (cheap, high-leverage):** add a one-line consult instruction (`scp-cli consult` / resolve_domain→consult_rules→audit_changed) to ACC's onboarding canonical (`acc/docs/guides/hooked-repo-onboarding-preamble.md`). SCP files a `propose()` + a cross-repo PR draft; **ACC authors/ratifies** (it owns the canonical); SCP-R-030 already gates the block's presence (marker grep). Concrete handoff, not hand-wavy.
- **R2.2 (mechanism, ACC-owned, cross-repo):** a consult-injection step that runs `scp-cli consult` on the changed files and injects applicable rules. **Verify-first:** read the existing `governance_context_injector.sh` to decide extend-vs-new. **ACC authors the hook**; SCP supplies `scp-cli consult` (exists) + design + the gating rule. Pilot on the RI repo. Reuse the UserPromptSubmit pattern (scopes to changed files; SessionStart is once/coarser). Latency: gate to first-prompt or changed-files-present to avoid ~500ms every prompt.
- **R2.3 (measurement — closes the "zero consumers" gap honestly):** define how we *know* consultation is happening — the acc-hook already HMAC-logs to `.acc/hook-audit-log/`; add a consult-invocation signal (the MCP/`scp-cli consult` call leaves a trace) and a simple per-repo "consulted in last N PRs?" readout. Also note: CI/Codex/non-Claude agents read the repo's `CLAUDE.md`/`AGENTS.md`, not `~/.claude/CLAUDE.md` — R2.1's per-repo line is what reaches them; the hook reaches interactive sessions.

## REACH-3 — Go coverage (LINKAGE only; auth ready, events not)

**Work packages**
- **R3.0 (cheap, advisory):** add `src/**/*.go` + `packages/**/*.go` (NOT blanket `**/*.go` — avoids vendored/example false positives) to `_FALLBACK_APPLIES_TO_BY_DOMAIN["architecture"]` so `consult_rules`/`audit_changed` surface architecture rules on Go. Advisory only; needs MCP restart. SCP self-work → Pattern-3 dispatch on `src/**` + `tests/**`. Acceptance: `consult_rules({domain:"architecture"})` against a Go changed-file surfaces ARCH-005.
- **R3.1 (real enforcement — LINKAGE only):** extend the live WP-SCP-028 auth-canonical workflow to extract Go **go.mod deps + ct-auth import presence**, feeding `input.adopter_ct_auth_deps`/`adopter_source_files` so the already-language-agnostic **R-009 (version-pin) + R-010 (import-presence)** fire on Go. Reuses CT's existing published+cosigned canonical (same trust path the Python rules already use). **Warn-baseline first.** Pre-flight: confirm the published+cosigned manifest carries `go` entries (not just the schema) before any enforce flip. Targets exist today (CT/PIM are gated + Go-heavy). Scope = extraction layer, not new Rego.
- **DEFER (explicit, no silent descope):** R-010 Go *shadow/re-export* detection (AST-level → risks crossing D-049; defer to a future WP with a D-049 check) and R-011 Go *claim-shape* (needs Go Authorization-handler detection). ARCH-005 Go *event-shape* Rego (blocked on ct-events-go authoring). **Note:** mapp-pim's live `pkg/events` bespoke `segmentio/kafka-go` usage stays ARCH-005-invisible until ct-events-go publishes + event-shape Rego lands — recorded so the carried exception is explicit.

---

## Execution discipline (applies to every WP at build time)

- **Per-WP acceptance criteria + rollback** as stated above; `enable-required-check.sh --restore` is the adoption undo.
- **Pre-flights for adopter WPs:** admin-PAT scope, signing posture, existing required checks — fail fast, don't half-apply.
- **SCP self-work (R3.0/R3.1):** operator seeds the Pattern-3 dispatch BEFORE the session (`scripts/operator/scp-pattern3-dispatch.sh "<paths>"`), teardown after. Never disable the hook.
- **Build method (GOV-004):** each build PR is TDD (operator-RED-test-first) + 3-agent adversarial review + `## R1 evidence` block; gated-merge with committer `james.brooke@mapp.com`.
- **Decisions:** file a `D-NNN` for the REACH program (approval of this plan = the authority); R2.1's cross-repo canonical edit is an ACC-coordinated decision. GOV-004/005/SVC-004 stay advisory — nothing here promotes them.

## Cross-workstream sequencing

1. **R1.0** (URL sweep) — quick docs PR, unblocks adoption.
2. **R1.1 + R2.1 + R2.2 on RI** — one brownfield repo proves gate + consult-line + consult-hook before any cascade; **R2.3** measurement wired alongside.
3. **R3.0 + R3.1** — SCP-internal; CT/PIM are live Go targets; parallel to the pilot.
4. **R1.2 cascade** — only after the pilot validates; sequential, operator-attended.

**Critical-path risk:** R2.2 depends on ACC (hook authorship) — cross-repo. R1.2 needs per-repo admin PAT. R3.1 depends on the dormant auth-canonical workflow internals + the published manifest carrying `go`.
