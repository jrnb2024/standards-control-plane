# TF-PIM-001 — Implementation WP — Path C (GitHub App credential)

**Status:** DRAFT v0.1 (post-ratification; pre-R1)
**Path ratified:** C — GitHub App with `repository_permissions: { contents: read }` scoped to `jrnb2024/standards-control-plane-` only (operator-attended convergence 2026-05-21)
**Origin:** `docs/plans/TF-PIM-001-cross-repo-checkout-auth.md` §5.0 Path C; closed 2026-05-21 at `dceab0c`
**Owner:** @jrnb2024 (D-031 single-operator-mode)
**Dispatch tier:** **Tier 2** (kernel-dangerous federation primitive change; operator-attended fire mandatory)
**Auth-surface:** YES — this WP IS the auth-surface change; 3-lens R-cycle to R-fixpoint mandatory pre-merge; orchestrator-attended

---

## R-cycle changelog

| R | Date | Round | Findings | Closure |
|---|---|---|---|---|
| v0.1 | 2026-05-21 | author | — | initial draft |
| v0.2 | 2026-05-21 | operator-strategic-review fold | 10 refinements (6 strategic-review answers + 4 additional) | folded inline; R1 dispatched |
| v0.3 | 2026-05-21 | R1 closures fold | 12 findings (2 MAJ + 7 MIN + 3 NIT) all ACCEPT-WITH-AMENDMENT / ITERATE-EXPECTED | all 12 folded inline; R1 evidence at `docs/reviews/TF-PIM-001/impl-WP-R-cycle/R1/` |
| v0.4 | 2026-05-21 | R2 closures fold + Option A R4 mechanical override | sec=ACCEPT (R-FIXPOINT-MET); arch-skeptic=ACCEPT-WITH-AMENDMENT (DIMINISHING-RETURNS; 1 new MIN finding ARCH-MIN-001-R2 in §7.5a rollback PATCH); pragmatist=ACCEPT (R-FIXPOINT-MET) | 1 finding folded inline; **R-fixpoint MET via Option A R4 mechanical override** per operator authorisation + `feedback_asymptotic_trajectory_split.md`; R2 evidence at `docs/reviews/TF-PIM-001/impl-WP-R-cycle/R2/` |
| v0.5 | 2026-05-23 | Wave G cure-worse amendment + Path C v2 design | 9 L31 axes surfaced during Wave G fix-forward (2026-05-22 → 2026-05-23); hard-stand-down ratified per ASC-2026-05-22-001; Path C v2 design baked in via new §11 | §11 added; Waves D/G/H sequencing notes added; 3-lens R1 dispatch fired on v0.5 itself per `feedback_orchestrator_auth_surface_plan_review_default.md`; returned: Lens A APPROVED + 1 MED; Lens B NOT APPROVED + 1 CRIT/3 HIGH/5 MED/1 LOW; Lens C NOT APPROVED + 1 CRIT/7 HIGH/6 MED |
| v0.6 | 2026-05-23 | v0.5 R1 closure fold | All 2 CRITs + 11 HIGHs + 12 MEDs + 1 LOW addressed | 2 CRITs folded: §11.2 reframed (7 SCP-side + 2 cross-surface) per Lens B CRIT-001; companion `TF-PIM-001-wave-d-prime-spec-draft.md` authored (~480 lines) with all verbatim execution-class artefacts per Lens C CRIT-001. HIGHs folded: axis I pre-flight validation (HIGH-001); §11.3 table now includes both checkout steps + transition column (HIGH-002); HARD CUT transition discipline explicit (HIGH-003); all Lens C HIGHs covered by companion verbatim text. MEDs folded: §11.4 Path A enumeration with 3-4 BARRIER content classes (A-MED-001 + B-MED-001/002/003); §11.6 Wave D' split into D'.1 + D'.2 PRs (B-MED-004); §11.6 PIM canary failure-mode branch (B-MED-005); FUP P-rating + TF renaming (C-MED-005/006); §12.7.7 amendment scope explicit (C-MED-002); D-050 amendment versioning explicit (C-MED-004); workflow-selftest fixture spec concrete (B-MED-001 + C-MED-001). LOW folded: §11.9 cross-references clarified (B-LOW-001) |
| v0.7 | 2026-05-23 | v0.6 R2 critical-finding fold | R2 returned: Lens A NOT APPROVED + 2 HIGH + 2 MED; Lens B R-FIXPOINT MET + 1 HIGH + 2 MED + 1 LOW; Lens C APPROVED — R-FIXPOINT MET. All R1 findings ✅ closed across all 3 lenses. R2 NEW findings: 2 critical (Lens A HIGH-005 fallback-downgrade attack + Lens A HIGH-004 regex-injection-in-error-message hygiene) folded; 6 others (MED/LOW + NEW-001/002/003/004) accepted as Wave D'.1 WP-spec input | HIGH-005 + Lens B NEW-001 (architectural — same concern): fallback `\|\| github.workflow_sha` REMOVED from `_scp-workflow` checkout step; both checkout steps now use pure `inputs.scp-sha` symmetrically. Workflow-selftest fixture updated to pass `scp-sha: ${{ github.sha }}` explicitly. HIGH-004 (hygiene): pre-flight validation error message redacts SCP_SHA on validation failure (prints char-count, not value). NEW-003 (`simulate-cross-repo` input documentation): note added to companion §2. Other R2 findings (NEW-002 sunset-period FUP; NEW-004 D-050 date hygiene; MED-007 substitution validation; MED-008 UI ceremony verification) explicitly accepted as Wave D'.1 WP-spec input — addressed during WP-spec authoring per L26+L27+L28 discipline, not folded into plan-doc itself. Per operator-ratified choice 2026-05-23 + Lens C APPROVED signal that design is implementable |

R-fixpoint criterion: no new significant findings on a fresh 3-lens round, OR R4 mechanical override at R3 if diminishing-returns trajectory matches `feedback_asymptotic_trajectory_split.md`.

**Status v0.4:** R-FIXPOINT MET 2026-05-21 (Option A R4 mechanical override invoked). Plan-doc merged + Wave A through Wave F discharged through it.

**Status v0.5:** R1 dispatch returned full disposition 2026-05-23 (2 CRITs + 11 HIGHs + 12 MEDs + 1 LOW across 3 lenses; details in v0.6 changelog row above).

**Status v0.6:** R2 dispatch returned disposition 2026-05-23 (Lens A NOT APPROVED + 2 HIGH + 2 MED; Lens B R-FIXPOINT MET + 4 low-friction; Lens C APPROVED + R-FIXPOINT MET).

**Status v0.7:** RATIFIED 2026-05-23. All R1 findings ✅ closed across 3 lenses. R2 critical findings folded inline (HIGH-005 fallback-downgrade architectural + HIGH-004 regex-injection hygiene); 6 R2 non-critical findings explicitly accepted as Wave D'.1 WP-spec input per operator ratification. Lens C R-FIXPOINT MET on R2 + Lens B R-FIXPOINT MET on R2 + Lens A residual findings folded inline → v0.7 deemed ratified for Wave D'.1 Codex Tier 2 dispatch authoring. Wave G + Wave H re-fire authorized post-Wave-D'.1 merge per §11.6 sequencing.

## §1 Plan

### 1.1 Why this WP exists

Path C was ratified 2026-05-21 as the canonical fix for **TF-PIM-001** (P0) — the cross-repo `actions/checkout` authentication failure that blocks every external WP-SCP-024 cascade adopter. PIM PR #236 surfaced the failure 2026-05-19; PIM `main`'s `policy-check / scp/policy-check` required-check has been relaxed operator-attended since then pending this WP closing.

The 3-agent review at `docs/reviews/TF-PIM-001/shortlist-A-C-D/` (sec=Strong C, arch-skeptic=Strong C, pragmatist=Strong A; operator-attended convergence resolved 2C+1A in favour of C on irreversibility-asymmetry grounds) committed the estate to: GitHub App authoring + SCP-controlled workflow code obtaining the App installation token + cross-repo `actions/checkout` using that token + ADOPT-001 §12.7 updated + D-NNN ADR ratifying the App-credential surface.

### 1.2 What this WP delivers

- A GitHub App (`scp-federation-primitive`) registered in @jrnb2024 with `repository_permissions: { contents: read }` scoped to `jrnb2024/standards-control-plane-` only.
- App private key stored as SCP-repo secret (`SCP_FEDERATION_APP_PRIVATE_KEY`) under D-031 single-operator custody.
- Reusable workflow `.github/workflows/policy-check.yml` amended: token-exchange step added; cross-repo `actions/checkout` steps (lines 107, 1149-1154) use the App installation token via `token:` parameter.
- ADOPT-001 §12.7 updated: new sub-section documenting App-install ceremony; §12.7.5 amended for de-adoption-side App-installation revocation; §12.7.10 reaffirmed (no inversion under Path C); §12.7.13 supply-chain section adds `generate-app-token` action SHA-pin tracking.
- New D-NNN ADR (provisional **D-050**) ratifying Path C App-credential surface + §12.7.10 invariant preservation + key custody under D-031 + reversal mechanism.
- Workflow-selftest harness coverage for the token-exchange failure mode (TF-PIM-001-ARCH-002).
- External-adopter cross-repo verification (PIM canary green) + PIM `main` required-check restoration (TF-PIM-001-PLAN-004).

### 1.3 What this WP does NOT deliver

- v1.3.0 release cut — independent track per D-049 §Sequencing item 1 (self-dogfood-only at v1.3.0; TF-PIM-001 is the artefact-gate on adopter-side consumption, not on the v1.3.0 ship).
- Renovate cascade changes — Path C is Renovate-neutral on the preset; existing `renovate/v*` tag tracking continues unchanged.
- Cohort-wide adopter wrapper updates — Path C does not require any adopter wrapper change (TF-PIM-001-PLAN-005 closes as N/A-UNDER-RATIFIED-PATH).
- Multi-org adopter App-install coordination tooling — out-of-scope at the 5-cohort all-`@jrnb2024` namespace; captured as TF-PIM-001-ARCH-004 for future surface.
- Second-maintainer onboarding for App-key co-custody — operator-paced; sequenced after the 2026-07-21 quarterly D-031 bus-factor-1 review.

## §2 Acceptance criteria

Five criteria, all required for WP closure:

1. **External-adopter cross-repo green.** At least one external adopter (PIM is the canary candidate) runs the federation-primitive wrapper cross-repo end-to-end with **all 12 policy-check steps complete with PASS verdict (v0.3 ARCH-MAJ-002 closure)**. Evidence: successful GitHub Actions run URL on a PIM PR exercising the wrapper at the new policy-check.yml SHA. The "Populate .scp-runtime (self-call fallback)" + "Check out SCP repo at workflow ref for schema lookup" steps both succeed; AND no `SCP-RNNN` rule emits a deny finding (the canary PR is designed denial-free per Wave G Action step 3). If a deny finding fires unexpectedly, that is a separate investigation per §7.6 Branch 4 — AC #1 is NOT satisfied until a denial-free run is captured.

   **Non-claim — what AC #1 does NOT validate:** AC #1 validates federation primitive cross-repo execution (one external adopter). Multi-adopter validation is a separate concern handled by Phase 2 cascade slices 024D-024G; the Recommender deny-gate onboarding per D-049 D3 ratification is a separate concern (it consumes Path C federation but requires its own cohort-onboarding ceremony at the cascade slice level). AC #1's "PIM canary green" is necessary but NOT sufficient for "the estate's federation cascade is fully resilient" — that's a Threshold-A-class assertion that lives in WP-SCP-024 §USER-GATE-E, not in this WP's closure ceremony.

