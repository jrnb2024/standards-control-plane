# Operator runbook — 2026-05-25 session followups

**Companion to:** `docs/continuation-prompts/2026-05-25-session-close-comprehensive-handoff.md`
**Filed:** 2026-05-25
**Audience:** operator (`@jrnb2024`)

5 follow-up items remain after the 2026-05-25 session close. Each is documented below with **step-by-step instructions + scripts** where applicable. Order is rough priority; items 4 + 5 are autonomous-eligible (I open the PRs; you merge) and so listed last with minimal operator surface.

---

## 1. Cut the v1.3.0 release tag (10 min interactive)

**Why:** PR #155 shipped SCP-R-007 + SCP-R-008 + the v1.3.0 manifest bump but **the tag itself has not been cut**. Cutting the tag is what triggers Renovate to auto-PR PIM + CT with the new rules active.

**Script:** [`scripts/operator/cut-release.sh`](../../scripts/operator/cut-release.sh) — 4-phase release ceremony driver. Refuses CI environments per SCP-operator-script convention.

### Quick path (interactive, prompts at each phase)

```bash
cd ~/Projects/standards-control-plane
git fetch origin main
scripts/operator/cut-release.sh \
  --version v1.3.0 \
  --sha d9cf52544eea7eb2b0cc5486187952eaef40b1e1
```

That command runs:
1. **Pre-flight** — verify SHA is on origin/main + tag doesn't exist + `version-manifest.json` declares `1.3.0`. (~2 s.)
2. **Release-gate dry-run** — `gh workflow run release-gate.yml -f dry_run_tag=v1.3.0`; waits for completion via `gh run watch`. (~1-2 min.)
3. **Tag + push** — `git tag -a v1.3.0 <SHA>` + `git push origin v1.3.0`. Triggers `on:push:tags` observer; script waits for that too. (~1-2 min.)
4. **GitHub release** — `gh release create v1.3.0` with auto-extracted release notes from commit log since the last tag.

Between phases the script prompts `[y/N]` so you can abort if anything looks wrong. Pass `--yes` to auto-confirm (use with care).

### Just verify the dry-run first

```bash
scripts/operator/cut-release.sh \
  --version v1.3.0 \
  --sha d9cf52544eea7eb2b0cc5486187952eaef40b1e1 \
  --dry-run-only
```

This stops after Phase 2 (release-gate dry-run). Useful if you want to confirm the gate is happy before committing to the tag-push.

### Custom release notes

If you want to write release notes by hand instead of auto-extracting from commits:

```bash
# Pre-write the notes:
cat > /tmp/v1.3.0-notes.md <<'EOF'
# v1.3.0 — WP-SCP-025 Phase 1: SCP-R-007 + SCP-R-008

…your prose here…
EOF

scripts/operator/cut-release.sh \
  --version v1.3.0 \
  --sha d9cf52544eea7eb2b0cc5486187952eaef40b1e1 \
  --notes-file /tmp/v1.3.0-notes.md
```

### What changes downstream

