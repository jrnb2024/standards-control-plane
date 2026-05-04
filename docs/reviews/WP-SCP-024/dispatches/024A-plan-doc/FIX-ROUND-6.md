# 024A — fix-round-6 audit (R6 → fix → R7 candidate)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-024-estate-cascade-plan`
**Pre-fix-round-6 HEAD:** `72a7a83`

## R6 finding tally

3× parallel Sonnet R6: all 3 CHANGES_REQUESTED.

| Lens | Verdict | new CRIT | new MAJ | new MIN | new nit |
|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 1 | 0 | 0 |
| safety_bypass | CHANGES_REQUESTED | 0 | 3 | 0 | 0 |
| completeness | CHANGES_REQUESTED | 0 | 2 | 1 | 0 |
| **total raw new** | — | **0** | **6** | **1** | **0** |

After dedup:
- §6 024C/D/E/F slice rows unconditional "invocation log" — correctness only (R6-NEW-MAJ-001 correctness) = 1 unique MAJ
- Regex prose mismatch (`.{20,}` allows whitespace; prose says non-whitespace) — safety + completeness BOTH flagged (R6-NEW-MAJ-001 safety + R6-NEW-MAJ-002 completeness) = 1 unique MAJ
- §6 024B "non-empty description" stale (R6-NEW-MAJ-002 safety) = 1 unique MAJ
- cascade-status absent/unrecognised → fail-closed (R6-NEW-MAJ-003 safety) = 1 unique MAJ (NEW DEFECT CLASS)
- Regex file-scoping ambiguous — STATUS.md vs DISPATCH-NOTE (R6-NEW-MAJ-001 completeness) = 1 unique MAJ
- §5.6 vs §8 first-bullet wording inconsistency (R6-NEW-MIN-001 completeness, pre-existing) = 1 unique MIN

After dedup: **0 CRIT + 5 unique new MAJ + 1 MIN**.

## Per-finding disposition

### MAJ (5 unique, all inline-fixed)

| ID | Lens(es) | Disposition | Action |
|---|---|---|---|
| **R6-NEW-MAJ-001 (correctness)** | correctness | **INLINE-FIX** | §6 slice plan rows 024C/D/E/F unconditionally listed "invocation log" as deliverable (without the conditional carve-out that §1 + §3 + §5.2 + §6 024B + §8 all carry). Fix: each row's Deliverable column rewritten as "deliverables conditional on `cascade-status:` per §5.2 + invariant 2 — `onboarded`/`onboarded-operator-bump` paths ship invocation-log entry + post-bake; `blocked-on-adopter-conflict` path ships TF-conflict reference instead per invariant 10 with NO log entry". |
| **R6-NEW-MAJ-001 (safety + completeness, dedup)** | safety, completeness | **INLINE-FIX** | Regex `.{20,}` matched 20+ characters including whitespace, but prose said "≥20 non-whitespace characters." A description of 20 spaces would pass the regex but fail the prose. **Fix:** regex changed from `.{20,}` to `\S.{19,}` — `\S` anchor at start of description requires non-whitespace; `.{19,}` allows the remaining 19+ chars to be anything. Prose updated to match. New worked example added: `❌ TF-024X-renovate-jrnb2024-pim (open):                    ` (all-whitespace description fails the `\S` anchor). |
| **R6-NEW-MAJ-002 (safety)** | safety | **INLINE-FIX** | §6 024B acceptance criteria still said "status field + non-empty description" for both TF-row paths — pre-fix-round-5 framing. Fix: rewrote 024B row to reference invariant 2's regex format spec **literally** (not paraphrased). Both `onboarded-operator-bump` and `blocked-on-adopter-conflict` paths now require "matching invariant 2's regex format spec literally" + the file-agnostic property. |
| **R6-NEW-MAJ-001 (completeness)** | completeness | **INLINE-FIX** | Regex header scoped to "STATUS.md list marker" via the `^- **` prefix, but the `blocked-on-adopter-conflict` path's TF reference lives in DISPATCH-NOTE (prose paragraph, not bullet list). Fix: regex restructured to be **file-agnostic** — dropped the `^- **` prefix; regex now matches the TF reference content alone, anywhere on a line. The line can have any wrapping (STATUS.md `- **...**`, DISPATCH-NOTE prose, etc.) — regex doesn't care. New worked example added: `✅ See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.` (DISPATCH-NOTE prose embedding passes). |
| **R6-NEW-MAJ-003 (safety)** | safety | **INLINE-FIX** (NEW DEFECT CLASS) | The CI script's behavior when `cascade-status:` was absent or had an unrecognised value was completely unspecified. A DISPATCH-NOTE lacking the field entirely could bypass all enforcement if the script fails-open on parse error. **Fix:** invariant 2 now ships an explicit fail-closed default — "if `cascade-status:` is absent OR contains a value not in the enumerated set `{onboarded, onboarded-operator-bump, blocked-on-adopter-conflict}`, the script exits non-zero (CI fails)." §6 024B acceptance updated to enumerate **all four CI behaviours** (3 named paths + fail-closed default). |