2. **PIM `main` required-check restored.** The 2026-05-19 operator-attended relaxation reverses; `policy-check / scp/policy-check` re-enters PIM `main`'s required contexts. Evidence: `gh api repos/jrnb2024/mapp-pim/branches/main/protection --jq '.required_status_checks.contexts'` returns a set containing `"policy-check / scp/policy-check"`. Invocation log entry written to `docs/reviews/WP-SCP-020/branch-protection-log.md`.

3. **ADOPT-001 §12.7 fully updated.** New sub-section (provisionally §12.7.16) documents the App-install ceremony; §12.7.5 amended for de-adoption-side App-installation revocation; §12.7.10 explicitly reaffirmed (no `secrets: inherit` anywhere — Path C is App-credential not PAT); §12.7.13 adds the `generate-app-token` action's SHA pin to supply-chain tracking.

4. **D-050 ADR ratified.** ADR landed in `docs/decisions/D-050-tf-pim-001-app-credential-surface-2026-MM-DD.md` + DECISIONS.md row appended. Captures: App-credential scope (`contents: read` on SCP repo only); §12.7.10 invariant preservation rationale; key-custody posture under D-031 + bus-factor-1 mitigation; reversal mechanism (delete App or revoke installations).

5. **R1-evidence-on-fix-PR satisfies cardinal-rule-2 3-lens.** Per `feedback_r1_surface_must_cite_ci.md`, the fix PR's `## R1 evidence` block carries all three lenses populated + CI citation pair (workflow run URL + `mergeStateStatus` post-merge) on merge.

## §3 Scope

### 3.1 In-scope (this WP delivers)

- GitHub App authoring (Wave A) — `scp-federation-primitive` App; `repository_permissions: { contents: read }`; private key generation + SCP-repo secret storage
- D-NNN ADR drafting + ratification (Wave B) — D-050 covering App-credential surface
- ADOPT-001 §12.7 updates (Wave C) — new §12.7.16 App-install ceremony; §12.7.5 de-adoption update; §12.7.10 reaffirmation; §12.7.13 supply-chain addition
- Reusable workflow change (Wave D) — `.github/workflows/policy-check.yml` token-exchange step + `token:` parameter on cross-repo `actions/checkout`
- Workflow-selftest harness coverage (Wave E) — token-exchange failure mode test fixture per TF-PIM-001-ARCH-002
- SCP-self dogfood verification (Wave F) — verify SCP-self CI runs green on a test PR with the new workflow
- External-adopter cross-repo verification (Wave G) — PIM canary; operator-attended App install on PIM; verify all 12 policy-check steps green
- PIM `main` required-check restoration (Wave H) — operator-attended `enable-required-check.sh --preserve-existing-contexts` invocation + invocation log entry + TF-PIM-001 closure

### 3.2 Out-of-scope (deferred or routed elsewhere)

