# R1 dispositions — cross-repo audit_changed / resolve_domain estate coverage

**Change:** `fix/audit-changed-cross-repo` — audit_changed gains `repo_root` + `area_hint`
(MCP) / `--repo-root` (CLI); repo root threads through diff resolution, scope extraction,
review-evidence resolution, and all evaluator file readers (ContextVar
`use_audit_repo_root`); resolve_domain gains a glob tier backed by the new shared
`standards_control_plane/applies_to.py` (fallback tables moved from
`mcp_server/resources.py`, estate `services/**` shapes added).

**Review protocol:** 3 parallel adversarial lenses (correctness / safety_bypass /
completeness_governance) run 2026-07-05 against the full worktree diff vs origin/main.
Safety lens verdict: **no HARD-STOP findings**.

## Dispositions

| # | Lens | Finding | Severity | Disposition |
|---|------|---------|----------|-------------|
| C1 | correctness | `area_hint` not in the audit cache key — a retry with a corrected hint served the stale cached response | med-high | **FIXED**: hint folded into `_audit_cache_key`; test `test_audit_cache_key_distinguishes_area_hints` |
| C2 | correctness | CLI `--repo-root` accepted a non-root directory → silently empty/mis-resolved diffs | medium | **FIXED**: `changed_audit.resolve_worktree_root` validation (expanduser + `git rev-parse --show-toplevel` + `samefile`), exit 2 on failure; test `test_cli_audit_changed_rejects_repo_root_that_is_not_a_worktree_root` |
| C3 | correctness | Stale cache on dirty external worktrees (key = commit SHAs, content = working tree) | medium | **FIXED**: results for an external `repo_root` are never cached; test `test_audit_changed_does_not_cache_external_repo_root_results`. SCP-self caching unchanged (pre-existing shape). |
| C4 | correctness | `_match_segments` exponential in `**` count (measured: 8×`**` hung) | low/latent | **FIXED**: consecutive-`**` collapse + (path,pattern)-index memoisation; perf guard test in `tests/test_applies_to.py` |
| C5 | correctness | Root comparison rejected non-canonical-case paths on APFS | low | **FIXED**: `os.path.samefile` in both validators; git's toplevel returned as canonical root |
| C6 | correctness | Empty-string `area_hint` → opaque schema E021 | low | **FIXED**: normalised to absent; test `test_audit_changed_treats_blank_area_hint_as_absent` |
| C7 | correctness | `dir/**` glob matches a plain file named `dir` (diverges from git pathspec) | negligible | **ACCEPTED**: documented `**` = zero-or-more segments; over-eager domain resolution only |
| S1 | safety | Arbitrary-worktree read reachability | — | **VERIFIED SAFE**: stdio MCP + CLI only; HTTP `/audit` never reads `repo_root` from the body. Documented in adopter contract. |
| S2 | safety | Path-escape boundaries vs the new root | — | **VERIFIED AIRTIGHT** (symlink, `..`, absolute-path probes all contained) |
| S3 | safety | Vacuous clean pass indistinguishable from real pass | medium | **FIXED (legibility)**: response now carries `domains_evaluated` + `resolve_confidence` (0.0 = governance fallback = vacuous); adopter contract documents the reading |
| S4 | safety | CLI `--repo-root` + `--write-output` co-mingles foreign findings into SCP stores | medium | **FIXED**: combination refused (exit 2); MCP path was already read-only |
| S6 | safety | Hostile-repo git config (`core.fsmonitor`) execution on git calls in a foreign worktree | low | **ACCEPTED + DOCUMENTED**: trusted-worktree caveat in adopter contract; hardening env vars noted as follow-up |
| G1 | completeness | `review_evidence._resolve_repo_path` missed by root-threading — adopter `docs/reviews/**` diffs crashed or read SCP's own evidence | **high** | **FIXED**: resolves via `audit_repo_root()` fallback chain; RED/GREEN regression test `test_build_changed_file_audit_result_reads_adopter_review_evidence` |
| G2 | completeness | Stale `tools.py` line refs in the adopter contract | medium | **FIXED**: line numbers replaced with `register_tools` references |
| G3 | completeness | Mixed exact+glob / exact+fuzzy confidence branches untested | medium | **FIXED**: `test_resolve_domain_demotes_exact_confidence_when_mixed_with_lower_tiers` |
| G4 | completeness | `--repo-root`+`--write-output` untested provenance-free write path | medium | **FIXED** (same as S4) |
| G7 | completeness | E021 now covers repo_root validation classes, undocumented | low | **FIXED**: remediation paragraph added to mcp-error-codes.md |
| G8a | completeness | `area_hint` without `repo_root` untested | low | **FIXED**: `test_audit_changed_passes_area_hint_without_repo_root` |
| C-note | correctness | Pure-Python SCP diffs now resolve to architecture (glob tier) instead of the governance fallback — evaluator routing change for SCP's own src-only diffs | — | **ACCEPTED (intended)**: flagged in PR body |

## Follow-ups (not in this PR)

1. **FR-SCP-1401 supersession annotations** — `docs/requirements/WP-SCP-014-requirement-spec.md`, `docs/plans/PROG-SCP-001-autonomous-execution-plan.md:50`, `README.md:92` still state the repo-bounded constraint; annotate when the operator files the DECISIONS.md row (D-number assignment is operator-gated).
2. **Declared `applies_to` end-to-end** — `standards-rule.schema.json` (`additionalProperties: false`) cannot carry `applies_to`, and `RuleRecord` has no field for it; when it gains one, `_registry_glob_domain_map` must pass the declared list (today it passes `declared=None`, which would silently ignore declarations the resource plane honours).
3. **Git hardening for foreign roots** — optional `-c core.fsmonitor=false -c core.hooksPath=/dev/null` on git invocations when `repo_root` is external.
4. **WP-SCP-026 doc annotation** — `docs/plans/WP-SCP-026-mcp-consumer-integration-v1.md:53-54` describes the pre-glob resolve_domain; annotate on next touch.
5. **derive_area_id provenance** — derived area depends on the worktree directory name; two checkouts of the same repo yield different area ids. Acceptable for read-only audits; revisit if cross-repo findings ever persist.
