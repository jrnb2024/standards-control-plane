# TF-PIM-001 Wave E dispatch JSON — sec lens R2

**Dispatched:** 2026-05-21 PM (post v0.2 fold)
**Agent type:** Plan (read-only)
**Model:** Sonnet
**Worktree isolation:** yes
**Lens domain:** threat-model + auth-surface + backdoor-attack-surface + bypass-prevention
**Artefact under review:** Wave E dispatch JSON v0.2

---

**Verdict:** ACCEPT
**Convergence signal:** R-FIXPOINT-MET
**Findings count:** 1 total (0 BLOCKING + 0 MAJ + 0 MIN + 1 NIT)
**R1 closures verified:** SEC-BLOCKING-001 CLOSED, SEC-MAJ-001 CLOSED, SEC-MIN-001 CLOSED, SEC-MIN-002 CLOSED, SEC-NIT-001 CLOSED
**New findings:** 1 NIT (SEC-NIT-002-R2 — §12.7.7 citation precision in notes)

---

## R1 closure verification

### SEC-BLOCKING-001 — VERIFIED CLOSED

EDIT 7 fully specified: `!= 2` → `!= 3` plus message string update. CMD 23 (`grep -F 'if local_uses_count != 3:'`), CMD 24 (`grep -F 'exactly three times'`), CMD 25 (Python re.findall with `\s*$` end-of-line anchor) provide complete machine enforcement.

### SEC-MAJ-001 — VERIFIED CLOSED

EDIT 3 annotation now reads `::error file=.github/workflows/policy-check.yml,title=SCP-E001 (selftest)::Simulated...` — both `file=` parameter and `(selftest)` title suffix present (CMD 8). Notes documents SCP-E001 reuse rationale.

### SEC-MIN-001 — VERIFIED CLOSED

Invariant 1 now explicitly states EDIT 3 is `run:`-only. CMD 29 (`! awk '/Simulate App token-exchange failure/,/exit 1/' ... | grep -qF 'actions/checkout'`) provides machine-enforced negative check across the step body range.

### SEC-MIN-002 — VERIFIED CLOSED

EDIT 5b assertion now accepts `failure` OR `cancelled` (CMD 22 verifies). Error message correctly triages all three outcomes.

### SEC-NIT-001 — VERIFIED CLOSED

Accidental mis-set scenario added to both EDIT 1's `description:` and `notes` blast-radius section.

---

## New findings

### SEC-NIT-002-R2

**Type:** NIT
**Title:** §12.7.7 citation in notes overstates the explicit definition
**Where:** `notes` field — `SCP-E001 annotation surface preservation` section

**Finding:** Notes state §12.7.7 includes "App token-exchange failure" in its enumeration; actual §12.7.7 table only enumerates "OPA/Conftest binary unreachable, SHA256 mismatch, lockfile pin missing." The live behavioral precedent for SCP-E001 on App-installation revocation is in §12.7.16 (line 1314: "If an adopter revokes the App installation … subsequent PRs … will fail with SCP-E001 (infra fetch fail)"), not in §12.7.7.

**Security impact:** None. SCP-E001 reuse is semantically correct (App token-exchange is an infrastructure failure mode per the established §12.7.16 behavioral pattern). D-050 invariant 5 preserved.

**Suggested closure (optional; post-R-fixpoint hygiene):** In notes, change `§12.7.7 defines SCP-E001 as "Infrastructure fetch failure" (OPA/Conftest binary unreachable, SHA256 mismatch, lockfile pin missing, App token-exchange failure)` to `§12.7.7 defines SCP-E001 as "Infrastructure fetch failure" (OPA/Conftest binary unreachable, SHA256 mismatch, lockfile pin missing); §12.7.16 establishes the live behavioral precedent that App installation revocation emits SCP-E001 — the same failure class semantically`.

---

## Federation-primitive invariants 1-5 disposition

All preserved under v0.2. §12.7.10 invariant fully preserved (CMDs 16+17 enforce). No new SCP-EXXX code introduced (D-050 invariant 5 preserved; `(selftest)` suffix is title-content, not a new code).

## Convergence signal rationale

R-FIXPOINT-MET. All five R1 SEC findings verified closed. Single new NIT is documentation citation precision with zero security impact. The dispatch JSON v0.2 is ready for Codex Tier 2 fire pending operator-attended authorisation.
