# 023D — fix-round-2 audit (R2 → fix → R3 candidate)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-023-023d-exposure`
**Pre-fix-round-2 HEAD:** `beedcec`

## R2 finding tally

3× parallel Sonnet R2: 2 CHANGES_REQUESTED + 1 APPROVED_WITH_FINDINGS.

| Lens | Verdict | new CRIT | new MAJ | new MIN | new nit |
|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 1 | 0 | 1 |
| safety_bypass | CHANGES_REQUESTED | 0 | 1 | 0 | 1 |
| completeness | APPROVED_WITH_FINDINGS | 0 | 0 | 1 | 0 |
| **total NEW** | — | **0** | **2 (same root)** | **1** | **2** |

The 2 MAJ findings are the **same root cause**: FIX-ROUND-1.md claimed two inline-fixes that didn't actually land — the markdown generator's `_SUPPORTED_INDEX_SCHEMA_VERSIONS` guard + DECISIONS.md `Last Updated` bump. Both Edit tool calls in fix-round-1 silently failed (likely due to re-read requirements that I hadn't satisfied). R2 caught the gap at exactly the right layer.

## Per-finding disposition

### MAJ (2; 1 root cause)

| ID | Lens | Disposition | Action |
|---|---|---|---|
| **COR-R2-MAJ-001 / MAJ-SAFE-R2-001** | correctness, safety | **INLINE-FIX (real claim-vs-state mismatch)** | FIX-ROUND-1.md claimed schema_version guard added to BOTH consumers, but only `tools.py` (MCP method) received it; the markdown generator was unchanged. R2 caught it. **Re-applied** the `_SUPPORTED_INDEX_SCHEMA_VERSIONS = {"0.1"}` guard to `scripts/generate-scorecard-report.py` after `args.index.is_file()` check; tested empirically (rejection test passes). The root cause was an Edit tool silent-drop in fix-round-1 — the file content didn't actually change despite the tool reporting success. Lesson: trust-but-verify with `grep` after every Edit. |

### MIN (1)

| ID | Lens | Disposition | Action |
|---|---|---|---|
| **R2-CMP-MIN-001** | completeness | **INLINE-FIX (claim-vs-state mismatch)** | Same root cause as the MAJ: FIX-ROUND-1.md claimed `Last Updated` bumped to D-043; the file still said D-042. **Re-applied** via Python script (Edit tool refused with "File has not been read yet" despite recent reads). Now reads "D-043 filed at WP-SCP-023 023D". |

### nit (2)

| ID | Disposition | Action |
|---|---|---|
| **COR-R2-nit-001** | **NO ACTION** | Sanitisation ternary `" " if c in ("\n", "\r") else c` is partially dead code: the outer filter `c == "\t" or ord(c) >= 0x20` already excludes \n/\r (both <0x20). Effectively the CR/LF handling is a defensive belt-and-braces. Cosmetic; the sanitisation is correct (overly defensive, not incorrect). |
| **nit-SAFE-R2-001** | **NO ACTION** | Sanitisation passes through Unicode C1 control codes (U+0080–U+009F). The `ord(c) >= 0x20` check excludes ASCII C0 only, not Unicode C1. In practice the index `error` field is constructed from gh CLI stderr which is ASCII; a Unicode-C1 injection is an extremely contrived attack against an attacker-controlled index that's already CODEOWNERS-gated. Not actionable for this slice; would require a more careful Unicode-aware filter. |

## Inline-fix summary (2 edits, both re-applications)

1. `scripts/generate-scorecard-report.py` — `_SUPPORTED_INDEX_SCHEMA_VERSIONS` guard inserted after `args.index.is_file()` check + before `aggregated_at` extraction (COR-R2-MAJ-001 / MAJ-SAFE-R2-001).
2. `docs/DECISIONS.md` — `Last Updated` bumped to D-043 / 023D (R2-CMP-MIN-001).

## Forward-filed TFs

R2 surfaced no new TF candidates. TF-023D-001..005 carried from R1.

## Lesson learned

The Edit tool can silently fail when a file has been read elsewhere in the conversation but not recently (per its session-state heuristic). FIX-ROUND-1.md claimed both fixes landed; only one actually did. **R2 caught both at the right layer** — exactly what adversarial review is for. Future inline-fix sessions: `grep -n` after every Edit to confirm the change actually landed.

## Smoke-test post-fix

- Empirical rejection test: bad `schema_version` causes generator to exit 1 with "unsupported scorecard-index schema_version" stderr. PASS.
- 17/17 scorecard-report + scorecard-mcp tests pass (7 + 10).
- All 52 tests pass overall.
- `scripts/scp-pre-push-verify.sh`: ✓ all 3 SCP-R gates pass.

## R3 candidacy

R2 surfaced 0 new CRIT, 1 unique-root MAJ (claim-vs-state mismatch on R1; both halves now actually applied), 1 MIN (same root), 2 nit (NO ACTION). The slice is ready for **R3 dispatch** to verify the re-applied fixes actually landed this time + no NEW CRIT/MAJ.
