# 020h2 fix-round-1 (post-r1)

**Date:** 2026-05-01

## Triggers

R1 dispatch returned (commit 6d248f3 reviewed):

- **R1 correctness** (`review-correctness.json`, ~6.8 min, PASS_WITH_FINDINGS): 1 MIN + 3 nit. No CRIT/MAJ.
- **R1 safety** (`review-safety.json`, ~4.6 min, BLOCKED): **2 MAJ** + 1 MIN + 2 nit.
- **R1 completeness** (`review-completeness.json`, ~5.7 min, BLOCKED): **1 MAJ** (overlaps with SAFE-001) + 2 MIN + 1 nit.

3 distinct MAJ findings (SAFE-001 ≡ COMP-MAJ-001 collapses to one). Per `feedback_protocol_over_shortcuts.md` no descoping; all findings closed inline or extended TF-007.

## Closures applied

| Finding | Severity | Closure |
|---|---|---|
| SAFE-001 + COMP-MAJ-001 | MAJ | ADOPT-001 §12.7 stale references rewritten: §12.7.13 retitled "Supply-chain posture (post-020H.2)"; Regal bullet describes SHA256 verification IS now wired; fork-and-pin paragraph removed (no longer needed); §12.7.1 pre-deployment callout drops the TF-020H3-001 reference; §12.7.9 pre-commit hook note updated to say Regal IS now SHA256-verified in CI (local hook still doesn't invoke Regal). New §12.7.13 paragraphs added: Sigstore-attestation status (TF-007 extended to cover Regal); lockfile/version-pin governance (CODEOWNERS coverage); RUNNER_TEMP TOCTOU assumption (closes SAFE-004 via documentation); asset-shape pin (rationale + defensive check reference). |
| SAFE-002 | MAJ | CODEOWNERS extended with `scripts/** @jrnb2024` and `vendor/** @jrnb2024` inserted before the `/CODEOWNERS` self-protection line per the existing ORDERING INVARIANT. Comment block names the closure: cryptographic root-of-trust files (lockfile + version pins + adopter helpers + bypass-pairing verifier) now route through @jrnb2024 review. In single-operator count=0 mode the rule is documentary; in multi-maintainer mode it is machine-enforced. `vendor/**` is pre-emptive — directory does not exist today but `resolve_*()` helpers reference it as offline-CI fallback. |
| SAFE-003 | MIN | `policy-check.yml` adds `assert_bare_binary_shape()` helper that emits an explicit `emit_infra_failure` if the downloaded Regal asset begins with the gzip magic bytes (`1f8b`). Defends against a silent shape transition if a future Regal release moves to tarball shipping. Called from `resolve_regal()` after both the curl-download and vendor-fallback paths. |
| SAFE-004 | nit | RUNNER_TEMP TOCTOU window between `verify_sha256` and `cp` is documented in §12.7.13 "RUNNER_TEMP TOCTOU assumption" — same design as `resolve_opa`, no regression. Self-hosted-runner caveat included. |
| SAFE-005 | nit | `read_lockfile_field` Python helper now catches `(KeyError, TypeError)` so a structurally-malformed lockfile (e.g. `{"regal": "oops"}`) emits a clear `malformed lockfile structure` message instead of an uncaught Python traceback. |
| COMP-MIN-001 | MIN | TF-007 in STATUS.md extended to cover Regal explicitly: "also wire a Regal Sigstore soft-warn at re-tightening time — Regal is published via OPA's pipeline and almost certainly shares the same upstream attestation gap timeline." Conftest also named for completeness. |
| COMP-MIN-002 | MIN | DISPATCH-NOTE 'Post-merge STATUS.md update' rewritten to (a) correct the "TWO places" miscount (now THREE with explicit numbering); (b) name the structural deferral for the 020H.2 'landed' record; (c) name the carrier — next opened slice on main (020H.1 or SCP-073.sec, whichever opens first) — whose first commit MUST backfill STATUS.md line ~124. Carrier slice's DISPATCH-NOTE acceptance checklist will name the backfill explicitly. |
| COMP-nit-001 | nit | `policy-check.yml` post-cp comment block extended to explicitly state SAFE-011's compliance path: "no second verify on BIN_DIR/regal — same design as resolve_opa". Future maintainer auditing the diff against SAFE-011's literal mitigation text now has the rationale in-line. |
| COR-MIN-001 | MIN | `scripts/scp-policy-check` header comment block added: "NOT REPRODUCED LOCALLY: Regal lint. Regal lint runs CI-only against the policy bundle itself." Documents the deliberate scope boundary; closes COR-MIN-001 via Option B (the lighter-lift documentation path; Option A — adding regal lint to the local script — is forward-compat work for a future slice). |
| COR-nit-001 | nit | DISPATCH-NOTE "TWO places" miscount fixed to "THREE sections". |
| COR-nit-002 | nit | `policy-check.yml` Regal smoke test changed from `>/dev/null 2>&1` to `>/dev/null` so stderr (regal's own error output on failure) flows to the runner log. Improves diagnostic fidelity for the SHA-passing-but-corrupt-binary edge case (cross-architecture binary, glibc mismatch, FS-level bit flip). |
| COR-nit-003 | nit | Acknowledged as structural: 020H.2 "landed" record cannot be pre-merge — addressed by COMP-MIN-002 closure (carrier slice backfill). |

## Closures NOT applied

None. All R1 findings closed.

## Re-review

Fix-round-1 closures invalidate the prior R1 baseline. R2 lens
dispatch (correctness + safety + completeness) recurses next on
the post-fix-round-1 state. Per `feedback_recursive_adversarial_review.md`,
recurse until no new BLOCKING findings.
