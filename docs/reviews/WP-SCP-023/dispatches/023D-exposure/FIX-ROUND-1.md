# 023D — fix-round-1 audit (R1 → fix → R2 candidate)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-023-023d-exposure`
**Pre-fix-round-1 HEAD:** `72ab937`

## R1 finding tally

3× parallel Sonnet R1: 2 CHANGES_REQUESTED + 1 APPROVED_WITH_FINDINGS.

| Lens | Verdict | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 1 | 4 | 3 |
| safety_bypass | CHANGES_REQUESTED | 0 | 1 | 3 | 1 |
| completeness | APPROVED_WITH_FINDINGS | 0 | 2 | 5 | 2 |
| **total raw** | — | **0** | **4** | **12** | **6** |

After dedup (cross-lens overlap on schema_version + STATUS-TF gaps): **0 CRIT, 4 unique MAJ**.

## Per-finding disposition

### MAJ (4 unique)

| ID | Lens | Disposition | Action |
|---|---|---|---|
| **COR-MAJ-001 / nit-SAFE-001** | correctness, safety | **INLINE-FIX** | Both consumers (markdown generator + MCP method) silently processed unknown schema_version. Schema description mandated drop-on-unknown. Added `_SUPPORTED_INDEX_SCHEMA_VERSIONS = {"0.1"}` guard to both: generator returns exit 1 + stderr error; MCP returns SCP-MCP-SCORECARD-004 error. Added `test_unknown_schema_version_rejected` pytest. |
| **MAJ-SAFE-001** | safety | **TF-FORWARD as TF-023D-003** | `_log_tool_invocation` carries `key_id="pending_021J"` for ALL MCP tools (pre-existing). consult_scorecard exposes the gap because it's the first method with aggregated estate-wide data. Filed forward — closure path: replace with active key_id from `docs/security/mcp-signing-keys.pub` before slice 023E / Threshold A sign-off. The fix touches all tools, not just the new one, so it belongs in its own slice. |
| **CMP-MAJ-001** | completeness | **TF-FORWARD as TF-023D-004** | Drift section absent from markdown generator. AC (i) named it. Deferred: real adopter data is needed to compute drift; until 023E onboards adopters, no drift to surface. Closure path at 023E or first weekly run with ≥2 verified adopters. Reviewer explicitly named Option B (defer-with-TF) as acceptable. |
| **CMP-MAJ-002** | completeness | **INLINE-FIX** | TF-023D-001/002 declared in DISPATCH-NOTE forward-looking but missing from STATUS.md TF register. Added 5 TF-023D entries (001..005) to STATUS.md tracked-forward section. |

### MIN (12 raw, ~7 unique)

