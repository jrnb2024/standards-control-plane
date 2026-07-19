# Portable mktemp Templates — R1 Review Findings

```scp-review-evidence
{
  "review_id": "PORTABLE-MKTEMP-SUFFIX",
  "area_id": "scp-mktemp-fix-scripts",
  "reviewed_at": "2026-07-19T00:00:00Z",
  "summary": "Three-lens R1 adversarial review of the BSD/macOS mktemp suffix fix (scp-policy-check + policy_check_invocation.sh) and the offline-mode conftest stub repair; all lenses CONFIRMED, no blocking findings.",
  "reviewed_paths": [
    "scripts/scp-policy-check",
    "lib/policy_check_invocation.sh",
    "tests/scripts/test_scp_policy_check.py",
    "STATUS.md"
  ],
  "findings": [
    {
      "finding_id": "RV-MKTEMP-001",
      "status": "resolved",
      "summary": "Latent test-env defect unmasked by the mktemp fix: the offline-mode test's fake conftest stub emitted nothing, so the conftest feed path fed empty output to the JSON parser (JSONDecodeError) once mktemp succeeded on a dirty tree; resolved same-PR by making the stub emit [] like real `conftest --output json` (base-head test stub idiom).",
      "domain": "governance"
    },
    {
      "finding_id": "RV-MKTEMP-002",
      "status": "accepted",
      "summary": "Completeness observation: the RED for this bug is macOS/BSD-only (GNU mktemp tolerates the suffix), so Linux CI carries no regression guard against re-introducing a post-X-suffix template; disclosed in STATUS.md. GOV-004 satisfied via pre-existing-tests-as-RED (2 failed -> 6/6 on macOS), the note-and-justify pattern the operator accepted at the 2026-07-11 PM precedent — no redundant new test authored.",
      "domain": "governance"
    },
    {
      "finding_id": "RV-MKTEMP-003",
      "status": "accepted",
      "summary": "GOV-002 enhancement-spec absence carried as a note-and-justify protocol deviation: two-line portability bugfix slice, non-kernel-dangerous, narrow scope (PR #247 / arch-003-client-wrapper precedent).",
      "domain": "governance"
    }
  ]
}
```

**Slice:** portable mktemp templates (branch `fix/portable-mktemp-suffix`)
**Date:** 2026-07-19
**Gate:** build — 3-lens R1 (correctness / safety_bypass / completeness_governance)
**Status:** All lenses CONFIRMED; no blocking findings; accepted residuals documented

## Dispositions

| Lens | Verdict | Blocking findings | Disposition |
|------|---------|-------------------|-------------|
| correctness | CONFIRMED complete+correct | none | Every consumer of both renamed temp paths reads via shell variable, never by name/extension (`tar -xzf` keys on gzip magic; python reads by path); repo-wide grep `XXXXXX[A-Za-z0-9._-]` over scripts/ lib/ tests/ .github/ src/ policies/ is EMPTY — no other suffixed template; the offline test's lockfile sha is derived dynamically from the stub content (`_sha256(fake_conftest)`), so the [] change cannot break verification; no cleanup glob or sibling template (scp-data/scp-opa/scp-conftest dir) collides with the new names. |
| safety_bypass | CONFIRMED no weakening | none | Both temps still allocated atomically by a single `mktemp` call at 0600 — no mv/compose-name race introduced; SHA256 verification still gated (stub body hashed into the expected lockfile sha); diff touches zero verify/fail-closed/deny logic (grep for `verify_file_sha|ensure_cached_binary|emit_error|exit 1` in the diff: none); no verification step keys on the temp filename or extension. |
| completeness_governance | CONFIRMED standalone-complete | none | VERSIONING.md scope explicitly excludes `lib/policy_check_invocation.sh` + helper `scripts/` (internal-only surfaces) — no version-manifest bump owed; zero live-doc drift (only frozen historical review-audit artifacts carry the old template string — immutable audit trail, correctly untouched); STATUS.md dated entry present and style-consistent; GOV-004 RED-first satisfied via pre-existing-tests-as-RED (RV-MKTEMP-002); nothing in-scope left undone. |

## Provenance

macOS developer runs of `tests/scripts/test_scp_policy_check.py` failed 2/6 with
`mktemp: mkstemp failed ... scp-conftest.XXXXXX.json: File exists` whenever the invoking
working tree had a modified tracked `.json` (the conftest feed path then executes) — a
macOS-dev-only red that pattern-matched as flake while Linux CI stayed green. Post-fix:
6/6 twice consecutively with a dirty tracked `.json` (repeat-invocation proof) and 6/6 clean.
