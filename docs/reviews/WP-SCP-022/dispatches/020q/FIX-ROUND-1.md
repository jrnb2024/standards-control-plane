# 020Q — fix-round-1 audit (R1 → fix → R2 candidate)

**Date:** 2026-05-02 (PM-4)
**Branch:** `feature/wp-scp-022-020q-conflict-gate-suppression-corpus`
**Pre-fix-round-1 HEAD:** `05cab6d` (initial impl + DISPATCH-NOTE)

## R1 finding tally

3× parallel Sonnet R1: 2× CHANGES_REQUESTED + 1× APPROVED_WITH_CONDITIONS.

| Lens | Verdict | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 1 | 2 | 2 |
| safety_bypass | CHANGES_REQUESTED | 0 | 1 | 3 | 3 |
| completeness_governance | APPROVED_WITH_CONDITIONS | 0 | 1 | 3 | 3 |
| **total raw** | — | **0** | **3** | **8** | **8** |

After deduplicating cross-lens findings (the same underlying issue surfaced under multiple lenses):
- **Unique CRIT:** 0
- **Unique MAJ:** 3 — (a) rule-config fixture schema field name (correctness MAJ + safety MIN); (b) null `expires_at` Rego silent-bypass (safety MAJ + correctness MIN + completeness MIN); (c) RULE-TEMPLATE.md / conflict-gate.md fixture authoring checklist process gap (completeness MAJ).
- **Unique MIN:** ~5 — coverage-table staleness, `\d` Unicode regex divergence, `.gitignore` CODEOWNERS coverage, exception-handling broadening, STATUS.md "Today's chain" row.
- **Unique nit:** ~5.

## Per-finding disposition

### MAJ (3 unique)

| ID | Lens(es) | Disposition | Action |
|---|---|---|---|
| **C-COR-MAJ-001 / MIN-SAFETY-004** | correctness, safety | **INLINE-FIX** | Rule-config fixture used `reason:` but `schemas/rule-config.schema.json` requires `justification:`. Renamed in `tests/conflict_gate/fixtures/SCP-R-001/rule-config-disabled/.scp/rule-config.yaml`. |
| **MAJ-SAFETY-001 / C-COR-MIN-001 / COMP-MIN-003** | safety, correctness, completeness | **INLINE-FIX (Rego bug fix)** | A waiver entry with `expires_at: null` (JSON null, not absent key) left `scp_waiver_expired(w)` undefined in Rego — `not scp_waiver_expired(w)` then resolved to TRUE via negation-as-failure, treating the malformed waiver as ACTIVE. Real silent-bypass risk. Added a 4th clause to `policies/scp_common.rego` `scp_waiver_expired`: `expires_at := w.expires_at; not is_string(expires_at)` → expired. Python `_scp_waiver_expired` already had this branch, so no Python change. Added 6th conflict-gate fixture `SCP-R-001/waiver-null-expires-at/` to lock in the parity (input bad-mode + waiver with `expires_at: null` → expected deny). 12/12 fixtures now pass. |
| **COMP-MAJ-001** | completeness | **INLINE-FIX** | `docs/integrations/conflict-gate.md` §"Fixture authoring checklist" + `docs/reviews/rule-proposals/RULE-TEMPLATE.md` §8 didn't document the suppression-path fixture invariant. Without this update, every future rule RFC would land without waiver-suppressed/waiver-expired/rule-config-disabled coverage and the conflict-gate authority would silently regress. Both files updated to require the full corpus when the deny body uses `not scp_active_waiver_for(...)` or `not scp_rule_config_disabled(...)`. |

### MIN

