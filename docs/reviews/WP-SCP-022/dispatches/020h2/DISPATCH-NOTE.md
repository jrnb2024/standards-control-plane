# WP-SCP-022 slice 020H.2 — dispatch note

**Date:** 2026-05-01 (early hours, post-020H part 3 merge)
**Tier:** orchestrator-applied (Tier 1 only)
**Closes:** TF-020H3-001 (Regal SHA256 supply-chain gap; deadline 2026-05-14).

## Justification for not invoking Codex executor

Per `feedback_four_tier_dispatch.md` in-line escalation guidance.
This slice's substantive surface is **a structurally-derived addition
to an established verification pattern**:

- `scripts/.tool-versions` — one new line (`regal 0.40.0`).
- `scripts/scp-policy-check.lock` — one new top-level key (`regal`)
  with four platform sub-objects matching the existing OPA shape
  (single binary, no archive — Regal ships as a bare binary).
- `.github/workflows/policy-check.yml` — three insertions structurally
  parallel to the existing OPA pattern: (a) `REGAL_VERSION="$(read_tool_version regal)"`;
  (b) `REGAL_SHA256="$(read_lockfile_field regal ...)"`; (c) a new
  `resolve_regal()` function mirroring `resolve_opa()` byte-for-byte
  with name substitutions; (d) the existing `curl ... regal` block
  replaced with `REGAL_SOURCE="$(resolve_regal)"; cp ...; chmod +x;`.

Codex Tier 3 dispatch overhead would exceed the marginal benefit
on a derived pattern with this much structural symmetry — same
posture as 020G + 020h2's other recent dispatches.

## Slice acceptance

- [x] **(i) Lockfile entry.** Regal v0.40.0 added to `scripts/scp-policy-check.lock`
  for all four platforms (linux-x64, linux-arm64, darwin-arm64,
  darwin-x64). SHA256 sums sourced from upstream
  `https://github.com/open-policy-agent/regal/releases/download/v0.40.0/checksums.txt`
  on 2026-05-01:
  - `regal_Linux_x86_64`: `0301464f1b2ea4e2458cec63cdde4557db09bcbe47505a7bbbfe6bf47aeab234`
  - `regal_Linux_arm64`: `af9c2e76a6422628eb82cc228e259cf45e48934eb14c24558d8a7302b085fd99`
  - `regal_Darwin_x86_64`: `36e20a41743244e50bac95f649153d36c006d26ede4c2aceccd4f52675af36da`
  - `regal_Darwin_arm64`: `84a3685d4064acdcf7cf8d32ca3e92e5ba99d2d217e8ea018d5f249562d1ab8c`

- [x] **(ii) Tool-versions entry.** `regal 0.40.0` added to
  `scripts/.tool-versions` so the workflow reads version + SHA256
  from a single source of truth (matching OPA + Conftest pattern).

- [x] **(iii) Workflow verify.** `policy-check.yml` swapped the
  hardcoded `REGAL_VERSION="0.40.0"` for `read_tool_version regal`,
  added `REGAL_SHA256="$(read_lockfile_field regal "${PLATFORM_KEY}" sha256)"`,
  added a new `resolve_regal()` helper symmetric with `resolve_opa()`,
  and replaced the unverified `curl ... regal` block with
  `REGAL_SOURCE="$(resolve_regal)"; cp ...`. The runtime smoke test
  (`regal version`) is preserved as defense-in-depth against an
  SHA-passing-but-corrupt binary.

- [x] **(iv) Vendor-fallback parity.** `resolve_regal()` checks
  `vendor/regal/${REGAL_ASSET}` if the curl download fails, matching
  OPA's vendor fallback pattern. The vendor directory does not yet
  contain Regal binaries (`vendor/python/` only); the fallback is
  forward-compat infrastructure for offline / network-restricted
  CI environments.

