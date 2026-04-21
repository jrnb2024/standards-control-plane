# WP-SCP-020 — Adversarial review round 3

**Date:** 2026-04-21
**Plan version reviewed:** v0.3
**Reviewers (parallel):** Reviewer A (architect + security), Reviewer B (governance-realist + devex/BS-hunting)
**Outcome:** RETURN TO v0.4. Round-2 BLOCKINGs confirmed fixed; two new BLOCKINGs + four new MAJORs surfaced, all word-level tightenings (mechanism-naming gaps in the newly-added governance surfaces).

---

## Reviewer A (architect + security)

### Round-2 BLOCKING verification

| # | Round-2 BLOCKING | Grade |
|---|---|---|
| A-N1 Conflict-gate adapter + fixture path | **FIXED** |
| A-N2 Slice-ordering self-contradictory | **FIXED** |
| A-N3 Unknowns leak past plan merge | **FIXED** (U-sec-2 cleanly scoped as §14; §13 closes others) |
| A-N4 / B-BS-2 `scp_bypass` access control | **FIXED** in principle — see new N-2 |
| B-BS-1 / A-N5 Python-authoritative non-operational | **FIXED** (disagreement fails closed + SCP-E005) |
| B-BS-3 ≤ 12-line wrapper arithmetic | **FIXED** (literal YAML in plan; no count claim) |

All round-2 MAJORs cleanly folded.

### New findings from v0.3

- **[NEW MAJOR] N-2** 020B(viii-c) gate (2) enforceability ambiguous. Workflow CAN grep `git diff base..HEAD` for D-NNN + waivers.json entry, but plan doesn't name the script or regex. Same class as round-2 BS-2. Fix: 020B(viii-c) names `scripts/verify-bypass-pairing.sh` with regex; refuses on miss.
- **[NEW MAJOR] N-3** "or named approver" in 020C.1(iv) bus-factor-1. One-line fix: name approver set as `SCP-CODEOWNERS`.
- **[NEW MAJOR] N-4** Renovate SHA-pin marker unspecified. Wrapper has `@<commit-SHA>` + `# tag: v1.0.0` but no `# renovate: datasource=github-tags depName=…`. Without the marker in the canonical wrapper, adopters who copy-paste get zero Renovate tracking. Fix: 020H(part 3) YAML block includes Renovate regex-manager marker.
- **[NEW MAJOR] N-5** `scripts/scp-policy-check.lock` missing linux-arm64 (GitHub `ubuntu-24.04-arm` runners GA). Fix: 020B.2(ii) adds linux-arm64.
- **[NEW MINOR] N-6** 020J precondition phrasing conflates "plan-merge-blocking" with "slice-opening-precondition." Editorial fix: "U-sec-2 resolved at plan merge (§14)."
- **[NEW MINOR] N-1** 14-line wrapper actually 12 non-comment lines. Non-blocking.

### Fixpoint declaration

**RETURN TO v0.4** on N-2, N-3, N-4, N-5. Four word-level fixes. Estimated <30 min to land.

---

## Reviewer B (governance-realist + devex, BS-hunting)

### Round-2 verification

Round-2 findings fixed cleanly EXCEPT the `scp_bypass` gate model — which fixed the rules but not the mechanism. Similar class to the conflict-gate non-operationality caught in round 2.

### New findings from v0.3

- **[BLOCKING] F1** Three-gate `scp_bypass` is a null gate in the single-operator estate.
  - Gate 1 names `scp-break-glass` GitHub team with no statement that the team exists or will be created. Solo maintainer ⇒ self-approval allowed unless `require_review_from_non_author=true` is set.
  - Gate 2 "sibling commit in same PR" is on trust — workflow doesn't parse the PR diff.
  - Fix v0.4: (a) create `scp-break-glass` team explicitly or accept bus-factor-1 in §8; (b) 020D2 acceptance includes `required_approving_review_count=1` + `dismiss_stale_reviews` + `require_review_from_non_author`; (c) 020B(viii-c) Gate 2 validates D-NNN line-presence in diff + cross-refs `waivers.json.rule_id` at run time.

