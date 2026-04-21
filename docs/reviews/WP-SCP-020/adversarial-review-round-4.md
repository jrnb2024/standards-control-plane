# WP-SCP-020 — Adversarial review round 4

**Date:** 2026-04-21
**Plan version reviewed:** v0.4
**Reviewers:** single combined architect + security + governance + devex reviewer (round-3 reviewers converged tightly; single-reviewer fixpoint check is proportionate; if a new BLOCKING surfaces, round 5 reopens with parallel reviewers).
**Outcome:** RETURN TO v0.5. One genuine NEW-BLOCKER (regex mismatch) + one MAJOR (020K personal-account path ambiguity). Both single-line fixes.

---

## Round-3 verification table

| Finding | Grade | Reason if not clean |
|---|---|---|
| BLOCKING 1 — `scp_bypass` mechanism (F1 + N-2) | **NEW-BLOCKER** | `verify-bypass-pairing.sh` regex `^### D-0[0-9]{3}\s+\(20[0-9]{2}-` does not match actual D-NNN shape in `docs/DECISIONS.md` — which is a pipe-delimited table row (`\| D-0NN \| YYYY-MM-DD \|`), not a `###` heading. Script will always refuse with SCP-E004. Break-glass non-operational. |
| BLOCKING 2 — SCP-E005 unblock path (F2 + N-3) | **FIXED** | Separate-PR fixture-update flow is coherent; bus-factor-1 honestly declared in §8 with escalation + 2026-07-21 review. |
| MAJOR N-4/F3 — Renovate marker | **FIXED** | `datasource=github-tags` is correct for SHA-pin-plus-tag-comment (tracks repo tags; `github-actions` datasource requires `@v*` literal ref). Marker is inert without matching regex-manager block, but that lives in Renovate preset (020F). Acceptable. |
| MAJOR N-5/F4 — linux-arm64 | **FIXED** | `ubuntu-24.04-arm` runner name correct; Dependabot watch on `scripts/.tool-versions` added. |
| MAJOR F5 — SCP-R-003 disambiguation | **FIXED** | "Every manifest in changed-file set" + SCP-E006 zero-manifest record unambiguous. |
| MAJOR F6 — weekly cron | **FIXED** | `"0 9 * * MON"` UTC fine (GH Actions default). |
| MINOR N-6 — precondition phrasing | **FIXED**. |

## New-BLOCKER scrutiny on v0.4-specific bits

- **Slice 020K actionability.** GitHub teams require an **organization** account; `jrnb2024`'s namespace type is not declared in the plan. Free orgs support teams (since 2019); personal accounts cannot create teams. If `jrnb2024` is genuinely a personal user account, 020K(a) is unexecutable. The plan hedges with "single-operator-mode note" as alternative in 020K(c) — escape hatch saves the slice, but ambiguity should be nailed down. **Soft NEW-BLOCKER / hard MAJOR.** One-line fix: 020K must explicitly branch on namespace type.
- **`verify-bypass-pairing.sh` regex.** **Confirmed broken.** Primary NEW-BLOCKER.
- **§8 bus-factor acceptance.** Honest, not hiding. Named risk, named escalation, dated review. Real plan decision.
- **Renovate datasource.** `github-tags` correct.
- **Cron UTC.** Fine.

## Fixpoint declaration

**RETURN TO v0.5** on:

1. **BLOCKING (regex mismatch).** Correct `verify-bypass-pairing.sh` regex to match pipe-row shape `^\|\s*D-0[0-9]{3}\s*\|\s*20[0-9]{2}-[0-9]{2}-[0-9]{2}\s*\|` — verified against current `docs/DECISIONS.md` shape.
2. **MAJOR (020K branching).** Branch 020K on namespace type: org path creates team; personal-account path skips team creation. James confirms namespace type alongside U-sec-2 at plan merge.

Both single-line edits. Round 5 should confirm fixpoint on v0.5.
