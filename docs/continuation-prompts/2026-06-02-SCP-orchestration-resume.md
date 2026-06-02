# SCP orchestration session — clean restart prompt (2026-06-02)

**Drafted:** 2026-06-02 (end of the WP-SCP-030 ship-it session). Supersedes `2026-05-30-SCP-orchestration-resume.md`.
**Session character:** SCP coordination / orchestration session. Tracks the estate canonical-conformance rollout; resumes per-domain build work when each domain's authority finishes its handoff.
**How to use:** paste the DROP-IN block into a fresh Claude Code session, OR point a session at this file. Everything needed to reconstruct state cold is on-disk (this prompt says where) — **verify live, do not trust this summary.**

---

## DROP-IN (paste this)

```
SCP orchestration session — resume. Read this file in full first:
standards-control-plane/docs/continuation-prompts/2026-06-02-SCP-orchestration-resume.md
Then run the PRE-FLIGHT, evaluate the ONE resume signal (auth cosign) + the passive observation windows, and act per the DECISION TREE.
```

---

## Headline state (what changed since 2026-05-30)

**WP-SCP-030 is DONE — shipped end-to-end and FIRING in production.** SCP-R-030 (the first D-058 canonical-conformance rule) gates that hooked-repo adopters carry the canonical acc-hook onboarding preamble.
- A.3 6-repo marker propagation → B.1 rule (#196) → companion-workflow activation (#201; the additive Option-A `opa eval` repo-level pass) → **v1.4.0 cut** (`56594d2`) → **B.2 cohort opt-in**: CT #484 + PIM #385 opted-in (`acc-hook-installed: true`) → **SCP-R-030 firing on CT + PIM**; doc-agent #77 bumped (not hooked, no opt-in).
- **4-week observation window OPEN → D-060** (deny-promote / hold-at-warn / re-scope).
- ⚠️ **Two recorded observation blind-spots — D-060 MUST account for both:** (1) element checks are whole-file greps → a stripped-preamble-but-marker-present file still PASSes via incidental substrings (`FUP-WP-SCP-030-ELEMENT-HEURISTIC-HARDENING-001`); (2) the repo-level eval step **fails OPEN** on an opa error → a broken eval silently yields no findings (`FUP-WP-SCP-030-FAIL-CLOSED-AT-DENY-PROMOTE-001`, which D-060 deny-promotion must convert to fail-closed in the same PR). **Both mean the observation UNDER-counts drift: a low `element_missing` count is NOT evidence preambles are healthy.**

**WP-SCP-028 (auth) is the ONE open thread — parked, launch-ready, gated on CT.**

## The repo-level eval substrate (reusable — auth will extend it)
The companion PR (#201) built a dedicated, additive `opa eval` repo-level pass in `policy-check.yml` (after the conftest per-file pass) that materialises `input.rule_config` + `input.claude_md_present` + `input.claude_md`, filtered to `REPO_LEVEL_RULES`. **This is the substrate WP-SCP-028's activation extends** (it also un-dormants SCP-R-006, deliberately left out of scope). Conftest per-file pass (SCP-R-001..008) untouched.

---

## Root context + hook discipline
Runs cleanly from a session rooted at **`~/Projects`** (parent dir) — SCP docs are writable without tripping the acc-hook (it loads only when SCP is the project root). If SCP-rooted and writing SCP **source** (`policies/**`, `scripts/**`, `schemas/**`, `tests/**`, `.github/workflows/**` *for safety*, `pyproject.toml`, root `STATUS.md`, `.claude/**`), use the **D-057 dispatch ceremony** (`scripts/operator/scp-pattern3-dispatch.sh "<paths>"` before; `--teardown` after). **Never disable the hook.** Docs/`CLAUDE.md`/memory always-allowed.

## Pre-flight (verify LIVE — do NOT trust this summary)
```bash
git -C ~/Projects/standards-control-plane fetch origin --tags
git -C ~/Projects/standards-control-plane log --oneline origin/main -6
gh release view v1.4.0 -R jrnb2024/standards-control-plane --json tagName --jq .tagName   # expect v1.4.0
```
Then read: `STATUS.md` (top chain) · `docs/decisions/D-058-...md` · `docs/plans/WP-SCP-028-auth-canonical-conformance-v1.md` · the SCP section of `~/.claude/projects/-Users-amplience-Projects/memory/MEMORY.md`.

---

## The ONE resume signal + decision tree

### Domain — AUTH (WP-SCP-028) — blocked on CT's cosign impl

**Signal (both must be true to launch):**
```bash
# prereq-1: protected_primitives present (already MET; re-confirm)
gh api repos/jrnb2024/control-tower/contents/contracts/auth-contract-v1.yaml --jq '.content' \
  | base64 -d | grep -q '^protected_primitives:' && echo "P1 ok"
# prereq-3 (THE GATE): .sig.bundle is a REAL sigstore cert chain, not the HMAC placeholder
gh api repos/jrnb2024/control-tower/contents/contracts/auth-contract-v1.yaml.sig.bundle --jq '.content' \
  | base64 -d | grep -qi 'sigstore\|-----BEGIN\|certificate' \
  && echo "COSIGN LIVE → AUTH LAUNCHABLE" || echo "cosign still placeholder → auth parked"
```

- **If COSIGN LIVE:** the autonomous-run prompt is ready at `docs/continuation-prompts/2026-05-30-WP-SCP-028-auth-canonical-autonomous.md` — **already de-gated** (its §0.0 records the real published shape: two-tier `protected_primitives` tier_deny/tier_warn × py/ts/go, `claim_shape_version` 2.0.0 MAJOR, `issuers:` block, cosign-now-required, **version → v1.5.0 not v1.4.0**). Launch it via the **full D-057 dispatcher** (build a `.acc/launch-*.sh` helper like the WP-SCP-030 ones, or run `scp-pattern3-dispatch.sh` with the §0.2 scope, then drop the "Read and execute …" line into an SCP-rooted session). It authors SCP-R-009/010/011; **firing then needs a companion activation that EXTENDS the #201 repo-level substrate** + the same coupling guard. D-059 reserved.
- **If parked:** CT's `WP-CT-VENDOR-WHEEL-COSIGN-001` impl hasn't landed (it was plan-stage 2026-06-02; Class A only per ASC-2026-06-01-001). Nothing buildable SCP-side. Report + stand by. (Operator chose 2026-06-02 to PARK rather than author the rules dormant — no firing benefit until cosign, and the flagship is cleaner authored against real signed artifacts.)

---

## Standing / passive items
- **D-060 — WP-SCP-030 observation** (4 weeks from 2026-06-02). Watch SCP-R-030 firing rate / false-positives / real marker-drop catches across CT + PIM. **Honour the two blind-spots above.** Reserved decision: deny-promote / hold / re-scope.
- **026F observation** → 2026-06-23 (MCP consult; zero consumers so far → D-056 trending "hold").
- **shopify-app onboarding** — adopter #5 of the WP-SCP-024 cohort; ~20-30 min operator-attended ceremony (`FUP-WP-SCP-024-SHOPIFY-APP-ONBOARDING-001`).
- **SCP-R-006** — still dormant; the #201 substrate now makes `input.rule_config` materialisable, but SCP-R-006's *extra* inputs were deliberately NOT wired (decision: SCP-R-030-only). It is the next consumer of the substrate when wanted.
- **SCP-wrapper bump-sweep** — all 3 cohort adopters now at `@56594d2` (v1.4.0) after B.2. Next sweep after the next release tag.

## Discipline (estate-wide; non-negotiable)
- 3-lens adversarial review (correctness / safety_bypass / completeness_governance) on any rule/plan/strategic decision. safety_bypass REJECT on an auth or merge-gate surface = hard stop.
- NEVER commit to main outside a PR. NEVER disable the acc-hook (declare scope via dispatch). Stage explicitly. STATUS chain row on every PR (triggers `check-invocation-log-entry`); PR body carries a `## R1 evidence` block (3 plain `- lens:` lines).
- **Cross-repo writes (CT/PIM/etc.): the operator's local checkouts are often dirty — never use them.** Use an isolated worktree off `origin/main` OR the GitHub API. **Signing gotcha (learned 2026-06-02):** GitHub **contents-API commits are UNSIGNED** → blocked by `required_signatures` on CT/PIM. Fix = worktree off origin/main + `git -c user.email=208332699+jrnb2024@users.noreply.github.com commit -S` + `git push --force` (the noreply email is always-verified; a real force-push, not `--force-with-lease`, since a fresh worktree lacks the remote-tracking ref). CT is `strict` (require-up-to-date) + has required `ok` rollup + `validate PR body`; PIM CI is slow (go-services + playwright + contract-tests, ~5-8 min).

## What shipped this session (2026-06-02)
WP-SCP-030 close-out: #196 merged (B.1) → #201 merged (companion activation, kernel-dangerous, 3-lens R1 ACCEPT — its first CI run caught a real fail-open eval bug via the selftest oracle, fixed in-round) → **v1.4.0 cut + released** → **B.2 cascade** (CT #484 + PIM #385 opt-in + doc-agent #77 bump, all signed-commit via worktrees). Plus WP-SCP-028 prep: #197 (auth-prompt canonical-shape update + cosign de-gate) + #198 (companion scope) + #200 (companion autonomous prompt). MEMORY SCP line refreshed to v1.4.0 + SCP-R-030 firing.

---

**Closes when:** CT lands cosign → auth run authors SCP-R-009/010/011 → companion activation → D-059 (auth) + D-060 (hooked-repo) ratified at their observation closes.