- [x] **(v) Fail-closed semantics.** `emit_infra_failure` on every
  resolve failure with `SCP-E001` annotation (matches the OPA +
  Conftest pattern). The `--input -` payload-construction style is
  not relevant here — this is a binary download path.

## Out-of-scope (deferred)

- **Sigstore attestation soft-warn.** OPA gets a soft-warn via
  `gh attestation verify` (HTTP 404 today since OPA v1.x has not
  published attestations). Regal is published via OPA's pipeline
  and almost certainly has the same gap. Not adding the soft-warn
  here keeps the slice minimal; folds into TF-007 (re-tighten
  Sigstore when OPA upstream begins publishing).

- **`gh attestation verify` for Regal.** Same rationale.

- **Vendor binaries on disk.** `resolve_regal()` references
  `vendor/regal/${REGAL_ASSET}` but the directory does not exist
  today. Adding actual vendored binaries is a separate decision
  about offline-CI support; out-of-scope for this slice.

## Why this is `020H.2` (not `020H part 4`)

SCP's slice naming convention:
- `020H part N` — pre-Threshold-A v1.0.0-cut sequence (`020H part 1`,
  `020H part 2`, `020H part 3` all merged before / at v1.0.0).
- `020H.N` — post-Threshold-A follow-up sub-series (`020H.1` =
  VERSIONING.md + rule-RFC + rollback-detection cron;
  **`020H.2` = this slice, Regal SHA256 verification**).

The dot-N notation was clarified in ADOPT-001 §12.7.13 + DISPATCH-NOTE
fix-round-5 for the 020H part 3 slice.

## STATUS.md update — landed in-PR + post-merge backfill

This PR's diff carries the following STATUS.md updates (THREE
sections — corrects the "TWO places" miscount flagged by 020H.2
R1 COR-nit-001):

1. **Tracked-forward items from 020H part 3**: TF-020H3-001
   marked ✅ closed in 020H.2.
2. **Open scheduled follow-ups**: TF-020H3-001 2026-05-14 row
   removed (deadline now closed).
3. **Post-Threshold-A backlog**: **020H part 3** marked ✅ landed
   (PR #75, commit `347fde2`, deferred from 020H pt 3 DISPATCH-NOTE
   since the merge SHA was not knowable until merge); **020H.2**
   marked **IN FLIGHT (this PR's branch)**.

**Post-merge backfill (one remaining structural deferral).** The
020H.2 "landed" record (PR # + commit SHA) cannot be written
pre-merge since the squash SHA is not yet known (R1 COR-nit-003).
Carrier: the **next opened slice on main** (020H.1 — VERSIONING.md,
or SCP-073.sec — SECURITY.md publication, whichever opens first).
The carrier slice's first commit MUST update STATUS.md line ~124
to strike-through `020H.2` and append `✅ landed <date> (PR #N,
commit <sha>)`, mirroring the 020H part 3 entry. The DISPATCH-NOTE
of whichever slice opens first will name this backfill explicitly
in its acceptance checklist (closes 020H.2 R1 COMP-MIN-002).

This is the same pattern 020H part 3 used (its merge-SHA backfill
landed in 020H.2's first commit at `STATUS.md` line 122).

## R1 review

3× parallel Sonnet R1 review (correctness / safety_bypass /
completeness_governance) on the post-edit state. Recurse to
fixpoint per `feedback_recursive_adversarial_review.md`.

## Files

- `scripts/.tool-versions` — `regal 0.40.0` added.
- `scripts/scp-policy-check.lock` — `regal` block added.
- `.github/workflows/policy-check.yml` — REGAL_VERSION / REGAL_SHA256 / resolve_regal / SHA256-verified Regal download.
- `STATUS.md` — TF-020H3-001 closure + scheduled-follow-up deletion + 020H pt 3 + 020H.2 backlog mark.
- `docs/reviews/WP-SCP-022/dispatches/020h2/DISPATCH-NOTE.md` — this file.
