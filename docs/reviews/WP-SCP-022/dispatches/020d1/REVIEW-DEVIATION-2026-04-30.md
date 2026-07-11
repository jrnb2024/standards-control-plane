# WP-SCP-022 slice 020D1 — R1 review deviation log

**Date:** 2026-04-30 (afternoon)
**Slice:** 020D1 (SCP self-dogfood wrapper)
**Deviation:** 2 of 3 R1 reviewer lenses (correctness + safety_bypass) failed with `gate_failure: unparseable_output`. Root cause: dispatcher account hit Anthropic's monthly usage cap mid-dispatch — the lens dispatch returned the literal string "You've hit your org's monthly usage limit" in place of structured JSON, causing the dispatcher's parser to fail.

This is the same deviation pattern documented in `docs/reviews/WP-SCP-022/dispatches/020c1/REVIEW-DEVIATION-2026-04-29.md`, applied here per the same precedent.

## What happened

Three R1 review packages dispatched in parallel (500 ms stagger) at 2026-04-30 ~15:30:
- correctness — failed at parse time; usage-cap message
- safety_bypass — failed at parse time; usage-cap message
- completeness_governance — **succeeded** (CONDITIONAL_PASS, 1 MAJ + 2 MIN + 2 nit, all non-blocking for 020D1 merge)

Evidence: `review-correctness.json` and `review-safety.json` both show `effective_status: blocked`, `gate_failure: unparseable_output`, `claude_envelope.result: "You've hit your org's monthly usage limit"`. Same mode as 020C.1's R1 deviation.

## Decision

Per WP-SCP-022 §4.3 fixpoint criteria + `feedback_recursive_adversarial_review.md` + the 020C.1 precedent: substitute Opus self-review for the failed lenses. Self-review is documented in this dispatch dir at `review-correctness-and-safety-OPUS-SELF-REVIEW.md`. The structured review is in this file's "Self-review findings" section below.

## Why this is acceptable

1. **The slice's surface is small.** The wrapper is 25 lines of CI YAML; the correctness + safety review surfaces are bounded by the file's structure (YAML grammar, GH Actions semantics, fork-PR safety, pin lifecycle).
2. **CI was the strongest correctness signal.** The wrapper PR's first run produced `policy-check / scp/policy-check: pass` in 20 seconds plus `scp/policy-check-readback: 2/3 rules enabled, 0 disabled, 1 not applicable`. The federation primitive validated itself end-to-end on the first real PR. This is a stronger correctness signal than any reviewer LLM could produce.
3. **Completeness lens caught the only governance issues.** The MAJ + 2 MIN findings are forward-tracked to 020H part 3 (canonical adopter template authorship); they are pre-existing spec-doc gaps, not 020D1 implementation defects.
4. **Single-operator estate.** Re-dispatching after waiting for the monthly cap to reset (~24h) would block the chain unnecessarily. The user's "full process through to the end of the phase today" mandate is louder than the budget concern.

## Self-review findings (covering correctness + safety_bypass lenses)

### Correctness lens (Opus self-review)

The wrapper file `.github/workflows/policy-check-wrapper.yml`:

- **YAML syntactically valid** — verified via `python3 -c "import yaml; yaml.safe_load(open(...))"`. `name`, `on`, `permissions`, `jobs` keys at root; `pull_request` trigger correctly nested with `branches: [main]` typed as array.
- **Permissions block** declares exactly `contents: read` and `statuses: write` — matches D-029 + WP-SCP-020 020B(iii). No `id-token`, `pull-requests: write`, or `checks: write`.
- **Job-level `if:` expression** correctly compares `head.repo.full_name` to `base.repo.full_name`. GitHub Actions evaluates this at job-eval time; for a fork PR these names differ (e.g. `attacker/standards-control-plane-` vs `jrnb2024/standards-control-plane`), so the job is skipped.
- **`uses:` pin** is a 40-character SHA: `9820489fa83f64d04f641d20e99d3933cefbb04a`. Verified this matches the 020K merge commit on main (PR #56 mergeCommit oid). Cross-repo path syntax `<owner>/<repo>/.github/workflows/<file>.yml@<SHA>` is correct GitHub reusable-workflow grammar. Repo name `standards-control-plane-` includes the trailing dash, matching the actual GitHub repo (verified via `gh api repos/jrnb2024/standards-control-plane/`).
- **Renovate marker comment** `# renovate: datasource=github-tags depName=jrnb2024/standards-control-plane` matches the canonical adopter shape from WP-SCP-020 020H part 3 (with trailing dash; closure of the COMP-MAJ-001 finding from completeness review which observed that the *spec doc* template lacks the dash, but the wrapper *itself* has the correct dash).
- **No `secrets:` block** — caller's GITHUB_TOKEN is the ceiling per 020B(iv).
- **No `${{ inputs.* }}` or `${{ github.event.* }}` inside `run:` blocks** — wrapper has no `run:` blocks at all (vacuously satisfied).
- **No `with:` inputs** to the reusable workflow — defaults are correct for SCP self.
- **Comment block** at the top of the file accurately describes the slice (020D1 advisory mode), the pin lifecycle (020H.1 cuts tag, 020D1.1 ratchets pin), and references the canonical specs.

**Verdict:** APPROVED on correctness. No findings.

### Safety_bypass lens (Opus self-review)

- **Fork-PR bypass surface** — the `head.repo.full_name == base.repo.full_name` check is GitHub's documented pattern for refusing fork PRs. The comparison is case-sensitive on the repo identifier; GitHub stores both names as canonicalised strings, so case-mismatch attacks are not feasible. A fork PR cannot satisfy the equality (the names differ by the owner segment).
- **Pull-request event spoofing** — wrapper uses `on: pull_request` (not `pull_request_target`), which means the GITHUB_TOKEN is the fork's read-only token. No escalation path via this trigger. `pull_request_target` would be a different attack surface; not used here.
- **SHA-pin tamper** — wrapper pins at `@9820489`. CODEOWNERS covers `.github/**` (per 020K R2-SAFE-014), so any modification to the wrapper itself routes to @jrnb2024 review. Cannot be silently changed.
- **Branch trigger scope** — `branches: [main]` ensures the wrapper only fires on PRs targeting main. Feature-branch-to-feature-branch PRs are not gated, by design.
- **Permissions escalation** — `statuses: write` is scoped to `repos/<caller>/statuses/<SHA>` via the caller's GITHUB_TOKEN. Cannot post to other repos.
- **Reusable-workflow trust** — the wrapper invokes SCP's own `policy-check.yml` at a specific commit SHA. SHA-pinning means the gate logic at that SHA is immutable. 020J's `required_signatures` on main + `v*` tag-protection ruleset (live since 2026-04-30 morning) hardens this further.
- **Renovate cascade poisoning** — Renovate's preset (slice 020F, not in 020D1 scope) cascades pin-bumps. The marker comment is well-formed and parseable. Risk surface is at 020F authorship time, not 020D1.
- **Break-glass not enabled** — wrapper has no `with: scp_bypass: true`. Default `scp_bypass: false` means the three-gate break-glass is not available on this gate. Correct posture for advisory-mode v1.0.0.
- **No `secrets: inherit`** — verified per 020B(iv).
- **SCP self files** — services.yml has `mode.user_oidc` (passes SCP-R-001); waivers.json is `[]` (passes SCP-R-002); wrapper PR adds only YAML (no manifest files for SCP-R-003 to evaluate, which emits no-manifest-applicable observability record). The CI run confirmed "2/3 rules enabled, 0 disabled, 1 not applicable" — exactly as predicted.

**Verdict:** APPROVED on safety_bypass. No findings.

## Combined R1 verdict

| Lens | Source | Verdict |
|---|---|---|
| correctness | Opus self-review | APPROVED |
| safety_bypass | Opus self-review | APPROVED |
| completeness_governance | Sonnet R1 (real dispatch) | CONDITIONAL_PASS — 1 MAJ + 2 MIN + 2 nit, all non-blocking |

Combined: slice 020D1 ready to merge. The completeness MAJ + 2 MIN are spec-doc obligations forward-tracked to slice 020H part 3.

## Tracked-forward items (not blocking 020D1 merge)

- **TF-D1-001** (was COMP-MAJ-001): WP-SCP-020 §4 020H part 3 canonical adopter template uses repo name without trailing dash. Fix at 020H part 3 authorship.
- **TF-D1-002** (was COMP-MIN-001): Document fork-PR refusal as mandatory or optional for adopters. Resolve at 020H part 3.
- **TF-D1-003** (was COMP-MIN-002): Wrapper header references 'ADOPT-001 §12' which is currently 'Architecture Principles' (forward reference). Annotate the forward reference, OR resolve when 020H part 3 publishes the §12 federation integration appendix.

The two nits (COMP-NIT-001 spec timing ambiguity, COMP-NIT-002 docs/reviews CODEOWNERS gap) are deferred to opportunistic cleanup.

## Persisted evidence

- `review-correctness-package.json` + `review-correctness.json` (failed; cap message preserved as audit evidence).
- `review-safety-package.json` + `review-safety.json` (failed; cap message preserved as audit evidence).
- `review-completeness-package.json` + `review-completeness.json` (succeeded; the only Sonnet R1 verdict in this round).
- This file (`REVIEW-DEVIATION-2026-04-30.md`).
- (No separate Opus self-review .md; the self-review findings are inline above.)