- v1.3.0 release cut + SCP-R-005 ship — independent track per D-049 §Sequencing
- 4 cohort adopters beyond PIM (CT, MDA, Recommender, shopify-app) — App-install ceremony per adopter is a one-time onboarding step folded into future cascade slices (024D-024G); not part of this WP
- Multi-org adopter coordination surface — TF-PIM-001-ARCH-004; deferred to first non-`@jrnb2024`-namespace adopter
- Second-maintainer co-custody onboarding — deferred to 2026-07-21 quarterly D-031 review per TF-PIM-001-SEC-005
- 90-day App-key rotation execution — first rotation due 2026-08-21 (or earlier if account access changes); rotation SOP authored here, execution is operator-paced
- FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001 fix — unblocks once this WP closes (scaffolder can be verified against a real adopter run); separate impl slice opens after this WP. **Validation-evidence-reuse (v0.3 ARCH-MIN-002 closure):** Wave G's PIM canary CI run URL IS the validation evidence for the scaffolder fix — the scaffolder generated PIM's wrapper (PR #234 instance), so PIM's CI run validates the scaffolder output directly. The scaffolder fix impl slice does NOT require a separate verification run; it consumes Wave G's evidence URL as the proof-of-correctness for the scaffolder template change (BACKLOG path (a): remove `with: scorecard-emit: false` from scaffolder template).

### 3.3 Inherited tracked-forward items

From `docs/reviews/TF-PIM-001/shortlist-A-C-D/sec-lens-r1.md` + `arch-skeptic-lens-r1.md`:

| ID | Title | Wave |
|----|-------|------|
| TF-PIM-001-SEC-001 | App-credential rotation SOP | Wave A + Wave C (docs) |
| TF-PIM-001-SEC-002 | ADOPT-001 §12.7.5 de-adoption update | Wave C |
| TF-PIM-001-SEC-003 | `generate-app-token` action SHA-pin + supply-chain registration | Wave D + Wave C (§12.7.13) |
| TF-PIM-001-SEC-004 | Per-adopter App-install access verification | Wave G (PIM scope; future cascade slices for others) |
| TF-PIM-001-SEC-005 | 2026-07-21 quarterly review extension | TF carried to operator agenda (out-of-scope this WP) |
| TF-PIM-001-ARCH-001 | App private-key rotation schedule (90-day) | Wave A (SOP) + 2026-08-21 first execution (out-of-scope) |
| TF-PIM-001-ARCH-002 | Selftest harness coverage for App token-exchange failure | Wave E |
| TF-PIM-001-ARCH-003 | ADOPT-001 §12.7 App-install ceremony documentation | Wave C |
| TF-PIM-001-ARCH-004 | Multi-org adopter App-install coordination | TF carried (out-of-scope this WP; first non-@jrnb2024 adopter) |
| TF-PIM-001-ARCH-005 | D-NNN ADR for Path C App-credential surface | Wave B |

10 TF items; 8 in-scope across Waves A-G; 2 TF-carried (TF-PIM-001-SEC-005 + ARCH-004) as documented future surfaces.

## §4 Waves

Waves sequenced for delivery order. Each wave's outcome gates the next; waves D + E may parallelise once App credential is in SCP secrets (Wave A complete).

### Wave A — GitHub App authoring (operator-attended; no code change)

**Outcome.** `scp-federation-primitive` GitHub App exists in @jrnb2024 with scope `repository_permissions: { contents: read }` on `jrnb2024/standards-control-plane-` only. Private key stored as SCP-repo secret `SCP_FEDERATION_APP_PRIVATE_KEY`. App ID stored as `SCP_FEDERATION_APP_ID` (not strictly secret but stored alongside).

**Actions.**

*Pre-ceremony `.pem` discipline (MANDATORY — landed v0.2 per operator strategic-review):*

0a. `.gitignore` pattern check — verify SCP repo `.gitignore` contains `*.pem` BEFORE generating the App key. Add the pattern if missing (commit + push that change first).
0b. Pre-commit hook verification — verify any local pre-commit hook (if installed) rejects staged `.pem` files. If no hook installed, document the discipline as a procedural ceremony step.

*Ceremony:*

1. Operator: GitHub UI → @jrnb2024 settings → Developer settings → GitHub Apps → New GitHub App
2. Configure: name `scp-federation-primitive`; homepage URL = SCP repo URL; webhook disabled; permissions = `Repository permissions: Contents: Read-only`; installation scope = "Only on this account"
3. Generate private key; download `.pem` file to a path NOT inside any git worktree (e.g., `~/Downloads/scp-federation-primitive-YYYY-MM-DD.private-key.pem`)
4. SCP repo → Settings → Secrets → Actions → New repository secret `SCP_FEDERATION_APP_PRIVATE_KEY` with the .pem contents
5. Add second secret `SCP_FEDERATION_APP_ID` with the App's numeric ID (for ergonomic env var)
6. Verify App appears at https://github.com/settings/apps/scp-federation-primitive

*Post-ceremony audit (MANDATORY — landed v0.2 per operator strategic-review):*

7. `gh api --paginate repos/jrnb2024/standards-control-plane-/actions/secrets --jq '.secrets[].name' | grep -E "SCP_FEDERATION_APP_(ID|PRIVATE_KEY)"` — confirms BOTH secrets stored. Both must be listed. **`--paginate` flag is MANDATORY (v0.3 SEC-MIN-001 closure)** — without it, GitHub's default 30-item pagination silently truncates the response; if the SCP repo accumulates >30 secrets over time, the audit would return a false negative and the operator could proceed to step 8 destroying the only copy of the private key.
8. `shred -u ~/Downloads/scp-federation-primitive-YYYY-MM-DD.private-key.pem` — secure-delete the `.pem` file after upload + audit. On macOS where `shred` is not standard: `srm -P ~/Downloads/...private-key.pem` or equivalent secure-delete. Verify `.pem` is gone from filesystem.
9. Clear shell history if the operator copy-pasted the key contents through a terminal (`history -c` for bash; equivalent for other shells).
10. **Author App-key rotation SOP file (v0.3 SEC-NIT-001 closure).** Commit a documentation file at `docs/security/app-key-rotation-sop.md` (or equivalent path under `docs/security/`) capturing the 5 content items from TF-PIM-001-SEC-001: (a) key generation procedure; (b) secret storage location + scope (repo-level Actions secret; not org-level); (c) rotation triggers (calendar: 90-day cadence per TF-PIM-001-ARCH-001; event: suspected compromise, account access change, quarterly D-031 review per TF-PIM-001-SEC-005); (d) rotation procedure (generate new key → update repo secret → verify at least one external adopter runs green → delete old key); (e) account-compromise response (delete App entirely → key rotation has no meaning under account compromise; App deletion revokes all installation tokens within minutes). Cross-ref from §12.7.16 (Wave C) and from the D-050 ADR (Wave B).

**Verification.** Operator confirms (a) App + secrets stored (step 7 returns both names; `--paginate` was used); (b) `.pem` securely deleted (step 8 verified); (c) no `.pem` file remains in any local git worktree (`find ~/Projects -name "*.pem" -type f` returns nothing under SCP-related paths); (d) rotation SOP file committed under `docs/security/`. **(v0.3 SEC-NIT-001 closure adds item (d).)**

**Risk surface.** Wave A is the highest single-event risk in the WP — leaking the `.pem` during transit or post-upload-not-deleted gives an attacker the App credential. Mitigation: 4-step `.pem` discipline (0a `.gitignore` check + 0b pre-commit hook verification + step 7 post-upload secrets audit + step 8 `shred -u` secure delete) hardens the canonical attack surface (committed-by-mistake; left-on-disk-post-upload). See §7.1 for the full risk surface decomposition.

**Wave A Tier:** operator-attended (no Codex dispatch; GitHub-UI ceremony)

### Wave B — D-050 ADR drafting + ratification

**Outcome.** `docs/decisions/D-050-tf-pim-001-app-credential-surface-YYYY-MM-DD.md` authored + DECISIONS.md row appended; status DRAFT in file until merge ceremony.

**Actions.**
1. Author D-050 ADR per the existing D-NNN structure (Context / Decision / Rationale / Justification / Cross-references / Tracked-forward items / Sequencing if applicable)
2. ADR captures: App-credential scope decision; §12.7.10 invariant preservation rationale; key-custody posture under D-031; reversal mechanism; relation to TF-PIM-001 plan-doc + ratification evidence files
3. DECISIONS.md row appended (single-table record)
4. Operator review at PR opening; merge ratifies (DRAFT → ACCEPTED at next status-bookkeeping commit per ADR ceremony)

**Verification.** D-050 ADR file present + DECISIONS.md row present; cross-refs to TF-PIM-001 plan-doc + evidence files + sec/arch-skeptic lens TF items.

**Wave B merge ceremony (mandatory operator-attendance — landed v0.2):** D-050's merge is operator-attended ceremony — explicit `gh pr merge` by operator OR explicit operator authorisation via paste-back to orchestrator (matching the established ADR-class merge pattern; D-049 followed the same shape). **Mechanical auto-merge is NOT authorised for ADR-class artefacts** — even when CI is green and `mergeStateStatus: CLEAN`. The ADR ratifies an architectural commitment (App-credential surface + §12.7.10 invariant preservation rationale + key-custody posture under D-031 + reversal mechanism); operator strategic sign-off at merge time is the ratification.

**Wave B Tier:** operator-paced authoring; **operator-attended merge** (no auto-merge for ADR-class)

### Wave C — ADOPT-001 §12.7 updates

**Outcome.** ADOPT-001 §12.7 updated as follows:

- **New §12.7.16 App-install ceremony.** Documents: (a) GitHub App name + install URL; (b) required installation scope (`contents: read` on `standards-control-plane-` only); (c) org-admin access requirement per adopter (D-031 single-operator-mode means @jrnb2024 self-installs on all 5 cohort adopters under @jrnb2024 namespace); (d) what happens if installation is revoked (SCP-E001 emission, not silent); (e) how to verify installation is active before invoking `enable-required-check.sh`.
- **§12.7.5 amended (de-adoption).** New step: after wrapper deletion + branch-protection removal, adopter org-admin must revoke the `scp-federation-primitive` App installation from Settings → Integrations → GitHub Apps. Residual installation = persistent unnecessary access vector.
- **§12.7.10 reaffirmed.** Explicit note: Path C ratified 2026-05-21 with `secrets: inherit` STILL prohibited. App credential obtained inside SCP-controlled workflow code; never passed via caller secrets. §12.7.10 invariant fully preserved.
- **§12.7.13 amended (supply-chain).** Adds the `generate-app-token` action as a SHA-pinned dependency tracked in `scripts/scp-policy-check.lock` (or equivalent supply-chain tracking shape). **Action selection decision rule (operator-strategic-review v0.2):** PRIMARY is `actions/create-github-app-token` (GitHub first-party) for supply-chain provenance + cohesion with the existing `actions/checkout` pattern; FALLBACK is `tibdex/github-app-token` (well-established third-party) **only if** `actions/create-github-app-token` has a documented blocker at SHA-pin time (e.g., the version we'd pin has a known CVE, or the action publishes no commit SHAs we can pin to). The fallback decision MUST be documented in §12.7.13 inline (named action; pinned SHA; the documented blocker that triggered fallback; the verification step proving the fallback action's supply-chain posture). Default expectation: PRIMARY chosen unless Wave D dispatch surfaces a concrete blocker.

**Actions.**
1. Read existing ADOPT-001 §12.7 verbatim to anchor edits
2. Author §12.7.16 covering the 5 substantive items above
3. Amend §12.7.5 with revocation step
4. Add reaffirmation footnote to §12.7.10
5. Amend §12.7.13 with action SHA-pin

**Verification.** §12.7 reads coherently end-to-end; cross-refs to D-050 + this WP plan-doc.

**Wave C Tier:** operator-paced authoring; can dispatch Codex for §12.7.16 drafting (mechanical-doc-add) at operator discretion

### Wave D — Reusable workflow change (Codex Tier 2 dispatch)

**Outcome.** `.github/workflows/policy-check.yml` amended: token-exchange step added; cross-repo `actions/checkout` steps (lines 107, 1149-1154 in current SHA) use the App installation token via `token:` parameter.

**Actions.**
1. Pin the `generate-app-token` action by 40-char commit SHA. **PRIMARY: `actions/create-github-app-token@<SHA>`** (GitHub first-party action; chosen for supply-chain provenance + cohesion with the existing `actions/checkout` pattern). **FALLBACK: `tibdex/github-app-token@<SHA>`** (well-established third-party) — engaged ONLY if PRIMARY has a documented blocker at SHA-pin time (e.g., the version we'd pin has a known CVE; the action publishes no commit SHAs we can pin to; the action's permissions surface doesn't match our `repository_permissions: { contents: read }` requirement). The fallback decision rule is canonical-documented in §12.7.13 amend (Wave C). Default expectation: PRIMARY chosen; FALLBACK requires Codex dispatch to surface a concrete blocker + that blocker must be captured in §12.7.13 inline (named action; pinned SHA; documented blocker; verification step proving the fallback action's supply-chain posture).
2. Add "Obtain App installation token" step BEFORE the cross-repo `actions/checkout` step at line 107:
   ```yaml
   - name: Obtain SCP federation App installation token
     id: scp-app-token
     if: github.action_ref != ''
     uses: actions/create-github-app-token@<SHA-PIN>
     with:
       app-id: ${{ secrets.SCP_FEDERATION_APP_ID }}
       private-key: ${{ secrets.SCP_FEDERATION_APP_PRIVATE_KEY }}
       owner: jrnb2024
       repositories: standards-control-plane-
   ```
3. Update the "Checkout SCP runtime repository" step (line 107) to use `token: ${{ steps.scp-app-token.outputs.token }}` — preserve `persist-credentials: false`
4. Update the "Check out SCP repo at workflow ref for schema lookup" step (line 1149) identically
5. Preserve all other workflow logic + invariants
6. SCP-self dogfood case (same-repo invocation; `github.action_ref` empty): token-exchange step skips per the `if:` guard; default `GITHUB_TOKEN` continues to suffice for the self-call fallback

**Verification.** Workflow YAML parses cleanly; no other workflow logic touched.

**Wave D Tier:** **Tier 2 Codex dispatch** (kernel-dangerous federation primitive change). Operator-attended fire. Standard four-tier protocol: Codex executor; 3-lens R1+R2 review (sec / arch-skeptic / pragmatist per `feedback_orchestrator_auth_surface_plan_review_default.md`); DO-NOT-EDIT sub-agent mandate per `feedback_subagent_review_only_scope_must_be_enforced`; R-cycle to R-fixpoint MET; preflight grep MANDATORY.

### Wave E — Workflow-selftest harness coverage (TF-PIM-001-ARCH-002)

**Outcome.** `tests/workflow-selftest/` (or equivalent path) gains coverage for the App token-exchange failure mode — when the App key is misconfigured / installation missing / GitHub App API unavailable, the workflow fails with `SCP-E001` rather than continuing silently.

**Parallelism with Wave D (clarified v0.2; refined v0.3 ARCH-MIN-001 closure):** Wave E **fixture-design authoring** (test design + env-var contract + selftest harness updates) **may run in parallel** with Wave D's authoring. **HOWEVER:** the `SCP_TEST_SIMULATE_APP_TOKEN_FAILURE` env-var check injected into `policy-check.yml`'s token-exchange step (Wave E Actions step 2) **MUST land in the same PR as Wave D** — both Wave D and Wave E modify `policy-check.yml`; separate PRs would conflict on that file. The mandatory coupling is: Wave E fixture-design parallels Wave D authoring; Wave E env-var injection commits with the Wave D PR (single commit OR Wave E's selftest changes merged into the same Wave D PR branch before Wave D's Tier 2 dispatch fires). Wave E **verification** (selftest CI run shows the fixture executing) depends on the merged Wave D + Wave E PR landing first.

**Approach selection (v0.2 strategic-review decision):**

- **v0.1 ships mock-based coverage.** A stub-mode env-var flag `SCP_TEST_SIMULATE_APP_TOKEN_FAILURE=1` short-circuits the token-exchange step to emit `SCP-E001` without actually attempting the GitHub App API call. Rationale: simpler to author + test; deterministic in CI without external dependencies; sufficient to verify the workflow's error-path code is wired correctly. Less robust than real-API coverage but acceptable as v0.1 of the selftest fixture.
- **TF-PIM-001-ARCH-002 follow-up adds real-API coverage.** A future fixture exercises a real (test) App with an intentionally-broken installation, calling the real GitHub App API and verifying the actual failure mode. Out-of-scope for this WP; tracked-forward.

**Actions.**

1. Identify the existing selftest harness structure (workflow fixture-pass / fixture-fail entries)
2. Add the `SCP_TEST_SIMULATE_APP_TOKEN_FAILURE` env-var flag check at the top of the token-exchange step in `policy-check.yml`; when set, exit with `SCP-E001` annotation immediately
3. Add fixture entry in selftest workflow exercising this env-var (workflow-level test that passes the env-var into the reusable workflow's run-context)
4. Verify the workflow emits `SCP-E001` annotation + commit-status fail under the simulated failure
5. Document the new fixture in `tests/workflow-selftest/README.md` (or equivalent) + cross-ref to TF-PIM-001-ARCH-002
6. Document the mock-vs-real-API decision rationale + the follow-up real-API coverage TF in the fixture doc

**Verification.** Selftest CI run shows the new fixture executing + producing the expected `SCP-E001` error code under simulated failure mode.

**Wave E Tier:** Tier 2 Codex dispatch (touches CI fixture + workflow indirectly). Authoring parallel with Wave D acceptable; verification gated on Wave D landing first.

### Wave F — SCP-self dogfood verification

**Outcome.** SCP-self CI runs green on a test PR with the new policy-check.yml workflow.

**Actions.**
1. Open a small test PR on SCP itself (after Waves A + B + C + D + E land) — could be a docs-only PR or this WP plan-doc's closure amend
2. Verify all 4 required checks pass: `policy-check / scp/policy-check`, `policy-check-readback`, `check-invocation-log-entry`, `validate PR body`
3. Verify the SCP-self dogfood path: `github.action_ref` empty → token-exchange step skips → self-call fallback engages → all 12 policy-check steps complete
4. Capture evidence URL

**Verification.** Test PR's CI rollup all SUCCESS; SCP-self dogfood unchanged.

**Wave F Tier:** operator-attended (verify-only)

### Wave G — External-adopter cross-repo verification (PIM canary)

**Outcome.** PIM exercises the new federation primitive cross-repo with all 12 policy-check steps green.

**Actions.**
1. Operator-attended App install on PIM (`mapp-pim/mapp-pim`): visit `https://github.com/apps/scp-federation-primitive/installations/new` → select PIM repo → confirm scope = `Read access to code on jrnb2024/standards-control-plane-` only
2. Verify installation via `gh api /app/installations` (requires authenticated as the App; alternative: PIM repo Settings → Integrations → GitHub Apps shows the install)
3. Open a small test PR on PIM. **Canary PR MUST be designed denial-free (v0.3 ARCH-MAJ-002 closure).** Recommended shape: a noop change to a file path outside ALL `SCP-R-*` evaluation surface (e.g., add a docs section to a `README.md` in a non-frontend path; explicitly avoid `services.yml`, `policies/`, any `.scp/` config, any TypeScript/JavaScript path that might trigger SCP-R-001..004). If a `SCP-R-NNN` deny finding fires on the canary PR despite this design intent, that is a separate investigation per §7.6 Branch 4 (NOT a federation-primitive failure) — but AC #1 is NOT satisfied until a denial-free canary run is captured. GitHub Actions runs the wrapper which invokes the SCP reusable workflow cross-repo
4. Verify all 12 policy-check steps complete + green; capture run URL
5. Verify the App token was successfully obtained + used for both cross-repo checkout steps; `persist-credentials: false` preserved (no App token written to artefacts)

**Verification.** PIM CI run URL with all 12 policy-check steps green; App installation verified active.

**Wave G Tier:** operator-attended

### Wave H — PIM `main` required-check restoration + TF-PIM-001 closure

**Outcome.** PIM `main`'s `policy-check / scp/policy-check` re-enters required contexts; TF-PIM-001 closes; STATUS.md + BACKLOG.md updated.

**Actions.**
1. Operator runs `scripts/enable-required-check.sh --repo mapp-pim/mapp-pim --branch main --preserve-existing-contexts` (dry-run first via `--plan`)
2. Verify post-PUT: `gh api repos/mapp-pim/mapp-pim/branches/main/protection --jq '.required_status_checks.contexts'` returns set containing `"policy-check / scp/policy-check"`
3. Invocation log entry written to `docs/reviews/WP-SCP-020/branch-protection-log.md`
4. STATUS.md `Last updated:` header refresh + new "Today's chain" entry capturing TF-PIM-001 closure
5. BACKLOG.md Phase 12 → strikethrough TF-PIM-001 row with closure date + cross-ref to this WP's final commit
6. FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001 unblock signal — open separate impl slice once scaffolder can be verified against a real adopter run (out-of-scope this WP, captured as follow-up)

**Verification.** PIM `main` protection state restored; STATUS.md + BACKLOG.md reflect closure; invocation log entry committed.

**Wave H Tier:** operator-attended

## §5 Review shape

### 5.1 R-cycle protocol for this plan-doc

3-lens R1 from R1 (auth-adjacent — TF-PIM-001 IS the auth-surface):

- **Lens 1 — correctness.** Does the plan-doc accurately reflect Path C ratified scope? Are all 10 TF-PIM-001-{SEC,ARCH}-* items mapped to a wave or explicitly TF-carried? Are §3.2 out-of-scope items consistent with the ratification rationale (irreversibility-asymmetry preserved; multi-org coordination deferred)?
- **Lens 2 — safety_bypass.** Does any wave introduce a new bypass surface? Does Wave D's workflow change preserve §12.7.10 invariant + invariants 1-5 from the plan-doc's §4 threat-model recap? Are the App secret storage requirements (`SCP_FEDERATION_APP_PRIVATE_KEY` as repo-scoped, not org-scoped) explicit? Does Wave A's operator-attended ceremony adequately mitigate `.pem` exposure risk during transit?
- **Lens 3 — completeness_governance.** Are all 5 §2 acceptance criteria captured + verifiable? Is the D-050 ADR scope sufficient? Does §3 inherited-TF table close the loop with the evidence files? Is Tier 2 dispatch operator-attended fire explicit at Wave D?

R-cycle to R-fixpoint MET (no new significant findings on a fresh round) OR R4 mechanical override at R3 if diminishing-returns trajectory.

### 5.2 R-cycle protocol for individual waves

- Wave A (operator-attended ceremony) — no R-cycle; operator-verified at execution
- Wave B (ADR drafting) — 3-lens R1; operator-attended merge
- Wave C (ADOPT-001 doc updates) — 3-lens R1; mechanical-doc-add pattern
- Wave D (workflow change — Tier 2) — 3-lens R1+R2 to R-fixpoint MET; Codex dispatch; operator-attended fire; cure-worse trigger active; Option A R4 mechanical override at R3 if diminishing-returns
- Wave E (selftest fixture) — 3-lens R1; same-PR coupling with Wave D acceptable
- Wave F (SCP-self verify) — operator-attended; no R-cycle
- Wave G (PIM canary) — operator-attended; cross-cutting check against §2 acceptance criterion 1
- Wave H (PIM restoration + closure) — operator-attended; cross-cutting check against §2 criteria 2 + 5

### 5.3 DO-NOT-EDIT sub-agent mandate

Per `feedback_subagent_review_only_scope_must_be_enforced` (sample-size-2 across CT + Recommender 48h; load-bearing pending ACC harness-level fix per ACC PR #247):

All R-cycle sub-agents dispatched for this WP MUST be read-only (Plan agent type per the established estate pattern; no Edit/Write/NotebookEdit tools). Sub-agent outputs return as text to the orchestrator; orchestrator writes evidence files. Sub-agents writing to disk = scope-breach failure = R0 trigger.

### 5.4 Preflight grep — MANDATORY pre-R1

Per `feedback_dispatch_scope_omission_pre_flight_check` + `feedback_int_pre_grep_at_plan_ready`:

Before R1 dispatch, run:

```bash
grep -oE "(INT-|FUP-|TF-|ASC-|D-)[A-Z0-9_-]+" docs/plans/TF-PIM-001-impl-path-c-app-credential.md | sort -u
# Cross-check each citation against BACKLOG.md (INT/FUP/TF) OR docs/decisions/ (D-NNN) OR memory dir (feedback_*)
```

HARD-FAIL on phantom citation. If any citation has no backing artefact, fold filing into this plan-doc as a v0.2 amend before R1 dispatch.

### 5.5 Cure-worse trigger

If R-cycle fixpoint stalls past R3 with diminishing-returns (per `feedback_asymptotic_trajectory_split.md`):

- R3 closures introduce new latent defects in the just-fixed area → diminishing-returns signal
- Trigger: Option A R4 mechanical override (sub-agent dispatches a fresh perspective; if same finding-class re-emerges, surface as scope-split candidate)
- Scope-split candidate: carve sub-surface to sibling slice (Wave D's selftest harness coverage carve to Wave E was already this pattern at plan-doc authoring time)

## §6 Verify

### 6.1 SCP-self dogfood acceptance (Wave F)

```bash
# After Wave D ships:
gh pr create --repo jrnb2024/standards-control-plane- --base main --head <test-branch> --title "test: dogfood verify post-Path-C workflow change" --body "..."
gh pr view <#> --json statusCheckRollup --jq '[.statusCheckRollup[] | .conclusion // .state]'
# Expect: all SUCCESS for 4 required checks
```

### 6.2 External-adopter cross-repo green (Wave G)

```bash
# After Wave A + D ship + App installed on PIM:
gh pr create --repo mapp-pim/mapp-pim --base main --head <pim-test-branch> --title "test: cross-repo verify post-Path-C" --body "..."
# Wait for CI; capture run URL
gh run list --repo mapp-pim/mapp-pim --branch <pim-test-branch> --limit 1 --json status,conclusion,url
# Expect: status=COMPLETED, conclusion=SUCCESS; all 12 policy-check steps green
```

### 6.3 PIM `main` required-check restored (Wave H)

```bash
gh api repos/mapp-pim/mapp-pim/branches/main/protection --jq '.required_status_checks.contexts'
# Expect: array containing "policy-check / scp/policy-check"
```

### 6.4 §12.7.10 invariant preservation (cross-cutting) — v0.3 SEC-MIN-002 + ARCH-NIT-001 closures

```bash
# Primary verification: estate-wide code search.
# Authentication scope requirement: GITHUB_TOKEN or PAT with `repo` scope
# (gh search code covers private repos for authenticated identities with repo scope).
gh search code --owner=jrnb2024 'secrets: inherit'
# Expect: zero matches in ANY policy-check-wrapper.yml file in the @jrnb2024 namespace,
# INCLUDING SCP-self (jrnb2024/standards-control-plane-/.github/workflows/policy-check-wrapper.yml).
# (v0.3 ARCH-NIT-001 closure — scope explicitly includes SCP-self wrapper, not only adopter wrappers.)

# Caveat: GitHub Code Search has known indexing lag (minutes to hours typically; longer
# occasionally). A recently added `secrets: inherit` may not appear in search results
# during the lag window.

# Secondary verification (v0.3 SEC-MIN-002 closure):
# For the Wave D fix PR specifically, run a LOCAL grep against the SCP repo checkout
# to confirm no `secrets: inherit` was introduced by the workflow change:
cd /Users/amplience/Projects/standards-control-plane
grep -rE 'secrets:[[:space:]]*inherit' .github/workflows/
# Expect: zero matches.
# The Wave D R-cycle protocol (§5.2) MUST include this local grep as part of the
# Wave D fix PR's R-cycle self-verification (the local check is indexing-lag-free
# and authoritative for the fix PR's own changeset).
```

### 6.5 R1-evidence-on-fix-PR (Wave D + cross-cutting)

PR body for the Wave D Codex dispatch slice MUST carry:

```
## R1 evidence

- correctness: <link to lens evidence file + CI URL>
- safety_bypass: <link to lens evidence file + CI URL>
- completeness_governance: <link to lens evidence file + CI URL>

CI citation pair:
- policy-check / scp/policy-check: SUCCESS @ <CI URL>
- mergeStateStatus: CLEAN
```

Per `feedback_r1_surface_must_cite_ci.md`.

## §7 Risks

### 7.1 Wave-A `.pem` exposure during App private-key upload

**Risk.** Operator downloads `.pem` from GitHub Apps settings; uploads to SCP repo secret; clipboard or filesystem retains the private key briefly. Three canonical attack surfaces: (a) committed-by-mistake into a git worktree; (b) left-on-disk-post-upload + indexed by a backup/sync process; (c) shell-history-captured if pasted through a terminal.

**Mitigation — 4-step `.pem` discipline (v0.2 landed; see Wave A Actions):**
- **0a — `.gitignore` pattern check pre-generate.** `*.pem` in SCP repo `.gitignore` BEFORE the App key is generated — addresses attack surface (a)
- **0b — Pre-commit hook verification.** Local pre-commit hook (if installed) rejects staged `.pem` files; otherwise procedural ceremony step — defense-in-depth on attack surface (a)
- **Step 7 — Post-upload audit.** `gh api --paginate .../actions/secrets --jq '.secrets[].name'` confirms BOTH `SCP_FEDERATION_APP_PRIVATE_KEY` + `SCP_FEDERATION_APP_ID` are stored before proceeding — proves the upload landed. **`--paginate` flag is MANDATORY (v0.3 SEC-MIN-001 closure)** — without it, GitHub's default 30-item pagination silently truncates the response and the audit returns a false negative on repos with >30 secrets.
- **Step 8 — `shred -u` secure delete.** After audit success, securely delete the `.pem` file from local filesystem — addresses attack surfaces (b) and partially (c)
- **Step 9 — Shell history clear.** `history -c` (or shell-equivalent) — closes attack surface (c)
- **SCP repo secret is scoped to Actions context only** (not org-level; not visible in repo settings UI except as `********`)
- **If exposure suspected:** delete App + recreate; rotation procedure documented in TF-PIM-001-SEC-001 / ARCH-001

**Severity.** HIGH if exposure occurs (full App credential leaked); LOW probability if Wave A 4-step discipline followed in full.

### 7.2 Tier 2 Codex dispatch on Wave D introduces unanticipated workflow regression

**Risk.** The workflow change is auth-surface-touching + executes on every adopter PR; a regression could block every external adopter simultaneously.

**Mitigation.**
- Tier 2 dispatch per WP-SCP-022 protocol: Codex executor; 3-lens R1+R2 to R-fixpoint MET; DO-NOT-EDIT sub-agent mandate
- Wave E selftest harness coverage exercises the token-exchange failure mode before Wave D's PR merges
- Wave F SCP-self dogfood verification fires before any external adopter is exposed
- Wave G PIM canary is the first external-adopter exposure; broader cohort exposure deferred to future cascade slices
- Rollback mechanism: revert the Wave D PR; SCP-self continues working (same-repo `GITHUB_TOKEN` self-call fallback); external adopters return to pre-WP failure mode (no NEW failure introduced by rollback)

**Severity.** MEDIUM (bounded blast radius — only external adopters affected; SCP-self continues green; rollback is single-PR revert)

### 7.3 D-031 single-operator bus-factor on App-credential custody

**Risk.** @jrnb2024 holds the App private key exclusively. Account compromise OR @jrnb2024 unavailable during key rotation = blocked external adopter cascade.

**Mitigation.**
- Rotation SOP authored in Wave A + Wave C; 90-day rotation cadence per TF-PIM-001-ARCH-001
- 2026-07-21 quarterly D-031 review (TF-PIM-001-SEC-005) extends to include App-key custody audit
- Second-maintainer onboarding (operator-paced) eliminates bus-factor-1 once it lands
- App installation tokens auto-rotate every 1 hour (GitHub-managed); compromise window is bounded by token TTL not key TTL

**Severity.** MEDIUM (same bus-factor-1 risk as every other SCP-side governance artefact; not novel to this WP)

### 7.4 `generate-app-token` action's upstream supply-chain (per TF-PIM-001-SEC-003)

**Risk.** The new third-party action (`actions/create-github-app-token` or equivalent) becomes a new supply-chain dependency. Upstream compromise → SCP federation primitive compromise.

**Mitigation.**
- 40-char commit SHA pin (no tag refs) per WP-SCP-022 supply-chain posture
- CODEOWNERS coverage on `.github/**` ensures unauthorised SHA-pin updates are blocked
- Sigstore attestation status evaluated at Wave D (same TF-007 parallel for OPA / Conftest / Regal — if action publishes Sigstore attestations, `gh attestation verify` ratchets up)
- Action selection: prefer `actions/create-github-app-token` (GitHub first-party) over third-party for provenance

**Severity.** LOW-MEDIUM (single SHA-pin dependency; mitigated by existing supply-chain posture)

### 7.5a Wave D rollback strategy (if Wave F dogfood fails) (v0.2 added)

**Risk.** Wave D's workflow change lands; Wave F SCP-self dogfood verification surfaces an unanticipated regression (token-exchange step misbehaves on real GitHub Actions; cross-repo checkout fails despite App-install present; some interaction with the existing workflow logic breaks).

**Explicit rollback path:**

1. **Revert Wave D commit on fresh branch.** New branch `chore/revert-tf-pim-001-wave-d` based on main; `git revert <wave-d-merge-commit-SHA>`; push + open revert PR; standard CI + self-merge per pre-authorised pattern.
2. **SCP-self workflow reverts to default `GITHUB_TOKEN`.** The same-repo `github.action_ref` empty branch still works; SCP-self CI continues green.
3. **Operator-attended temporary branch-protection toggle (v0.3 ARCH-MAJ-001 closure).** `policy-check / scp/policy-check` removed from SCP main's required contexts ONLY IF Wave D regression also breaks SCP-self dogfood. **Invocation shape: direct `gh api PATCH` (NOT `enable-required-check.sh --restore`).** Rationale: SCP-self's branch protection was installed via WP-SCP-020 020D2, NOT via `enable-required-check.sh` forward-mode; there is no captured pre-state JSON in `docs/reviews/WP-SCP-020/branch-protection-log.md` for `--restore` to consume per D-047. The operator must construct the toggle manually. Suggested invocation:

   ```bash
   # Step 1 — Capture current state first (MANDATORY; the captured JSON is the
   # source-of-truth for both rollback-time toggle AND restoration; v0.4 ARCH-MIN-001-R2
   # closure — full state preservation, not memory-reconstruction):
   gh api repos/jrnb2024/standards-control-plane-/branches/main/protection > /tmp/scp-main-pre-rollback.json

   # Step 2 — Toggle: rebuild contexts array EXCEPT policy-check / scp/policy-check.
   # Uses jq extraction from the pre-state capture so the OTHER required contexts
   # (`check-invocation-log-entry`, `policy-check-readback`, `validate PR body`,
   # any future additions) are preserved verbatim. v0.4 ARCH-MIN-001-R2 closure
   # — the prior v0.3 illustrative PATCH hard-coded only one context which would
   # have silently dropped `policy-check-readback` + `validate PR body` if executed
   # verbatim under rollback time-pressure.
   #
   # Extract preserved contexts (all current contexts MINUS the SCP policy-check one):
   PRESERVED_CONTEXTS=$(jq -c '[.required_status_checks.contexts[] | select(. != "policy-check / scp/policy-check")]' /tmp/scp-main-pre-rollback.json)
   echo "Preserved contexts (to keep): $PRESERVED_CONTEXTS"
   # Sanity-check the operator can read what's about to land — if PRESERVED_CONTEXTS
   # is unexpectedly empty or omits a context that should be there, abort + investigate
   # BEFORE the PATCH fires.

   # Construct full PATCH body from the pre-state, replacing only contexts:
   jq --argjson preserved "$PRESERVED_CONTEXTS" \
      '.required_status_checks.contexts = $preserved' \
      /tmp/scp-main-pre-rollback.json \
      > /tmp/scp-main-rollback-target.json

   # Apply PATCH:
   gh api -X PATCH repos/jrnb2024/standards-control-plane-/branches/main/protection \
     --input /tmp/scp-main-rollback-target.json

   # Verify:
   gh api repos/jrnb2024/standards-control-plane-/branches/main/protection --jq '.required_status_checks.contexts'
   # Expect: the original contexts minus `policy-check / scp/policy-check`
   ```

   **Restoration** (post Wave D v0.2 landing) uses the captured `/tmp/scp-main-pre-rollback.json` DIRECTLY as the PATCH input (`gh api -X PATCH ... --input /tmp/scp-main-pre-rollback.json`) — full state restore, no manual reconstruction needed. `enable-required-check.sh --restore` remains NOT applicable for SCP-self until 020D2's installation is retroactively logged. If SCP-self continues green during Wave F (the common case), no protection toggle needed on SCP — this step only fires when SCP-self dogfood ALSO fails.
4. **Debug + author v0.2 of Wave D.** Diagnose the regression; iterate the Wave D workflow change; new R-cycle to R-fixpoint MET; new Codex Tier 2 dispatch (operator-attended fire) on the corrected v0.2 of Wave D.
5. **Wave F re-verify; Wave G re-attempt only after F green.** Strict gate — no external adopter exposure until SCP-self is provably green at the new Wave D version.

**Mitigation invariants under rollback:**
- App + secrets stored in Wave A remain intact (no need to re-do Wave A on rollback — rollback is workflow-level only)
- ADOPT-001 §12.7 updates from Wave C remain intact (docs can stay published; they document the intended-state behavior; an explicit "WAIVED PENDING WAVE D v0.2" callout may be added)
- D-050 ADR remains ratified (the architectural commitment to App-credential surface is path-direction-correct; only the workflow change is regressed)

**Severity.** LOW-MEDIUM (rollback is fully bounded; SCP-self dogfood acts as the firewall preventing external-adopter exposure before regression confirmation; Wave G PIM canary is the earliest external-adopter exposure point per §4 wave sequencing)

### 7.5 Path C 1-2 week implementation timeline overruns + PIM degraded state persists longer

**Risk.** Wave D's R-cycle stalls past R3 (cure-worse trigger fires); plan-doc authoring + R-cycle + dispatch + verification takes longer than estimated.

**Mitigation.**
- D-049 §Sequencing decouples v1.3.0 ship from TF-PIM-001 close; PIM degraded state does not block v1.3.0 ship-readiness
- PIM team's productive work continues during the degraded window (Phase 4 labeller workflow per operator's calendar note)
- §10 STEP 1 escalation path (re-open with E + F) remains available if A/C/D timing becomes load-bearing — though arch-skeptic already evaluated E/F as not Pareto-better than C
- §5.5 cure-worse trigger + Option A R4 mechanical override actively monitors for diminishing-returns

**Severity.** LOW (timeline slip is bounded; no second-order failure)

### 7.6 Wave G failure-mode decision tree (PIM canary cross-repo verification) (v0.2 added)

**Risk.** Wave G PIM canary surfaces a failure during cross-repo verification — what's the diagnosis + remediation tree?

**Decision tree:**

1. **App-install verified active but token-exchange fails.** SCP-side workflow issue. Symptoms: token-exchange step emits `SCP-E001`; checkout steps skip; logs show GitHub App API errors. Diagnosis: App private key wrong in SCP secret OR App ID wrong OR `actions/create-github-app-token` (or fallback) misconfigured. Remediation: debug the workflow on SCP-self first (re-run Wave F); iterate Wave D if needed; do NOT proceed to retry Wave G until SCP-self repassed Wave F.

2. **App-install fails OR not visible on PIM after install ceremony.** Operator-attended re-install. Symptoms: PIM workflow can't find the App installation; permissions errors. Diagnosis: org-admin access on PIM didn't materialise; install scope didn't pick the right repo; install was on @jrnb2024 account-level not PIM-repo-level. Remediation: verify org-admin access via `gh api user/installations`; re-do install ceremony with explicit repo scope; document the install-path in §12.7.16 if a step was missed.

3. **Token exchanges successfully but cross-repo checkout fails.** Cross-repo permission scope issue. Symptoms: token-exchange step green; subsequent `actions/checkout` step fails with permission-denied. Diagnosis: App's `repository_permissions` not `{ contents: read }` OR scope set to wrong repo. Remediation: verify App permissions match `repository_permissions: { contents: read }` on `jrnb2024/standards-control-plane-` only; if scope drift detected, this is an App-config-level issue + must update §12.7.16 verification step (post-install verify) to catch this before Wave H restoration runs.

4. **All 12 federation-primitive infrastructure steps execute successfully but a `SCP-RNNN` deny finding fires (v0.3 ARCH-MAJ-002 reword).** Federation-primitive infrastructure is WORKING AS DESIGNED — the workflow executed, the rule evaluated, the deny fired correctly. **However, AC #1 is NOT satisfied by this run** — AC #1 requires "all 12 policy-check steps complete with PASS verdict" (v0.3 wording). The canary PR was designed denial-free per Wave G Action step 3; a deny finding indicates the canary-PR-design intent was missed (e.g., the chosen file path was inside an SCP-R-* evaluation surface after all). Diagnosis: re-examine the canary PR's changeset against `policies/SCP-R-*.rego` evaluation paths; if the deny is a true positive, the PR was misdesigned and a fresh canary PR needs to be opened. If the deny is a false positive on the federation primitive's part, that's a separate `SCP-RNNN` defect surface (not a TF-PIM-001 failure). **Remediation:** re-open Wave G with a corrected canary PR; do NOT mark AC #1 satisfied until a denial-free run is captured. Branches 1-3 above remain the federation-primitive failure surface; Branch 4 is the canary-PR-design failure surface (separable concern).

5. **Persistent failure after 2 verification attempts.** Operator-attended escalation. Symptoms: Wave G fails on first attempt → operator diagnoses + iterates → Wave G fails on second attempt with the same root cause OR a related root cause. Diagnosis: structural blocker in Path C implementation that wasn't surfaced in R-cycle review. Remediation: file ASC; consider §10 STEP 1 escalation of the parent plan-doc (re-open with Paths E + F); operator-attended architectural-scope decision. Do not retry Wave G a third time without operator authorisation + a documented diagnosis.

**Severity.** LOW (decision tree is bounded; persistent failure has explicit escalation; no unbounded retry loop)

## §8 Standdown semantics

Real triggers only (per estate-wide discipline):

1. CRIT arch-scope question (operator-attended ASC)
2. Cure-worse-than-disease (R3 ship-proposal trigger)
3. Real context window degradation
4. ASC needing operator authorisation
5. Genuine resource constraint (Sonnet quota)

If implementation WP authoring (this v0.1 → v0.X iteration) surfaces an architectural-scope question on App-token surface vs SCP-side workflow restructure → file ASC + stand down for operator authorisation.

Otherwise: chain through R-cycle to R-fixpoint MET; then surface for operator review before any Wave D Codex dispatch fires.

### 8.1 Recommended operator-attended gate batching (v0.3 PRAG-NIT-001 closure)

Waves A (App authoring ceremony), B (D-050 ADR merge), F (SCP-self dogfood verify), G (PIM canary + App install), and H (PIM required-check restoration + closure) are all operator-attended. To minimise operator-attention context-switches under D-031 single-operator-mode, batch as follows:

- **Session 1 (Wave A + Wave B):** App authoring ceremony followed by D-050 ADR merge in the same session, IF the D-050 ADR is pre-drafted before the operator session begins (Wave B's authoring step is operator-paced; if completed in a prior session, the merge step is short-enough to batch with Wave A).
- **Session 2 (Wave D Tier 2 dispatch fire):** standalone — Wave D's R-cycle is multi-day; the dispatch fire itself is one operator-attended moment but the R-cycle iteration is autonomous-scope.
- **Mechanical (Wave F):** SCP-self dogfood verify is a single CI run + evidence capture; can be done by the operator as a checkbox between Sessions 2 and 3 (not strictly a "session").
- **Session 3 (Wave G + Wave H):** PIM canary App install + cross-repo verify + PIM main required-check restoration + closure ceremony in one session. Both waves short (45 min + 20 min); sequential by design; natural batching point.

Total: 3 operator-attended sessions + 1 mechanical Wave F verify (vs 5 separate sessions if not batched). Each batched session needs ~1 hour of operator attention.

## §9 Follow-ups

- TF-PIM-001-PLAN-002 (D-NNN ADR) — INHERITED from the closed plan-doc; delivered in Wave B
- TF-PIM-001-PLAN-004 (PIM required-check restoration) — INHERITED; delivered in Wave H
- TF-PIM-001-SEC-001..005 — INHERITED from sec lens evidence file; mapped per §3.3 table
- TF-PIM-001-ARCH-001..005 — INHERITED from arch-skeptic lens evidence file; mapped per §3.3 table
- **FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001 (P1) — unblocks at Wave G PIM canary green (v0.3 PRAG-MIN-001 closure).** Close condition: Wave G success (PIM canary CI run all 12 steps PASS verdict + denial-free, per AC #1 wording) IS the unblock signal. Immediately-actionable fix at Wave H closure: BACKLOG path (a) — remove `with: scorecard-emit: false` from scaffolder template (`scripts/scaffold-downstream.sh`). File separate impl slice at Wave H closure; do NOT defer to next cascade batch. Validation-evidence: Wave G CI run URL serves both TF-PIM-001 AC #1 AND scaffolder fix validation (per §3.2 v0.3 ARCH-MIN-002 closure).
- **TF-PIM-001-ARCH-002 real-API selftest coverage follow-up (v0.3 ARCH-MIN-003 closure).** Wave E ships mock-based fixture (`SCP_TEST_SIMULATE_APP_TOKEN_FAILURE` env-var); real-API coverage adds a fixture that exercises a real (test) App with an intentionally-broken installation, calling the real GitHub App API and verifying the actual failure mode. Operator-paced; sequenced after Wave H closure; close condition: a real-API selftest fixture lands under `tests/workflow-selftest/` (or equivalent) and exercises in CI.
- **WP-SCP-024 §5.2 amendment at first 024D dispatch (v0.3 PRAG-MIN-002 closure — explicit).** WP-SCP-024 §5.2 (per-adopter onboarding contract) MUST be amended at the FIRST 024D cascade slice dispatch to add: "App-install ceremony per adopter is a cascade-slice deliverable; operator-attended; the §12.7.16 install ceremony is the canonical gate that runs BEFORE `enable-required-check.sh` per adopter." Without this amendment, the 024D dispatch runner may not know to look at §12.7.16 for the install step.
- **Recommender cascade slice is first practical test of same-namespace App-install (v0.3 PRAG-MIN-002 closure — second part).** D-049 D3 commits Recommender as first deny-gate adopter; Recommender's cascade slice (within 024D-024G) is the first instance of a non-PIM App-install ceremony in a real adopter context. The §12.7.16 ceremony documentation should be validated against Recommender's specific repo state at that cascade slice; if §12.7.16 needs amendment based on what Recommender's onboarding surfaces, that amendment captures the multi-org coordination start (even if Recommender is also in @jrnb2024 namespace — same-namespace install is still a different ceremony shape from PIM's brownfield-canary install).
- 2026-08-21 first App-key rotation execution — operator-attended; per TF-PIM-001-ARCH-001 cadence
- 2026-07-21 quarterly D-031 review extension — operator-attended; per TF-PIM-001-SEC-005
- Future cascade slices (024D-024G) inherit App-install ceremony per adopter — see WP-SCP-024 §5.2 amendment entry above

## §10 Closure

WP-closure when all 5 §2 acceptance criteria are satisfied:

1. ✅ External-adopter (PIM) cross-repo run green
2. ✅ PIM `main` `policy-check / scp/policy-check` required-check restored
3. ✅ ADOPT-001 §12.7 updated (§12.7.16 added; §12.7.5 amended; §12.7.10 reaffirmed; §12.7.13 amended)
4. ✅ D-050 ADR ratified
5. ✅ R1-evidence-on-fix-PR satisfies cardinal-rule-2 3-lens + CI citation pair

Closure ceremony:
- STATUS.md final entry under "Today's chain (YYYY-MM-DD — TF-PIM-001 CLOSED)" capturing all 5 criteria + evidence URLs
- BACKLOG.md Phase 12 → TF-PIM-001 row strikethrough with closure date + closure-commit SHA
- This plan-doc Status flips DRAFT → CLOSED at the closure-ceremony commit
- D-049 §Sequencing item 2 ("TF-PIM-001 closes") artefact-gate satisfied → Recommender becomes the natural next deny-gate adopter per D-049 D3 ratification

---

## §11 Wave G Path C v2 amendment (v0.5 — 2026-05-23 per ASC-2026-05-22-001)

### 11.1 Why this amendment exists

TF-PIM-001 Waves A-F discharged cleanly through 2026-05-22 per the v0.4 plan-doc. Wave G (PIM canary cross-repo verify) ran into a cascading fix-forward cycle 2026-05-22 → 2026-05-23 that surfaced **9 distinct L31 axes** (content-semantic verification gaps). After ≥4 fix-forward rounds with new architectural findings on each round, operator ratified HARD STAND-DOWN per cure-worse cardinal rule 2 + the formalized R2-fix-cycle rule from Recommender Option B pre-review.

Per ASC-2026-05-22-001 ratification, this §11 captures the 9-axis evidence + Path C v2 redesign baking all axes in upfront. It is the disciplined response the stand-down was protecting time for — design-forward not fix-forward.

### 11.2 L31 findings — 7 SCP-side axes + 2 cross-surface references

**v0.6 reframe (R1 Lens B CRIT-001 closure):** the original v0.5 §11.2 table conflated axes that surfaced in SCP TF-PIM-001 Wave G (which THIS amendment addresses) with axes that surfaced in PIM Phase 4 WP-502 (which is a separate workpackage with its own closure path). v0.6 separates the two surfaces explicitly so the closure-scope claim is honest.

#### 11.2.1 In-scope: 7 SCP-side axes that this v2 amendment closes

| Axis | Description | v1 (Waves A-G v0.4) status | v2 (this amendment) closure |
|---|---|---|---|
| C | Cross-repo secrets propagation — `${{ secrets.X }}` empty in callee context | v1 assumed secrets flow; failed | v2 axis G closure also closes axis C (same root cause — caller-side `secrets: inherit` opens the flow channel) |
| D | Artefact-pin currency — adopter wrappers pinned to pre-impl SHAs | v1 plan-doc didn't specify wrapper-bump step | v2 ADOPT-001 §12.7.16b amendment (verbatim text in companion `docs/decisions/D-050-v2-amendment-text.md`) + Wave G v2 action step |
| E | App-install per-install repo-access scope selection | v1 click-through guidance conflated install location with repo access | v2 ADOPT-001 §12.7.16a amendment (verbatim text in companion doc) + Wave G v2 ceremony |
| F | Estate-wide adopter caller-permissions propagation | v1 didn't propagate 023B attest-scorecard caller-perms requirement to adopter wrappers | v2 closed via PR #142 (scaffolder template adds caller-job `attestations: write + id-token: write`) |
| G | Cross-repo `workflow_call` secrets explicit-pass-vs-inherit semantics | v1 forbade `secrets: inherit` IN callee, didn't address caller side | v2 Option α ratified via ASC-2026-05-22-001 — caller uses `secrets: inherit`; closed via PR #142 |
| H | Workflow-context-variable semantic — `github.action_*` doesn't apply to reusable workflows | v1 used `github.action_repository` + `github.action_ref` (wrong) | v2 closed via PR #142 — hardcoded SCP repo + `github.workflow_sha` (axis I follow-on below) |
| I | Cross-repo reusable-workflow self-SHA awareness — `github.workflow_sha` resolves to CALLER's wrapper SHA, not callee's loaded-from SHA | PR #142 axis H fix used `github.workflow_sha`; failed cross-repo | v2 explicit `inputs.scp-sha` pattern + adopter-side mirror requirement (§11.5 design; companion Wave-D'-WP-spec-draft companion doc captures verbatim YAML) |

#### 11.2.2 Cross-surface reference (NOT closed by this amendment)

The following 2 axes surfaced concurrently in a DIFFERENT workpackage (PIM Phase 4 WP-502 catalog authoring) but informed the L31 estate memo's 9-axis discipline framework. They are NOT in TF-PIM-001 scope:

| Axis | Surface | Description | Closure path (NOT this amendment) |
|---|---|---|---|
| A | PIM Phase 4 WP-502 | Content provenance gap — Codex invents content when canonical source unspecified | Closed PIM-side via WP-502 15-goal target-validated trim (operator-ratified 2026-05-22; landed in PIM PR #258) |
| B | PIM Phase 4 WP-502 | Target validity gap — content provenance correct but cited targets don't exist | Closed PIM-side via WP-502 surface-existence-check step (added as Step 1.5 in PIM session's WP-502 discovery flow; lessons-learned captured in L31 estate memo) |

#### 11.2.3 Sample-size summary

**9 axes total / 3 surfaces / ~48h.** L31 estate memo at `~/.claude/projects/-Users-amplience-Projects/memory/feedback_content_semantic_verification_gap.md` captures the discipline framework. **7 of 9 closed by this TF-PIM-001 amendment (axes C/D/E/F/G/H/I); 2 of 9 closed independently in PIM Phase 4 (axes A/B).**

Future cross-repo / adopter-pattern WPs should apply the 7-axis SCP-side framework AND the 2-axis PIM-side framework per L31 estate memo §3 (Discipline framework). Both surfaces of evidence inform any future content-heavy or cross-repo authoring discipline.

### 11.3 Path C v1 vs v2 — what changes

**v0.6 update (R1 Lens B HIGH-002 closure):** the original v0.5 §11.3 table only mentioned `.scp-runtime` checkout step for the `ref:` arg fix; v0.6 explicitly lists BOTH checkout steps (`.scp-runtime` + `_scp-workflow`) so the change-diff is faithful. Adopter-wrapper transition discipline (Lens B HIGH-003) folded into the new "Transition" column.

| Dimension | v1 (Waves A-G v0.4) | v2 (this amendment) | Transition |
|---|---|---|---|
| Cross-repo secrets pattern | Caller-side `secrets: inherit` ASSUMED but not specified | Caller-side `secrets: inherit` EXPLICITLY in scaffolder template (axis G Option α) | HARD CUT — existing adopter wrappers without `secrets: inherit` (only PIM currently) bumped via Wave G v2 re-fire |
| App-install repo-access | UI ceremony assumed correct | Explicit "Repository access" UI prompt callout in ADOPT-001 §12.7.16a (axis E; verbatim text in companion `docs/plans/TF-PIM-001-wave-d-prime-spec-draft.md` §8) | Operator-attended UI re-config on existing adopter installs (PIM already done 2026-05-22 mid-Wave-G) |
| Adopter wrapper bump cadence | Implicit (Renovate-automated) | Explicit ADOPT-001 §12.7.16b wrapper-bump procedure documented (axis D; verbatim text in companion §9) | Renovate regex-rule template provided; manual fallback documented for adopters without Renovate self-host |
| Reusable workflow `repository:` arg | `github.action_repository` (wrong) | Hardcoded `jrnb2024/standards-control-plane-` (axis H — closed in PR #142) | Closed; no transition needed |
| Reusable workflow `ref:` arg (.scp-runtime checkout) | `github.action_ref` (wrong) then `github.workflow_sha` (also wrong) | Explicit `inputs.scp-sha` passed from caller (axis I; companion §3 verbatim) | HARD CUT — `inputs.scp-sha` is `required: true`; existing wrappers without `scp-sha:` fail GHA startup validation with clear error; only PIM affected (only existing adopter); fixed via Wave G v2 re-fire |
| Reusable workflow `ref:` arg (_scp-workflow checkout) | `github.workflow_sha` (works for SCP-self; WRONG for cross-repo) | `inputs.scp-sha \|\| github.workflow_sha` (axis I parallel fix; companion §4 verbatim) | Backward-compat for SCP-self (selftest) preserved via fallback; cross-repo callers MUST pass `scp-sha:` per axis I requirement |
| Adopter caller-job permissions | Not specified for `attest-scorecard` requirement | `attestations: write + id-token: write` at job level (axis F — closed in PR #142) | Existing PIM wrapper updated 2026-05-22 mid-Wave-G; scaffolder template canonical for future adopters |
| Estate-wide adopter propagation | No coordinated mechanism | Scaffolder template canonical shape (PR #142) + ADOPT-001 §12.7.16a/b + §12.7.7 amendments (axes D+E+F+G) | Cohort cascade slices 024D-024G generate adopter wrappers DIRECTLY from v2 scaffolder template — no transition needed |
| Workflow-selftest test coverage | No fixture for axis I (didn't exist in v1) | NEW fixture `tests/workflow/fixture-scp-sha-validation/` (companion §7 spec) | Net-new test addition; doesn't affect existing fixtures |
| `inputs.scp-sha` validation | N/A (didn't exist) | Pre-flight validation step (non-empty + 40-char hex regex; companion §2 verbatim) | First job step; runs BEFORE App-token-exchange; clear SCP-E001 annotation on validation failure |

### 11.4 Path C v2 vs alternative-path re-look

**v0.6 update (R1 Lens A MED-001 + Lens B MED-002 + MED-003 closure):** v0.5 re-look glossed over (a) actual sensitive content in SCP that would make Path A non-viable, and (b) realism of hybrid framing. v0.6 enumerates explicitly + amends recommendation honesty.

**Operator ratified Path C v2 2026-05-23 per ASC-2026-05-22-001.** The re-look below documents the rationale + retains alternative-path framing for future strategic re-evaluation.

#### 11.4.1 Path A — Make SCP repo public

**Behavior:** Default GITHUB_TOKEN can clone public repos. Eliminates ALL 7 SCP-side axes (cross-repo auth surface disappears).

**SCP content sensitivity enumeration (v0.6 R1 fold):**

| Content class | Files / location | Sensitivity | Path A viability impact |
|---|---|---|---|
| Policy rules (Rego) | `policies/*.rego` | Already-published via ADOPT-001 §12.7 + open-source convention | No barrier — could be public |
| Rule-config schema | `schemas/*.json` | Already-published via ADOPT-001 | No barrier |
| Governance docs | `docs/` (DECISIONS, ADOPT-001, plans, BACKLOG, STATUS) | Substantially already-published via ADOPT-001 + estate-convergence docs | No barrier |
| Scaffolder template | `templates/adopter-wrapper.yml.tmpl` | Already-published-equivalent (adopters consume it) | No barrier |
| Workflow source | `.github/workflows/policy-check.yml`, etc. | Adopters consume via pinned SHA refs (effectively public via ref) | No barrier |
| **Branch-protection invocation log** | `docs/reviews/WP-SCP-020/branch-protection-log.md` | Captures operator-attended PATCH operations on adopter repos with timestamps + admin identifiers; sensitivity: MEDIUM (admin-audit trail) | **BARRIER** — would need satellite-repo migration OR explicit redaction policy |
| **Break-glass procedure details** | ADOPT-001 §12.8 + related | Captures break-glass commands + bypass mechanics; sensitivity: MEDIUM (operational-secret-equivalent) | **BARRIER** — could be moved to private satellite OR redacted/aliased |
| **Scorecard aggregates** | `output/scorecards/` (per WP-SCP-023) | Per-adopter compliance posture; sensitivity: HIGH (cross-adopter benchmarking would be possible if public) | **BARRIER** — would need satellite-repo migration AND adopter consent |
| **R-cycle review evidence** | `docs/reviews/*/r*/` | Captures finding-by-finding security analysis (Lens A sec reviews); sensitivity: LOW-MEDIUM (reveals threat model but not exploits) | Tolerable; could be public with light redaction |
| **Audit logs** | `.acc/hook-audit-log/` (gitignored) | Per-worktree audit trail; not committed | No barrier (gitignored) |

**Path A net assessment:** 3-4 BARRIER content classes that would need satellite-repo migration OR redaction policy. Not insurmountable but requires non-trivial operator-strategic decision on each (especially scorecard aggregates per WP-SCP-023). Path A would also affect WP-SCP-024 cohort cascade discipline (adopter consent for public scorecard inclusion).

**Recommendation:** Path A is architecturally cleanest BUT the satellite-repo migration + adopter-consent-for-public-scorecards is a much bigger strategic conversation than TF-PIM-001 can resolve. Defer Path A as long-term simplification (P3 strategic FUP per §11.8).

#### 11.4.2 Path E — Public read-only mirror of SCP

**Behavior:** Keeps SCP private; auto-mirrors content (minus the 3-4 BARRIER classes from §11.4.1) to a public read-only repo; adopters consume from the mirror.

**Trade-off:** Mirror sync infrastructure (CI-driven; SHA-pinned for adopter consumption) + STILL cross-repo (just from public mirror to adopter). Doesn't eliminate auth axes — shifts them. Adopters still need wrapper bumps on mirror updates; mirror still needs cross-repo checkout pattern (just from a public source).

**Path E net assessment:** Adds infrastructure complexity (mirror sync + redaction pipeline) without eliminating axes. Not recommended unless the BARRIER content classes from §11.4.1 are explicit + non-negotiable.

#### 11.4.3 Path C v2 — Bake 7 SCP-side axes into design (RECOMMENDED + RATIFIED)

**Behavior:** Preserves SCP-private posture. Explicit `inputs.scp-sha` input + canonical adopter wrapper shape via scaffolder template + ADOPT-001 ceremony amendments. Complex but functional.

**Estate-cohesion:** v2 is HARD CUT on `inputs.scp-sha` (required field). Existing adopter wrappers without `scp-sha:` will fail GHA startup validation with clear error post-v2 ship. Only PIM is affected currently (PIM wrapper bumped via Wave G v2 re-fire). Cohort cascade slices 024D-024G generate adopter wrappers from v2 scaffolder template natively (no transition).

**Path C v2 net assessment (operator-ratified):** Smallest viable change that closes the 7 SCP-side axes with documented design intent. Estate-cohesive once PIM bump lands.

#### 11.4.4 Hybrid framing — REVISED

**v0.5 framing (rejected per Lens B MED-003):** "Adopters onboarded under Path C v2 work today. SCP repo could be made public at any future point (Path A) and the cross-repo machinery becomes a no-op." This is unsound — Path A's no-op-claim only holds if audit-trail + scorecard aggregation requirements relax simultaneously, which §11.4.1 shows is non-trivial.

**v0.6 revised hybrid framing:** Path C v2 today provides estate-cohesive functional architecture. Path A migration in the future is POSSIBLE but NOT automatic — it requires:
1. Operator-strategic decision on the 3-4 BARRIER content classes (§11.4.1)
2. Satellite-repo migration OR redaction policy for BARRIER classes
3. Adopter consent for public scorecard inclusion (WP-SCP-023 dependency)
4. SCP wrapper machinery becomes simpler-but-not-no-op (App credential still useful for audit logging even if not strictly needed for read access)

Hybrid framing is captured as P3 strategic FUP per §11.8; does NOT preclude Path C v2 estate-deployment in the meantime.

#### 11.4.5 Recommendation summary (v0.6 — operator-ratified)

Path C v2 ratified 2026-05-23. Path A deferred as P3 strategic conversation (requires §11.4.1 BARRIER-class operator decisions). Path E not recommended (adds infrastructure without eliminating axes).

### 11.5 Path C v2 design — the 7-SCP-axis-baked architecture

**v0.6 update:** v0.5 included inline YAML examples + ADOPT-001 amendment text that R1 Lens C correctly identified as WP-spec-level detail rather than plan-doc-level design intent. v0.6 moves verbatim execution-class artefacts to companion `docs/plans/TF-PIM-001-wave-d-prime-spec-draft.md` per L26+L27+L28 discipline (verbatim text lives in WP-spec-class artefacts, not plan-doc). §11.5 now captures DESIGN INTENT + references companion for execution.

For verbatim execution-class text, see companion sections:
- **Companion §2** — `inputs.scp-sha` declaration in policy-check.yml (axis I primary closure)
- **Companion §3** — `.scp-runtime` checkout step v2 YAML (axis I + axis H final)
- **Companion §4** — `_scp-workflow` checkout step v2 YAML (axis I parallel)
- **Companion §5** — scaffolder template (`templates/adopter-wrapper.yml.tmpl`) diff
- **Companion §6** — pre-authored PIM wrapper text for Wave G v2 canary
- **Companion §7** — workflow-selftest fixture spec (axis I test coverage)
- **Companion §8** — ADOPT-001 §12.7.16a verbatim (axis E App-install Repository access ceremony)
- **Companion §9** — ADOPT-001 §12.7.16b verbatim (axis D wrapper SHA-pin bump procedure)
- **Companion §10** — adopter-wrapper transition discipline (R1 Lens B HIGH-003 closure)
- **Companion §11** — D-050 ADR v2 amendment text (operator-merge ceremony)
- **Companion §12** — Lens C MED follow-ups (FUP P-ratings + TF naming)

**SCP-side changes (additional to PR #142) — design intent summary:**

1. **`policy-check.yml`** gains `scp-sha` workflow_call input (`required: true`; 40-char hex regex) + pre-flight validation step (closes axis I primary). Both `.scp-runtime` checkout + `_scp-workflow` checkout use `inputs.scp-sha` (the latter with `|| github.workflow_sha` fallback for SCP-self / selftest compatibility). Verbatim text: companion §2 + §3 + §4.
2. **Scaffolder template** (`templates/adopter-wrapper.yml.tmpl`) gains `scp-sha: {{SCP_SHA}}` in the caller-job `with:` block — the substitution makes `scp-sha:` always match the `@<SHA>` pin at scaffold time. Verbatim diff: companion §5.
3. **ADOPT-001 §12.7** receives 3 amendments:
   - §12.7.16a (App-install Repository access UI ceremony — closes axis E) — companion §8 verbatim
   - §12.7.16b (wrapper SHA-pin bump procedure — closes axes D + I joint cadence) — companion §9 verbatim
   - §12.7.7 amendment (caller-side `secrets: inherit` architectural rationale — closes axis G + preserves §12.7.10 invariant literally) — companion §12 MED-002 verbatim
4. **Workflow-selftest harness** gains a new fixture (`tests/workflow/fixture-scp-sha-validation/`) exercising 5 test cases including required-input-missing + malformed-SHA + cross-repo mock — companion §7 spec.
5. **D-050 ADR** receives a 2026-05-23 amendment row (no new D-NNN) capturing the 7-axis closure + Option α architectural choice + axis I `inputs.scp-sha` pattern — companion §11 verbatim.

**Adopter-side changes (Wave G v2 PIM canary template + cohort cascade 024D-024G):**

PIM wrapper post-v2 shape is the operator-pre-authored mirror of the new scaffolder template (companion §6 verbatim). `<NEW_SCP_SHA>` placeholder replaced with the post-Wave-D' merge SHA at Wave G v2 fire time.

For future cohort cascade slices 024D-024G, the v2 scaffolder template generates correctly-shaped wrappers natively — no transition discipline needed for new adopters. Existing adopter (PIM only) handled via Wave G v2 re-fire ceremony.

**Transition discipline:** HARD CUT on `inputs.scp-sha` (`required: true`). Pre-v2 wrappers without `scp-sha:` fail GHA startup validation with clear `Input required and not supplied: scp-sha` error — loud, actionable, no silent failure mode. Only PIM affected (only existing adopter); bumped via Wave G v2 re-fire. Companion §10 captures the full transition discipline rationale (R1 Lens B HIGH-003 closure).

### 11.6 Updated wave sequencing for v2 implementation

**v0.6 update (R1 Lens B MED-004 + MED-005 + Lens C MED-003 closure):** v0.5 estimate ("1 PR; ~1-2h") under-scoped the multi-PR coordination + post-v2 PIM canary failure-mode contingencies. v0.6 splits Wave D' into 3 sequenced PRs + adds explicit PIM canary failure-mode branch.

Pre-v2 already done (no re-work):
- ✅ Wave A — GitHub App authoring (App `scp-federation-primitive` registered + secrets stored at SCP; 2026-05-21)
- ✅ Wave B — D-050 ADR ratified v1 (PR #136; 2026-05-21) — v2 amendment scheduled in Wave D'.2 below
- ✅ Wave C — ADOPT-001 §12.7 updates v1 (PR #136; 2026-05-21) — v2 amendments §12.7.16a/b/.7 scheduled in Wave D'.2
- ✅ Wave D — policy-check.yml token-exchange v1 (PR #139; 2026-05-21) — v2 axis-I patch scheduled in Wave D'.1
- ✅ Wave E — workflow-selftest mock fixture v1 (PR #139; 2026-05-21) — v2 axis-I fixture scheduled in Wave D'.1
- ✅ Wave F — SCP-self dogfood verify (PR #140; 2026-05-22)
- ✅ Wave G axes C+F+G+H consolidation (PR #142; 2026-05-23)

New work for v2 (split per R1 Lens B MED-004):

**Wave D'.1 — SCP-side code-class changes (single PR):**
- `policy-check.yml`: add `scp-sha` input + pre-flight validation step + fix both checkout steps (companion §2/§3/§4)
- Scaffolder template: add `scp-sha: {{SCP_SHA}}` (companion §5)
- Workflow-selftest fixture: add `tests/workflow/fixture-scp-sha-validation/` (companion §7)
- Scaffolder test updates: extend assertions for `scp-sha:` presence
- Estimated: ~1.5h orchestrator (author + 3-lens R1 on Wave D' WP-spec + R-cycle to R-fixpoint MET + Codex Tier 2 dispatch fire + merge)

**Wave D'.2 — Documentation amendments (separate PR, single chore-class):**
- ADOPT-001 §12.7.16a + §12.7.16b verbatim text per companion §8 + §9
- ADOPT-001 §12.7.7 amendment per companion §12 MED-002
- D-050 ADR row amendment per companion §11 (status preserved; rationale + invariants + closure path extended)
- STATUS.md + BACKLOG.md ratchet for ASC-2026-05-22-001 close + Wave D' completion narrative
- Estimated: ~30-45min orchestrator (chore-class; light R-cycle since docs-only)

**Wave G v2 — Operator-attended PIM canary re-run:**
- PIM wrapper text: operator copies companion §6 verbatim into PIM repo, substituting `<NEW_SCP_SHA>` with Wave D'.1 merge SHA
- Verify App install Repository access = `jrnb2024/standards-control-plane-` per ADOPT-001 §12.7.16a (PIM already has this configured 2026-05-22; quick re-verify only)
- Open canary PR on PIM; verify all 12 policy-check steps green
- Estimated: ~30min operator-attended

**Wave G v2 failure-mode contingencies (R1 Lens B MED-005 closure):**

Wave G v2 success assumes:
(a) v2 closes SCP-side axes C/D/E/F/G/H/I (handled by Wave D'.1 + .2)
(b) PIM's WP-502 has closed PIM-side axes A/B (handled by PIM Phase 4 closure 2026-05-22)

If PIM canary fails at a NEW step post-v2 (any step beyond the previously-blocking ones), the failure is NOT a v2 design regression but a NEW finding. Disposition:
- If failure is in SCP runtime policy-check execution (steps 5-11 in the 12-step run) → likely a substantive policy-rule violation on PIM's canary content; surface for canary-PR-content adjustment per §7.6 Branch 4 of the original plan-doc
- If failure is in axes A/B (PIM-side content provenance/validity) → re-escalate to PIM Phase 4 / PIM Phase 5 closure; out-of-scope for TF-PIM-001 closure
- If failure surfaces a NEW L31 axis → strict cure-worse trigger; stand down + ship-proposal per cardinal rule 2; do NOT iterate (lessons from Wave G 2026-05-22-23 still binding)

**Wave H — Per existing plan-doc; unchanged.** ~20 min operator-attended.

**Total v2 close estimate (R1 Lens B MED-004 corrected):** ~2-2.5h orchestrator (D'.1) + ~30-45min orchestrator (D'.2) + ~50 min operator-attended (G v2 + H) = ~3-4h total wall-clock end-to-end, assuming clean R-cycles + no further axis surfacing.

### 11.7 D-050 ADR amendment scope

Per ASC-2026-05-22-001 ratification, D-050 receives a v2 amendment capturing:

1. **`secrets: inherit` architectural choice** (axis G Option α) — caller-side inherit pattern; rationale for why this doesn't violate §12.7.10 PAT-broad-grant prohibition (App-credential broad-grant is materially different)
2. **`scp-sha` input pattern** (axis I) — explicit pass-through closes the GHA-context-variable gap; documented as canonical adopter pattern
3. **Adopter ceremony amendments** (axes D + E + F) — wrapper-pin currency cadence; App-install repo-access scope discipline; estate-wide adopter caller-permissions coordination
4. **Re-look summary** (§11.4) — Path C v2 vs Path A / E / hybrid; recommended Path C v2 with hybrid-to-Path-A as long-term option

ADR amendment is an `ACCEPTED` row update (status preserved; rationale + invariants + closure path extended). Not a new ADR (D-NNN reservation NOT needed) because Path C remains the ratified architecture — just with v2 implementation details.

### 11.8 Deferred follow-ups (post v2 close)

**v0.6 update (R1 Lens C MED-005 + MED-006 closure):** FUP P-rating + TF naming corrected per R1 feedback.

- **TF-PIM-001-WORKFLOW-CALL-SECRETS-EXPLICIT-DECLARATION-V2** (renamed from `TF-SCP-PATH-C-...` per Lens C MED-006 — aligns with TF-PIM-001 naming convention; not a new WP) — explicit `on.workflow_call.secrets` declaration + per-call pass-through (Option β architectural shape). Estate-wide hardening once 024D-024G cohort cascade stable. P3.
- **FUP-SCP-ADOPTER-WRAPPER-PERMISSIONS-PROPAGATION** — estate-wide adopter wrapper update coordination for cohort cascade slices 024D-024G. **Re-rated P2** (down from P1 per Lens C MED-005): cohort cascade slices 024D-024G generate adopter wrappers DIRECTLY from the v2 scaffolder template — they never have the pre-v2 shape, so the propagation gap doesn't apply to future adopters. Existing PIM wrapper bump is handled via Wave G v2 re-fire (operator-attended). FUP captures the cohort-coordination ceremony for completeness but isn't blocking.
- **Cure-worse rule estate-wide promotion** — formalized rule from Recommender Option B pre-review (2026-05-22): "If R2 fix-cycle surfaces NEW CRIT/HIGH ≥ original R1 severity in same WP-class: immediately file SHIP-PROPOSAL + stand down. Do NOT iterate R3 without explicit operator authorization." Promote into `feedback_autonomous_directive_scope_interpretation.md` Reading A canonical as hardening amendment. P2.
- **L31 9-axis discipline framework adoption** — incorporate as preflight checklist in WP-spec authoring discipline for any cross-repo / adopter-pattern WP. P2.
- **Path A consideration** — full operator-strategic discussion on whether to make SCP repo public as long-term simplification (requires §11.4.1 BARRIER-class operator decisions on branch-protection invocation log + break-glass procedure details + scorecard aggregates). P3 (architectural; non-urgent).

### 11.9 Cross-references

**v0.6 update (R1 Lens B LOW-001 closure):** ASC-2026-05-22-001 cross-reference clarified — file location is in operator's memory directory (estate-wide reference), NOT in-repo. Reader accesses via the memory path explicitly noted below.

In-repo references:
- `docs/plans/TF-PIM-001-wave-d-prime-spec-draft.md` — v0.5/v0.6 companion with verbatim execution-class artefacts (Wave D'.1 + .2 source-of-truth)
- D-050 ADR row in `docs/DECISIONS.md` (PR #136 ratified v1 2026-05-21; pending v2 amendment per §11.7 + companion §11)
- PR #139 (Waves D + E impl + workflow-selftest fix-forward; 4 commits including the discriminator + permissions fixes)
- PR #140 (Wave F SCP-self dogfood verify)
- PR #142 (Wave G consolidated 5-axis closure — axes C+F+G+H)
- PIM PR #259 (PIM canary; standing-down with 9-axis evidence chain preserved across 4 commits)
- `templates/adopter-wrapper.yml.tmpl` (canonical scaffolder template; pending Wave D'.1 amendment)
- `.github/workflows/policy-check.yml` (reusable workflow; pending Wave D'.1 amendment)

Estate-memory references (NOT in-repo; located at `~/.claude/projects/-Users-amplience-Projects/memory/`):
- `ASC-2026-05-22-001.md` — operator ratification record for Option α (2026-05-23) + this v0.6 §11 redesign
- `feedback_content_semantic_verification_gap.md` — L31 9-axis estate memo + discipline framework
- `feedback_autonomous_directive_scope_interpretation.md` — Reading A canonical + cure-worse cardinal rule 2 authority

External references:
- Recommender Option B pre-review (2026-05-22) — source of the formalized cure-worse rule (R2-fix-cycle ship-proposal trigger); awaiting Recommender session R-FIXPOINT MET surface for fold into Reading A canonical

## §10 Closure (UPDATED v0.5)

WP-closure when all 5 §2 acceptance criteria are satisfied UNDER PATH C v2:

1. ⏳ External-adopter (PIM) cross-repo run green — pending v2 Wave G re-run
2. ⏳ PIM `main` `policy-check / scp/policy-check` required-check restored — pending v2 Wave H
3. ✅ ADOPT-001 §12.7 updated — Wave C delivered baseline; v2 amendment adds §12.7.16a/b + §12.7.7 amendment
4. ✅ D-050 ADR ratified — Wave B delivered baseline; v2 amendment captures architectural-detail updates
5. ⏳ R1-evidence-on-fix-PR satisfies cardinal-rule-2 3-lens + CI citation pair — pending v2 Wave G + H PRs

Closure ceremony unchanged from v0.4 EXCEPT add to STATUS.md final entry: reference to ASC-2026-05-22-001 + §11 v0.5 amendment + the 9-axis L31 evidence chain.

---

**End of plan-doc v0.7 — RATIFIED 2026-05-23.** v0.5 R1 returned 26 findings; v0.6 folded all per cardinal rule 1; v0.6 R2 returned 8 new findings (2 architectural-class HIGH + 6 low-friction MED/LOW). v0.7 folds the 2 architectural HIGHs inline (HIGH-005 fallback-downgrade closure via removing `_scp-workflow` fallback + workflow-selftest fixture passes `scp-sha:` explicitly; HIGH-004 redact-on-error hygiene); 6 low-friction R2 findings explicitly accepted as Wave D'.1 WP-spec input. Per Lens C R-FIXPOINT MET signal + Lens B R-FIXPOINT MET + operator-ratified disposition: v0.7 is the design-ratification artefact. Wave D'.1 Codex Tier 2 dispatch authoring may proceed per §11.6 sequencing.
