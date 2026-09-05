# R1 review — chore: canonicalise repo slug `jrnb2024/standards-control-plane-` → `jrnb2024/standards-control-plane`

**Change class:** mechanical canonicalisation (GitHub repo-rename cleanup). Drop the trailing hyphen left over from the rename. All references currently redirect, so nothing is broken today; this removes latent rot for any future SHA-pinned or non-redirecting consumer.

**Scope boundary (GOV-001):** replace the owner-prefixed slug `jrnb2024/standards-control-plane-` only. Out of scope (flagged, not absorbed): bare non-owner-prefixed `standards-control-plane-` in prose; the `-mirror` sibling repo; the `standards-control-plane-docs` area_id.

**Transform applied:** `s{jrnb2024/standards-control-plane-(?![A-Za-z0-9])}{jrnb2024/standards-control-plane}g` — negative-lookahead isolates the slug (the only alphanumeric follower repo-wide is `m` = `-mirror`, a different repo).

## Verification (tests / evidence, GOV-003)

- **Per-file purity:** every changed file differs from `origin/main` by nothing but the slug substitution (`git show origin/main:<f> | perl <transform>` == working tree). 0 unexpected impure files. STATUS.md is the one documented exception (6 historical refs deliberately preserved — see below).
- **Suites run green locally:** scorecard-report golden (repairs a latent-red: `generate-scorecard-report.py` already emitted the canonical slug) + scorecard-emit schema + test_changed_audit → 28 passed; scorecard-aggregator + conflict_gate → 23 passed; all 13 per-rule OPA rego suites → pass (incl. SCP-R-004 23/23); check_invocation_log shell → pass.
- **Boundary preserved:** `jrnb2024/standards-control-plane-mirror` (×3, docs) untouched; `standards-control-plane-docs` area_id (`tests/test_changed_audit.py`) untouched; bare prose forms untouched.

## Three-lens adversarial review (GOV-004)

- correctness: SOUND. Every changed line is only the slug substitution; no in-scope reference missed (only `-mirror` survives); scorecard-report goldens now match the already-canonical generator (repairs latent red).
- safety_bypass: SAFE. Renovate depName + regex now consistent with the live wrapper marker (same `jrnb2024` owner; SHA pin unchanged; github-tags resolves via redirect). Schema `$id`/`$ref` resolution is path-based, not `$id`-URL-based — unaffected. Aggregator `expected_scp_workflow_ref`: change brings the schema pattern into agreement with the already-canonical runtime `SCP_WORKFLOW_REF_PREFIX`; mismatch direction is fail-closed (`verification_failure`), never silent-accept. `service.py` `/status` URL is a display string.
- completeness_governance: COMPLETE for functional surfaces (0 owner-prefixed old slugs remain in any non-doc/non-historical file; template `adopter-wrapper.yml.tmpl` already emits the canonical `uses:` so no downstream adopter inherits stale). One over-application into STATUS.md historical rename-narrative was found and fixed (below).

## Dispositions

- **STATUS.md historical-narrative restorations (fix applied):** the sweep over-applied into lines where the old owner-prefixed slug is the semantic subject. Restored the trailing dash on: the "renamed from `…-` (trailing dash) to `…`" line (was self-contradictory); the hardcoded discriminator value `github.repository != '…-'` (×2, historical record of the literal value at PR #139); the three "(trailing dash added)" refs on the TF-020H3-003 bullet. Release URLs and `gh api repos/…` command paths stay canonical (they resolve today; same repo).
- **Excluded — PR #247:** `tests/workflow/fixture-fail/expected-annotations.json` (merged PR #247 owns/fixed it on main).
- **Excluded — CI gate (note-and-justify, not silent descope):** `docs/reviews/WP-SCP-020/branch-protection-log.md` + `docs/reviews/WP-SCP-024/{024B-core,024B-extras,024C,024E-mapp-doc-agent-cascade-slice}/DISPATCH-NOTE.md` (5 refs). Canonicalising these would trip the required `check-invocation-log-entry` cascade gate, which requires a real cascade DISPATCH-NOTE + STATUS invocation-log entry this chore does not have. Fabricating one would be a false governance record. These are redirect-valid historical records; sweep them in a future cascade-authored change.
- **audit_changed advisory findings:** F-GOV-002 (no enhancement spec) — note-and-justify per GOV-005 (no theatre for a mechanical rename cleanup). F-ARCH-003 (`service.py` uses `httpx.`) — pre-existing in the file; this diff only touched a display-URL literal. F-GOV-003 (review evidence) — this file.

## Governance disclosure (D-057)

Authored from a Claude Code session rooted at the parent dir `/Users/amplience/Projects` (not the SCP repo), so the acc-hook PreToolUse gate was not in effect — the same disclosed condition under which the D-057 PR itself was authored. Work was done in an isolated `git worktree` off `origin/main` to avoid disrupting the concurrent live fixture-fail session sharing the primary checkout. Operator approved proceeding on gated paths under this disclosure.
