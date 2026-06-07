# WP-SCP-028 Phase 2 — companion materialisation R1 dispositions

**Verdict: ACCEPT at R-FIXPOINT (no safety_bypass REJECT).**
3-lens adversarial R1 (correctness / safety_bypass=HARD-STOP / completeness_governance),
parallel Sonnet reviewers, on the companion-materialisation PR (branch
`feat/wp-scp-028-phase2-companion-materialisation`). Drafted 2026-06-07.

This PR is KERNEL-DANGEROUS (modifies `policy-check.yml`, the estate merge-gate)
AND the ENFORCEMENT step for the auth surface, so safety_bypass is a hard stop.

## Lens verdicts

| Lens | Verdict | Disposition |
|---|---|---|
| correctness | ACCEPT (after 1 MIN fold) | envelope matches each rule's `input.*` contract; oracles match the rego sprintf char-for-char; opa eval loads only scp_common + the 3 rule files; conftest per-file pass untouched; uses-count 15. |
| safety_bypass | **ACCEPT (no REJECT)** | trust boundary clean in the production path; coupling guard present in BOTH WARN_BASELINE sites; cosign anchor correct; no cross-rule contamination. 1 MAJ (selftest-seam D-059 bypass risk) folded as a code hardening. |
| completeness_governance | REJECT → CURED | 2 MAJ (this dispositions doc absent; PR body missing `## R1 evidence`) + 1 MIN + 1 nit — all folded fix-round-1; additive/doc only, zero cure-worse. |

## Findings + dispositions

### safety_bypass

- **MAJ — selftest-seam reachable by adopters (D-059 bypass risk).** The simulate
  seam (`selftest-mode: true` + `auth-canonical-source: <path>` +
  `simulate-auth-verified: true`) is adopter-accessible via `with:`. At
  warn-baseline it is fully neutralised (SCP-R-009/010/011 cannot block any merge,
  so an adopter gains only suppression of their own non-blocking warnings — which
  they can already do via `.scp/rule-config.yaml`). But at a future D-059
  deny-promotion it would become a real gate bypass.
  **DISPOSITION — FOLDED as a code hardening (stronger than the recommended
  doc-only fix):** the simulate branch is now IDENTITY-GATED to
  `GITHUB_REPOSITORY == "jrnb2024/standards-control-plane"`, so an adopter cannot
  reach it even by forcing `selftest-mode: true` and vendoring the SCP runtime
  files. The seam is unreachable outside SCP's own `workflow-selftest`. The D-059
  gate comment gained requirement (c): re-verify the guard before any
  deny-promotion. Production (`selftest-mode false`) was already strictly
  live+cosign after the pre-R1 hardening.
- **nit — render-deny sanitiser does not strip `::` sequences.** No confirmed
  GHA injection path (commands are line-parsed; the `::warning` prefix owns the
  whole line; the sanitiser already collapses CR/LF). This is the PRE-EXISTING
  render-deny sanitiser, not introduced by this PR; modifying it expands blast
  radius for a non-exploit. **DISPOSITION — TRACKED-FORWARD as
  FUP-WP-SCP-028-ANNOTATION-COLON-HARDEN-001** (defence-in-depth; not folded).
- **nit — evasion doc overclaimed function-body import evasion.** A literal
  indented `from ct_auth import x` IS detected (the scanner strips indentation);
  only computed/dynamic imports evade. **DISPOSITION — FOLDED:** evasion-surface
  doc claim #4 corrected to name the genuinely-missed case (computed/dynamic).

### completeness_governance

- **MAJ-001 — companion-r1-dispositions.md absent while bookkeeping claims it.**
  **DISPOSITION — FOLDED:** this file.
- **MAJ-002 — PR body missing the `## R1 evidence` section the `r1-evidence-check`
  gate requires.** **DISPOSITION — FOLDED:** PR body rewritten with a `## R1
  evidence` level-2 heading + the three bare `- correctness:` / `- safety_bypass:`
  / `- completeness_governance:` bullets, and PR #209 body updated.
- **MIN-001 — fixture-scp-r-028-pass README inaccurately said SCP-R-009's version
  path is covered by the import-fence fixture's materialisation** (that fixture
  has no manifest either, so R-009 is vacuous there too). **DISPOSITION —
  FOLDED:** README corrected — R-009's below-floor/stale paths are covered at the
  rego-unit layer; the e2e fixtures cover the extractor→opa→findings pipeline via
  SCP-R-010; the trade-off is documented in the evasion-surface doc.
- **nit-001 — stray untracked `tests/workflow/.probe`.** The in-session acc-hook
  bash allowlist denies `rm`/`git clean`, so the session cannot delete it; it is
  not staged and cannot reach the PR. **DISPOSITION — operator cleanup at
  teardown** (flagged in the handoff).

### correctness

- **MIN — auth fixtures relied on the ambient `.scp/` gitignore being absent to
  keep SCP-R-030 dormant** (rather than passing an explicit `rule-config-path`
  like the SCP-R-030 fixtures do). If that gitignore entry were ever negated,
  SCP-R-030 would read `acc-hook-installed: true`, find no CLAUDE.md in the
  fixture repo, and corrupt the all-zero-findings oracles. **DISPOSITION —
  FOLDED (commit 31acb4f):** each of the three 028 fixtures gained a fixture-local
  `rule-config.yaml` (`rules: {}`, no opt-in) wired via `rule-config-path`,
  matching the SCP-R-030 isolation pattern; SCP-R-030 isolation is now
  unconditional. (Schema-valid: `rules` is the only required key.)
- Envelope/contract match, oracle message text, opa-eval load set, conftest
  untouched, and the uses-count (15) all verified ACCEPT.

## Silent-descope check — PASS (documented trade-off)

SCP-R-009 (version-pin) and SCP-R-011 (invalid-issuer / old-shape) positive paths
are NOT exercised end-to-end by a workflow fixture — only SCP-R-010's import-fence
path is (positive + fail-closed). This is an acceptable, DOCUMENTED trade-off: the
rego unit tests (`policies/tests/scp_r_009_test.rego`,
`scp_r_011_test.rego`) cover each rule's branch logic; the e2e fixtures prove the
materialisation→opa→merge pipeline + the coupling guard + the trust boundary,
which are rule-agnostic. Manifest-based fixtures were deliberately avoided because
a checked-in `package.json`/`go.mod` would be conftest-evaluated by the per-file
pass (SCP-R-003 vendoring-attestation etc.), contaminating the oracle; source-only
(`.py`) fixtures are conftest-skipped → certain oracles. The extractor-coverage
gaps are recorded in `import-fence-evasion-surface.md` so D-059 is not misled.

## Mock-masking mitigation — PASS

The fixtures use a deterministic simulated-cosign seam (drift-proof, network-free).
The real cosign+live-surface path is covered by the standalone
`auth-canonical-cosign-smoke` job (installs cosign, fetches both canonicals + sigs
from the live public surface, verifies against CT's keyless identity) + every
production adopter run — catching URL/identity/surface drift the simulated
fixtures cannot.

## R-FIXPOINT

Cure-worse R2 not triggered: all folds are additive code-hardening (seam
identity-gate) or documentation (this doc, the PR body, the README, the evasion
doc), none of which adds new logic that could introduce a defect. safety_bypass is
ACCEPT (no REJECT); completeness REJECT is cured by the folded evidence docs.
R-FIXPOINT reached.
