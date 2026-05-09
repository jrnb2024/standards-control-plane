# DISPATCH-NOTE — WP-SCP-024 slice 024B-core

**Date:** 2026-05-09
**Branch:** `feature/wp-scp-024-024b-core` (off main `04135f0`)
**Predecessor:** WP-SCP-024 024A plan-doc v0.1 (PR #102, 2026-05-04). Originally scoped as 024B; split per `SCOPE-CORRECTION-2026-05-09.md` (this dir). Extras-parking branch preserves original 024B work + 7-round R-cycle audit.
**Successor target:** WP-SCP-024 024B-extras (branches from merged core). Then 024C PIM canary cascade.
**Decision filed:** D-044 (scoped to core: scaffolder operational contract + adopter-template versioning + cascade-status CI enforcement script).

cascade-status: not applicable

This slice does not onboard a cohort adopter; it ships the scaffolder + CI enforcement script that 024C–F will consume. CI enforcement workflow wiring (`.github/workflows/check-invocation-log-entry.yml`) is OUT OF SCOPE for this slice — defers to 024B-extras.

## Scope (in)

| Deliverable | Path | Notes |
|---|---|---|
| Scaffolder helper | `scripts/scaffold-downstream.sh` | Per plan-doc §5.3. Bootstrap-only guard (CI=true / GITHUB_ACTIONS=true refusal). Arg validation: --adopter-repo, --default-branch enum {main,master,develop}, --scp-sha 40-char hex + HEAD lineage check, --scorecard-emit enum, --output-dir writable + path-normalised system-path denylist (incl /private/var/* macOS canonicalisation). Emits 4 files: wrapper + CODEOWNERS-snippet + CASCADE-PR-BODY + MANIFEST.json (SHA256 audit). Refuses non-existent SHAs (exit 2); warns but continues if SHA not main HEAD. |
| Adopter wrapper template | `templates/adopter-wrapper.yml.tmpl` | Canonical adopter wrapper shape per ADOPT-001 §12. Substitutions: `{{DEFAULT_BRANCH}}`, `{{SCP_SHA}}`, `{{SCORECARD_EMIT}}`. Workflow-level permissions: `contents: read + statuses: write` ONLY (least-privilege baseline; opt-in adopters add attestations:write + id-token:write per ADOPT-001 §12.7.15 step 2). Fork-PR refusal `if:` clause preserved. Renovate inline-comment marker `# renovate: datasource=github-tags depName=jrnb2024/standards-control-plane-` immediately before `uses:` line — enables Renovate auto-bump in adopter repos (per plan-doc invariant 8 Threshold A criterion). |
| Cascade-status CI enforcement script (CLI) | `scripts/check-invocation-log-entry.sh` | Implements plan-doc invariant 2's 4 CI behaviours: (a) **fail-closed default** for absent/unrecognised cascade-status; (b) `onboarded` → log entry present + target match; (c) `onboarded-operator-bump` → log entry present + target match + STATUS.md TF-024X-renovate-<adopter-slug> row matching invariant 2 regex literally; (d) `blocked-on-adopter-conflict` → DISPATCH-NOTE TF-024X-conflict-<adopter> reference matching regex literally + log file NOT modified in PR diff. Plus: (e) `not applicable` (tooling-slice carve-out, exit 0). Regex via python3 -c with re.search() (PCRE-style; plan-doc §2 invariant 2 byte-for-byte). Exactly-one-match assertion (closes multi-occurrence injection bypass). Adopter-slug canonicalisation per plan-doc spec. **CLI tool only — GitHub Actions workflow wiring DEFERS to 024B-extras.** |
| Scaffolder unit tests | `tests/scaffolder/test_scaffold_downstream.sh` | 7+ test cases: happy path; substitution; MANIFEST validity; arg validation failures; bootstrap-only guard (CI + GITHUB_ACTIONS); default-branch master + develop variants; scorecard-emit=true variant; non-HEAD-SHA warn path; system-path denylist (incl macOS /private/var canonicalisation, gated on Darwin). Output dirs created under $TMPDIR (cleaned by EXIT trap). |
| CI enforcement script tests | `tests/check_invocation_log/test_check_invocation_log_entry.sh` | All 4 CI behaviours tested + `not applicable` carve-out. 6 worked-example matrix cases from plan-doc §2 invariant 2 (2 ✅ + 4 ❌). Phantom-2-entry test for SAFE-003. Exactly-one cascade-status match enforcement test. Adopter-slug canonicalisation test (jrnb2024/repo.foo_bar → jrnb2024-repo-foo-bar). **--restore-mode tests OUT OF SCOPE — defer to 024B-extras.** |
| D-044 row | `docs/DECISIONS.md` | Scoped to core: scaffolder operational contract + adopter-template versioning + cascade-status CI enforcement script (CLI). 024B-extras may reserve sibling D-NNN at extras-slice authoring time. |
| STATUS.md update | `STATUS.md` | "Today's chain (2026-05-09 — slice 024B-core)" entry. Plus split-decision audit row. |
| Scope-correction note | `docs/reviews/WP-SCP-024/024B-core/SCOPE-CORRECTION-2026-05-09.md` | Documents the split decision + R6→R7→R8 empirical justification. Already filed on this branch. |

## Scope (out)

- **`scripts/enable-required-check.sh --restore` mode** + posture-degradation flags + `--expected-wrapper-sha` tag-validation + Gate-3 working-tree prior-entry detection. **Defers to 024B-extras.**
- **ADOPT-001 §12.8 break-glass procedure** (3-gate playbook). **Defers to 024B-extras.**
- **`.github/workflows/check-invocation-log-entry.yml`** (CI workflow wiring). **Defers to 024B-extras.**
- **Step 7 operator-interactive `--restore` real-repo round-trip demo.** Defers to 024B-extras.
- 024C PIM cascade kickoff. Unblocked when 024B-extras merges.
- TF-023E-002 closure (workflow restructure). Carry-forward; not blocking.
- D-021 May-31 atomic-workday filing. Independent track.
- Estate-auth coordination checklist + MCP adopter contract docs. Hold.

## Cascade-status spec recap

The script enforces the spec from plan-doc §2 invariant 2. Regex (Python re):

```
TF-024X-(renovate|conflict)-[a-z0-9]+(?:-[a-z0-9]+)+(?:\*\*)? \((open|pending|in-progress|closed)\): \S.{19,}
```

Worked-example matrix (all 6 tested in test_check_invocation_log_entry.sh):

- ✅ ex1: STATUS.md bullet-bold form `- **TF-024X-renovate-jrnb2024-pim** (open): Renovate disabled on PIM; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.`
- ✅ ex2: DISPATCH-NOTE prose form `See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.`
- ❌ ex3: bare-prefix stub (no status field)
- ❌ ex4: empty description
- ❌ ex5: all-whitespace description (\\S anchor at description start)
- ❌ ex6: too-short description (≥20 chars after `: ` required)

## Acceptance criteria

- [ ] Scaffolder emits 4 files for known fixture; substitutions correct; MANIFEST validates.
- [ ] Adopter wrapper template carries Renovate marker for auto-bump.
- [ ] CI enforcement script implements all 5 cascade-status check-paths (4 enforcement + `not applicable`).
- [ ] Tests pass for both scaffolder + CI enforcement script.
- [ ] No --restore-mode content in any file (extras carve-out clean).
- [ ] No `.github/workflows/check-invocation-log-entry.yml` (extras carve-out clean).
- [ ] No ADOPT-001 §12.8 break-glass content (extras carve-out clean).
- [ ] D-044 row scoped to core deliverables.
- [ ] STATUS.md entry documents the split + this slice's outcome.
- [ ] 3-lens R1+R2 fixpoint reached (0 CRIT + 0 MAJ on a complete cycle). **Reduced surface = expect 1–2 R-cycles.**
- [ ] CI green (own self-dogfood policy-check + scp/policy-check-readback + conflict-gate).

## Cross-repo coordination

None for 024B-core. Cascade-start announcement files at 024C kickoff (per plan-doc §5.5).

## FLA pilot safety findings reviewed

[none new since 2026-05-04 (024A close)] — slice 024B-core is internal scaffolding; no FLA implications.

## Protocol deviation note

Same deviation as parent 024B: direct `codex exec` / `claude -p` (kernel hook lives in ACC, not SCP; per-repo install pattern is FUP-ACC-INSTALL-TARGET-REPO-001 — still open). Compensating manual steps (scope check + verify-cmds + audit log) apply to this slice as well.

## Sequencing

| Phase | Work | Mode | Wall |
|---|---|---|---|
| 0 (now) | DISPATCH-NOTE + scope-correction filed; core files staged from extras-parking | Opus | done |
| 1 | Codex executor: surgical clean of test_check_invocation_log_entry.sh (remove --restore tests); D-044 row; STATUS.md entry; verify scaffolder + check-invocation-log-entry.sh have no extras coupling | Codex T3 | ~30 min |
| 2 | Manual scope check + verify-commands run | Opus | ~5 min |
| 3 | 3× parallel Sonnet R1 review (sequential dispatch with 64k cap; lessons from extras-parking R8 dispatcher pattern) | Sonnet | ~30 min |
| 4 | Fix-rounds (expected 0–1 round given reduced surface) | Codex + Sonnet | variable |
| 5 | R-fixpoint + self-merge per D-040 | Opus | ~10 min |

Target: 024B-core merged within ~2–3 hours (vs 4 days + $50 reviewer cost on the original 024B).

## Reservation guard

D-044 stays reserved for this slice (core). Codex must NOT assign D-044 to anything else. 024B-extras may file sibling D-NNN at extras-authoring time.

---

**Status:** DRAFT v0.1 — awaiting Codex T3 surgical-clean dispatch.