### MIN (1 unique)

| ID | Disposition | Action |
|---|---|---|
| **R6-NEW-MIN-001** (completeness) | **INLINE-FIX** | §5.6 first Threshold A bullet said "≥3 adopters have required-check live + invocation log entries committed" while §8 first bullet said only "≥3 adopters have required-check as a required status check on default branch". Pre-existing inconsistency. **Fix:** §5.6 first bullet rewritten to phrase identically to §8 — "≥3 of {PIM, recommender, mapp-doc-agent, control-tower, shopify-app} have `policy-check / scp/policy-check` as a required status check on default branch (per `cascade-status: onboarded` or `onboarded-operator-bump`; `blocked-on-adopter-conflict` adopters do NOT count until a successor sub-slice onboards them per invariant 10)." Adds explicit cascade-status conditioning to make it consistent with the rest of the plan-doc. |

## Inline-fix summary (~6 edits across 1 file)

`docs/plans/WP-SCP-024-estate-cascade.md`:
- **Invariant 2 lead-in** — fail-closed default added.
- **Invariant 2 format-spec block** — regex restructured (file-agnostic; `\S.{19,}` non-whitespace anchor); prose updated; 6 worked examples (was 3).
- **§5.6 Threshold A first bullet** — phrased identically to §8 first bullet with cascade-status conditioning.
- **§6 024B row** — references invariant 2's regex spec literally; enumerates all 4 CI behaviours (fail-closed + 3 named).
- **§6 024C/D/E/F rows** — Deliverable columns made conditional on `cascade-status:`.

Plan-doc grew ~5 lines.

## R7 candidacy

R6 surfaced 0 new CRIT, 5 unique new MAJ (all inline-fixed), 1 MIN (closed). Six rounds of recursive review have hardened the cascade-status spec across:

- §1 Purpose item 2 (fixed at R5)
- §3 Programme protocol item (b) (fixed at R4)
- §5.2 cascade-status field enum (fixed at R3 + R5)
- §5.6 Threshold A first bullet (fixed at R6)
- §6 024B acceptance row (fixed at R5 + R6)
- §6 024C/D/E/F slice rows (fixed at R6)
- §7 R-024-06 mitigation (fixed at R4 + R5)
- §7 R-024-07 mitigation (fixed at R5)
- §8 Threshold A row 2 (fixed at R5)
- DISPATCH-NOTE risk surface item 4 (fixed at R5)
- DISPATCH-NOTE criterion (iii) (fixed at R5)

**Plus** the substantive defect-class additions:
- Three-value cascade-status enum (R3 → R5)
- Negative assertion for conflict-close (R3)
- Meaningful-content qualifier (R4)
- Regex format spec (R5)
- Regex non-whitespace anchor + file-agnostic scoping (R6)
- Fail-closed default for absent/unrecognised values (R6)

If R7 returns 0 new CRIT + 0 new MAJ on a complete cycle, **R7 fixpoint reached**.

## Pattern observation (final)

**6 consecutive rounds caught propagation gaps + new defect classes in this clause.** The clause has now stabilised structurally — every substantive defect class has an explicit spec, and the propagation is now machine-checkable via grep ("look for every reference to `cascade-status` and `branch-protection-log` and `TF-024X` and ensure each has the conditional + meaningful-content treatment").

The fix-round pattern observation from FIX-ROUND-5 ("comprehensive grep sweep BEFORE the next R round") proved insufficient — fix-round-5's sweep missed the §6 slice plan rows because they say "invocation log" without the word "entry". Lesson: when sweeping, grep for the **concept** (every reference to the audit trail OR cascade-status OR TF-024X) not just the literal phrase.