| ID | Lens(es) | Disposition | Action |
|---|---|---|---|
| **C-COR-MIN-002 / COMP-MIN-002** | correctness, completeness | **INLINE-FIX** | `docs/integrations/conflict-gate.md` "Coverage of the v1.0.0 rule library" table was stale (only listed `{allow, deny}` for SCP-R-001/002 and didn't list SCP-R-004 at all). Updated to enumerate the new fixture set per rule + added the SCP-R-004 row. |
| **COMP-MIN-001** | completeness | **INLINE-FIX** | STATUS.md "Today's chain (2026-05-02)" table needed both the TF-006 ✅ marker (already done in initial commit) AND a new 020Q row. Added rows 16 (TF-020P-005, retroactive) + 17 (020Q this slice). |
| **MIN-SAFETY-002 / C-COR-nit-001** | safety, correctness | **INLINE-FIX** | Python `\d` matches Unicode decimal digits while Rego `[0-9]` is ASCII-only — engine divergence on Arabic-Indic dates etc. Added `re.ASCII` flag to `_DATEISH_DATE_RE` and `_DATEISH_DATETIME_RE`. Pre-existing parallel risk noted via TF-020L-001 (Unicode-whitespace SCP-R-004 regex); this fix is independent. |
| **MIN-SAFETY-003** | safety | **INLINE-FIX** | `.gitignore` was not covered by any CODEOWNERS entry. The slice's negation rule (`!tests/conflict_gate/fixtures/**/.scp/`) is governance-relevant — a future broader rule could un-ignore production `.scp/` and leak operator rule-config. Added `/.gitignore @jrnb2024` to CODEOWNERS (inserted before /CODEOWNERS self-protection per ORDERING INVARIANT). |

### nit

| ID | Lens(es) | Disposition | Action |
|---|---|---|---|
| **C-COR-nit-002** | correctness | **INLINE-FIX** | `_load_sibling_waivers` / `_load_sibling_rule_config` only caught JSONDecodeError / YAMLError. Broadened to also catch UnicodeDecodeError + OSError; added explicit `encoding="utf-8"` to `read_text()` calls. |
| **nit-SAFETY-005** | safety | **NO ACTION** | Waiver-id collision risk across fixtures — flagged as a hypothetical concern. All fixture waiver-ids carry the `W-CG-FIXTURE-020Q-NNN-XX` prefix which is unique per fixture; no collision risk in current corpus. No action required. |
| **nit-SAFETY-006** | safety | **NO ACTION** | Symlink-following in fixture loaders. Test-time only; fixtures are checked into the repo tree under CODEOWNERS coverage. Tightening would require explicit `Path.is_file(follow_symlinks=False)` calls (Python 3.13+) or stat-without-follow. Not actionable for ASCII fixture corpus; flag retained for audit trail. |
| **nit-SAFETY-007** | safety | **NO ACTION** | Up to 1000 chars stdout / 500 stderr surfaced in `RuntimeError` from `_run_opa`. Test-time-only error path; reaches CI logs only on opa eval failure. The information disclosure risk is bounded to error-path output that operators need for diagnosis. Acceptable trade-off; flag retained for audit trail. |
| **COMP-NIT-001** | completeness | **NO ACTION** | Coverage matrix observation — SCP-R-002/004 don't have rule-config-disabled/waiver-expired fixtures. Symmetric coverage would be desirable but not blocking; meaningful production tests don't require every fixture for every rule (the 020Q corpus exercises every code path at least once across the rule set). Filed forward as **TF-020Q-001** (symmetric corpus expansion). |
| **COMP-NIT-002** | completeness | **NO ACTION** | Helper docstrings already cite Rego source lines (lines 94-104, 54-72, 44-49, 77-81 — verifiable in `tests/conflict_gate/test_conflict_gate.py`). Reviewer concern was about "explicit line citation" wording — already present. |
| **COMP-NIT-003** | completeness | **NO ACTION** | SCP-R-002/waiver-suppressed meta-waiver reason includes URL (per SCP-R-004 v1.1.0 requirement) — concern was that the URL points at a "see TF-006" issue rather than a real artefact. Filing fixture URL targets at the canonical TF-006 pointer is consistent with how slice 020M / 020N fixtures referenced their TFs. No action. |

## Inline-fix summary (8 edits across 7 files)

1. `policies/scp_common.rego` — added 4th `scp_waiver_expired` clause for null/non-string `expires_at` (closes MAJ-SAFETY-001 silent-bypass).
2. `tests/conflict_gate/test_conflict_gate.py` — `re.ASCII` flag on both regexes (C-COR-nit-001 / MIN-SAFETY-002); broadened exception clauses + explicit `encoding="utf-8"` (C-COR-nit-002).
3. `tests/conflict_gate/fixtures/SCP-R-001/rule-config-disabled/.scp/rule-config.yaml` — `reason` → `justification` (C-COR-MAJ-001 / MIN-SAFETY-004).
4. `tests/conflict_gate/fixtures/SCP-R-001/waiver-null-expires-at/{input.yml, waivers.json, expected-verdict.json}` — NEW fixture exercising null-expires_at fail-closed (locks in MAJ-SAFETY-001 fix).
5. `docs/integrations/conflict-gate.md` — updated coverage table + fixture authoring checklist (C-COR-MIN-002 / COMP-MIN-002 / COMP-MAJ-001).
6. `docs/reviews/rule-proposals/RULE-TEMPLATE.md` §8 — suppression-path fixture invariant (COMP-MAJ-001).
7. `STATUS.md` — added rows 16 (TF-020P-005 retroactive) + 17 (020Q) to "Today's chain (2026-05-02)" (COMP-MIN-001).
8. `CODEOWNERS` — `/.gitignore @jrnb2024` (MIN-SAFETY-003).

## Forward-filed TFs

- **TF-020Q-001** (low priority): symmetric suppression-path corpus expansion — add `waiver-expired` and `rule-config-disabled` fixtures for SCP-R-002 + SCP-R-004 to mirror SCP-R-001's complete coverage. Opportunistic; file when 2nd rule needs additional suppression-path testing or as part of general corpus maintenance.

## Smoke-test post-fix

- `pytest tests/conflict_gate/`: 12/12 passed (was 11/11; added waiver-null-expires-at).
- `scripts/scp-pre-push-verify.sh`: ✓ all 3 SCP-R gates pass; coverage 98.58% (above 90% threshold).

## R2 candidacy

R1 surfaced 0 CRIT, 3 unique MAJ (all closed inline including a real Rego silent-bypass bug fix), 5 unique MIN (5 inline-fixed), 5 unique nit (1 inline-fixed + 3 no-action + 1 TF-forwarded). The slice is ready for **R2 dispatch** to verify no NEW CRIT/MAJ findings emerge against the fix-round-1 surface. Per `feedback_recursive_adversarial_review.md` fixpoint criterion: R2 must surface 0 CRIT + 0 MAJ on a complete cycle.