- PIM Renovate detects the new tag; auto-PR within ~24h to bump PIM's wrapper pin from `@15a56d6` to `@d9cf525`. When that PR merges + PIM's policy-check stays GREEN, that's the first ≥1 Renovate cycle for **024C bake-clean**.
- CT same. **024D bake-clean** progresses similarly.
- SCP-self wrapper is already at `@d9cf525` (PR #160) so SCP-self has no Renovate-bump pending.

---

## 2. Monitor 024D bake observation (passive)

**Why:** WP-SCP-024 §5.2 invariant 8 requires ≥1 calendar week + ≥1 Renovate cycle clean before a cascade slice closes. CT 024D started bake 2026-05-25; target close window ≥2026-06-01.

**Script:** [`scripts/operator/check-bake-status.sh`](../../scripts/operator/check-bake-status.sh) — read-only; reports criteria status + the live required-check on the adopter.

### Daily / weekly check

```bash
cd ~/Projects/standards-control-plane
scripts/operator/check-bake-status.sh \
  --adopter jrnb2024/control-tower \
  --onboard-date 2026-05-25
```

Sample output once bake-clean:
```
[bake] ===== bake-observation check: jrnb2024/control-tower (onboarded 2026-05-25) =====
[bake] ✓ criterion 1: 8 days elapsed since onboard (≥7)
[bake] ✓ criterion 2: 1 Renovate-issued wrapper bump(s) merged
[bake]   #NNN merged 2026-05-27T… — chore(deps): bump SCP wrapper to @<SHA>
[bake]   ✓ latest Renovate bump's policy-check: success
[bake] live state verification:
[bake]   ✓ 'policy-check / scp/policy-check' is a required status check on jrnb2024/control-tower@main
[bake] ✓ READY for close-out: criteria 1 + 2 met. …
```

Exit code 0 means bake-clean ready for close-out; exit 1 means still in progress.

### What you do when bake-clean

When the script exits 0, ask me (or the next session) to author the **024D close-out PR**:
- Amend `docs/reviews/WP-SCP-024/024D-control-tower-cascade-slice/DISPATCH-NOTE.md` to mark bake-clean criteria satisfied
- File a STATUS chain entry documenting close
- Note: `cascade-status: onboarded` is already set on the DISPATCH-NOTE (declared at slice open per the enum); the close-out PR ratifies the AC criteria, not the enum

### Also check PIM (024C)

```bash
scripts/operator/check-bake-status.sh \
  --adopter jrnb2024/mapp-pim \
  --onboard-date 2026-05-24
```

PIM is 1 day ahead of CT on the bake clock; criterion 1 already met. Criterion 2 (Renovate cycle) fires once v1.3.0 cuts (item 1 above).

---

## 3. Onboard 024E cohort adopters (mapp-doc-agent + recommender)

**Why:** Each cohort adopter onboarded brings the cascade closer to Threshold A (≥3 of 5). After CT (adopter #2), 024E pairs mapp-doc-agent + recommender as adopters #3 + #4 per WP-SCP-024 §5.1 sequencing.

**Pre-requisites:**
- 024D bake-clean OR your judgement that you want to proceed in parallel
- Each adopter must have the SCP federation App installed + secrets set (same ceremony as CT in this session)

### Step A — Scaffold both adopter wrappers (autonomous-eligible; ask me)

I can run `scripts/scaffold-downstream.sh` for each of them and open the adopter PRs as DRAFTs. Tell me to:

```
scaffold mapp-doc-agent + recommender as cohort adopters #3 + #4 (024E)
```

I'll produce the scaffolder output, open PRs on both adopter repos, and HALT before the operator-attended steps (App-install + branch-protection mutation).

### Step B — App-install ceremony on each adopter (operator-attended; ~5 min each)

Per ADOPT-001 §12.7.16a:

1. Open https://github.com/settings/apps/scp-federation-primitive → **Install App** (or "Configure" if already showing the listing)
2. Under **Repository access**, click **Select repositories ▾** → add **both** `jrnb2024/mapp-doc-agent` and `jrnb2024/Recommender` → **Save**
3. For each adopter, go to its **Settings → Secrets and variables → Actions** and add **both**:
   - `SCP_FEDERATION_APP_ID` = `3795720`
   - `SCP_FEDERATION_APP_PRIVATE_KEY` = the same `.pem` contents (or rotate if you shredded)

If you rotate the App private key:

```bash
# After downloading the new .pem:
# Update SCP-self's secret too (so PIM + CT continue to work with the new key)
# This is operator-attended via the GitHub UI on:
#   github.com/jrnb2024/standards-control-plane/settings/secrets/actions
#   github.com/jrnb2024/mapp-pim/settings/secrets/actions
#   github.com/jrnb2024/control-tower/settings/secrets/actions
#   github.com/jrnb2024/mapp-doc-agent/settings/secrets/actions
#   github.com/jrnb2024/Recommender/settings/secrets/actions
# Then shred the new .pem locally.
shred -u ~/Downloads/scp-federation-primitive.*.private-key.pem 2>/dev/null || \
  rm -P ~/Downloads/scp-federation-primitive.*.private-key.pem
```

### Step C — Smoke-test PR on each adopter (operator-paced)

After step B, ask me to open a small smoke-test PR on each adopter (similar to CT PR #429). The PR's CI run is the first cross-repo App-token-exchange test on that adopter. If `policy-check / scp/policy-check` goes GREEN, the wrapper is verified working end-to-end.

### Step D — Branch-protection mutation (operator-attended; ~3 min each)

**Note:** the `--preserve-existing-contexts` flag now correctly preserves 5 operator-preference fields (per PR #162 closure). You should NOT see the regression we hit with CT.

For each adopter:

```bash
cd ~/Projects/standards-control-plane

# 1. Dry-run first
scripts/enable-required-check.sh --plan \
  --repo jrnb2024/mapp-doc-agent --branch main \
  --preserve-existing-contexts

# 2. Capture pre-state for break-glass rollback
gh api repos/jrnb2024/mapp-doc-agent/branches/main/protection \
  > ~/mda-main-protection-pre-024e.json

# 3. Apply
scripts/enable-required-check.sh \
  --repo jrnb2024/mapp-doc-agent --branch main \
  --preserve-existing-contexts

# 4. Verify
gh api repos/jrnb2024/mapp-doc-agent/branches/main/protection \
  --jq '.required_status_checks.contexts'
# Expected: includes "policy-check / scp/policy-check"
```

Repeat steps 1-4 for `jrnb2024/Recommender`. The script will emit invocation-log markdown blocks — keep the output for the close-out PR.

### Step E — 024E close-out PR (autonomous-eligible; ask me)

Once steps B-D are done for both adopters, ask me to author the SCP-side close-out PR (DISPATCH-NOTE + branch-protection-log appends + STATUS chain entry). Same shape as 024D close-out (PR #161).

---

## 4. Land SCP-R-006 workflow-input materialisation (autonomous-eligible; v1.4.0 ready-to-cut)

**Why:** PR #158 shipped SCP-R-006 Rego at content-addition footprint. The companion workflow extension to materialise `input.services_yml` / `input.signed_manifest` / etc. is kernel-dangerous + needs Codex Tier 2 first-fire. Once that lands, R-006 starts firing on adopters AND v1.4.0 can cut.

**Operator surface:** ratify a Codex Tier 2 dispatch I'll author + merge the resulting PR. Steps:

### Step A — Ask me to author the dispatch JSON + plan-doc

```
Author the SCP-R-006 workflow-input materialisation Codex Tier 2 dispatch
```

I'll:
1. Write the dispatch JSON at `docs/governance/work-packages/scp-r-006-workflow-input-materialisation.json` with Tier 2 model (`gpt-5.4 xhigh`) + scope_boundary precisely pinned
2. Author the plan-doc capturing the EDITs + verify_commands
3. Run 3-lens R1+R2 R-cycle to R-fixpoint MET
4. Open the dispatch JSON as a DRAFT PR for your review
5. HALT for your operator-attended first-fire authorisation

### Step B — Fire the Codex Tier 2 dispatch (operator-attended)

Once the dispatch JSON is ready (R-fixpoint MET) and you've reviewed:

```bash
# This is operator-attended Codex CLI invocation; runs from your shell.
# The dispatch JSON contains all the wiring.
codex run docs/governance/work-packages/scp-r-006-workflow-input-materialisation.json
```

(Exact command shape will be in the dispatch JSON's `runbook` section once I author it.)

### Step C — Cut v1.4.0

After the workflow PR merges, repeat **item 1 (Cut release)** with `--version v1.4.0` and the new main HEAD SHA.

---

## 5. File D-054 ADR (autonomous-eligible; trivial)

**Why:** WP-SCP-026 plan-doc v1.0 (PR #159) ratified Shape C strategically but D-054 was reserved without a formal DECISIONS.md row + standalone ADR file. The plan-doc carries the rationale; the ADR formalises it.

**Operator surface:** merge the PR I'll open.

### Step A — Ask me to author the ADR

```
Author D-054 ADR formalising WP-SCP-026 Shape C ratification
```

I'll:
1. Author `docs/decisions/D-054-wp-scp-026-shape-c-ratification-2026-05-25.md`
2. Add a `D-054` row to `docs/DECISIONS.md` table
3. Open as a PR

### Step B — Merge (operator click; ~30 s)

ADR-class but Shape-C-already-ratified-by-#159 — the ADR is bookkeeping. Single-operator early-merge OK per D-040.

---

## Suggested order

1. **Item 1** (v1.3.0 release) — unblocks Renovate cascade on PIM + CT; ~10 min
2. **Item 5** (D-054 ADR) — fast bookkeeping; ~5 min once I open the PR
3. **Item 4 step A** (ask me to author SCP-R-006 workflow dispatch) — autonomous work; I HALT for your operator-attended fire later
4. **Item 2** (bake check) — run a few times over the next week
5. **Item 4 step B + C** (Codex Tier 2 fire + v1.4.0 cut) — when v1.3.0 has had a few days to settle
6. **Item 3** (024E onboarding) — when 024D bake-clean OR you're ready to parallelise

If you want to compress: items 1 + 5 + "ask me to start item 4 step A + item 3 step A" can all happen in one short interactive session today. Items 2/4-fire/3-onboarding ceremony spread over the next ~2 weeks.

---

## Script summary

| Script | Purpose | Refuses CI? | State-mutating? |
|---|---|---|---|
| `scripts/operator/cut-release.sh` | 4-phase release ceremony (pre-flight + dry-run + tag-push + release) | ✅ yes | yes (tags + GitHub release) |
| `scripts/operator/check-bake-status.sh` | Reports WP-SCP-024 §5.2 invariant 8 bake observation status | n/a (read-only) | no |
| `scripts/enable-required-check.sh` (pre-existing) | Branch-protection mutation per ADOPT-001 §12.7.3 | ✅ yes | yes (branch protection) |
| `scripts/scaffold-downstream.sh` (pre-existing) | Emit cohort adopter wrapper artefacts per D-044 | ✅ yes | no (writes to local output dir) |

All scripts under `scripts/operator/` are bash + refuse CI per SCP-operator-script convention (`refuses CI=true / GITHUB_ACTIONS=true`). Run from your interactive terminal session in `~/Projects/standards-control-plane`.