- **[BLOCKING] F2** SCP-E005 has no documented unblock path. "James (or named approver)" = bus factor 1. On SCP-E005, what does the PR author DO to unblock?
  - Fix v0.4: 020C.1(iii) prose — amending D-NNN lands in a *separate* PR that updates `tests/conflict_gate/fixtures/<rule>/<scenario>/expected-verdict.json`; original PR rebases. Name at least one backup approver OR document bus-factor-1 in §8 as accepted operational risk.

- **[MAJOR] F3** 14-line wrapper has no Renovate marker. (≡ A N-4)
- **[MAJOR] F4** Lock missing linux-arm64. (≡ A N-5)
- **[MAJOR] F5** SCP-R-003 manifest-marker ambiguity — "at least one" vs "all present must have marker"? Fix: "for every manifest file present in the changed-file set, marker required; repos with zero manifests return allow + SCP-E006 `no-manifest-applicable` observability record."
- **[MAJOR] F6** Post-release rollback detection has no cron. A bad release that passes release-canary but breaks downstream silently is invisible until workflow-selftest is next triggered. Fix: 020H.1(iv)(e) weekly scheduled workflow in SCP self replays canaries against `@main` + `@v1.*`; diverging result opens issue.
- **[MINOR] F7** Disabled-rules read-back is write-only until WP-SCP-023. Commit-status line is fine. Optional nice-to-have: `scripts/scp-report-disabled-rules`.

### Fixpoint declaration

**RETURN TO v0.4** on F1, F2 (BLOCKING). Fold F3–F6 (MAJOR). F7 optional.

---

## Round-3 consolidation

**2 unique BLOCKINGs (after dedup A-N2/N-3 ≈ B-F1/F2 on mechanism-naming):**

| # | Finding | v0.4 fix |
|---|---|---|
| 1 | `scp_bypass` three-gate enforcement is words not mechanism (F1 + N-2) | New slice 020K: `scp-break-glass` team created OR bus-factor-1 accepted; 020D2 adds branch-protection flags `require_review_from_non_author` + `required_approving_review_count=1` + `dismiss_stale_reviews`; 020B(viii-c) adds `scripts/verify-bypass-pairing.sh` with concrete regex for D-NNN + `waivers.json.rule_id` matching; workflow step `bypass-gate` invokes it and fails closed on miss. |
| 2 | SCP-E005 unblock path + bus-factor (F2 + N-3) | 020C.1(iii) prose: amending D-NNN → separate PR → updates fixture expected-verdict → original PR rebases. Named approver set = `SCP-CODEOWNERS` (solo today = James only; §8 accepts bus-factor-1 operational risk with escalation path to second approver if estate grows). |

**4 MAJORs:**

| # | Finding | v0.4 fix |
|---|---|---|
| N-4 / F3 | Renovate marker missing in wrapper | 020H(part 3) wrapper block includes `# renovate: datasource=github-tags depName=jrnb2024/standards-control-plane` above the `uses:` line. |
| N-5 / F4 | linux-arm64 missing | 020B.2(ii): add linux-arm64; Dependabot/Renovate entry for `scripts/.tool-versions`. |
| F5 | SCP-R-003 ambiguity | 020C: "for every manifest file present in changed-file set; zero-manifest repos return allow + SCP-E006." |
| F6 | No scheduled post-release canary replay | 020H.1(iv): new clause (e) weekly scheduled workflow-dispatch in SCP self replays `canary/deliberate-violation-pre|post|waived` against released `@main` + `@v1.*`; opens issue on divergence. |

**1 MINOR:** N-6 phrasing fix in 020J precondition text.

**Non-blocking observations:** N-1 (line count), N-7 (canary mandatoriness), F7 (disabled-rules optional script).

v0.4 should land in one focused edit round; round-4 expected to confirm fixpoint.