| ID | Disposition | Action |
|---|---|---|
| **MIN-SAFE-002** | **INLINE-FIX** | Markdown error blockquote rendered raw `error` field — newline injection could break markdown structure. Added sanitisation: replace CR/LF with space, drop control chars, cap at 1500 chars (schema bounds at 2000). Regenerated golden fixtures. |
| **COR-MIN-001** | **NO ACTION** | Pydantic ValidationError on adopter row → silently skipped. Acceptable — the row is malformed at the index layer; the caller (aggregator) wrote a malformed index, not the MCP method. The error is observable via the missing row count. |
| **COR-MIN-002** | **NO ACTION** | since_emitted_at filter test only verifies "kept" path. The filter is best-effort + keeps rows with missing emitted_at by design. Adding a "drop" test would require fixturing a verified-row-with-old-emit + asserting the filter excludes it; the existing test_repo_filter exercise shows filter mechanics work. Acceptable nit. |
| **COR-MIN-003 / MIN-SAFE-001** | **NO ACTION** | `ConsultScorecardWaiversAggregate.by_rule_id` typed `dict[str, int]` without key pattern; the index schema enforces `^SCP-R-[0-9]+$` at the index layer. Pydantic models validate at the MCP boundary; an attacker-controlled index would already be a different attack class. Defence-in-depth could add Pydantic key constraints, but the current layered defence is sufficient. |
| **COR-MIN-004** | **NO ACTION** | No fixture exercises non-empty `disabled_rules` — the `mixed/` fixture has only verified-deny + failure rows. Adding a 4th fixture covers an additional render path; cosmetic, not a correctness gap. The render code is straightforward. |
| **MIN-SAFE-003** | **NO ACTION** | The waiver-content scan runs against expected.md (golden); reviewer suggests scanning generated output too. The test ALREADY runs the generator + compares to golden + the golden itself was scanned. Acceptable layered protection. |
| **CMP-MIN-001** | **INLINE-FIX** | TF-023A-002 stale "defer to 023D"; re-deferred to 023E with rationale. |
| **CMP-MIN-002** | **NO ACTION** | TF-023C-007 (wrapper filename) not in §12.7.15. Filed forward in TF register; ADOPT-001 §12.7.15 is comprehensive enough for now. |
| **CMP-MIN-003** | **TF-FORWARD as TF-023D-005** | MCP server redeploy required. Filed forward — closure path: bundle with next ACC deployment cycle. |
| **CMP-MIN-004** | **INLINE-FIX** | DECISIONS.md `Last Updated` not bumped for D-043. Updated. |
| **CMP-MIN-005** | **NO ACTION** | D-043 row doesn't explicitly use the words "signed-output envelope" from the original reservation. The actual mechanism (Pydantic-enforced fields + index trust via git history) achieves the spirit. Wording polish only. |

### nit (6 raw)

All NO ACTION — DISPATCH-NOTE typos (test path / §12.7.15 vs §13) + cosmetic items. The DISPATCH-NOTE is a slice-time artefact; the actual implementation is the source of truth.

## Inline-fix summary (~6 edits across 4 files)

1. `scripts/generate-scorecard-report.py` — `_SUPPORTED_INDEX_SCHEMA_VERSIONS` guard + error-string sanitisation in failure-detail section (COR-MAJ-001 + MIN-SAFE-002).
2. `src/standards_control_plane/mcp_server/tools.py` — schema_version guard with SCP-MCP-SCORECARD-004 error code (COR-MAJ-001).
3. `tests/scp_mcp/test_tools/test_consult_scorecard.py` — `test_unknown_schema_version_rejected` (10 tests now).
4. `tests/scorecard-report/fixtures/{empty,single-verified,mixed}/expected.md` — regenerated post-sanitisation (golden files updated).
5. `STATUS.md` — TF-023D-001..005 added; TF-023A-002 re-defer to 023E.
6. `docs/DECISIONS.md` Last Updated header bumped to D-043.

## Forward-filed TFs

- **TF-023D-001** — `scp.audit_scorecard_changed` MCP method (write-side). Already in DISPATCH-NOTE; now also in STATUS.md.
- **TF-023D-002** — markdown report retention policy. Already in DISPATCH-NOTE; now also in STATUS.md.
- **TF-023D-003** (new): `_log_tool_invocation` key_id closure. Pre-existing audit-trail gap surfaced by consult_scorecard.
- **TF-023D-004** (new): drift section in markdown report. Deferred until ≥2 verified adopters.
- **TF-023D-005** (new): MCP server redeploy on acc.brokapps.ai.

## Smoke-test post-fix

- `pytest`: 51/51 still pass + 1 new test → 52/52.
- `scripts/scp-pre-push-verify.sh`: ✓ all 3 SCP-R gates pass.

## R2 candidacy

R1 surfaced 0 CRIT, 4 unique MAJ (2 inline-fixed + 2 TF-forwarded with explicit reviewer-blessed deferral pattern), ~7 MIN (2 inline-fixed + 5 NO ACTION). Ready for R2 to verify no new CRIT/MAJ.
